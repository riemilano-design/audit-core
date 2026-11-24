# -*- coding: utf-8 -*-
"""便 TR2: 提案に誤りを 1 か所入れ、確定の席に見せる画面(1 社 1 枚の HTML)を作る(封 §3)。AI を使わない。

使い方: python3 -E screen_tr2.py <TR2 の根> <材料定義の md> <席の folder の根>
読むもの: <根>/propose/{n}.json(提案の席の答え。信頼しない data として JSON で読むだけ)・<根>/co{n}/期1/書き出し.xlsx
書くもの: <根>/shown/{n}.json(誤りを入れた候補)・<根>/inject/{n}.json(入れた誤り。集計だけが読む)
          <席の folder の根>/c{n}/画面.html(確定の席に渡す)
誤りの選び方: 定義の 15 の順で、成分が 2 つ以上の最初の項目の最後の成分を落とし、その行を使わない行へ移す
(どこにも使わない行になる時だけ。使う行のままなら、落とすだけ)。無ければ最初の項目の列をもう一方の期の列に替える。
"""
import copy
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_tr2 as L  # noqa: E402

ROOT, DEFMD, SEAT = sys.argv[1:4]
NUMS = [51, 52, 53, 54, 55, 56]
ORDER = ["売上高@当期", "売上高@前期", "営業利益@当期", "営業利益@前期", "経常利益@当期", "当期純利益@当期", "減価償却費@当期",
         "現金及び預金@当期末", "流動資産合計@当期末", "資産合計@当期末", "短期借入金@当期末", "長期借入金@当期末", "負債合計@当期末",
         "純資産合計@当期末", "純資産合計@前期末"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def inject(prop, book):
    p = copy.deepcopy(prop)
    by = {"%s@%s" % (i["項目"], i["期"]): i for i in p["項目"]}
    for key in ORDER:
        it = by.get(key)
        if it and len(it.get("成分") or []) >= 2:
            c = it["成分"].pop()
            still = any(L._key(x) == L._key(c) for j in p["項目"] for x in j.get("成分") or [])
            if not still:
                p.setdefault("使わない行", []).append({"シート": c["シート"], "行": c["行"], "何番目": c.get("何番目") or 1})
            return p, {"項目": key, "形": "成分を 1 つ落とした", "成分": c}
    it = by[ORDER[0]]
    c = it["成分"][0]
    cfg = p["シート"][c["シート"]]
    h = int(cfg["見出しの行"]) - 1
    head = [L.text(x) for x in book[c["シート"]][h]]
    vcols = [x for x in head if x and x not in (cfg["行の見出しの列"], "コード")]
    other = next(x for x in vcols if x != c["列"])
    old = c["列"]
    for x in it["成分"]:
        x["列"] = other
    return p, {"項目": ORDER[0], "形": "列を替えた", "前": old, "今": other}


def fmt(v):
    return "{:,}".format(v) if isinstance(v, int) else html.escape(L.text(v))


def screen(n, p, book, defmd):
    led = L.make_ledger(p, book)
    use = {}
    for key, comps in led["項目"].items():
        for c in comps:
            use.setdefault(L._key(c), []).append(key)
    unused = {tuple(u) for u in led["使わない"]}
    b = ['<h1>台帳の確定 ― 第 %d 社</h1>' % n,
         '<p>会計ソフトの書き出しのどの升から、資料の数を読むかの候補です。確かめて、確定してください。確定した台帳は来期以降も使います。</p>']
    b.append("<h2>1. 項目ごとの候補</h2>")
    vals, _ = L.naive(led, book)
    for key in ORDER:
        comps = led["項目"].get(key) or []
        b.append("<h3>%s</h3><table><tr><th>シート</th><th>行</th><th>何番目</th><th>列</th><th>符号</th><th>升の値</th></tr>" % html.escape(key.replace("@", "・")))
        for c, pos in zip(comps, led["位置"].get(key) or []):
            x = book[pos["シート"]][pos["r"]][pos["c"]] if pos else "(見つからない)"
            b.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td style='text-align:right'>%s</td></tr>" % (
                html.escape(c["シート"]), html.escape(c["行"]), c.get("何番目") or 1, html.escape(c["列"]),
                "+" if int(c.get("符号") or 1) > 0 else "−", fmt(x)))
        b.append("</table><p>足した値(円): <b>%s</b></p>" % (fmt(vals[key]) if key in vals else "(読めない)"))
    b.append("<h2>2. シートごとの全部の行</h2>")
    for s, g in book.items():
        cfg = p["シート"].get(s) or {}
        if not cfg.get("使う"):
            b.append("<h3>%s(候補: 使わないシート)</h3>" % html.escape(s))
        else:
            b.append("<h3>%s(見出しの行 %s・行の見出しの列「%s」・単位 %s)</h3>" % (
                html.escape(s), cfg.get("見出しの行"), html.escape(cfg.get("行の見出しの列", "")), html.escape(cfg.get("単位", ""))))
        lay = L.layout(g, cfg) if cfg.get("使う") else None
        rowkey = {i: (s, lab, k) for i, lab, k in lay[2]} if lay else {}
        b.append("<table><tr><th>行の番号</th>%s<th>使い方(候補)</th></tr>" % "".join("<th></th>" for _ in range(max(len(r) for r in g))))
        for i, row in enumerate(g):
            k = rowkey.get(i)
            if k is None:
                how = ""
            elif k in use:
                how = "使う: " + "・".join(x.replace("@", "・") for x in use[k])
            elif k in unused:
                how = "使わない"
            else:
                how = "<b style='color:#c05621'>未決</b>"
            b.append("<tr><td>%d</td>%s<td>%s</td></tr>" % (i + 1, "".join("<td>%s</td>" % fmt(x) for x in row), how))
        b.append("</table>")
    b.append("<h2>3. 材料の定義</h2><pre style='white-space:pre-wrap'>%s</pre>" % html.escape(defmd))
    css = "body{font-family:sans-serif;font-size:10pt;max-width:200mm;margin:6mm auto}table{border-collapse:collapse;margin:2mm 0}td,th{border:1px solid #ccd;padding:1px 5px}th{background:#f3f5f9}"
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>台帳の確定</title><style>%s</style></head><body>%s</body></html>' % (css, "\n".join(b))


def main():
    with open(DEFMD, encoding="utf-8") as f:
        defmd = f.read()
    for n in NUMS:
        book = L.load_book(os.path.join(ROOT, "co%d" % n, "期1", "書き出し.xlsx"))
        prop = load(os.path.join(ROOT, "propose", "%d.json" % n))
        shown, inj = inject(prop, book)
        for d, obj in (("shown", shown), ("inject", inj)):
            os.makedirs(os.path.join(ROOT, d), exist_ok=True)
            with open(os.path.join(ROOT, d, "%d.json" % n), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=1)
        os.makedirs(os.path.join(SEAT, "c%d" % n), exist_ok=True)
        with open(os.path.join(SEAT, "c%d" % n, "画面.html"), "w", encoding="utf-8") as f:
            f.write(screen(n, shown, book, defmd))
        print(n, inj["項目"], inj["形"])


if __name__ == "__main__":
    main()
