# customer_report_build.py の約束を確かめる(0 USD・1 秒未満)。1 つでも外れたら rc=1。run_diagnosis.sh が毎回、組む前に走らせる。
# 約束: (1) 仕込んだ誤りを「丸め方の違い」に数えない、(2) 抜粋・値の字を変えない(| \ ** ` <sub> & や、前後・途中の空白を含んでも)、(3)「1. 違う」の節だけを数え、当たる行は全部を順に一覧に出す、(4) 形が違えば止まる、(5) 表紙の読み方の文が在る。
# 使い方(audit-core の中で): python3 -B sales/customer_report_selfcheck.py
import sys, os, re, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import customer_report_build as B
from adapters.xbrl.report import cell
from adapters.xbrl.report_customer import FOOT_LINE

bad = []


def check(name, got, want):
    if got != want:
        bad.append('%s: got %r want %r' % (name, got, want))


# (1) 丸め方の判定。真 = 丸め方だけで説明できる。偽 = できない(仕込んだ誤り・符号違い・括弧なし)。
ROUNDING = [
    ('381億円', '381 億円(380.6427)', True),
    ('1,457百万円', '1,458 百万円(1,457.848)', True),
    ('945百万円', '946 百万円(945.793)', True),
    ('15億円', '14 億円(14.6539)', True),
    ('14.7億円', '14.6 億円(14.6539)', True),
    ('14.6億円', '14.7 億円(14.6539)', True),
    ('△684百万円', '△685 百万円(△684.279)', True),
    ('△685百万円', '△684 百万円(△684.5)', True),
    ('381億円', '380 億円（380.6427）', True),
    ('0百万円', '1 百万円(0.3)', True),
    ('60.6%', '60.7 %(60.65)', True),
    ('1,645百万円', '1,465 百万円(1,465.387)', False),
    ('60.6%', '61.7 %', False),
    ('60.6%', '61.7 %(61.7)', False),
    ('802百万円', '△803 百万円(△802.686)', False),
    ('△802百万円', '803 百万円(802.686)', False),
    ('14.5億円', '14.7 億円(14.6539)', False),
    ('14.8億円', '14.7 億円(14.6539)', False),
    ('△686百万円', '△685 百万円(△684.999)', False),
    ('383億円', '381 億円(380.6427)', False),
    ('379億円', '381 億円(380.6427)', False),
    ('1百万円', '0 百万円(0.3)', False),
    ('1,458百万円', '1,457 百万円(1,456.999)', False),
    ('38,064百万円', '3,806 百万円(3,806.4)', False),
    ('約381億円', '381 億円(380.6427)', False),
    ('―', '381 億円(380.6427)', False),
    ('1' * 30 + '百万円', '1 百万円(' + '1' * 30 + '.5)', False),
]
for s, x, want in ROUNDING:
    check('rounding_only(%s | %s)' % (s, x), B.rounding_only(s, x), want)

# (2) 字を変えない。道具と同じ cell() で表の行を作り、組んだ HTML の欄を元の字と比べる。
RAW = ['売上高は**38,064百万円**となり', 'コード `abc` を含む', '<sub>小さい字</sub>と<b>太字</b>', '営業 | 経常 の順',
       '円記号 \\ と \\| の並び', 'A & B &amp; C', '- 行頭の棒', '**片方だけ',
       ' 先頭に半角の空白', '末尾に半角の空白 ', '\u3000先頭に全角の空白', '末尾に全角の空白\u3000', '途中に  半角が 2 つ', '途中に\u3000\u3000全角が 2 つ',
       '\tタブで始まりタブで終わる\t', '\u00a0切れない空白で始まる', '  半角 2 つで始まり 2 つで終わる  ',
       '末尾に切れない空白\u00a0', '\x1c区切りの字で始まる', '区切りの字で終わる\x1c', '\u2003幅の広い空白で始まり終わる\u2003', '\x0b縦のタブで始まり終わる\x0b']
SUMMARY = ['| 区分 | 件数 | 意味 |', '|---|---|---|', '| 違う | %d | 文の値と**違う**。 |', '| 一致 | 0 | 一致した |', '| 合計 | %d | |']


def report(diff_rows, match_rows=(), listed=()):
    L = ['# %s の数の点検' % cell('会社 | **名** `x`'), '', '地の文 `code`。', '']
    L += [x % len(diff_rows) if '%d' in x else x for x in SUMMARY]
    L += ['', '## 1. 違う ― %d 件' % len(diff_rows), '']
    if diff_rows:
        L += ['| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |', '|---|---|---|---|---|']
        L += ['| %s | %s | %s | %s | %s |' % tuple(cell(c) for c in r) for r in diff_rows]
    else:
        L += ['(なし)']
    L += ['', '## 3. 対象外 ― %d 件' % len(listed), '']
    L += ['- %s: %s(%s)' % (cell('N9%02d' % k), cell(t), cell('出典に無い')) for k, t in enumerate(listed)]
    L += ['', '## 4. 一致 ― %d 件' % len(match_rows), '']
    if match_rows:
        L += ['| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |', '|---|---|---|---|---|']
        L += ['| %s | %s | %s | %s | %s |' % tuple(cell(c) for c in r) for r in match_rows]
    L += ['', '---', '', FOOT_LINE]
    return '\n'.join(L)


def tool_part(page):
    return page.split('<div id="tool">', 1)[1]


diff = [('N%03d' % k, t, '1,645百万円', '1,465 百万円(1,465.387)', '売上高 当期') for k, t in enumerate(RAW)]
page, n, flagged = B.build(report(diff, listed=RAW))
tds = [html.unescape(x) for x in re.findall(r'<td>(.*?)</td>', tool_part(page).split('<h2>', 1)[1], re.S)]
check('抜粋の欄', tds[1::5], RAW)
check('文の値の欄', tds[2::5], ['1,645百万円'] * len(RAW))
check('出典の値の欄', tds[3::5], ['1,465 百万円(1,465.387)'] * len(RAW))
lis = [html.unescape(x) for x in re.findall(r'<li>(.*?)</li>', tool_part(page), re.S)]
check('箇条書き', lis, ['N9%02d: %s(出典に無い)' % (k, t) for k, t in enumerate(RAW)])
check('題(印を見た目に直さない)', html.unescape(re.search(r'<h1>(.*?)</h1>', page).group(1)), '会社 | **名** `x` の数の点検')
check('違うの行数', n, len(RAW))
check('仕込んだ誤りは一覧に出ない', flagged, [])
check('道具の太字', '<b>違う</b>' in tool_part(page), True)
check('道具の末尾の 1 行', '<small>' in tool_part(page) and '<code>.provenance.json</code>' in tool_part(page), True)

# (3)「1. 違う」の節だけを数える。一致の節に丸め方の形の行が在っても数えない。
d2 = [('N001', 'あ', '381億円', '380 億円(380.6427)', '売上高 当期'), ('N002', 'い', '1,645百万円', '1,465 百万円(1,465.387)', '売上高 当期')]
m2 = [('N003', 'う', '945百万円', '946 百万円(945.793)', '純利益 当期')]
page, n, flagged = B.build(report(d2, match_rows=m2))
check('節 1 だけ: 行数', n, 2)
check('節 1 だけ: 一覧', [f[0] for f in flagged], ['N001'])
check('表紙の件数', '「違う」2 件のうち 1 件' in page, True)
# 当たる行が 2 つ以上: 全部を、表の順に出す(最初の 1 行だけ・最後の 1 行だけ、にならない)。
d4 = [('N001', 'あ', '381億円', '380 億円(380.6427)', '売上高 当期'), ('N002', 'い', '1,645百万円', '1,465 百万円(1,465.387)', '売上高 当期'),
      ('N003', 'う', '945百万円', '946 百万円(945.793)', '純利益 当期'), ('N004', 'え', '△684百万円', '△685 百万円(△684.279)', '営業損失 当期')]
page, n, flagged = B.build(report(d4))
check('当たる行が 3 つ: 行数', n, 4)
check('当たる行が 3 つ: 一覧', flagged, [(r[0], r[2], r[3]) for r in (d4[0], d4[2], d4[3])])
check('当たる行が 3 つ: 表紙の件数', '「違う」4 件のうち 3 件' in page, True)
check('当たる行が 3 つ: 表紙の表', re.findall(r'<tr><td>(N\d+)</td>', page.split('<div id="tool">', 1)[0]), ['N001', 'N003', 'N004'])
page, n, flagged = B.build(report([('N<1>', 'あ', '381億円', '380 億円(380.6427)', '売上高 当期')]))
check('一覧の欄は escape', '<td>N&lt;1&gt;</td><td>381億円</td>' in page.split('<div id="tool">', 1)[0], True)
page, n, flagged = B.build(report([]))
check('0 件: 行数', (n, flagged), (0, []))
check('0 件: 2 つ目の枠は出ない', page.count('class="notice"'), 1)
page, n, flagged = B.build(report([]), '添え書き <b> & 1 行目\n2 行目')
check('添え書きは escape', '添え書き &lt;b&gt; &amp; 1 行目<br>2 行目' in page, True)

# (5) 表紙の読み方の文(送ったメールと返事の約束に当たる文)が、道具の出力より前に在る。
front = B.build(report(d2))[0].split('<div id="tool">', 1)[0]
for want in ['点検に生成 AI は使っていません。', '数字・判定・抜粋の字は変えていません', '道具の当て違いの場合があります。', '最後のご判断は御社でお願いします。',
             '道具の当て違いと見てください', 'この一覧は機械的な計算で出しています']:
    check('表紙の文: ' + want, want in front, True)

# 欄の分け方。外すのは、表の書式が足した半角空白 1 つずつだけ。末尾の空の欄も 1 欄に数える。
for line, want in [('| a | b | |', ['a', 'b', '']), ('| a |  |', ['a', '']), ('| a | b', ['a', 'b']), ('| a | ', ['a', '']), ('|---|---|', ['---', '---']),
                   ('|  a  | \u3000b\u3000 |', [' a ', '\u3000b\u3000']), ('| a \\| b | c \\\\ |', ['a | b', 'c \\']),
                   ('| a |\r', ['a']), ('| a | b |\r\n', ['a', 'b'])]:
    check('split_row(%r)' % line, B.split_row(line), want)


# (4) 形が違えば止まる。
def stops(name, md):
    try:
        B.build(md)
    except B.ShapeError:
        return
    bad.append('%s: 止まらなかった' % name)


ok = report(d2)
stops('欄が 1 つ多い行', ok.replace('| N001 | あ |', '| N001 | あ | 余り |'))
stops('欄が 1 つ少ない行', ok.replace('| N001 | あ |', '| N001 |'))
stops('先頭の表の件数と合わない', ok.replace('| 違う | 2 |', '| 違う | 3 |'))
stops('先頭の表に 違う の行が無い', ok.replace('| 違う | 2 |', '| ちがう | 2 |'))
stops('違うの表の欄の名が違う', ok.replace('| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |', '| # | 文の抜粋 | 値 | 出典の値 | 出典 |', 1))

if bad:
    sys.stderr.write('customer_report_selfcheck: NG %d\n' % len(bad))
    for b in bad:
        sys.stderr.write('  ' + b + '\n')
    sys.exit(1)
print('customer_report_selfcheck: OK(丸め方 %d 例・字の保存 %d 例・節と一覧と形と表紙の検査)' % (len(ROUNDING), len(RAW)))
