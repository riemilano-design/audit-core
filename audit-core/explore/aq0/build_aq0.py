# -*- coding: utf-8 -*-
"""便 AQ0: RD2 で照合が止めた行と資料の決めを、1 社 1 枚の画面(HTML)に組む(封 explore/aq0/SEAL.md §2)。

使い方: python3 -I build_aq0.py <explore の folder> <RD2 の根> <AQ0 の根>
<AQ0 の根>/O/ と F/ に screen{n}.html(席に渡す画面)と key{n}.json(問いと値の対応。集計だけが読む)を書く。
止めた行の選びは RD2 の集計と同じ照合(S1〜S9)で決め、正解は読まない(正解は集計の時だけ)。
"""
import csv
import html
import json
import os
import re
import sys

EXPLORE, RD2, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = ["", EXPLORE, RD2, os.devnull]
sys.path.insert(0, os.path.join(EXPLORE, "rd2"))
sys.path.insert(0, os.path.join(EXPLORE, "rd0"))
import tally_rd2  # noqa: E402  (会社の番号 31〜41 を据える)

R = tally_rd2.R
V, tally_sv10, tally_sv2 = R.V, R.tally_sv10, R.tally_sv2
UNIT = {"円": 1, "千円": 1000, "百万円": 1000000}
FIXED = {  # 照合の字を言い換えた決まった文(S8・S9 は席の訳を出す)
    "S1": "出どころの数を足しても、埋めた値になりません。",
    "S7": "出どころが、数を貯める扱いでない資料の数です。",
    "S2": "出どころの行に、いつの数か(期)が付いていません。",
    "S3": "出どころの行の期が、求める期と合いません。",
    "S4": "出どころの行の単位が、項目の単位と合いません。",
    "S5": "出どころの行が実績の数ではありません(予算・見込みなど)。",
    "S6": "出どころの行が、会社全体の数ではありません(一部の数)。",
}
WORD = {"期末の従業員数": "従業員数"}  # 項目の言葉(行の見出しに含むかで候補を探す)
NOT_CAND = ("1株", "１株", "率", "比率")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def rows_of(n):
    with open(os.path.join(RD2, "r1", "store" + n, "貯め.csv"), encoding="utf-8") as f:
        return {int(r["番号"]): r for r in csv.DictReader(f)}


def num(s):
    t = str(s).replace(",", "").replace("△", "-").replace("▲", "-").strip()
    try:
        return int(t)
    except ValueError:
        return None


def yen(r):
    v = num(r.get("値"))
    if v is None:
        return None
    return v * UNIT.get(r.get("単位") or "", 1)


def fmt(v, unit):
    return "%s %s" % ("{:,}".format(v), unit)


def row_text(r):
    return "表 %s ・ 行「%s」 ・ 列「%s」 ・ 期 %s ・ %s %s" % (
        r.get("表"), r.get("行の見出し"), r.get("列の見出し"), r.get("期") or "(なし)",
        r.get("値"), r.get("単位") or "")


def mark_reason(marks, src):
    name = os.path.basename(src["file"])
    for m in marks:
        if os.path.basename(str(m.get("file"))) == name and src["行"] in (m.get("行") or []) \
                and (not m.get("列") or src["列"] in m["列"]):
            return "読み違えやすい数の印が付いています: " + str(m.get("訳") or "")
    return "読み違えやすい数の印が付いています。"


def stopped(n):
    """RD2 の照合が止めた 16 項目の行: [(項目, 理由の文)]。"""
    co = V.SetCompany(os.path.join(RD2, "r1", "conv"), n)
    marks = tally_sv10.load(os.path.join(RD2, "r4", "merged", "out" + n, "紛れ.json"))["印"]
    asks = {x["項目"]: x.get("訳") or "" for x in load(os.path.join(RD2, "ask", "out" + n, "聞く.json"))["項目"]
            if x.get("聞く") is True}
    out = []
    for item in R.SCOPE:
        a = co.answers.get(item) or {}
        v, src = a.get("値"), a.get("出どころ") or []
        if v is None:
            continue
        w = tally_sv2.judge(co, marks, item, v, src)
        if w is None and item in asks:
            w = "S9"
        if w is None:
            continue
        if w == "S9":
            why = "表の中に、この項目の候補が 2 つ以上あり、値が食い違います: " + re.sub(r"^強い理由\s*\d\s*[:：]\s*", "", asks[item])
        elif w == "S8":
            why = mark_reason(marks, src[0])
        else:
            why = FIXED.get(w, "照合が止めました。")
        out.append((item, why))
    return out


def candidates(item, filled_yen, src_rows, rows, period):
    word = WORD.get(item.split("_")[0], item.split("_")[0])
    used = {r["番号"] for r in src_rows}
    seen, same, other = {filled_yen}, [], []
    for k in sorted(rows):
        r = rows[k]
        head = r.get("行の見出し") or ""
        if word not in head or any(x in head for x in NOT_CAND) or r["番号"] in used:
            continue
        if item.startswith("期末の従業員数") != ((r.get("単位") or "") == "人"):
            continue
        y = yen(r) if (r.get("単位") or "") != "人" else num(r.get("値"))
        if y is None or y in seen:
            continue
        seen.add(y)
        (same if (r.get("期") or "") in ("", period) or period in (r.get("期") or "") else other).append((y, r))
    return (same + other)[:6]


def decisions(rows, period):
    """A の問い: (a) 範囲 と (b) 当期純利益の読み(出す時だけ)。"""
    cons = sum(1 for r in rows.values() if "連結" in (r.get("行の見出し") or "") + (r.get("列の見出し") or ""))
    qs = [{"問い": "A1", "種類": "範囲", "連結の行": cons, "案": "連結" if cons else "単体"}]
    parent, total = [], []
    for k in sorted(rows):
        r = rows[k]
        h = r.get("行の見出し") or ""
        if "当期純利益" not in h or any(x in h for x in NOT_CAND) or "非支配" in h:
            continue
        if period not in (r.get("期") or ""):
            continue
        y = yen(r)
        if y is None:
            continue
        (parent if "親会社株主" in h else total).append((y, r))
    if parent and total:
        p = parent[0]
        t = next((x for x in total if x[0] != p[0]), None)
        if t is not None:
            qs.append({"問い": "A2", "種類": "当期純利益", "親会社": p, "合計": t})
    return qs


CSS = """body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:10pt;line-height:1.6;max-width:200mm;margin:8mm auto;padding:0 4mm}
h1{font-size:15pt;margin:0 0 3mm}h2{font-size:12pt;margin:6mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}h3{font-size:10.5pt;margin:5mm 0 1.5mm}
table{border-collapse:collapse;width:100%;margin:2mm 0;font-size:9.5pt}th{background:#f3f5f9;text-align:left;width:28mm}th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}
.notice{border-left:1.2mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:0 0 5mm}.q{border:.3mm solid #d9dee8;padding:2mm 4mm;margin:3mm 0}
.choices{background:#f8f9fb;padding:1.5mm 3mm;margin-top:2mm}small{color:#51607a}"""


def choice(qid, opts):
    return '<div class="choices">選べるもの(問い %s): %s</div>' % (
        qid, " / ".join('<label><input type="radio" name="%s" value="%s"> %s</label>' % (qid, html.escape(v), html.escape(t)) for v, t in opts))


def build(n, ver):
    rows = rows_of(n)
    per = load(os.path.join(RD2, "co" + n, "正解", "期.json"))
    period = "%s〜%s" % (per["当期の始まり"], per["当期の終わり"])
    ans = {r["項目"]: r for r in load(os.path.join(RD2, "r1", "out" + n, "答え.json"))["行"]}
    body, key = [], {"会社": n, "版": ver, "問い": []}
    body.append('<h1>確かめてほしいこと ― 第 %s 社(当期 %s)</h1>' % (n, period))
    body.append('<div class="notice">機械が貯めた数から資料の項目を埋めました。作る前に決めてほしいこと(A)と、機械が自信を持てなかった項目(B)を並べています。問いごとに 1 つ選んでください。</div>')
    body.append("<h2>A. 資料の決め</h2>")
    for q in decisions(rows, period):
        if q["種類"] == "範囲":
            body.append('<div class="q"><h3>A1. 資料の数は、連結と単体のどちらで作りますか</h3><p>貯めた数のうち、見出しに「連結」を含む行は %d 行です。機械の案: <b>%s</b>。</p>%s</div>' % (
                q["連結の行"], q["案"], choice("A1", [("連結", "連結"), ("単体", "単体"), ("わからない", "わからない")])))
            key["問い"].append({"問い": "A1", "種類": "範囲", "案": q["案"]})
        else:
            (py, pr), (ty, tr) = q["親会社"], q["合計"]
            body.append('<div class="q"><h3>A2. 当期純利益は、どちらの数を使いますか</h3><table><tr><th>親会社株主に帰属する方</th><td>%s<br><small>%s</small></td></tr><tr><th>もう一方の「当期純利益」の行</th><td>%s<br><small>%s</small></td></tr></table>%s</div>' % (
                fmt(py, "円"), html.escape(row_text(pr)), fmt(ty, "円"), html.escape(row_text(tr)),
                choice("A2", [("親会社株主に帰属", "親会社株主に帰属する方"), ("もう一方", "もう一方の行"), ("わからない", "わからない")])))
            key["問い"].append({"問い": "A2", "種類": "当期純利益", "親会社株主に帰属": py, "もう一方": ty})
    body.append("<h2>B. 確かめてほしい項目</h2>")
    items = stopped(n)
    if not items:
        body.append("<p>(ありません)</p>")
    for i, (item, why) in enumerate(items, 1):
        qid = "B%d" % i
        a = ans[item]
        unit = "人" if item.startswith("期末の従業員数") else "円"
        src_rows = [rows[s["番号"]] for s in a.get("出どころ") or [] if s.get("番号") in rows]
        filled, filled_src = a["値"], src_rows
        cands = candidates(item, filled, src_rows, rows, period)
        flipped = False
        if ver == "F" and cands:
            (cy, cr), rest = cands[0], cands[1:]
            cands = sorted(rest + [(filled, src_rows[0] if src_rows else {"番号": 0})], key=lambda x: int(x[1].get("番号") or 0))
            filled, filled_src, flipped = cy, [cr], True
        t = ['<div class="q"><h3>%s. %s</h3><table>' % (qid, html.escape(item.replace("_", " ")))]
        t.append("<tr><th>埋めた値</th><td><b>%s</b><br><small>%s</small></td></tr>" % (
            fmt(filled, unit), "<br>".join(html.escape(row_text(r)) for r in filled_src) or "(出どころ無し)"))
        t.append("<tr><th>止めた訳</th><td>%s</td></tr>" % html.escape(why))
        for j, (cy, cr) in enumerate(cands, 1):
            t.append("<tr><th>候補%d</th><td>%s<br><small>%s</small></td></tr>" % (j, fmt(cy, unit), html.escape(row_text(cr))))
        t.append("</table>")
        opts = [("そのまま", "そのまま(埋めた値)")] + [("候補%d" % j, "候補%d" % j) for j in range(1, len(cands) + 1)] + [("別の値", "別の値を書く"), ("わからない", "わからない")]
        t.append(choice(qid, opts) + "</div>")
        body.append("".join(t))
        key["問い"].append({"問い": qid, "種類": "項目", "項目": item, "埋めた値": filled,
                           "候補": [c[0] for c in cands], "入れ替えた": flipped})
    js = ("<p><button onclick=\"var o=[];document.querySelectorAll('.choices').forEach(function(d){var c=d.querySelector('input:checked');"
          "if(c)o.push({'問い':c.name,'選び':c.value});});document.getElementById('o').textContent=JSON.stringify({'答え':o});\">選んだものを書き出す</button></p><pre id=\"o\"></pre>")
    doc = '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>確かめてほしいこと 第%s社</title><style>%s</style></head><body>%s%s</body></html>' % (n, CSS, "\n".join(body), js)
    d = os.path.join(OUT, ver)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "screen%s.html" % n), "w", encoding="utf-8") as f:
        f.write(doc)
    with open(os.path.join(d, "key%s.json" % n), "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)
    return key


def main():
    R.main()  # RD2 の集計と同じ形で r1/conv と r4/merged を作る(RD2 の根の中だけ。記録は os.devnull)
    for n in R.NUMS:
        ko = build(n, "O")
        kf = build(n, "F")
        nf = sum(q.get("入れ替えた") is True for q in kf["問い"])
        if not nf:
            os.remove(os.path.join(OUT, "F", "screen%s.html" % n))
            os.remove(os.path.join(OUT, "F", "key%s.json" % n))
        print(n, "A", sum(q["種類"] != "項目" for q in ko["問い"]), "B", sum(q["種類"] == "項目" for q in ko["問い"]), "F の行", nf)


if __name__ == "__main__":
    main()
