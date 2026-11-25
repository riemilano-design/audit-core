# -*- coding: utf-8 -*-
u"""便 XC0: 今年の答え(今年の XBRL)を見ずに、素の本文と前の年の XBRL だけから、表の中の数の fact を属性つきで置き、元と照らす。

軽い型(CLAUDE.md 作法 7)。engine は読むだけ(``_TR_RE``・``_row_label``)。前の便の measure/ の script は読み込んで関数を呼ぶだけ(写さない・変えない)。
今年の側から組む部品に渡すのは、今年の ``.htm`` から ix のタグを剥がした素の本文だけ。今年の表 F・表 H は採点にだけ使う。
"""
import bisect
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEAS = os.path.join(ROOT, "measure")
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)


def _load(name, fname):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(MEAS, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("_xc0_guard", "xbrl_prior_year_fact_guard_2026-11-22.py")   # 便 XZ1(XZ0・XY0・XG1・XG0 を読む)
Z, Y, N, W = G.Z, G.Y, G.N, G.W
I = Z.I
HP = _load("_xc0_place", "xbrl_place_context_build_2026-11-22.py")    # 便 XH0(置き場の規則)
X = _load("_xc0_wall", "xbrl_sheet_wall_2026-11-22.py")               # 便 XA0(符号の字)
B = _load("_xc0_inline", "xbrl_inline_build_2026-11-21.py")           # 便 XB0(剥がす・組む)

od = collections.OrderedDict
SEEN_MAX_NO = 3                     # 番号 3 以下の組は訓練(規則を作るのに見た)。判定は残りの 60 組だけ
CELL_RE = re.compile(r"<t[dh]\b", re.I)
TAG_RE = re.compile(r"<[^>]*>")
DIGIT_RE = re.compile(r"[0-9]")
FULL = ("name", "contextRef", "unitRef", "decimals", "scale", "format", "sign")
CLASSES = ("一致", "黙って違う", "止めた", "置かない")


class Stop(Exception):
    pass


# ======================================================================================================
# 素の本文の行と cell(今年の側も前の年の側も同じ切り方)
def plain_cells(plain):
    u"""素の本文 → [(行の番号, cell の中身の始まり, 終わり, td)]。行は engine の ``_TR_RE``。cell は便 XH0 の ``cells_of``。
    td は行の頭から cell の中身の始まりまでの ``<td``・``<th`` の数(便 XZ0 の ``read_rows`` の数え方と同じ)。"""
    rows = [(m.start(), m.end()) for m in I._TR_RE.finditer(plain)]
    starts = [s for s, _e in rows]
    out = []
    for _t, _r, _c, cs, ce in HP.cells_of(plain):
        k = bisect.bisect_right(starts, cs) - 1
        while k >= 0 and not (rows[k][0] <= cs < rows[k][1]):
            k -= 1
        if k < 0:
            continue
        td = len(CELL_RE.findall(plain[rows[k][0]:cs]))
        out.append((k, cs, ce, td))
    return out


def row_keys(plain):
    u"""素の本文 → 行ごとの (h, th, T)(便 XZ0 の ``read_rows`` と同じ決め方。見出しは便 XG1 の ``file_rows`` がタグを除いた字で探す)。"""
    matches = list(I._TR_RE.finditer(plain))
    frows = N.file_rows(plain)
    starts = [m.start() for m in Z.TABLE_RE.finditer(plain)]
    seen, out = {}, []
    for m, (rowtext, head) in zip(matches, frows):
        h = Z.norm_label(head) if head is not None else None
        serial = bisect.bisect_left(starts, m.start())
        ranks = seen.setdefault(h, {})
        if serial not in ranks:
            ranks[serial] = len(ranks)
        label = I._row_label(rowtext)
        out.append((h, ranks[serial], Z.norm_label(label) if label else u"", serial))
    return out


def predicted(plain, cells):
    u"""cell ごとの規則の置き場(便 XH0 の ``predict_cell``。空の fact は自己閉じにしない)→ {cell の番号: [(start, end)]}。"""
    out = {}
    for i, (_k, cs, ce, _td) in enumerate(cells):
        p = [(cs + s, cs + e) for s, e, _sf in HP.predict_cell(plain[cs:ce], False)]
        if p:
            out[i] = p
    return out


def head_marks(plain, cells, pred, keys):
    u"""表ごとの頭の印: 表の行のうち、規則が数を置く cell を持つ最初の行より前の行の字(タグ・数字を除き norm_label)。"""
    rows = [(m.start(), m.end()) for m in I._TR_RE.finditer(plain)]
    hasnum = set(cells[i][0] for i, p in pred.items() if any(s < e for s, e in p))
    by_ser = collections.defaultdict(list)
    for k, key in enumerate(keys):
        by_ser[key[3]].append(k)
    marks = {}
    for ser, ks in by_ser.items():
        head = []
        for k in ks:
            if k in hasnum:
                break
            head.append(plain[rows[k][0]:rows[k][1]])
        marks[ser] = u"|".join(DIGIT_RE.sub(u"", Z.norm_label(TAG_RE.sub(u"", t))) for t in head)
    return marks


# ======================================================================================================
# 前の年の表(前の年の答えだけを読む)
def prior_table(prior_files):
    u"""前の年の [(名, plain, F, H)] → (表: (h, th, T, td) → {属性の組}・頭の印: (h, th, T, td) → {印})。
    行の鍵は前の年の素の本文から作る(今年の側と同じ切り方)。fact の属性は前の年の表 F から。"""
    tab, sig = {}, {}
    for _name, plain, F, _H in prior_files:
        cells = plain_cells(plain)
        keys = row_keys(plain)
        pred = predicted(plain, cells)
        marks = head_marks(plain, cells, pred, keys)
        cstarts = [c[1] for c in cells]
        for e in F:
            if e["kind"] != "nonFraction":
                continue
            j = bisect.bisect_right(cstarts, e["start"]) - 1
            while j >= 0 and not (cells[j][1] <= e["start"] and e["end"] <= cells[j][2]):
                j -= 1
            if j < 0:
                continue
            k, _cs, _ce, td = cells[j]
            h, th, T, ser = keys[k]
            if not T:
                continue
            a = e["attrs"]
            nil = a.get("xsi:nil") == "true"
            tup = (a.get("name"), a.get("contextRef"), a.get("unitRef"), None if nil else a.get("decimals"),
                   None if nil else a.get("scale"), None if nil else a.get("format"), nil)
            tab.setdefault((h, th, T, td), set()).add(tup)
            sig.setdefault((h, th, T, td), set()).add(marks.get(ser, u""))
    return tab, sig


# ======================================================================================================
# 今年の側に置く(今年の答えは読まない)
def place(plain, tab, sig):
    u"""今年の素の本文 → (置いた fact [(start, end, 属性)]・止めた置き場 [(start, end, 理由)]・置かない置き場の数)。"""
    cells = plain_cells(plain)
    keys = row_keys(plain)
    pred = predicted(plain, cells)
    marks = head_marks(plain, cells, pred, keys)
    put, stop, skip = [], [], 0
    for i, spans in sorted(pred.items()):
        k, cs, _ce, td = cells[i]
        h, th, T, ser = keys[k]
        for s, e in spans:
            nil = s == e
            cands = tab.get((h, th, T, td), set()) if T else set()
            if not cands:
                skip += 1
                continue
            if marks.get(ser, u"") not in sig.get((h, th, T, td), ()):
                stop.append((s, e, u"表の頭の字が前の年と違う"))
                continue
            b3 = set(c[:3] for c in cands)
            if len(b3) != 1:
                stop.append((s, e, u"前の年の候補が 2 つ以上"))
                continue
            name, ctx, unit = next(iter(b3))
            a = od([("name", name), ("contextRef", ctx), ("unitRef", unit)])
            if nil:
                a["xsi:nil"] = "true"
            else:
                rest = set(c[3:6] for c in cands if not c[6])
                if len(rest) != 1:
                    stop.append((s, e, u"前の年の桁・書式が 1 つに決まらない"))
                    continue
                dec, scale, fmt = next(iter(rest))
                a["decimals"], a["scale"], a["format"] = dec, scale, fmt
                if X.reads_negative(B_strip(plain[cs:s])):
                    a["sign"] = "-"
            put.append((s, e, a))
    return put, stop, skip


def B_strip(s):
    return TAG_RE.sub(u"", s)


# ======================================================================================================
# 文脈・単位の定義(前の年の定義の日付を 1 年ずらす)
def shift_date(s, years=1):
    y, m, d = (int(x) for x in s.split("-"))
    try:
        return datetime.date(y + years, m, d).isoformat()
    except ValueError:                               # 2 月 29 日
        return datetime.date(y + years, m, 28).isoformat()


def shift_resources(prior_H):
    u"""前の年の表 H の文脈と単位 → {id: 定義}。文脈の期の日付を 1 年後にする。提出者の字・メンバーはそのまま。"""
    out = {}
    for r in prior_H["resources"]:
        if r["type"] == "context":
            c = json.loads(json.dumps(r))
            c["period"] = [[k, shift_date(v) if v else v] for k, v in r["period"]]
            out[r["id"]] = c
        elif r["type"] == "unit":
            out[r["id"]] = json.loads(json.dumps(r))
    return out


def same_resource(a, b):
    u"""定義が同じか。メンバーの並びの順は問わない(XBRL では順に意味が無い)。"""
    keys = ("type", "scheme", "ident", "period", "members", "has_scenario", "measures", "numerator", "denominator")

    def norm(r):
        d = json.loads(json.dumps(od((k, r.get(k)) for k in keys if k in r)))
        if d.get("members"):
            d["members"] = sorted(d["members"])
        return d
    return norm(a) == norm(b)


# ======================================================================================================
# 採点(今年の答えはここでだけ読む)
def compare(a_ans, a_put):
    u"""属性の比べ: 欄 FULL と空の fact か。違う欄の名の並び。"""
    diff = [k for k in FULL if (a_ans.get(k) or None) != (a_put.get(k) or None)]
    if (a_ans.get("xsi:nil") == "true") != (a_put.get("xsi:nil") == "true"):
        diff.append("nil")
    return diff


def score_pair(cur_zip, prior_zip):
    cur = B.build_files(B.load_package(cur_zip))
    prv = B.build_files(B.load_package(prior_zip))
    tab, sig = prior_table(prv)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    cur_H = next((H for _n, _p, _F, H in cur if H is not None), None)
    res = shift_resources(prior_H) if prior_H else {}
    acc = od([("答えの数の fact", 0), ("うち表の cell の中", 0), ("一致", 0), ("黙って違う", 0), ("止めた", 0), ("置かない", 0),
              ("余計に置いた", 0), ("置いた", 0), ("違う欄", collections.Counter()), ("止めた理由", collections.Counter()),
              ("置かない cell の数", 0),
              ("使った文脈", 0), ("使った文脈の定義が元と同じ", 0), ("使った単位", 0), ("使った単位の定義が元と同じ", 0),
              ("組んだ file", 0), ("組み直しで置いた fact が戻った file", 0)])
    used_ctx, used_unit = set(), set()
    for name, plain, F, _H in cur:
        put, stop, skip = place(plain, tab, sig)
        acc["置かない cell の数"] += skip
        acc["置いた"] += len(put)
        P = dict(((s, e), a) for s, e, a in put)
        S = dict(((s, e), why) for s, e, why in stop)
        cells = plain_cells(plain)
        cst = [c[1] for c in cells]
        hit = set()
        for e in F:
            if e["kind"] != "nonFraction":
                continue
            acc["答えの数の fact"] += 1
            j = bisect.bisect_right(cst, e["start"]) - 1
            inside = j >= 0 and cells[j][1] <= e["start"] and e["end"] <= cells[j][2]
            if inside:
                acc["うち表の cell の中"] += 1
            key = (e["start"], e["end"])
            if key in P:
                hit.add(key)
                d = compare(e["attrs"], P[key])
                if d:
                    acc["黙って違う"] += 1
                    acc["違う欄"]["+".join(d)] += 1
                else:
                    acc["一致"] += 1
            elif key in S:
                acc["止めた"] += 1
                acc["止めた理由"][S[key]] += 1
            else:
                acc["置かない"] += 1
        acc["余計に置いた"] += sum(1 for k in P if k not in hit)
        for s, e, a in put:
            used_ctx.add(a["contextRef"])
            if a.get("unitRef"):
                used_unit.add(a["unitRef"])
        # 組む: 置いた fact だけの表 F で .htm を組み、剥がし直して戻るか
        F2 = [od([("kind", "nonFraction"), ("self", False), ("start", s), ("end", e), ("parent", -1),
                  ("attrs", od((k, v) for k, v in a.items() if v is not None))]) for s, e, a in sorted(put, key=lambda q: (q[0], q[1]))]
        acc["組んだ file"] += 1
        try:
            text = B.build_text(plain, F2, None)
            p2, F3, _H3 = B.strip_text(text)
            back = p2 == plain and [(f["start"], f["end"], dict(f["attrs"])) for f in F3] == [(f["start"], f["end"], dict(f["attrs"])) for f in F2]
        except Exception:                                   # noqa: BLE001
            back = False
        if back:
            acc["組み直しで置いた fact が戻った file"] += 1
    if cur_H:
        ans = dict((r["id"], r) for r in cur_H["resources"] if r["type"] in ("context", "unit"))
        for c in used_ctx:
            acc["使った文脈"] += 1
            if c in res and c in ans and same_resource(res[c], ans[c]):
                acc["使った文脈の定義が元と同じ"] += 1
        for u in used_unit:
            acc["使った単位"] += 1
            if u in res and u in ans and same_resource(res[u], ans[u]):
                acc["使った単位の定義が元と同じ"] += 1
    acc["違う欄"] = od(sorted(acc["違う欄"].items()))
    acc["止めた理由"] = od(sorted(acc["止めた理由"].items()))
    return acc


def pairs():
    _docs, ps, _ex = Y.make_pairs(Z.DOCS_DIR, Z.PRIOR_DIR, Z.DOCS_WANT, 63)
    return [(n, p, pp) for n, _s, p, _ps, pp, _c in ps]


if __name__ == "__main__":
    which = sys.argv[1]
    out = []
    for n, p, pp in pairs():
        if which == "train" and n > SEEN_MAX_NO:
            continue
        if which == "judge" and n <= SEEN_MAX_NO:
            continue
        a = score_pair(p, pp)
        out.append(od([("番号", n)] + list(a.items())))
        print(n, json.dumps(a, ensure_ascii=False)[:400], flush=True)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
