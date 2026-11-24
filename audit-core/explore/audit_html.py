# -*- coding: utf-8 -*-
"""便の監査の報告(AUDIT.md)を、見本の診断レポートと同じ組みの HTML にする。字は足さない。
使い方: python3 -I audit_html.py <AUDIT.md> <AUDIT.html>"""
import html, re, sys
src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").read().split("\n")
def inline(t):
    if t.startswith("<small>") and t.endswith("</small>"):
        return "<small>%s</small>" % inline(t[7:-8])
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)
out, i, title = [], 0, "監査の報告"
while i < len(lines):
    l = lines[i]
    if l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
        out.append("<table><thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in rows[0]) + "</tr></thead><tbody>")
        out += ["<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>" for r in rows[2:]]
        out.append("</tbody></table>"); continue
    if l.startswith("> "):
        out.append('<div class="notice">%s</div>' % inline(l[2:]))
    elif l.startswith("- "):
        out.append("<ul>")
        while i < len(lines) and lines[i].startswith("- "):
            out.append("<li>%s</li>" % inline(lines[i][2:])); i += 1
        out.append("</ul>"); continue
    elif re.match(r"#+ ", l):
        m = re.match(r"(#+) (.*)", l); n = len(m.group(1))
        if n == 1: title = m.group(2)
        out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n))
    elif l.strip() == "---": out.append("<hr>")
    elif l.strip(): out.append("<p>%s</p>" % inline(l))
    i += 1
css = """@page{size:A4;margin:14mm 13mm}
body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:9.5pt;line-height:1.6;max-width:190mm;margin:8mm auto;padding:0 4mm}
h1{font-size:15pt;margin:0 0 3mm}h2{font-size:12pt;margin:6mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}
p{margin:1.5mm 0}table{border-collapse:collapse;width:100%;margin:2mm 0;font-size:9pt}
th{background:#f3f5f9;text-align:left;font-weight:700}th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}
tr{break-inside:avoid}hr{border:0;border-top:.3mm solid #d9dee8;margin:5mm 0 2mm}small{color:#51607a;font-size:8.5pt}
.notice{border-left:1.2mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:0 0 5mm;line-height:1.65}"""
open(dst, "w", encoding="utf-8").write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>%s</title><style>%s</style></head><body>%s</body></html>' % (html.escape(title), css, "\n".join(out)))
