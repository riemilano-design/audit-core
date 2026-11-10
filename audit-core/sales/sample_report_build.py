# 見本の診断レポート(report_customer の出力 .md)を、そのままの字で HTML に組む。字は足さない(表紙の注意書きだけ別枠)。
import sys, html, re
src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding='utf-8').read().split('\n')
m0 = re.match(r'# (.+?) 有価証券報告書', lines[0]); assert m0
name = m0.group(1)
n_name = sum(l.count(name) for l in lines)
lines = [l.replace(name, '(社名は伏せています)') for l in lines]
print('masked', n_name)
def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = t.replace('&lt;sub&gt;', '<small>').replace('&lt;/sub&gt;', '</small>')
    return t
out, i = [], 0
while i < len(lines):
    l = lines[i]
    if l.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        out.append('<table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in rows[0]) + '</tr></thead><tbody>')
        for r in rows[2:]:
            out.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
        out.append('</tbody></table>'); continue
    if l.startswith('- '):
        out.append('<ul>')
        while i < len(lines) and lines[i].startswith('- '):
            out.append('<li>%s</li>' % inline(lines[i][2:])); i += 1
        out.append('</ul>'); continue
    m = re.match(r'(#+) (.*)', l)
    if m: out.append('<h%d>%s</h%d>' % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
    elif l.strip() == '---': out.append('<hr>')
    elif l.strip(): out.append('<p>%s</p>' % inline(l))
    i += 1
css = '''@page{size:A4;margin:14mm 13mm}
body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:9.5pt;line-height:1.6}
h1{font-size:15pt;margin:0 0 3mm}h2{font-size:12pt;margin:6mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}h3{font-size:10.5pt;margin:4mm 0 1.5mm}
p{margin:1.5mm 0}table{border-collapse:collapse;width:100%;margin:2mm 0;font-size:9pt}
th{background:#f3f5f9;text-align:left;font-weight:700}th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}
tr{break-inside:avoid}ul{margin:1mm 0 1mm 5mm;padding:0;font-size:9pt}hr{border:0;border-top:.3mm solid #d9dee8;margin:5mm 0 2mm}small{color:#51607a;font-size:9pt}
.notice{border-left:1.2mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:0 0 5mm;font-size:9.5pt;line-height:1.65}
.notice b{display:block;font-size:10.5pt;margin-bottom:1mm}'''
notice = ('<div class="notice"><b>見本の診断レポート(Audit Core の出力そのまま)</b>'
  '原本は、EDINET で公開されている有価証券報告書です。点検した文章は、当方が実験のために AI に書かせた経営分析の文で、'
  '<b style="display:inline;font-size:inherit">同社が書いた文ではありません。</b>'
  'この枠より下は、道具が出した報告です。社名だけを伏せ、ほかは 1 字も変えていません(一致の行は省略の形式)。「違う」には、道具の当て違いも含まれます(例: 先頭の 3 行)。使った設定は P33E、点検に生成 AI は使っていません。</div>')
open(dst, 'w', encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>Audit Core 見本の診断レポート</title><style>%s</style></head><body>%s%s</body></html>' % (css, notice, '\n'.join(out)))
