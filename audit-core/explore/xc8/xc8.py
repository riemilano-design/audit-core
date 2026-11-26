# -*- coding: utf-8 -*-
u"""便 XC8: 便 XC7 の席の札を、要素の名をタクソノミで引いて確かめ(T1)、組んだ包みに入れて道具 P に読ませる(T2)。

T1 名の確かめ: 標準の前置き(`jp…_cor`)の要素は、EDINET タクソノミ 2025-11-01 の `*_cor_*.xsd` に同じ名の要素の定義が在る物だけ通す。
   提出者の要素は便 XC7 のとおり今年の提出者の xsd に在る物だけ。文脈・単位は便 XC7 のとおり。
T2 包みに入れる: 通った札を、規則で置いた数の fact と同じ形(空でない升は format=ixt:numdotdecimal、空の升は xsi:nil)で置き、
   便 XC6 の G1(無いメンバー)・G2(食い違う重なり)を規則の札と合わせて掛けてから、便 XC5 の組み方で包みを組む。
席の答えは便 XC7 で回した物をそのまま使う(席を回し直さない)。土台は便 XC7(画面・印)と便 XC6(組み方)。今年の答えは採点でだけ読む。
"""
import collections
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc8_xc7", os.path.join(os.path.dirname(HERE), "xc7", "xc7.py"))
X7 = importlib.util.module_from_spec(spec)
sys.modules["_xc8_xc7"] = X7
spec.loader.exec_module(X7)
C6, C5, C2, C1, C0, B = X7.C6, X7.C5, X7.C2, X7.C1, X7.C0, X7.B
od = collections.OrderedDict
TAX_ZIP = os.path.expanduser("~/.cache/audit-core/edinet-taxonomy-full/2025-11-01/1c_Taxonomy.zip")
COR_RE = re.compile(r"/taxonomy/([a-z-]+)/[0-9-]+/\1_cor_[0-9-]+\.xsd$")
NAME_RE = re.compile(r'<(?:xsd?:)?element\b[^>]*\bname="([^"]+)"')
STAT = collections.Counter()
SEATS = {}                       # 素の本文の字 → [(start, end, 札)]
_orig = C6._place3


def std_names():
    u"""タクソノミの `*_cor_*.xsd` → {前置き: 要素の名の集合}(前置きは `jppfs_cor` の形)。"""
    out = collections.defaultdict(set)
    with zipfile.ZipFile(TAX_ZIP) as z:
        for info in z.infolist():
            mm = COR_RE.search(info.filename)
            if not mm:
                continue
            text = z.read(info).decode("utf-8", "replace")
            out[mm.group(1).replace("-", "_") + "_cor" if "-" not in mm.group(1) else mm.group(1) + "_cor"] |= set(NAME_RE.findall(text))
    return out


def check_tag8(a, res, own, names):
    why = X7.check_tag(a, res, own)
    if why:
        return why
    pre, _c, local = (a.get("name") or u"").partition(":")
    if X7.STD_PREFIX_RE.match(pre) and local not in names.get(pre, ()):
        return u"要素がタクソノミに無い"
    return None


def as_fact(a, nil):
    u"""席の札 → 規則で置いた数の fact と同じ形の属性。"""
    if nil:
        return od([("name", a["name"]), ("contextRef", a["contextRef"]), ("unitRef", a.get("unitRef") or u""), ("xsi:nil", "true")])
    out = od()
    for k in ("name", "contextRef", "unitRef", "decimals", "scale", "sign"):
        if a.get(k) not in (None, u""):
            out[k] = str(a[k])
    out["format"] = "ixt:numdotdecimal"
    return out


def seat_tags(cur, prv, entries, answers, names, use_t1=True):
    u"""1 組の席の答え → SEATS(素の本文ごとの置く札)と数え。"""
    screens, marks, placed = X7.build_screen(cur, prv, entries)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    res = C0.shift_resources(prior_H)
    own = C6.OWN[0]
    plain_of = dict((nm, plain) for nm, plain, _F, _H in cur)
    SEATS.clear()
    c = collections.Counter()
    for mid, (nm, s, e, nil) in marks.items():
        a = answers.get(mid)
        if not a:
            continue
        why = check_tag8(a, res, own, names) if use_t1 else X7.check_tag(a, res, own)
        if why:
            c[u"形で落とした・" + why] += 1
            continue
        SEATS.setdefault(plain_of[nm], []).append((s, e, as_fact(a, nil)))
        c[u"席の札を置いた"] += 1
    return c, marks


def place_with_seats(plain, prior, res, rules):
    put, stop, skip, moved = _orig(plain, prior, res, rules)
    add = SEATS.get(plain, [])
    STAT[u"包みに渡した席の札"] += len(add)
    return sorted(put + add, key=lambda q: (q[0], q[1])), stop, skip, moved


def score_pair8(n, p, pp, answers, names, workdir, with_seats=True):
    entries = B.load_package(p)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(pp))
    C6.OWN[0] = C5.xsd_info(entries)[1]
    C2.place3 = lambda plain, prior, res, rules: C6.place3_g(plain, prior, res, rules)
    c, _marks = seat_tags(cur, prv, entries, answers, names)
    if not with_seats:
        SEATS.clear()
    STAT.clear()
    C6._place3 = place_with_seats
    try:
        acc = C6.score_pair(p, pp, workdir, ("G1", "G2"))
    finally:
        C6._place3 = _orig
        C2.place3 = _orig
    for k, v in sorted(c.items()):
        acc[k] = v
    acc[u"包みに渡した席の札"] = STAT[u"包みに渡した席の札"]
    return acc


def load_answers(base, head, n):
    out, k = {}, 0
    while os.path.exists(os.path.join(base, "%s%d_%d.json" % (head, n, k))):
        with open(os.path.join(base, "%s%d_%d.json" % (head, n, k)), encoding="utf-8") as f:
            out.update(json.load(f))
        k += 1
    return out


if __name__ == "__main__":
    which, base, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    with_seats = sys.argv[4] != "base" if len(sys.argv) > 4 else True
    dev, held = C1.split()
    nums = {"dev": [1, 2, 3], "held": [25, 26, 27, 28]}[which]
    head = {"dev": "d", "held": "h"}[which]
    names = std_names()
    rows = []
    for n, p, pp in [x for x in dev + held if x[0] in nums]:
        wd = tempfile.mkdtemp(prefix="xc8_")
        try:
            a = score_pair8(n, p, pp, load_answers(base, head, n), names, wd, with_seats)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        rows.append(od([(u"番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not isinstance(v, (dict, list))), ensure_ascii=False), flush=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
