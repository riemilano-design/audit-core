# -*- coding: utf-8 -*-
u"""封 docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md(XE0 ― 会社が Excel で出すとしたら、XBRL の言葉を 1 つも書かない欄だけで、今年の「型」はどれだけ決まり、どれだけ黙って違い、どれだけ止まるか)の測定。
**0 USD。LLM の席は呼ばない。道具(Arelle)は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は読まない・変えない。

工程は 3 つ(別の process で走らせる。封 §2・§5):

    python3 measure/xbrl_company_excel_2026-11-22.py --make <一時の folder>                  # 作る側: 今年の書類から xlsx の folder と答えの folder を別に書く(今年の書類の答えを読むのはこの工程だけ)
    python3 measure/xbrl_company_excel_2026-11-22.py --receive <xlsx の folder> <出力の folder>  # 受ける側: 今年の xlsx と去年の書類だけを読む(今年の zip も答えの folder も開かない)
    python3 measure/xbrl_company_excel_2026-11-22.py --score <出力の folder> <答えの folder>      # 採点: 受ける側の出力と答えを比べ、記録 fixtures/xbrl/cd8/company_excel_2026-11-22.json を排他で書く
    python3 measure/xbrl_company_excel_2026-11-22.py --check                                # 記録の形・組ごとの数からの導き直し(集計・予測の当たり外れ・旗)・禁止のものを検査する。置き場は読まない
    python3 measure/xbrl_company_excel_2026-11-22.py --dev --tmp <一時の folder>             # 番号 1・2・3 の 3 組だけを 3 工程通し、記録を書かず、数を表示する

組は便 XY0 の script(Y。``make_pairs``)・行の読み方は便 XZ0 の script(Z。``read_rows``)・表の頭の印は便 XZ1 の script(G。``head_mark``・``MEMBER_RE``)・字の読み出しは便 XG1 の script(N。``doc_texts``)・
答えの側の fact の読み方は便 XM0 の script(M。``analyze``・``period_name``・``number_value``)を importlib で呼ぶ(写さない・変えない)。
``M.derive_folder``・``M.process_doc`` は呼ばない。受ける側の関数は今年の zip の path も答えの folder も引数に取らない(組の番号と去年の path だけを渡す)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 組の分け: 番号が 3 以下の組が訓練の 3 組・4 以上の組が判定の 60 組(番号は便 XY0 の ``make_pairs`` の組の番号 = 今年の側の 67 本の昇順の位置。除いた書類の番号は飛ぶ)。
- xlsx に書かない fact の理由は、封 §3 に挙げた順(突き合わせの外 → 行の字が空 → 型の外 → 単位が書けない → 有効数字が 15 桁を超える)で先に当たった 1 つだけに数える(重ならない。D = 行の中の数の fact から全部を引いた数)。
- 有効数字の桁の数 = 表示の字から ``,`` と ``.`` を除き、先頭の 0 を除いた字の長さ。空の fact には無い。
- 負の印: 行の字の中で、fact のタグより前の最後の ``<td`` か ``<th`` の開きタグの後ろ(開きタグが無ければ行の頭)から fact のタグの手前までの字から、タグ・``&#160;``・空白(U+00A0・U+3000 を含む)を除いた末尾の 1 字。
- xlsx は openpyxl で書き読む。空の字は空のセルに戻る(見出しの字が空の字と「無い」は区別できない)ので、見出しの字の ``""`` は ``None`` と同じ鍵に数える(両方の年に同じに掛ける)。
  負の印つきの 0 は数のセルの符号を失う(``-0`` は 0 として読まれる)。その fact は「符号だけ違う」の「答えの値が符号つきの 0」に数える(封 §2-3)。
- 数のセルの表示形式は ``0``・``0.0``・``0.00``…(小数の桁の数 = 表示の字の小数の桁の数)に決め、読む側はこの形だけを読む(それ以外は止まる)。
- 負の印あり・表示の数が 0 の fact・空の fact・符号の向きが逆の fact の数は、書いた行(D)のうち、負の印あり・符号の向きが逆は空でない fact だけを数える。
- 候補が 1 つの止め(守り G・G1・G3・G2)の「止めずに決めていたら」は、守り 4 つ(と符号の向きが 2 通りの止め)を全部外して封 §2-2 の 8. で決めた中身を答えと比べる。去年の符号の向きが 2 通りのときは「順」で決める。
- 守り G3 は候補の区分の (軸, member) のうち member の名の、最初の ``:`` より後ろ(``:`` が無ければ全部)が ``MEMBER_RE`` に合うかで見る(軸の名は見ない)。
- 去年の表の鍵の表示の位の集まりは、場面の数(去年の同じ鍵と表示の位が違う fact)のためだけに持つ(決めには使わない)。
- 去年の書類・今年の書類の分析が断り(``M.Refuse``)を出したら止まる(封に断った組の決めが無い。XK0 の記録は 63 組で断りが 0 だった)。
- 突き合わせの外の file の fact の数は ``ix:nonFraction`` の数(隠しの中も含む)・うち行の中は ``read_rows`` が行の中に数えた数。
- 組の番号の並びの確かめと材料の並びの sha256 は ``make_pairs`` が返す今年の側の書類の並びから作る。
"""
from __future__ import print_function

import argparse
import bisect
import collections
import datetime
import decimal
import fractions
import importlib.util
import io
import json
import math
import os
import re
import sys
import zipfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load_sibling("_xe0_input_type_2026_11_22", "xbrl_input_type_2026-11-22.py")                     # 便 XM0 の script
G = _load_sibling("_xe0_prior_year_fact_guard_2026_11_22", "xbrl_prior_year_fact_guard_2026-11-22.py")   # 便 XZ1 の script
Z = G.Z                                                                                              # 便 XZ0 の script
Y = Z.Y                                                                                              # 便 XY0 の script
N = Z.N                                                                                              # 便 XG1 の script
W = M.W                                                                                              # 便 XG0 の script

SEAL_REL = "docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md"
SEAL_COMMIT = "aec0496d"
SCRIPT_REL = "measure/xbrl_company_excel_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/company_excel_2026-11-22.json"
DOCS_DIR = Y.DOCS_DIR
PRIOR_DIR = Y.PRIOR_DIR

# ---- 封 §1〜§4 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = Y.DOCS_WANT
PAIRS_WANT = Y.PAIRS_WANT
SEEN_MAX_NO = 3                                   # 番号がこれ以下の組が訓練の 3 組
TRAIN_WANT, JUDGE_WANT = 3, 60
DEV_NOS = (1, 2, 3)
SHEET_DOC, SHEET_NUM = u"書類", u"数"
HEAD_DOC = (u"当期の始まりの日", u"当期の終わりの日", u"提出の日")
HEAD_NUM = (u"見出しの字", u"表の番号", u"行の字", u"列の番号", u"表の頭の印", u"金額", u"期の始まりの日", u"期の終わりの日", u"単位の字")
NIL_CELL = u"－"
MARKS = u"△▲-－−"                                # 負の印の字
MAX_DIGITS = 15
VALUE_NONE = M.VALUE_NONE
JPY = u"通貨:JPY"
#: 単位の字の表(単位の形 × 表示の位 → 字)
UNIT_ROWS = ((JPY, 0, u"円"), (JPY, 3, u"千円"), (JPY, 6, u"百万円"), (M.UNIT_SHARES, 0, u"株"), (M.UNIT_SHARES, 3, u"千株"),
             (M.UNIT_PURE, 0, u"数"), (M.UNIT_PURE, -2, u"％"), (JPY + u"÷株", 0, u"円/株"))
#: 空の fact は表示の位が無いので、単位の形だけから決める
UNIT_FORM_ROWS = ((JPY, u"円"), (M.UNIT_SHARES, u"株"), (M.UNIT_PURE, u"数"), (JPY + u"÷株", u"円/株"))
LETTER_TO_UNIT = dict((s, (f, p)) for f, p, s in UNIT_ROWS)
LETTER_TO_FORM = dict((s, f) for f, _p, s in UNIT_ROWS)
UNIT_OF = dict(((f, p), s) for f, p, s in UNIT_ROWS)
FORM_LETTER = dict(UNIT_FORM_ROWS)
#: 受ける側の止めの理由(決める順)
STOPS = (u"去年に無い行", u"候補が 2 つ以上", u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う", u"符号の向きが 2 通り")
S_NONE, S_MULTI, S_HEAD, S_PERIOD, S_NUMBERED, S_UNIT, S_SIGN = STOPS
GUARDS = (S_HEAD, S_PERIOD, S_NUMBERED, S_UNIT)    # 候補が 1 つの止め(守り G・G1・G3・G2)
GUARD_LABEL = {S_HEAD: u"守り G 表の頭", S_PERIOD: u"守り G1 期", S_NUMBERED: u"守り G3 番号つき", S_UNIT: u"守り G2 単位"}
#: 採点で比べる欄(決めた欄の全部)
FIELDS = (u"名", u"個別か既定か", u"区分", u"期の日", u"期の種類", u"値", u"単位の形", u"表示の位", u"精度", u"空か")
FIELD_KEY = dict(zip(FIELDS, ("name", "target", "dims", "period", "pkind", "value", "form", "shift", "prec", "nil")))
EXCLUDES = (u"行の字が空", u"型の外", u"単位が書けない", u"有効数字が 15 桁を超える")
#: 封 §0 の訓練の 3 組の数(§3 の旗のために照らす 4 つ)
SEAL_TRAIN = collections.OrderedDict([(u"行の中の数の fact", 3434), (u"決めて全部同じ", 2636), (u"決めたが違う", 0), (u"止めた", 669)])
DOC_SAME_PCT = 95.0                               # XE0-9: この率以上の書類
#: 封 §4 の予測の境(記録には当たり外れも書く)。(下限, 下限を含むか, 上限, 上限を含むか)。None = 無い。率は D・行の中の数の fact・止めた・守りの止めに対する % か、組・fact の数。
BOUNDS = collections.OrderedDict([
    ("XE0-1", (74.0, True, None, False)), ("XE0-2", (None, False, 0.5, True)), ("XE0-3", (None, False, 30, True)), ("XE0-4", (16.0, True, 26.0, True)),
    ("XE0-5", (40.0, True, 65.0, True)), ("XE0-6", (None, False, 2.0, True)), ("XE0-7", (None, False, 1.0, True)), ("XE0-8", (35, True, None, False)),
    ("XE0-9", (None, False, 2, True))])
MIN_DIFF = 1                                      # XE0-2: 決めたが違うが 1 fact 以上
MIN_G12 = 1                                       # XE0-6: 守り G1 と G2 の止めが合わせて 1 fact 以上
LIMITS = [
    u"xlsx は、**道具で作られ受理された書類から起こした**もの。会社の手元の原稿ではない。行の字・表の並び・列の番号は、出来上がった書類のもので、経理の人が同じ字・同じ並びで書くかは測らない。",
    u"鍵の欄(見出し・表の番号・列の番号・表の頭の印)は「去年の書類と同じ並びの表に入れる」ことを会社に求める。これは XBRL の知識ではないが、会社の負担であり、この便は負担を測らない。",
    u"単位の字は答えから表で作った字。会社が実際に書く単位の字(「人」「倍」「回」など)は見ていない。",
    u"期の日は答えの文脈の日をそのまま書いた。会社が期をどう書くかは見ていない。",
    u"去年の書類が在る会社の、続いた 2 年だけ。63 組(判定は 60 組)。有報だけ。",
    u"数の fact で行の中に在るものだけ。文の fact・隠しの fact・行の外の数の fact・行の字が空の fact は扱わない。",
    u"XBRL の側を組んでいない。決めた型の行から XBRL が作れるかは便 XM0 の範囲(型も対応表も答えから作った)。",
    u"答えは提出された書類そのもので、提出された書類の誤りは見ていない。"]

Stop = W.Stop
Refuse = M.Refuse
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
TAG_RE = re.compile(r"<[^>]*>")
SPACE_RE = re.compile(r"[\s 　]")
FORMAT_RE = re.compile(r"^0(?:\.(0+))?$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
NOT_SUMMED = (u"番号",)
FACT_SIDE_KEYS = ("name", "target", "dims", "pkind", "period", "value", "form", "shift", "prec", "nil")


# ======================================================================================================
# 負の印・字(封 §1)
def negative_mark(rowtext, fact_start):
    u"""行の字と、その中の fact のタグの始まりの位置 → 負の印ありか(封 §1)。"""
    cells = list(Z.CELL_RE.finditer(rowtext[:fact_start]))
    seg = rowtext[cells[-1].start():fact_start] if cells else rowtext[:fact_start]
    seg = TAG_RE.sub(u"", seg).replace(u"&#160;", u"")
    seg = SPACE_RE.sub(u"", seg)
    return bool(seg) and seg[-1] in MARKS


def sig_digits(content):
    u"""表示の字 → 有効数字の桁の数(``,`` と ``.`` を除き、先頭の 0 を除いた字の長さ)。"""
    return len((content or u"").replace(u",", u"").replace(u".", u"").lstrip(u"0"))


def frac_digits(content):
    u"""表示の字 → 小数の桁の数。"""
    return len(content.split(u".")[1]) if u"." in content else 0


def hkey(h):
    u"""見出しの字 → 鍵に入れる字(空の字は無いと同じ。xlsx の空のセルに戻るため)。"""
    return h or None


def key_of(r):
    return (hkey(r["h"]), r["th"], r["T"], r["td"])


def local_name(name):
    u"""名の最初の ``:`` より後ろ(``:`` が無ければ全部)。"""
    return name.split(":", 1)[1] if ":" in name else name


# ======================================================================================================
# 1 年分を読む(両方の年に同じに掛ける。書類の字と答えの側の fact の突き合わせ)
def build_side(texts, files, an):
    u"""([(file 名, 字)], 表の並び files, ``M.analyze`` の戻り) → 行の中の数の fact の並びと突き合わせの外の数。
    file ごとに、字の中の fact の出た順と、``M.analyze`` の数の fact で隠しでないもの(その file のもの)の出た順を 1 対 1 に結ぶ。数が合わない file は結ばない。結んだ対で name と contextRef が違えば止まる。"""
    byfile = collections.defaultdict(list)
    for f in an["facts"]:
        if f["where"] == "F" and f["isnum"]:
            byfile[files[f["fi"]][0]].append(f)
    dec = an["dec"]
    recs = []
    st = od([("inrow", 0), ("files_out", 0), ("ix_out", 0), ("inrow_out", 0)])
    for name, text in sorted(texts, key=lambda q: q[0]):
        rows, _outside = Z.read_rows(text)
        inrow = sum(len(r[3]) for r in rows)
        st["inrow"] += inrow
        allm = list(Z.FACT_RE.finditer(text))
        xs = byfile.get(os.path.basename(name), byfile.get(name, []))
        if len(allm) != len(xs):
            st["files_out"] += 1
            st["ix_out"] += len(allm)
            st["inrow_out"] += inrow
            continue
        pos = dict((m.start(), i) for i, m in enumerate(allm))
        matches = list(Z.I._TR_RE.finditer(text))
        if len(matches) != len(rows):
            raise Stop(u"**行の並びが engine の _TR_RE の全部と 1 対 1 でない。止める**")
        marks = head_marks_by_table(text, matches)
        starts = [m.start() for m in Z.TABLE_RE.finditer(text)]
        for m, (h, th, T, facts) in zip(matches, rows):
            rowtext = m.group(0)
            hm = marks.get(bisect.bisect_left(starts, m.start()), u"")
            for fm, (td, a) in zip(Z.FACT_RE.finditer(rowtext), facts):
                x = xs[pos[m.start() + fm.start()]]
                if x["attrs"].get("name") != a.get("name") or x["attrs"].get("contextRef") != a.get("contextRef"):
                    raise Stop(u"**結んだ対で name か contextRef が違う。止める**")
                bad = bool(x["reasons"])
                recs.append(od([
                    ("h", h), ("th", th), ("T", T), ("td", td), ("hmark", hm), ("neg", negative_mark(rowtext, fm.start())),
                    ("name", x["attrs"]["name"]), ("target", x["target"]), ("dims", tuple(tuple(d) for d in x["dims"])),
                    ("pkind", x["period"][0]), ("dates", list(x["period"][1] or [])),
                    ("pn", None if bad else M.period_name(x["period"][0], x["period"][1], dec)),
                    ("value", x["value"]), ("form", x["form"]), ("shift", x["shift"]), ("prec", x["prec"]), ("nil", bool(x["nil"])),
                    ("content", x["content"]), ("sign", x["attrs"].get("sign")), ("bad", bad)]))
    return od([("dec", dict(dec)), ("records", recs), ("stats", st)])


def head_marks_by_table(text, matches):
    u"""file の字と行の当たり → {表の通し番号: 表の頭の印}(表の中で、最初に数の fact が出る行より前の行の字の並び。便 XZ1 の ``head_mark`` を呼ぶ)。"""
    starts = [m.start() for m in Z.TABLE_RE.finditer(text)]
    head_rows, closed = {}, set()
    for m in matches:
        ser = bisect.bisect_left(starts, m.start())
        if Z.FACT_RE.search(m.group(0)):
            closed.add(ser)
        elif ser not in closed:
            head_rows.setdefault(ser, []).append(m.group(0))
    return dict((ser, G.head_mark(r)) for ser, r in head_rows.items())


def read_zip_side(zip_path):
    u"""zip 1 本 → ``build_side`` の戻り(字の読み出し → 表を剥がす → 型の分析の順に前の便の関数を呼ぶ)。断り(``M.Refuse``)は止まる。"""
    with zipfile.ZipFile(zip_path) as z:
        texts = N.doc_texts(z)
    files, _names, _tables = M.P.peel_tables(M.B.load_package(zip_path))
    try:
        an = M.analyze(files)
    except Refuse as exc:
        raise Stop(u"**書類の分析が断りを出した(封に断った組の決めが無い)。止める: %s**" % exc.reason)
    return build_side(texts, files, an)


# ======================================================================================================
# 作る側(封 §2-1。今年の書類の答えを読む)
def exclusion_of(r):
    u"""fact 1 つ → xlsx に書かない理由か None(封 §3 の順で先に当たった 1 つ)。"""
    if not r["T"]:
        return EXCLUDES[0]
    if r["bad"]:
        return EXCLUDES[1]
    letter = FORM_LETTER.get(r["form"]) if r["nil"] else UNIT_OF.get((r["form"], r["shift"]))
    if letter is None:
        return EXCLUDES[2]
    if not r["nil"] and sig_digits(r["content"]) > MAX_DIGITS:
        return EXCLUDES[3]
    return None


def amount_cell(r):
    u"""fact → (数のセルの値か「－」, 表示形式)。空でない fact は表示の数(負の印ありなら負。小数の桁の数が 0 なら整数)。"""
    if r["nil"]:
        return NIL_CELL, "General"
    dig = frac_digits(r["content"])
    d = decimal.Decimal(r["content"].replace(u",", u""))
    if r["neg"]:
        d = -d
    v = int(d) if dig == 0 else float(d)
    return v, (u"0" if dig == 0 else u"0." + u"0" * dig)


def day_of(s):
    return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def sheet_rows_of(side):
    u"""1 年分(``build_side`` の戻り)→ (xlsx の行の並び, 答えの行の並び, 数)。xlsx に書かない fact は理由ごとに数える。"""
    rows, answers = [], []
    cnt = od([("inrow", side["stats"]["inrow"]), ("files_out", side["stats"]["files_out"]), ("ix_out", side["stats"]["ix_out"]), ("inrow_out", side["stats"]["inrow_out"])])
    for e in EXCLUDES:
        cnt[e] = 0
    for r in side["records"]:
        why = exclusion_of(r)
        if why is not None:
            cnt[why] += 1
            continue
        v, fmt = amount_cell(r)
        letter = FORM_LETTER[r["form"]] if r["nil"] else UNIT_OF[(r["form"], r["shift"])]
        dates = r["dates"]
        start, end = (dates[0], dates[1]) if r["pkind"] == "duration" else (None, dates[0])
        rows.append(od([("h", r["h"]), ("th", r["th"]), ("T", r["T"]), ("td", r["td"]), ("hmark", r["hmark"]), ("amount", v), ("fmt", fmt),
                        ("start", start), ("end", end), ("unit", letter)]))
        answers.append(od([("kind", M.KIND_NUM), ("name", r["name"]), ("target", r["target"]), ("dims", [list(d) for d in r["dims"]]), ("pkind", r["pkind"]), ("period", list(dates)),
                           ("value", r["value"]), ("form", r["form"]), ("shift", r["shift"]), ("prec", r["prec"]), ("nil", r["nil"]), ("mark", r["neg"])]))
    cnt["D"] = len(rows)
    if cnt["D"] != cnt["inrow"] - cnt["inrow_out"] - sum(cnt[e] for e in EXCLUDES):
        raise Stop(u"**D が行の中の数の fact から引いた数と合わない。止める**")
    return rows, answers, cnt


def write_xlsx(path, dec, rows):
    u"""書類のシート(当期の始まりの日・終わりの日・提出の日。日付のセル)と数のシート(1 行 9 欄)を排他で書く。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET_DOC
    ws.append(list(HEAD_DOC))
    ws.append([day_of(dec["start"]), day_of(dec["end"]), day_of(dec["filing"])])
    wn = wb.create_sheet(SHEET_NUM)
    wn.append(list(HEAD_NUM))
    for i, r in enumerate(rows, 2):
        wn.append([r["h"], r["th"], r["T"], r["td"], r["hmark"] or None, r["amount"], day_of(r["start"]) if r["start"] else None, day_of(r["end"]), r["unit"]])
        for col in "ACEI":
            c = wn["%s%d" % (col, i)]
            if isinstance(c.value, str):
                c.data_type = "s"
        wn["F%d" % i].number_format = r["fmt"]
    with open(path, "xb") as fh:
        wb.save(fh)


def make_pair_files(n, cur_side, xlsx_dir, ans_dir):
    u"""今年の側 1 組 → xlsx と答えの file を別の folder に書く。"""
    rows, answers, cnt = sheet_rows_of(cur_side)
    write_xlsx(os.path.join(xlsx_dir, u"%02d.xlsx" % n), cur_side["dec"], rows)
    write_new(os.path.join(ans_dir, u"%02d.json" % n), dumps(od([(u"番号", n), (u"数", cnt), (u"答え", answers)])))
    return cnt


def write_new(path, text):
    with open(path, "xb") as fh:
        fh.write(text.encode("utf-8"))


def make_folders(tmp, pairs, reader=None):
    u"""作る側: ``tmp`` の下に xlsx の folder と答えの folder を別に書く(今年の書類の答えを読むのはこの工程だけ)。pairs = ``make_pairs`` の組の並び。"""
    reader = reader or read_zip_side
    xdir, adir = os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"answer")
    os.makedirs(xdir)
    os.makedirs(adir)
    out = od()
    for n, _stem, p, _pstem, _pp, _code in pairs:
        out[n] = make_pair_files(n, reader(p), xdir, adir)
    return out


# ======================================================================================================
# 受ける側(封 §2-2。今年の書類も答えも開かない)
def prior_table(side):
    u"""去年の側(``build_side`` の戻り)→ 鍵 (h, th, T, td) ごとの集まり。T が空でなく型の外でない fact だけ。"""
    tab = {}
    for r in side["records"]:
        if not r["T"] or r["bad"]:
            continue
        e = tab.setdefault(key_of(r), od([("cands", set()), ("flips", set()), ("pns", set()), ("forms", set()), ("marks", set()), ("shifts", set())]))
        e["cands"].add((r["name"], r["target"], r["dims"]))
        if not r["nil"]:
            e["flips"].add(r["neg"] != (r["sign"] == "-"))
            e["shifts"].add(r["shift"])
        e["pns"].add(r["pn"])
        e["forms"].add(r["form"])
        e["marks"].add(r["hmark"])
    return tab


def read_xlsx(path):
    u"""xlsx 1 つ → (書類の決め(日の字), 数の行の並び)。"""
    wb = openpyxl.load_workbook(path)
    d = [c.value for c in wb[SHEET_DOC][2]]
    dec = od()
    for k, v in zip(("start", "end", "filing"), d):
        if not isinstance(v, datetime.datetime):
            raise Stop(u"**書類のシートの日が日付のセルでない。止める**")
        dec[k] = v.date().isoformat()
    rows = []
    for cells in wb[SHEET_NUM].iter_rows(min_row=2):
        v = [c.value for c in cells]
        if all(x is None for x in v):
            continue
        h, th, T, td, hm, amount, start, end, unit = v
        rows.append(od([("h", h), ("th", th), ("T", T), ("td", td), ("hmark", hm or u""), ("amount", amount), ("fmt", cells[5].number_format),
                        ("start", date_text(start)), ("end", date_text(end)), ("unit", unit)]))
    return dec, rows


def date_text(v):
    if v is None:
        return None
    if not isinstance(v, datetime.datetime):
        raise Stop(u"**日のセルが日付のセルでない。止める**")
    return v.date().isoformat()


def read_amount(cell, fmt):
    u"""数のセル → (空か, 負か, 表示の字(``,`` なし。数のセルのときだけ), 小数の桁の数)。「－」は空。"""
    if cell == NIL_CELL:
        return True, False, None, None
    if isinstance(cell, bool) or not isinstance(cell, (int, float)):
        raise Stop(u"**金額のセルが数でも「－」でもない。止める**")
    m = FORMAT_RE.match(fmt or u"")
    if m is None:
        raise Stop(u"**数のセルの表示形式が決めた形でない。止める**")
    dig = len(m.group(1)) if m.group(1) else 0
    neg = math.copysign(1.0, float(cell)) < 0
    a = decimal.Decimal(repr(abs(cell))) if isinstance(cell, float) else decimal.Decimal(abs(cell))
    q = a.quantize(decimal.Decimal(1).scaleb(-dig))
    return False, neg, format(q, "f"), dig


def decide_row(row, dec, e):
    u"""xlsx の 1 行と鍵の集まり ``e``(候補が 1 つ)→ (決めた中身, 去年が空で既定の順を使ったか)。封 §2-2 の 8.(守りは見ない)。"""
    (cand,) = e["cands"]
    nil, neg, content, dig = read_amount(row["amount"], row["fmt"])
    kind = "duration" if row["start"] else "instant"
    dates = [row["start"], row["end"]] if row["start"] else [row["end"]]
    if nil:
        form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE
        default = False
    else:
        form, shift = LETTER_TO_UNIT[row["unit"]]
        prec = -shift + dig
        flips = e["flips"]
        default = not flips
        flip = flips == set([True])
        value = M.number_value(content, shift, u"-" if neg != flip else None)
    return od([("name", cand[0]), ("target", cand[1]), ("dims", [list(d) for d in cand[2]]), ("pkind", kind), ("period", dates),
               ("value", value), ("form", form), ("shift", shift), ("prec", prec), ("nil", nil)]), default


def numbered_cand(cand):
    u"""候補の区分に番号つきの member が在るか(member の名の、最初の ``:`` より後ろで見る)。"""
    return any(G.MEMBER_RE.match(local_name(m)) for _ax, m in cand[2])


def receive_row(i, row, dec, tab):
    u"""xlsx の 1 行 → 行ごとの決め(か止めの理由)。次の順で、先に当たった止めで止める(封 §2-2)。"""
    e = tab.get(key_of(row))
    out = od([("i", i), ("stop", u""), ("decided", None), ("cf", None), ("default", False), ("shift_differs", False)])
    if e is None:
        out["stop"] = S_NONE
        return out
    if len(e["cands"]) >= 2:
        out["stop"] = S_MULTI
        return out
    nil = row["amount"] == NIL_CELL
    if not nil and e["shifts"]:
        out["shift_differs"] = LETTER_TO_UNIT[row["unit"]][1] not in e["shifts"]
    kind = "duration" if row["start"] else "instant"
    pn = M.period_name(kind, [row["start"], row["end"]] if row["start"] else [row["end"]], dec)
    form = LETTER_TO_FORM[row["unit"]] if nil else LETTER_TO_UNIT[row["unit"]][0]
    (cand,) = e["cands"]
    cf, default = decide_row(row, dec, e)
    guard = None
    if row["hmark"] not in e["marks"]:
        guard = S_HEAD
    elif pn is None or pn not in e["pns"]:
        guard = S_PERIOD
    elif numbered_cand(cand):
        guard = S_NUMBERED
    elif form not in e["forms"]:
        guard = S_UNIT
    if guard is not None:
        out["stop"], out["cf"] = guard, cf
        return out
    if not nil and len(e["flips"]) == 2:
        out["stop"] = S_SIGN
        return out
    out["decided"], out["default"] = cf, default
    return out


def receive_pair(xlsx_path, prior_side):
    u"""受ける側 1 組。引数は今年の xlsx の path と去年の側(``build_side`` の戻り)だけ。今年の zip・答えは取らない。"""
    dec, rows = read_xlsx(xlsx_path)
    tab = prior_table(prior_side)
    results = [receive_row(i, r, dec, tab) for i, r in enumerate(rows)]
    here = set(key_of(r) for r in rows)
    return od([("rows", results), ("lost", sum(1 for k in tab if k not in here))])


def receive_folder(xlsx_dir, out_dir, prior_paths, reader=None):
    u"""受ける側: xlsx の folder と去年の書類の path(組の番号 → path)だけを読み、行ごとの決めを出力の folder に書く。今年の zip も答えの folder も開かない。"""
    reader = reader or read_zip_side
    os.makedirs(out_dir)
    for n in sorted(prior_paths):
        xp = os.path.join(xlsx_dir, u"%02d.xlsx" % n)
        if not os.path.isfile(xp):
            raise Stop(u"**組 %d の xlsx が無い。止める**" % n)
        res = receive_pair(xp, reader(prior_paths[n]))
        write_new(os.path.join(out_dir, u"%02d.json" % n), dumps(od([(u"番号", n), (u"受けた", res)])))


# ======================================================================================================
# 採点(封 §2-3。受ける側の出力と答えの file を比べる)
def differing_fields(dec, ans):
    u"""決めた中身と答えの行 → 違う欄の名の並び(``FIELDS`` の順)。"""
    return [f for f in FIELDS if dec[FIELD_KEY[f]] != ans[FIELD_KEY[f]]]


def sign_only(dec, ans, diffs):
    u"""違うのは値だけで、絶対値は同じ(符号だけ違う)か。"""
    return diffs == [u"値"] and dec["value"].lstrip(u"-") == ans["value"].lstrip(u"-")


def two_(k=u"件数"):
    return od([(k, 0), (u"決めて全部同じ", 0), (u"決めたが違う", 0), (u"止めた", 0)])


def zero_entry():
    u"""組 1 つの数(全部 0)。"""
    return od([
        (u"行の中の数の fact", 0),
        (u"突き合わせの外", od([(u"file", 0), (u"ix:nonFraction の fact", 0), (u"うち行の中の数の fact", 0)])),
        (u"xlsx に書かなかった fact", od((e, 0) for e in EXCLUDES)),
        (u"D", 0), (u"決めて全部同じ", 0), (u"決めたが違う", 0), (u"止めた", 0),
        (u"決めたが違うの内訳", od([(u"欄ごと", od((f, 0) for f in FIELDS)), (u"符号だけ違う", 0), (u"符号だけ違うのうち答えの値が符号つきの 0", 0), (u"去年が空で既定の順を使った", 0)])),
        (u"止めた理由ごと", od((r, 0) for r in STOPS)),
        (u"守りの止め", od((GUARD_LABEL[g], od([(u"止めた", 0), (u"正しかった止め", 0)])) for g in GUARDS)),
        (u"場面", od([(u"負の印あり", 0), (u"表示の数が 0", 0), (u"空", 0), (u"符号の向きが逆", 0), (u"去年の同じ鍵と表示の位が違う", two_())])),
        (u"無くなった行", 0)])


def score_pair(n, cnt, answers, received):
    u"""組 1 つ → 記録の書類 1 つ。cnt = 作る側の数・answers = 答えの行の並び・received = 受ける側の出力。行は並びの順で 1 対 1。"""
    rows = received["rows"]
    if len(rows) != len(answers) or len(answers) != cnt["D"]:
        raise Stop(u"**受ける側の行の数と答えの行の数が合わない。止める**")
    ent = od([(u"番号", n)])
    ent.update(zero_entry())
    ent[u"行の中の数の fact"] = cnt["inrow"]
    ent[u"突き合わせの外"] = od([(u"file", cnt["files_out"]), (u"ix:nonFraction の fact", cnt["ix_out"]), (u"うち行の中の数の fact", cnt["inrow_out"])])
    ent[u"xlsx に書かなかった fact"] = od((e, cnt[e]) for e in EXCLUDES)
    ent[u"D"] = cnt["D"]
    inner, why = ent[u"決めたが違うの内訳"], ent[u"止めた理由ごと"]
    sc = ent[u"場面"]
    for res, ans in zip(rows, answers):
        sign_rev = (not ans["nil"]) and ans["mark"] != ans["value"].startswith(u"-")
        if res["stop"]:
            r = u"止めた"
            ent[u"止めた"] += 1
            why[res["stop"]] += 1
            if res["stop"] in GUARDS:
                g = ent[u"守りの止め"][GUARD_LABEL[res["stop"]]]
                g[u"止めた"] += 1
                if not differing_fields(res["cf"], ans):
                    g[u"正しかった止め"] += 1
        else:
            diffs = differing_fields(res["decided"], ans)
            if not diffs:
                r = u"決めて全部同じ"
                ent[r] += 1
            else:
                r = u"決めたが違う"
                ent[r] += 1
                for f in diffs:
                    inner[u"欄ごと"][f] += 1
                if sign_only(res["decided"], ans, diffs):
                    inner[u"符号だけ違う"] += 1
                    if ans["value"] == u"-0":
                        inner[u"符号だけ違うのうち答えの値が符号つきの 0"] += 1
                if res["default"]:
                    inner[u"去年が空で既定の順を使った"] += 1
        if ans["mark"] and not ans["nil"]:
            sc[u"負の印あり"] += 1
        if (not ans["nil"]) and ans["value"].lstrip(u"-") == u"0":
            sc[u"表示の数が 0"] += 1
        if ans["nil"]:
            sc[u"空"] += 1
        if sign_rev:
            sc[u"符号の向きが逆"] += 1
        if res["shift_differs"]:
            s = sc[u"去年の同じ鍵と表示の位が違う"]
            s[u"件数"] += 1
            s[r] += 1
    ent[u"無くなった行"] = received["lost"]
    return ent


def load_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.loads(fh.read(), object_pairs_hook=od)


def score_folders(out_dir, ans_dir, nos):
    u"""採点: 出力の folder と答えの folder の ``nos`` の組を比べる。(組ごとの記録の書類の並び, 答えの名の集まり(secret 用))。"""
    entries, names = [], set()
    for n in nos:
        a = load_json(os.path.join(ans_dir, u"%02d.json" % n))
        o = load_json(os.path.join(out_dir, u"%02d.json" % n))
        if a[u"番号"] != n or o[u"番号"] != n:
            raise Stop(u"**組の番号が file の番号と違う。止める**")
        entries.append(score_pair(n, a[u"数"], a[u"答え"], o[u"受けた"]))
        for r in a[u"答え"]:
            names.add(local_name(r["name"]))
            names.add(r["name"].split(u":", 1)[0])
            for ax, mb in r["dims"]:
                names.add(local_name(ax))
                names.add(local_name(mb))
    return entries, names


# ======================================================================================================
# 集計・予測の判定・旗
def totals_of(entries):
    u"""組ごとの数の並び → (訓練の 3 組・判定の 60 組・全部 63 組)の数の合計。"""
    def group(es):
        body = [od((k, v) for k, v in e.items() if k not in NOT_SUMMED) for e in es]
        return od([(u"組", len(es)), (u"数", M.sum_nested(body) if body else od())])
    return od([(u"訓練の 3 組", group([e for e in entries if e[u"番号"] <= SEEN_MAX_NO])),
               (u"判定の 60 組", group([e for e in entries if e[u"番号"] > SEEN_MAX_NO])),
               (u"全部", group(entries))])


def holds_bound(b, x):
    u"""予測の境(下限, 下限を含むか, 上限, 上限を含むか)に値 x(``Fraction`` か数)が入るか。"""
    lo, lo_in, hi, hi_in = b
    ok = True
    if lo is not None:
        c = fractions.Fraction(str(lo))
        ok = ok and (x >= c if lo_in else x > c)
    if hi is not None:
        c = fractions.Fraction(str(hi))
        ok = ok and (x <= c if hi_in else x < c)
    return ok


def rate_holds(n, d, b):
    u"""n ÷ d(%)が境 b に入るか(d が 0 なら入らない)。整数と ``Fraction`` で比べる。"""
    return d > 0 and holds_bound(b, fractions.Fraction(100 * n, d))


def rate_of(n, d):
    return od([(u"fact", n), (u"分母", d), (u"%", pct1(n, d))])


def judged(entries):
    u"""判定の 60 組(番号が 3 より大きい組)の数から予測 XE0-1〜XE0-9 の判定に要る数と当たり外れを導く。"""
    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]
    tot = M.sum_nested([od((k, v) for k, v in e.items() if k not in NOT_SUMMED) for e in rest]) if rest else od()
    D = tot.get(u"D", 0)
    same, diff, stop = tot.get(u"決めて全部同じ", 0), tot.get(u"決めたが違う", 0), tot.get(u"止めた", 0)
    inner = tot.get(u"決めたが違うの内訳", {})
    only_sign = inner.get(u"符号だけ違う", 0)
    gs = tot.get(u"守りの止め", {})
    g_stop = sum(gs[GUARD_LABEL[g]][u"止めた"] for g in GUARDS) if gs else 0
    g_ok = sum(gs[GUARD_LABEL[g]][u"正しかった止め"] for g in GUARDS) if gs else 0
    g12 = (gs[GUARD_LABEL[S_PERIOD]][u"止めた"] + gs[GUARD_LABEL[S_UNIT]][u"止めた"]) if gs else 0
    bad_unit = tot.get(u"xlsx に書かなかった fact", {})
    unw = (bad_unit.get(EXCLUDES[2], 0) + bad_unit.get(EXCLUDES[3], 0)) if bad_unit else 0
    inrow = tot.get(u"行の中の数の fact", 0)
    no_diff = sum(1 for e in rest if e[u"決めたが違う"] == 0)
    high = sum(1 for e in rest if rate_holds(e[u"決めて全部同じ"], e[u"D"], (DOC_SAME_PCT, True, None, False)))
    out = od()

    def put(key, body, hit):
        b = od(body)
        b[u"当たり"] = bool(hit)
        out[key] = b
    put(u"XE0-1 決めて全部同じ ÷ D", [(u"率", rate_of(same, D))], rate_holds(same, D, BOUNDS["XE0-1"]))
    put(u"XE0-2 決めたが違う ÷ D(1 fact 以上)", [(u"率", rate_of(diff, D))], diff >= MIN_DIFF and rate_holds(diff, D, BOUNDS["XE0-2"]))
    put(u"XE0-3 決めたが違うのうち符号だけ違う", [(u"fact", only_sign), (u"決めたが違う", diff)], holds_bound(BOUNDS["XE0-3"], only_sign))
    put(u"XE0-4 止めた ÷ D", [(u"率", rate_of(stop, D))], rate_holds(stop, D, BOUNDS["XE0-4"]))
    put(u"XE0-5 守りの止めのうち正しかった止め", [(u"率", rate_of(g_ok, g_stop))], rate_holds(g_ok, g_stop, BOUNDS["XE0-5"]))
    put(u"XE0-6 守り G1(期)と G2(単位)の止め ÷ D(1 fact 以上)", [(u"率", rate_of(g12, D))], g12 >= MIN_G12 and rate_holds(g12, D, BOUNDS["XE0-6"]))
    put(u"XE0-7 単位が書けない・15 桁を超える ÷ 行の中の数の fact", [(u"率", rate_of(unw, inrow))], rate_holds(unw, inrow, BOUNDS["XE0-7"]))
    put(u"XE0-8 決めたが違うが 0 の書類", [(u"書類", no_diff), (u"分母", len(rest))], holds_bound(BOUNDS["XE0-8"], no_diff))
    put(u"XE0-9 決めて全部同じ ÷ その書類の D が %s%% 以上の書類" % DOC_SAME_PCT, [(u"書類", high), (u"分母", len(rest))], holds_bound(BOUNDS["XE0-9"], high))
    return out


def seal_flag(entries):
    u"""封 §3 の「§0 と違う」の旗(訓練の 3 組の 4 つの数が §0 の数と違えば立つ。止めない)。"""
    t = totals_of(entries)[u"訓練の 3 組"][u"数"]
    got = od((k, t.get(k, 0)) for k in SEAL_TRAIN)
    return od([(u"訓練の 3 組の数", got), (u"封 §0 の数", od(SEAL_TRAIN)), (u"§0 と違う", dict(got) != dict(SEAL_TRAIN))])


ORIGIN = od([
    (u"名・個別か既定か・区分", u"去年から持ち越し"), (u"期の日", u"会社が書いた欄からそのまま"), (u"期の種類", u"規則で(日付が 1 つか 2 つか)"),
    (u"値の大きさ", u"会社が書いた欄からそのまま(表示の位は規則で)"), (u"値の符号", u"規則で(負の印)と去年から持ち越し(符号の向き)"),
    (u"単位の形・表示の位", u"規則で(単位の字の表の逆引き)"), (u"精度", u"規則で(数のセルの表示形式)"), (u"空か", u"会社が書いた欄からそのまま(「－」)")])


# ======================================================================================================
# 記録
def entry_problems(e):
    u"""組 1 つの数の導ける関係(数の足し算)。違えば理由の字。"""
    z = zero_entry()
    if list(e) != [u"番号"] + list(z):
        return u"組の欄が違う"
    ow = e[u"xlsx に書かなかった fact"]
    out = e[u"突き合わせの外"]
    if e[u"D"] != e[u"行の中の数の fact"] - out[u"うち行の中の数の fact"] - sum(ow.values()):
        return u"D が行の中の数の fact から引いた数と合わない"
    if out[u"うち行の中の数の fact"] > out[u"ix:nonFraction の fact"] or out[u"うち行の中の数の fact"] > e[u"行の中の数の fact"] or (out[u"file"] == 0) != (out[u"ix:nonFraction の fact"] == 0):
        return u"突き合わせの外の数が合わない"
    if e[u"決めて全部同じ"] + e[u"決めたが違う"] + e[u"止めた"] != e[u"D"]:
        return u"決めて全部同じ + 決めたが違う + 止めたが D と合わない"
    inner = e[u"決めたが違うの内訳"]
    if sum(inner[u"欄ごと"].values()) < e[u"決めたが違う"] or any(v > e[u"決めたが違う"] for v in inner[u"欄ごと"].values()):
        return u"違った欄の数が決めたが違うと合わない"
    if inner[u"符号だけ違う"] > e[u"決めたが違う"] or inner[u"符号だけ違うのうち答えの値が符号つきの 0"] > inner[u"符号だけ違う"] or inner[u"去年が空で既定の順を使った"] > e[u"決めたが違う"]:
        return u"符号だけ違うの数が合わない"
    if inner[u"符号だけ違う"] > inner[u"欄ごと"][u"値"]:
        return u"符号だけ違うが値の違いより多い"
    why = e[u"止めた理由ごと"]
    if sum(why.values()) != e[u"止めた"]:
        return u"止めた理由ごとの合計が止めたと合わない"
    for g in GUARDS:
        s = e[u"守りの止め"][GUARD_LABEL[g]]
        if s[u"止めた"] != why[g] or s[u"正しかった止め"] > s[u"止めた"]:
            return u"守りの止めの数が合わない"
    sc = e[u"場面"]
    if sc[u"負の印あり"] > e[u"D"] or sc[u"表示の数が 0"] > e[u"D"] or sc[u"空"] > e[u"D"] or sc[u"符号の向きが逆"] > e[u"D"]:
        return u"場面の数が D より多い"
    s = sc[u"去年の同じ鍵と表示の位が違う"]
    if s[u"決めて全部同じ"] + s[u"決めたが違う"] + s[u"止めた"] != s[u"件数"] or s[u"件数"] > e[u"D"]:
        return u"表示の位が違う fact の分けが合わない"
    return u""


def build_record(entries, material, secret_names, sha_script=None):
    u"""組ごとの数の並び(番号の昇順 63 組)→ (記録, 漏れの検査に使う材料)。書かない。"""
    nos = [e[u"番号"] for e in entries]
    if len(entries) != PAIRS_WANT or nos != sorted(set(nos)):
        raise Stop(u"**組が 63 でないか番号が昇順でない。止める**")
    tot = totals_of(entries)
    if tot[u"訓練の 3 組"][u"組"] != TRAIN_WANT or tot[u"判定の 60 組"][u"組"] != JUDGE_WANT:
        raise Stop(u"**組の数が訓練 3・判定 60・全部 63 でない。止める**")
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XE0(会社が Excel で出すとしたら、XBRL の言葉を書かない欄だけで今年の型はどれだけ決まり・黙って違い・止まるか)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha_script or sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od(material)
    rec[u"書類"] = entries
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XE0-1〜XE0-9。判定の 60 組だけ。当たり・外れ)"] = judged(entries)
    rec[u"型の欄ごとの出どころ"] = od(ORIGIN)
    rec[u"§3 の旗"] = seal_flag(entries)
    rec[u"限界"] = list(LIMITS)
    return rec, secret_names


def judged_key(rec):
    return [k for k in rec if k.startswith(u"予測の判定に要る数")][0]


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(欄・docID・EDINET コード・file の名・要素の名・日付の形)が無いか。在れば止める。secret = (行の字, 要素の局所名, docID の並び, EDINET コードの集まり, 見出しの字, 業種の値)。"""
    N.check_clean(rec, text, secret)
    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def verify_record(rec, text=None, want=PAIRS_WANT):
    u"""記録の形・組ごとの数からの導き直し(集計・予測の当たり外れ・旗)・禁止のものを検査する(置き場は読まない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"組の数"] != want:
        raise Stop(u"**記録の組が 63 でない。止める**")
    nos = [d.get(u"番号") for d in docs]
    if any(not isinstance(n, int) for n in nos) or nos != sorted(set(nos)):
        raise Stop(u"**記録の組の番号が昇順でない。止める**")
    for d in docs:
        why = entry_problems(d)
        if why:
            raise Stop(u"**記録の組の数が違う: %s。止める**" % why)
    if dumps(totals_of(docs)) != dumps(rec[u"集計"]):
        raise Stop(u"**記録の集計が組ごとの数と合わない。止める**")
    if dumps(judged(docs)) != dumps(rec[judged_key(rec)]):
        raise Stop(u"**記録の判定の数が組ごとの数と合わない。止める**")
    if dumps(seal_flag(docs)) != dumps(rec[u"§3 の旗"]):
        raise Stop(u"**記録の旗が組ごとの数と合わない。止める**")
    tot = rec[u"集計"]
    if (tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]) != (TRAIN_WANT, JUDGE_WANT) or rec[u"限界"] != list(LIMITS) or rec[u"型の欄ごとの出どころ"] != dict(ORIGIN):
        raise Stop(u"**記録の材料・限界・出どころが違う。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def secret_of(docs, pairs, names):
    u"""記録に書かないものの集まり(要素の局所名・docID・提出者のコード)。"""
    ecodes = set(p[5] for p in pairs)
    for x in docs:
        for s in x[2]:
            ecodes.update(re.findall(r"E\d{5}", s))
    return (set(), set(n for n in names if len(n) >= 3), [d[0] for d in docs] + [p[3] for p in pairs], ecodes, set(), set())


def material_of(docs, pairs):
    return [(u"今年の側の書類の本数", len(docs)), (u"今年の側の書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),
            (u"組の数", len(pairs)), (u"訓練の組の数", sum(1 for p in pairs if p[0] <= SEEN_MAX_NO)), (u"判定の組の数", sum(1 for p in pairs if p[0] > SEEN_MAX_NO)),
            (u"除いた今年の書類の数", len(docs) - len(pairs)),
            (u"前の年の側の組の相手の file 名の並びの sha256", sha256_bytes(u"\n".join(p[3] for p in pairs).encode("utf-8")))]


# ======================================================================================================
# 工程の入口
def prior_paths_of(pairs, nos=None):
    u"""``make_pairs`` の組 → {組の番号: 去年の path}(今年の path は渡さない)。"""
    return dict((p[0], p[4]) for p in pairs if nos is None or p[0] in nos)


def score_run(out_dir, ans_dir, root=ROOT, docs=None, prior=None, out=None, say=print):
    u"""採点の工程: 出力の folder と答えの folder から記録を排他で書く。"""
    docs_, pairs, _ex = Y.make_pairs(docs or DOCS_DIR, prior or PRIOR_DIR)
    entries, names = score_folders(out_dir, ans_dir, [p[0] for p in pairs])
    rec, secret = build_record(entries, material_of(docs_, pairs), secret_of(docs_, pairs, names))
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    show_flag(rec, say)
    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))
    return rec


def show_flag(rec, say=print):
    say(u"§3 の旗: %s" % (u"立った" if rec[u"§3 の旗"][u"§0 と違う"] else u"立たない"))


def check(root=ROOT, rec_path=None, say=print, want=PAIRS_WANT):
    u"""記録の形・組ごとの数からの導き直し・禁止のものを検査する。置き場は読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=od)
    verify_record(rec, text, want)
    say(u"--check: 記録の形・組ごとの数からの導き直し・禁止のものの検査は通った(組 %d)" % len(rec[u"書類"]))
    return rec


def dev_summary(entries):
    u"""封 §0 の見たものと並べて読める数(3 組の合計)。"""
    t = M.sum_nested([od((k, v) for k, v in e.items() if k not in NOT_SUMMED) for e in entries])
    gs = t[u"守りの止め"]
    why = t[u"止めた理由ごと"]
    return od([
        (u"組", len(entries)), (u"行の中の数の fact", t[u"行の中の数の fact"]), (u"突き合わせの外", dict(t[u"突き合わせの外"])), (u"xlsx に書かなかった fact", dict(t[u"xlsx に書かなかった fact"])),
        (u"D", t[u"D"]), (u"決めて全部同じ", t[u"決めて全部同じ"]), (u"決めたが違う", t[u"決めたが違う"]), (u"決めたが違うの内訳", dict((k, (dict(v) if isinstance(v, dict) else v)) for k, v in t[u"決めたが違うの内訳"].items())),
        (u"止めた", t[u"止めた"]), (u"止めた理由ごと", dict(why)), (u"守りの止め", dict((k, dict(v)) for k, v in gs.items())),
        (u"場面", dict((k, (dict(v) if isinstance(v, dict) else v)) for k, v in t[u"場面"].items())), (u"無くなった行", t[u"無くなった行"]),
        (u"封 §0 と照らす", seal_flag(entries))])


def dev_run(tmp, docs_dir=None, prior_dir=None, say=print, reader=None, pairs=None):
    u"""番号 1・2・3 の 3 組だけを 3 工程(別の folder を通して)通す。記録は書かない。番号 4 以上の組は読まない。"""
    if pairs is None:
        _docs, pairs, _ex = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR)
    sub = [p for p in pairs if p[0] in DEV_NOS]
    make_folders(tmp, sub, reader)
    receive_folder(os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"out"), prior_paths_of(sub), reader)
    entries, _names = score_folders(os.path.join(tmp, u"out"), os.path.join(tmp, u"answer"), [p[0] for p in sub])
    say(json.dumps(dev_summary(entries), ensure_ascii=False, indent=1))
    return entries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--make", metavar="TMP", help="作る側: 一時の folder の下に xlsx の folder と答えの folder を別に書く")
    ap.add_argument("--receive", nargs=2, metavar=("XLSX_DIR", "OUT_DIR"), help="受ける側: xlsx の folder と去年の書類だけを読み、出力の folder に書く")
    ap.add_argument("--score", nargs=2, metavar=("OUT_DIR", "ANSWER_DIR"), help="採点: 出力の folder と答えの folder を比べ、記録を排他で書く")
    ap.add_argument("--check", action="store_true", help="記録の形・組ごとの数からの導き直し・禁止のものを検査する。置き場は読まない")
    ap.add_argument("--dev", action="store_true", help="番号 1・2・3 の 3 組だけを 3 工程通して表示する。記録は書かない(--tmp が要る)")
    ap.add_argument("--tmp", default=None, help="--dev の一時の folder(まだ無い場所)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="今年の側の置き場(既定は封の字)")
    ap.add_argument("--prior", default=None, help="前の年の側の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
    elif a.dev:
        if not a.tmp:
            raise Stop(u"**--dev には --tmp が要る。止める**")
        dev_run(a.tmp, a.docs, a.prior)
    elif a.make:
        _docs, pairs, _ex = Y.make_pairs(a.docs or DOCS_DIR, a.prior or PRIOR_DIR)
        make_folders(a.make, pairs)
    elif a.receive:
        _docs, pairs, _ex = Y.make_pairs(a.docs or DOCS_DIR, a.prior or PRIOR_DIR)
        receive_folder(a.receive[0], a.receive[1], prior_paths_of(pairs))
    elif a.score:
        score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)
    else:
        raise Stop(u"**工程の指定が無い(--make・--receive・--score・--check・--dev)。止める**")


if __name__ == "__main__":
    main()
