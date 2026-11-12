# お客さま向けの診断レポート(report_customer の出力 .md)を HTML に組む。数字・判定・抜粋の字は変えない(太字などの見た目だけ整える)。
# 足すのは表紙の枠だけ: (1) 読み方の注意、(2)「違う」のうち、出典の値を四捨五入か切り捨てすると文の値と同じになる行の一覧(機械の計算。生成 AI は使わない)、(3) 任意の添え書き。
# 使い方: python3 sales/customer_report_build.py report.md out.html [添え書き.txt]
# 確かめ: python3 sales/customer_report_selfcheck.py(run_diagnosis.sh が毎回、組む前に走らせる)
import sys, html, re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_DOWN

NUM = r'[△▲\-−]?[0-9][0-9,]*(?:\.[0-9]+)?'


class ShapeError(Exception):
    """report.md の形が、この道具の知っている形と違う。黙って組まずに止まる。"""


def dec(t):
    return Decimal(re.sub(r'[△▲\-−,]', '', t))


def rounding_only(stated, source):
    """文の値「381億円」・出典の値「381 億円(380.6427)」→ 括弧の中を文の値の小数の桁で四捨五入か切り捨てすると文の値になるか。"""
    ms, mx = re.match(r'\s*(%s)' % NUM, stated), re.search(r'[(（]\s*(%s)\s*[)）]' % NUM, source)
    if not (ms and mx):
        return False
    s, x = ms.group(1), mx.group(1)
    if bool(re.match(r'[△▲\-−]', s)) != bool(re.match(r'[△▲\-−]', x)):
        return False
    q = Decimal(1).scaleb(-(len(s.split('.')[1]) if '.' in s else 0))
    try:
        return dec(s) in (dec(x).quantize(q, rounding=ROUND_HALF_UP), dec(x).quantize(q, rounding=ROUND_DOWN))
    except InvalidOperation:  # 桁が多すぎて丸められない数は、丸め方の違いに数えない
        return False


def unpad(c):
    """欄の前後から、表の書式(「| %s |」)が足した半角空白を 1 つずつだけ外す。全角の空白・タブ・2 つ目の半角空白は字として残す。"""
    if c.startswith(' '):
        c = c[1:]
    if c.endswith(' '):
        c = c[:-1]
    return c


def split_row(line):
    """表の 1 行を欄に分ける。report.cell が付けた「\\|」「\\\\」は元の字(| と \\)に戻す。"""
    s = line.rstrip('\r\n')
    if s.startswith('|'):
        s = s[1:]
    cells, cur, i, closed = [], '', 0, False
    while i < len(s):
        ch = s[i]
        if ch == '\\' and i + 1 < len(s) and s[i + 1] in '\\|':
            cur += s[i + 1]; i += 2; closed = False
            continue
        if ch == '|':
            cells.append(unpad(cur)); cur = ''; closed = True
        else:
            cur += ch; closed = False
        i += 1
    if not closed:
        cells.append(unpad(cur))
    return cells


def unesc(t):
    return re.sub(r'\\([\\|])', r'\1', t)


def plain(t):
    """お客さまの文が入りうる所(節の中の表・箇条書き・見出し)。escape だけ。"""
    return html.escape(t)


def tool_inline(t):
    """道具が自分で書いた字だけの所(先頭の区分の表・地の文・末尾の 1 行)。太字・等幅・小さい字の印を見た目に直す。"""
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = t.replace('&lt;sub&gt;', '<small>').replace('&lt;/sub&gt;', '</small>')
    return t


CSS = '''@page{size:A4;margin:14mm 13mm}
body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:9.5pt;line-height:1.6}
h1{font-size:15pt;margin:0 0 3mm}h2{font-size:12pt;margin:6mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}h3{font-size:10.5pt;margin:4mm 0 1.5mm}
p{margin:1.5mm 0}table{border-collapse:collapse;width:100%;margin:2mm 0;font-size:9pt}
th{background:#f3f5f9;text-align:left;font-weight:700}th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}
tr{break-inside:avoid}ul{margin:1mm 0 1mm 5mm;padding:0;font-size:9pt}hr{border:0;border-top:.3mm solid #d9dee8;margin:5mm 0 2mm}small{color:#51607a;font-size:9pt}
.notice{border-left:1.2mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:0 0 4mm;font-size:9.5pt;line-height:1.65}
.notice b.t{display:block;font-size:10.5pt;margin-bottom:1mm}.notice table{background:#fff}'''


def build(md, cover=''):
    """report.md の字 → (HTML の字, 「違う」の行数, 丸め方だけで説明できる行の一覧)。形が違えば ShapeError。"""
    lines = md.split('\n')
    out, i, flagged, n_diff, section, declared = [], 0, [], 0, '', None
    while i < len(lines):
        l = lines[i]
        if l.startswith('|'):
            start, rows = i, []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(split_row(lines[i])); i += 1
            head = rows[0]
            for k, r in enumerate(rows):
                if len(r) != len(head):
                    raise ShapeError('表の行の欄の数が見出しと違います(%d 行目)' % (start + k + 1))
            fmt = plain if section else tool_inline
            if not section:
                for r in rows[2:]:
                    if r[0] == '違う' and re.fullmatch(r'[0-9,]+', r[1]):
                        declared = int(r[1].replace(',', ''))
            if section.startswith('1. 違う'):
                if not ('文の値' in head and '出典の値' in head):
                    raise ShapeError('「1. 違う」の表に 文の値・出典の値 の欄が在りません')
                a, b = head.index('文の値'), head.index('出典の値')
                for r in rows[2:]:
                    n_diff += 1
                    if rounding_only(r[a], r[b]):
                        flagged.append((r[0], r[a], r[b]))
            out.append('<table><thead><tr>' + ''.join('<th>%s</th>' % fmt(c) for c in head) + '</tr></thead><tbody>')
            for r in rows[2:]:
                out.append('<tr>' + ''.join('<td>%s</td>' % fmt(c) for c in r) + '</tr>')
            out.append('</tbody></table>')
            continue
        if l.startswith('- '):
            out.append('<ul>')
            while i < len(lines) and lines[i].startswith('- '):
                out.append('<li>%s</li>' % plain(unesc(lines[i][2:]))); i += 1
            out.append('</ul>')
            continue
        m = re.match(r'(#+) (.*)', l)
        if m:
            if len(m.group(1)) == 2:
                section = m.group(2)
            out.append('<h%d>%s</h%d>' % (len(m.group(1)), plain(unesc(m.group(2))), len(m.group(1))))
        elif l.strip() == '---':
            out.append('<hr>')
        elif l.strip():
            out.append('<p>%s</p>' % tool_inline(l))
        i += 1
    if declared is None:
        raise ShapeError('先頭の区分の表に「違う」の件数の行が在りません')
    if declared != n_diff:
        raise ShapeError('先頭の表の「違う」%d 件と、「1. 違う」の表の %d 行が合いません' % (declared, n_diff))
    notice = ('<div class="notice"><b class="t">診断レポートの読み方</b>'
      '色のついた枠より下は、道具(Audit Core)が出した報告です。数字・判定・抜粋の字は変えていません(太字などの見た目だけ整えています)。点検に生成 AI は使っていません。'
      '「違う」は、文の誤りの場合と、道具の当て違いの場合があります。どちらかは道具は決めません。最後のご判断は御社でお願いします。'
      '確かめるのは数字だけで、意見・見通し・文章の良し悪しは判断しません。</div>')
    if flagged:
        notice += ('<div class="notice"><b class="t">「違う」%d 件のうち %d 件は、丸め方の違いだけで説明できます(道具の当て違いと見てください)</b>'
          '次の行は、出典の値(括弧の中)を文の値の桁で四捨五入するか切り捨てると、文の値と同じになります。'
          '道具はいま、単位(百万円・億円など)ごとに丸め方が違う文章 ― たとえば百万円の数は切り捨て、億円の数は四捨五入 ― では、片方の丸め方だけで照らすことがあり、そのときこの形の「違う」が出ます。'
          'この一覧は機械的な計算で出しています(下の表の行は変えていません)。'
          '<table><thead><tr><th>#</th><th>文の値</th><th>出典の値</th></tr></thead><tbody>%s</tbody></table></div>'
          % (n_diff, len(flagged), ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(html.escape(c) for c in f) for f in flagged)))
    if cover:
        notice += '<div class="notice"><b class="t">添え書き(道具の出力ではありません)</b>%s</div>' % '<br>'.join(html.escape(x) for x in cover.split('\n'))
    page = '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>Audit Core 診断レポート</title><style>%s</style></head><body>%s<div id="tool">%s</div></body></html>' % (CSS, notice, '\n'.join(out))
    return page, n_diff, flagged


def main(argv):
    src, dst = argv[1], argv[2]
    cover = open(argv[3], encoding='utf-8').read().strip() if len(argv) > 3 else ''
    try:
        page, n_diff, flagged = build(open(src, encoding='utf-8').read(), cover)
    except ShapeError as e:
        sys.stderr.write('組めません(report.md の形が想定と違います): %s\n' % e)
        return 3
    open(dst, 'w', encoding='utf-8').write(page)
    print('diff_rows', n_diff, 'rounding_only', len(flagged), ' '.join(f[0] for f in flagged))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
