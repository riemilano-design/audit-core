# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md(便 UM0)の「素材を作る側」。**答えを知っている側。**

作り物の会社(番号 ``i``)の素材・正解の束・材料の変異 M1〜M11・資料の変異 D1〜D5・段 A・B・C の集計・記録を作る。**費用は 0・API は呼ばない。**
同じ ``i`` なら cell の値と字は何度作っても同じ(値の乱数の種は ``20261123 * 1000 + i``。xlsx の byte は同じでなくてよい)。

    python3 universal_source_gen_2026-11-23.py --make <i> --out <folder> [--product A|B]      # 素材(決算.xlsx・月次売上.csv・借入金一覧.csv・人員.csv)と指定.json
    python3 universal_source_gen_2026-11-23.py --gold <i> --out <file> [--product A|B]        # 正解の束(B は b01 だけ)
    python3 universal_source_gen_2026-11-23.py --write-defs <folder>                          # 定義表 A・B
    python3 universal_source_gen_2026-11-23.py --tally-a --companies 101 102 103 [--out <f>]  # 段 A の集計(検査は別の file の関数を importlib で呼ぶ)
    python3 universal_source_gen_2026-11-23.py --tally-bc --seat-dir <folder> --companies ... # 段 B・C の集計(席の出力は <folder>/<i>/材料_A.json・材料_B.json・資料_A.md)
    python3 universal_source_gen_2026-11-23.py --record --seat-dir <folder> [--out <f>]       # 本番の 12 社の記録(席の出力が全部そろってから 1 回だけ)

**本番だけの 12 社(i = 1〜12)の素材は、監査 GO を経て commit されるまで作らない・走らせない。** この file の ``--make``・``--gold`` は i が 1〜12 でも動くが、開発の間は 101〜103 だけに使う。

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 経常利益か当期純利益のどちらかが負になる社: i = 5・10 と(開発の)102 は経常利益を正のまま当期純利益だけ負にする。
- 値の字の書き方: 負の値は字の cell(``-1,234``・``△1,234``・``(1,234)``)・L2 は正の値も字の cell(``1,234``)・それ以外の正の値は数の cell。CSV は ``i`` が偶数なら月次売上、奇数なら借入金の値を桁区切りで書く。
- 月の字の形は ``(i // 2) % 3``(0 → ``M月``・1 → ``YYYY年M月``・2 → ``YYYY/MM``)。月は当期の始まりから時間順。
- 見出しの飾り(罠 T7)は ``(i + 行の番号) % 4``(飾りなし・``Ⅰ ``・``N. ``・前後に全角の空白と空白)。見出しの表の言い方は ``(i + id の番号) % 表の字の数``。
- 素材の和の行の並びは、合計の行を除く明細の行の全部。
"""
from __future__ import print_function

import calendar
import collections
import copy
import csv
import datetime
import importlib.util
import io
import json
import os
import random
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECK_REL = "measure/universal_check_2026-11-23.py"
DEFS_REL = "fixtures/universal/um0"

DEV = (101, 102, 103)
PROD = tuple(range(1, 13))
SEED_BASE = 20261123 * 1000
od = collections.OrderedDict

# ============================================================ 定義表の表と、表の外の言い方(表の外は素材を作る側だけが持つ)
KANJI = [u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九", u"十", u"十一", u"十二"]
#: (id, 名, 単位, 期, 見出しの表, 表の外, 取り方)
ROWS_A = [
    (u"a01", u"売上高(当期)", u"円", u"当期", [u"売上高", u"売上高合計"], [u"営業収益"]),
    (u"a02", u"売上高(前期)", u"円", u"前期", [u"売上高", u"売上高合計"], [u"営業収益"]),
    (u"a03", u"売上総利益(当期)", u"円", u"当期", [u"売上総利益"], [u"粗利益"]),
    (u"a04", u"営業利益(当期)", u"円", u"当期", [u"営業利益"], [u"営業損益"]),
    (u"a05", u"営業利益(前期)", u"円", u"前期", [u"営業利益"], [u"営業損益"]),
    (u"a06", u"経常利益(当期)", u"円", u"当期", [u"経常利益"], [u"経常損益"]),
    (u"a07", u"当期純利益(当期)", u"円", u"当期", [u"当期純利益"], [u"税引後利益"]),
    (u"a08", u"減価償却費(当期)", u"円", u"当期", [u"減価償却費"], [u"償却費"]),
    (u"a09", u"現金及び預金(当期末)", u"円", u"当期末", [u"現金及び預金", u"現金預金"], [u"現預金"]),
    (u"a10", u"流動資産合計(当期末)", u"円", u"当期末", [u"流動資産合計"], [u"流動資産計"]),
    (u"a11", u"資産の総額(当期末)", u"円", u"当期末", [u"資産合計", u"資産の部合計"], [u"総資産"]),
    (u"a12", u"短期借入金(当期末)", u"円", u"当期末", [u"短期借入金"], [u"短期借入"]),
    (u"a13", u"長期借入金(当期末)", u"円", u"当期末", [u"長期借入金"], [u"長期借入"]),
    (u"a14", u"負債合計(当期末)", u"円", u"当期末", [u"負債合計", u"負債の部合計"], [u"負債計"]),
    (u"a15", u"純資産(当期末)", u"円", u"当期末", [u"純資産合計", u"純資産の部合計"], [u"資本合計"]),
    (u"a16", u"純資産(前期末)", u"円", u"前期末", [u"純資産合計", u"純資産の部合計"], [u"資本合計"]),
]
ROWS_A += [(u"a%d" % (16 + k), u"月次売上高(当期の%sか月目)" % KANJI[k - 1], u"円", u"当期の月:%d" % k, [u"売上高", u"月次売上高"], [u"売上金額"]) for k in range(1, 13)]
ROWS_A += [
    (u"a29", u"借入金一覧の残高の合計(当期末)", u"円", u"当期末", [u"期末残高", u"残高"], [u"借入残高"]),
    (u"a30", u"期末の従業員数(当期末)", u"人", u"当期末", [u"期末従業員数", u"従業員数"], [u"社員数"]),
]
ROW_B1 = (u"b01", u"人件費(当期)", u"円", u"当期", [u"人件費", u"人件費合計"], [u"人件費計"])
ALL_ROWS = dict((r[0], r) for r in ROWS_A + [ROW_B1])
SUM_IDS = (u"a29",)
NO_READ_IDS = (u"a29", u"a30")          # 期の読み 無し
T5_LIST = [u"a03", u"a06", u"a07", u"a09", u"a10", u"a12", u"a13", u"a14"]
CALC_A = [
    {u"id": u"a31", u"名": u"借入金合計", u"単位": u"円", u"期": u"当期末", u"式": u"和", u"入力": [u"a12", u"a13"], u"桁": 0},
    {u"id": u"a32", u"名": u"自己資本比率", u"単位": u"純数", u"期": u"当期末", u"式": u"比", u"入力": [u"a15", u"a11"], u"桁": 4},
    {u"id": u"a33", u"名": u"債務償還年数", u"単位": u"年", u"期": u"当期", u"式": u"比の分母和", u"入力": [u"a31", u"a04", u"a08"], u"桁": 2},
]
CALC_B = [
    {u"id": u"b02", u"名": u"売上高増減率", u"単位": u"純数", u"期": u"当期", u"式": u"増減率", u"入力": [u"a01", u"a02"], u"桁": 4},
    {u"id": u"b03", u"名": u"営業利益率", u"単位": u"純数", u"期": u"当期", u"式": u"比", u"入力": [u"a04", u"a01"], u"桁": 4},
    {u"id": u"b04", u"名": u"一人当たり売上", u"単位": u"純数", u"期": u"当期", u"式": u"比", u"入力": [u"a01", u"a30"], u"桁": 0},
]
B_IDS = [u"a01", u"a02", u"a04"] + [u"a%d" % k for k in range(17, 29)] + [u"a30", u"b01"]
REL_A = [{u"id": u"R1", u"左": [u"a%d" % k for k in range(17, 29)], u"右": [u"a01"]},
         {u"id": u"R2", u"左": [u"a11"], u"右": [u"a14", u"a15"]},
         {u"id": u"R3", u"左": [u"a29"], u"右": [u"a12", u"a13"]}]
REL_B = [REL_A[0]]


def def_row(r):
    i, name, unit, per, table, _out = r
    d = od([(u"id", i), (u"名", name), (u"単位", unit), (u"期", per), (u"範囲", u"全社")])
    if i in SUM_IDS:
        d[u"取り方"] = u"素材の和"
    else:
        d[u"取り方"] = u"素材"
    d[u"見出し"] = list(table)
    d[u"期の読み"] = u"無し" if i in NO_READ_IDS else u"要る"
    return d


def def_json(product):
    if product == u"A":
        rows = [def_row(r) for r in ROWS_A] + [od([(u"id", c[u"id"]), (u"名", c[u"名"]), (u"単位", c[u"単位"]), (u"期", c[u"期"]), (u"範囲", u"全社"),
                                                  (u"取り方", u"計算"), (u"式", c[u"式"]), (u"入力", c[u"入力"]), (u"桁", c[u"桁"])]) for c in CALC_A]
        return od([(u"成果物", u"A"), (u"題", u"銀行向けの説明資料"), (u"行", rows), (u"関係", REL_A)])
    rows = [def_row(ALL_ROWS[i]) for i in B_IDS] + [od([(u"id", c[u"id"]), (u"名", c[u"名"]), (u"単位", c[u"単位"]), (u"期", c[u"期"]), (u"範囲", u"全社"),
                                                         (u"取り方", u"計算"), (u"式", c[u"式"]), (u"入力", c[u"入力"]), (u"桁", c[u"桁"])]) for c in CALC_B]
    return od([(u"成果物", u"B"), (u"題", u"月次の経営会議の資料"), (u"行", rows), (u"関係", REL_B)])


def write_defs(folder):
    os.makedirs(folder, exist_ok=True)
    for p in (u"A", u"B"):
        with io.open(os.path.join(folder, "definition_%s.json" % p), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(def_json(p), ensure_ascii=False, indent=1) + u"\n")


# ============================================================ 日付
def addm(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return datetime.date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def iso(d):
    return d.strftime("%Y-%m-%d")


def params(i):
    end = {1: datetime.date(2026, 3, 31), 2: datetime.date(2025, 12, 31), 0: datetime.date(2025, 9, 30)}[i % 3]
    start = addm(end + datetime.timedelta(days=1), -12)
    pe = start - datetime.timedelta(days=1)
    return {
        "i": i, "form": {1: "L1", 2: "L2", 0: "L3"}[i % 3], "cs": start, "ce": end, "ps": addm(start, -12), "pe": pe,
        "mult": (1, 1000, 1000000)[(i // 3) % 3], "jp": i % 2 == 1, "cur_left": i % 4 in (0, 1),
        "has_staff": i % 3 != 0, "has_dep": i % 4 != 0, "neg": {1: "-", 2: u"△", 0: "()"}[i % 3],
        "month_form": (i // 2) % 3, "neg_net": i in (5, 10, 102),
        "t5": sorted(set([T5_LIST[i % 8], T5_LIST[(i + 3) % 8]])),
    }


def unit_label(mult):
    return {1: None, 1000: u"(単位:千円)", 1000000: u"(単位:百万円)"}[mult]


def pick(table, i, ident):
    return table[(i + int(ident[1:])) % len(table)]


def decorate(h, i, k):
    t = (i + k) % 4
    return [h, u"Ⅰ " + h, u"%d. " % (k % 9 + 1) + h, u"　" + h + u" "][t]


def gnum(v):
    u"""素材を作る側の「数の cell」(数なら int、でなければ None)。"""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v
    if not isinstance(v, str):
        return None
    t = v.strip().replace(u",", u"")
    neg = False
    if t[:1] in (u"-", u"△", u"▲"):
        neg, t = True, t[1:]
    elif len(t) >= 2 and t[0] == u"(" and t[-1] == u")":
        neg, t = True, t[1:-1]
    if not t or not (t.isascii() and t.isdigit()):
        return None
    return -int(t) if neg else int(t)


def text_num(v, neg):
    s = u"{:,}".format(abs(v))
    if v < 0:
        if neg == u"-":
            return u"-" + s
        if neg == u"△":
            return u"△" + s
        return u"(" + s + u")"
    return s


def split(total, n, rng):
    w = [rng.randint(5, 15) for _ in range(n)]
    s = sum(w)
    vals = [total * x // s for x in w]
    vals[-1] += total - sum(vals)
    return vals


class Co(object):
    pass


def build(i):
    u"""会社 ``i`` の素材(file ごとの cell の表)・材料の位置(``meta``)・値を作る。乱数は種だけで決まる。"""
    p = params(i)
    rng = random.Random(SEED_BASE + i)
    m = p["mult"]
    q = 10 ** 6 // m
    co = Co()
    co.i, co.p = i, p
    # ---- 値(表示の単位の整数)
    def rr(a, b):
        return rng.uniform(a, b)
    S = rng.randint(300 * q, 9000 * q)
    Sp = int(round(S * rr(.8, 1.2)))
    pl, plp = {}, {}
    for key, scale, dst in (("cur", S, pl), ("prev", Sp, plp)):
        cogs = int(round(scale * rr(.55, .7)))
        gp = scale - cogs
        pers = int(round(scale * rr(.10, .15)))
        oth = int(round(scale * rr(.08, .12)))
        sga = pers + oth
        op = gp - sga
        ni = int(round(scale * .01 * rr(.5, 1.5)))
        ne = int(round(scale * .01 * rr(.5, 1.5)))
        ordi = op + ni - ne
        net = int(round(ordi * .7))
        if p["neg_net"] and key == "cur":
            net = -int(round(scale * rr(.01, .03)))
        dep = int(round(scale * rr(.02, .04)))
        dst.update({"a01": scale, "cogs": cogs, "a03": gp, "b01": pers, "sga": sga, "a04": op, "nonop_inc": ni, "nonop_exp": ne,
                    "a06": ordi, "a07": net, "a08": dep})
    bs, bsp = {}, {}
    for scale, dst in ((S, bs), (int(round(S * rr(.85, 1.1))), bsp)):
        cash = int(round(scale * rr(.05, .15)))
        recv = int(round(scale * rr(.1, .2)))
        fixed = int(round(scale * rr(.3, .6)))
        s_ = int(round(scale * rr(.03, .08)))
        o_ = int(round(scale * rr(.05, .1)))
        l_ = int(round(scale * rr(.05, .15)))
        ol = int(round(scale * rr(.01, .03)))
        cur_a = cash + recv
        total = cur_a + fixed
        cur_l = s_ + o_
        fix_l = l_ + ol
        liab = cur_l + fix_l
        dst.update({"a09": cash, "recv": recv, "a10": cur_a, "fixed": fixed, "a11": total, "a12": s_, "other_cl": o_, "cur_l": cur_l,
                    "a13": l_, "fix_l": fix_l, "a14": liab, "a15": total - liab})
    co.pl, co.plp, co.bs, co.bsp = pl, plp, bs, bsp
    months = split(S * m, 12, rng)
    prior_months = [int(x * rr(.8, 1.2)) for x in split(Sp * m, 12, rng)]
    dept_sales = split(S, 3, rng)
    a, b = rng.randint(0, 100), rng.randint(0, 100)
    dept_op = [pl["a04"] * a // 200, pl["a04"] * b // 200]
    dept_op.append(pl["a04"] - sum(dept_op))
    staff_total = rng.randint(50, 2000)
    staff_reg = int(staff_total * rr(.6, .8))
    n_loans = rng.randint(3, 6)
    n_short = rng.randint(1, n_loans - 1)
    short_parts = split(bs["a12"] * m, n_short, rng)
    long_parts = split(bs["a13"] * m, n_loans - n_short, rng)
    lenders = [u"北辰銀行", u"東和信金", u"みなと信組", u"開発政策金融", u"西国銀行", u"丘の上銀行"]
    loans = [(lenders[k], u"短期", v) for k, v in enumerate(short_parts)] + [(lenders[n_short + k], u"長期", v) for k, v in enumerate(long_parts)]
    co.months, co.loans, co.staff = months, loans, (staff_total, staff_reg)
    # ---- 素材の表
    meta = {}
    files = od()
    text_all = p["form"] == "L2"
    neg = p["neg"]

    def cv(v):
        return text_num(v, neg) if (v < 0 or text_all) else v

    def per_label(block):
        if p["jp"]:
            return (u"当期", u"前期") if block == "PL" else (u"当期末", u"前期末")
        if block == "PL":
            return (u"%d年%d月期" % (p["ce"].year, p["ce"].month), u"%d年%d月期" % (p["pe"].year, p["pe"].month))
        return (u"%d年%d月末" % (p["ce"].year, p["ce"].month), u"%d年%d月末" % (p["pe"].year, p["pe"].month))

    ucell = unit_label(m)
    cur_col, prev_col = (2, 3) if p["cur_left"] else (3, 2)
    co.cols = (cur_col, prev_col)
    sheets = od()
    if p["form"] == "L2":
        names = {"PL": u"試算表", "BS": u"試算表", "DEPT": u"部門別"}
    elif p["form"] == "L1":
        names = {"PL": u"損益", "BS": u"貸借", "DEPT": u"部門別"}
    else:
        names = {"PL": u"PL", "BS": u"BS", "DEPT": u"部門別"}
    for nm in set(names.values()):
        sheets[nm] = {}
    if ucell:
        for nm in sheets:
            sheets[nm][(1, 1)] = ucell
    t5 = set(p["t5"])

    def heading_of(ident, k):
        base = ident
        if ident in ALL_ROWS:
            if ident in t5:
                base = ALL_ROWS[ident][5][0]
            else:
                src = {"a02": "a01", "a05": "a04", "a16": "a15"}.get(ident, ident)
                base = pick(ALL_ROWS[src][4], i, src)
        return decorate(base, i, k)

    def emit(block, start_row, rows):
        sh = sheets[names[block]]
        lt, rt = per_label(block)
        hdr = [u"科目", lt if p["cur_left"] else rt, rt if p["cur_left"] else lt]
        if block == "PL":
            hdr.append(u"当期予算")
        for c, v in enumerate(hdr, 1):
            sh[(start_row, c)] = v
        r = start_row
        for k, (ident, label, cur, prv, budget) in enumerate(rows):
            r += 1
            if ident == "sep":
                sh[(r, 1)] = label
                continue
            if ident in ALL_ROWS or ident in ("a02", "a05"):
                txt = heading_of(ident, k)
            else:
                txt = decorate(label, i, k)
            sh[(r, 1)] = txt
            sh[(r, cur_col)] = cv(cur)
            sh[(r, prv_col(block))] = cv(prv)
            if budget is not None:
                sh[(r, 4)] = cv(budget)
            # 材料の位置
            if ident in ALL_ROWS or ident in ("a02", "a05"):
                for pid, col, val, hcell in ((ident, cur_col, cur, 0), ):
                    pass
            meta_rows[ident] = (names[block], r, txt, block, cur, prv, hdr)
        return r

    def prv_col(block):
        return prev_col

    meta_rows = {}
    bud = lambda x: int(round(x * rr(.9, 1.1)))
    pl_rows = [
        ("a01", None, pl["a01"], plp["a01"], bud(pl["a01"])),
        ("cogs", u"売上原価", pl["cogs"], plp["cogs"], bud(pl["cogs"])),
        ("a03", None, pl["a03"], plp["a03"], bud(pl["a03"])),
        ("sep", u"【販売費及び一般管理費】", 0, 0, None),
        ("b01", None, pl["b01"], plp["b01"], bud(pl["b01"])),
        ("sga", u"販売費及び一般管理費合計", pl["sga"], plp["sga"], bud(pl["sga"])),
        ("a04", None, pl["a04"], plp["a04"], bud(pl["a04"])),
        ("nonop_inc", u"営業外収益", pl["nonop_inc"], plp["nonop_inc"], bud(pl["nonop_inc"])),
        ("nonop_exp", u"営業外費用", pl["nonop_exp"], plp["nonop_exp"], bud(pl["nonop_exp"])),
        ("a06", None, pl["a06"], plp["a06"], bud(pl["a06"])),
        ("a07", None, pl["a07"], plp["a07"], bud(abs(pl["a07"]))),
    ]
    if p["has_dep"]:
        pl_rows.append(("a08", None, pl["a08"], plp["a08"], bud(pl["a08"])))
    bs_rows = [
        ("sep", u"【資産の部】", 0, 0, None),
        ("a09", None, bs["a09"], bsp["a09"], None), (u"recv", u"売掛金", bs["recv"], bsp["recv"], None),
        ("a10", None, bs["a10"], bsp["a10"], None), (u"fixed", u"固定資産合計", bs["fixed"], bsp["fixed"], None),
        ("a11", None, bs["a11"], bsp["a11"], None),
        ("sep", u"【負債の部】", 0, 0, None),
        ("a12", None, bs["a12"], bsp["a12"], None), (u"other_cl", u"未払金", bs["other_cl"], bsp["other_cl"], None),
        (u"cur_l", u"流動負債合計", bs["cur_l"], bsp["cur_l"], None),
        ("a13", None, bs["a13"], bsp["a13"], None), (u"fix_l", u"固定負債合計", bs["fix_l"], bsp["fix_l"], None),
        ("a14", None, bs["a14"], bsp["a14"], None),
        ("sep", u"【純資産の部】", 0, 0, None),
        ("a15", None, bs["a15"], bsp["a15"], None),
    ]
    # 損益
    pl_rows2 = [(a, b_, c, d, e) for (a, b_, c, d, e) in pl_rows]
    if p["form"] == "L2":
        end_pl = emit("PL", 2, pl_rows2)
        emit("BS", end_pl + 3, bs_rows)
    else:
        emit("PL", 3, pl_rows2)
        emit("BS", 3, bs_rows)
    # 部門別
    dsh = sheets[names["DEPT"]]
    for c, v in enumerate([u"部門", u"売上高", u"営業利益"], 1):
        dsh[(3, c)] = v
    for k, nm in enumerate([u"東日本事業部", u"西日本事業部", u"海外事業部"]):
        dsh[(4 + k, 1)] = nm
        dsh[(4 + k, 2)] = cv(dept_sales[k])
        dsh[(4 + k, 3)] = cv(dept_op[k])
    dsh[(7, 1)] = u"合計"
    dsh[(7, 2)] = cv(sum(dept_sales))
    dsh[(7, 3)] = cv(sum(dept_op))
    files["決算.xlsx"] = sheets
    # 月次売上.csv
    grp_m = i % 2 == 0
    grp_l = i % 2 == 1

    def fmt(v, grp):
        return u"{:,}".format(v) if grp else str(v)

    mrows = [[u"月", u"売上高", u"前年同月"]]
    month_labels = []
    for k in range(12):
        d = addm(p["cs"], k)
        lab = [u"%d月" % d.month, u"%d年%d月" % (d.year, d.month), u"%d/%02d" % (d.year, d.month)][p["month_form"]]
        month_labels.append(lab)
        mrows.append([lab, fmt(months[k], grp_m), fmt(prior_months[k], grp_m)])
    files["月次売上.csv"] = mrows
    lrows = [[u"借入先", u"区分", u"期末残高", u"利率"]]
    for nm, kind, v in loans:
        lrows.append([nm, kind, fmt(v, grp_l), u"%.2f%%" % (rng.randint(5, 30) / 10.0)])
    if i % 2 == 0:
        lrows.append([u"合計", u"", fmt(sum(v for _n, _k, v in loans), grp_l), u""])
    files["借入金一覧.csv"] = lrows
    if p["has_staff"]:
        files["人員.csv"] = [[u"項目", u"人数"], [u"期末従業員数", str(staff_total)], [u"うち正社員", str(staff_reg)], [u"うちパート", str(staff_total - staff_reg)]]
    co.files = files
    co.meta_rows = meta_rows
    co.month_labels = month_labels
    co.names = names
    # ---- 材料の位置
    def addr(r, c):
        return u"%s%d" % (chr(64 + c), r)

    mats = od()
    for ident in [r[0] for r in ROWS_A] + [u"b01"]:
        row = ALL_ROWS[ident]
        unit, per = row[2], row[3]
        absent = (ident == "a08" and not p["has_dep"]) or (ident == "a30" and not p["has_staff"])
        if absent:
            mats[ident] = {"absent": True}
            continue
        if re.fullmatch(u"a(1[7-9]|2[0-8])", ident):
            k = int(ident[1:]) - 16
            mats[ident] = {"file": u"月次売上.csv", "pos": {u"行": 1 + k, u"列": 2}, "rowh": month_labels[k - 1], "colh": u"売上高", "mult": 1,
                           "value": months[k - 1], "kind": u"素材"}
        elif ident == "a29":
            n = len(loans)
            mats[ident] = {"file": u"借入金一覧.csv", "col": 3, "rows": list(range(2, 2 + n)), "colh": u"期末残高", "mult": 1,
                           "value": sum(v for _a, _b, v in loans), "kind": u"素材の和"}
        elif ident == "a30":
            mats[ident] = {"file": u"人員.csv", "pos": {u"行": 2, u"列": 2}, "rowh": files["人員.csv"][1][0], "colh": u"項目" if False else u"人数",
                           "mult": 1, "value": staff_total, "kind": u"素材"}
        else:
            blk_id = {"a02": "a01", "a05": "a04", "a16": "a15"}.get(ident, ident)
            sh, r, txt, block, curv, prvv, hdr = meta_rows[blk_id]
            use_prev = ident in ("a02", "a05", "a16")
            col = prev_col if use_prev else cur_col
            mats[ident] = {"file": u"決算.xlsx", "pos": {u"sheet": sh, u"セル": addr(r, col)}, "rowh": txt, "colh": hdr[col - 1],
                           "mult": m, "value": prvv if use_prev else curv, "kind": u"素材", "block": block, "row": r, "col": col, "sheet": sh}
    co.mats = mats
    return co


def period_json(co, ident):
    p = co.p
    per = ALL_ROWS[ident][3]
    if per == u"当期":
        return od([(u"始まり", iso(p["cs"])), (u"終わり", iso(p["ce"]))])
    if per == u"前期":
        return od([(u"始まり", iso(p["ps"])), (u"終わり", iso(p["pe"]))])
    if per == u"当期末":
        return od([(u"時点", iso(p["ce"]))])
    if per == u"前期末":
        return od([(u"時点", iso(p["pe"]))])
    k = int(per.split(u":")[1])
    return od([(u"始まり", iso(addm(p["cs"], k - 1))), (u"終わり", iso(addm(p["cs"], k) - datetime.timedelta(days=1)))])


def gold_material(co, ident):
    a = co.mats[ident]
    if a.get("absent"):
        return od([(u"id", ident), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
    unit = ALL_ROWS[ident][2]
    if a["kind"] == u"素材":
        src = od([(u"種類", u"素材"), (u"file", a["file"]), (u"位置", od([(k, a["pos"][k]) for k in ((u"sheet", u"セル") if u"sheet" in a["pos"] else (u"行", u"列"))])), (u"行の見出し", a["rowh"]),
                  (u"列の見出し", a["colh"]), (u"表示の倍率", a["mult"])])
    else:
        src = od([(u"種類", u"素材の和"), (u"file", a["file"]), (u"列", a["col"]), (u"行の並び", list(a["rows"])), (u"列の見出し", a["colh"]), (u"表示の倍率", a["mult"])])
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", str(a["value"] * a["mult"])), (u"単位", unit), (u"期間", period_json(co, ident)),
               (u"範囲", u"全社"), (u"出どころ", src)])


def product_ids(product):
    return [r[0] for r in ROWS_A if r[0] not in (u"a31",)] if product == u"A" else None


def request_ids(product):
    if product == u"A":
        return sorted(r[0] for r in ROWS_A)
    return [u"b01"]


def gold_bundle(co, ids=None):
    ids = sorted(ids if ids is not None else request_ids(u"A"))
    return od([(u"型の版", u"u0"), (u"材料", [gold_material(co, i) for i in ids])])


def spec_json(co, product):
    return od([(u"成果物", product), (u"当期の始まり", iso(co.p["cs"])), (u"当期の終わり", iso(co.p["ce"]))])


def absent_ids(co):
    return [i for i, a in co.mats.items() if a.get("absent") and i != "b01"]


# ============================================================ 書き出し
def write_files(co, folder, product=u"A"):
    import openpyxl
    os.makedirs(folder, exist_ok=True)
    for name, body in co.files.items():
        path = os.path.join(folder, name)
        if name.endswith(".xlsx"):
            wb = openpyxl.Workbook()
            wb.remove(wb.active)
            for sn, cells in body.items():
                ws = wb.create_sheet(sn)
                for (r, c), v in cells.items():
                    ws.cell(row=r, column=c, value=v)
            wb.save(path)
        else:
            with io.open(path, "w", encoding="utf-8", newline=u"") as fh:
                csv.writer(fh).writerows(body)
    with io.open(os.path.join(folder, u"指定.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(spec_json(co, product), ensure_ascii=False, indent=1) + u"\n")


# ============================================================ 材料の変異 M1〜M11
MULT_NEXT = {1: 1000, 1000: 1000000, 1000000: 1}
MUT_CODES = (u"M1", u"M2", u"M3", u"M4", u"M5", u"M6", u"M7", u"M8", u"M9", u"M10", u"M11")


def _items(bundle):
    return dict((m[u"id"], m) for m in bundle[u"材料"])


def _replace(bundle, ident, new):
    out = copy.deepcopy(bundle)
    out[u"材料"] = [new if m[u"id"] == ident else m for m in out[u"材料"]]
    return out


def other_period(co, ident):
    p = co.p
    per = ALL_ROWS[ident][3]
    if per == u"当期":
        return od([(u"始まり", iso(p["ps"])), (u"終わり", iso(p["pe"]))])
    if per == u"前期":
        return od([(u"始まり", iso(p["cs"])), (u"終わり", iso(p["ce"]))])
    if per == u"当期末":
        return od([(u"時点", iso(p["pe"]))])
    if per == u"前期末":
        return od([(u"時点", iso(p["ce"]))])
    k = int(per.split(u":")[1])
    s = addm(p["cs"], k - 1 - 12)
    return od([(u"始まり", iso(s)), (u"終わり", iso(addm(s, 1) - datetime.timedelta(days=1)))])


def _grid(co, a):
    f = co.files[a["file"]]
    if a["file"].endswith(".xlsx"):
        return f[a["sheet"]]
    return dict(((r, c), v) for r, row in enumerate(f, 1) for c, v in enumerate(row, 1))


def _next_num_row(co, a, ident):
    u"""素材の ``位置`` の 1 つ下の数の行(同じ列)。無ければ None。戻りは (行, cell の値)。"""
    g = _grid(co, a)
    r0, c = (a["row"], a["col"]) if a["file"].endswith(".xlsx") else (a["pos"][u"行"], a["pos"][u"列"])
    maxr = max(r for r, _c in g)
    for r in range(r0 + 1, maxr + 1):
        v = g.get((r, c))
        if gnum(v) is not None:
            return r, v, g
    return None


def _addr(r, c):
    return u"%s%d" % (chr(64 + c), r)


def make_mutant(co, gold, code, ident, ident2=None):
    u"""材料の変異 1 つ。作れなければ None。戻りは変異した束(元と違うことを確かめてから返す)。"""
    items = _items(gold)
    m = items.get(ident)
    if m is None:
        return None
    new = copy.deepcopy(m)
    a = co.mats.get(ident, {})
    if code == u"M8":
        if m[u"状態"] != u"在る":
            return None
        new = od([(u"id", ident), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
    elif code == u"M9":
        if m[u"状態"] != u"無い":
            return None
        row = ALL_ROWS[ident]
        first = row[4][0]
        isx = ident == "a08"
        src = od([(u"種類", u"素材"), (u"file", u"決算.xlsx" if isx else u"人員.csv"),
                  (u"位置", od([(u"sheet", co.names["PL"]), (u"セル", u"Z99")]) if isx else od([(u"列", 9), (u"行", 99)])),
                  (u"行の見出し", first), (u"列の見出し", first), (u"表示の倍率", 1)])
        new = od([(u"id", ident), (u"状態", u"在る"), (u"数値", u"1000000"), (u"単位", row[2]), (u"期間", period_json(co, ident)),
                  (u"範囲", u"全社"), (u"出どころ", src)])
    elif code == u"M10":
        m2 = items.get(ident2)
        if m2 is None or m[u"状態"] != u"在る" or m2[u"状態"] != u"在る" or m[u"数値"] == m2[u"数値"]:
            return None
        n1, n2 = copy.deepcopy(m), copy.deepcopy(m2)
        n1[u"出どころ"], n2[u"出どころ"] = m2[u"出どころ"], m[u"出どころ"]
        n1[u"数値"], n2[u"数値"] = m2[u"数値"], m[u"数値"]
        out = copy.deepcopy(gold)
        out[u"材料"] = [n1 if x[u"id"] == ident else (n2 if x[u"id"] == ident2 else x) for x in out[u"材料"]]
        return out if out != gold else None
    else:
        if m[u"状態"] != u"在る":
            return None
        if code == u"M1":
            new[u"数値"] = str(int(m[u"数値"]) + 1)
        elif code == u"M2":
            new[u"数値"] = str(int(m[u"数値"]) * 1000)
        elif code == u"M3":
            new[u"出どころ"][u"表示の倍率"] = MULT_NEXT[m[u"出どころ"][u"表示の倍率"]]
        elif code == u"M6":
            new[u"期間"] = other_period(co, ident)
        elif code == u"M4":
            if a.get("kind") != u"素材" or not a["file"].endswith(".xlsx") or ident in NO_READ_IDS:
                return None
            ocol = co.cols[0] if a["col"] == co.cols[1] else co.cols[1]
            g = _grid(co, a)
            v = g.get((a["row"], ocol))
            n = gnum(v)
            hdr = co.meta_rows[{"a02": "a01", "a05": "a04", "a16": "a15"}.get(ident, ident)][6]
            if n is None:
                return None
            new[u"出どころ"][u"位置"] = od([(u"sheet", a["sheet"]), (u"セル", _addr(a["row"], ocol))])
            new[u"数値"] = str(n * a["mult"])
            new[u"出どころ"][u"列の見出し"] = hdr[ocol - 1]
        elif code in (u"M5", u"M7"):
            if a.get("kind") != u"素材":
                return None
            hit = _next_num_row(co, a, ident)
            if hit is None:
                return None
            r, v, g = hit
            n = gnum(v)
            if a["file"].endswith(".xlsx"):
                new[u"出どころ"][u"位置"] = od([(u"sheet", a["sheet"]), (u"セル", _addr(r, a["col"]))])
            else:
                new[u"出どころ"][u"位置"] = od([(u"行", r), (u"列", a["pos"][u"列"])])
            new[u"数値"] = str(n * a["mult"])
            if code == u"M5":
                new[u"出どころ"][u"行の見出し"] = g.get((r, 1))
        elif code == u"M11":
            if a.get("kind") != u"素材の和" or len(a["rows"]) < 2:
                return None
            rows = a["rows"][:-1]
            g = _grid(co, a)
            new[u"出どころ"][u"行の並び"] = rows
            new[u"数値"] = str(sum(gnum(g[(r, a["col"])]) for r in rows) * a["mult"])
        else:
            return None
    out = _replace(gold, ident, new)
    return out if out != gold else None


def mutant_plan(co, gold):
    u"""(code, id, id2) の並び。"""
    ids = [m[u"id"] for m in gold[u"材料"]]
    plan = []
    for code in (u"M1", u"M2", u"M3", u"M4", u"M5", u"M6", u"M7", u"M8", u"M9", u"M11"):
        for ident in ids:
            plan.append((code, ident, None))
    for k in range(len(ids) - 1):
        plan.append((u"M10", ids[k], ids[k + 1]))
    return plan


# ---- 検査の規則ごとに 1 つだけ破る追加の変異(M の表の外。封の変異の数に混ぜない)
X_CODES = (u"X0", u"XH", u"XU", u"XM", u"XG")


def make_extra(co, gold, code, ident):
    items = _items(gold)
    m = items.get(ident)
    if m is None or m[u"状態"] != u"在る":
        return None
    new = copy.deepcopy(m)
    if code == u"X0":          # K0: 数値の字の形だけ(先頭の 0)
        new[u"数値"] = u"0" + m[u"数値"] if not m[u"数値"].startswith(u"-") else u"-0" + m[u"数値"][1:]
    elif code == u"XH":        # K2: 申告の行の見出しだけ別の字
        if m[u"出どころ"][u"種類"] != u"素材":
            return None
        new[u"出どころ"][u"行の見出し"] = u"別の見出し"
    elif code == u"XU":        # K5: 単位だけ別の字
        new[u"単位"] = u"人" if m[u"単位"] == u"円" else u"円"
    elif code == u"XM":        # K5: 倍率を別の値にして数値を cell に合わせ直す(K1 は通る)
        if m[u"単位"] != u"円":
            return None
        old = m[u"出どころ"][u"表示の倍率"]
        nm = MULT_NEXT[old]
        new[u"出どころ"][u"表示の倍率"] = nm
        new[u"数値"] = str(int(m[u"数値"]) // old * nm)
    elif code == u"XG":        # K8: 範囲だけ別の字
        new[u"範囲"] = u"部門"
    else:
        return None
    out = _replace(gold, ident, new)
    return out if out != gold else None


def source_mutant(co, kind):
    u"""素材のほうを書き換え、材料もその値に合わせる(K1〜K6 を通り、関係だけが破れる)。戻りは (co の写し, 束, 関係の名)。"""
    co2 = copy.deepcopy(co)
    gold = gold_bundle(co2)
    if kind == u"R1":
        a = co2.mats["a17"]
        rows = co2.files["月次売上.csv"]
        old = gnum(rows[1][1])
        rows[1][1] = u"{:,}".format(old + 1000) if i_even(co2.i) else str(old + 1000)
        a["value"] = old + 1000
    elif kind == u"R2":
        a = co2.mats["a11"]
        sh = co2.files["決算.xlsx"][a["sheet"]]
        pos = (a["row"], a["col"])
        old = gnum(sh[pos])
        new = old + 1
        sh[pos] = text_num(new, co2.p["neg"]) if co2.p["form"] == "L2" else new
        a["value"] = new
    elif kind == u"R3":
        a = co2.mats["a29"]
        rows = co2.files["借入金一覧.csv"]
        old = gnum(rows[1][2])
        rows[1][2] = u"{:,}".format(old + 1000) if not i_even(co2.i) else str(old + 1000)
        a["value"] += 1000
    return co2, gold_bundle(co2), kind


def i_even(i):
    return i % 2 == 0


def relation_seen(co, kind):
    u"""その関係を検査が見るか(両辺の材料が全部在って、表の外・無いで止まっていない)。"""
    ids = {u"R1": [u"a%d" % k for k in range(17, 29)] + [u"a01"], u"R2": [u"a11", u"a14", u"a15"], u"R3": [u"a29", u"a12", u"a13"]}[kind]
    bad = set(co.p["t5"]) | set(absent_ids(co))
    return not (set(ids) & bad)


# ============================================================ 資料の変異 D1〜D5
DOC_CODES = (u"D1", u"D2", u"D3", u"D4", u"D5")
_NUMTAG = re.compile(u"(?P<neg>[-△▲])?(?P<num>[0-9][0-9,]*(?:\\.[0-9]+)?)(?P<unit>%|百万円|千円|円|年|人)?\\[材料:(?P<id>[^\\]]*)\\]")
_WORDTAG = re.compile(u"(?P<word>無い|確認待ち)\\[材料:(?P<id>[^\\]]*)\\]")
UNIT_NEXT = {u"百万円": u"千円", u"千円": u"円", u"円": u"百万円"}


def doc_mutants(text, rows_unit):
    u"""(code, 通し番号, 変異した字) の並び。作れなければ字は None。``rows_unit`` は id → 単位。"""
    out = []
    nums = list(_NUMTAG.finditer(text))
    words = list(_WORDTAG.finditer(text))
    for k, m in enumerate(nums):
        a, b = m.span(u"num")
        s = text[a:b]
        pos = next((x for x, ch in enumerate(s) if ch.isdigit()), None)
        new = None
        if pos is not None:
            d = (int(s[pos]) + 1) % 10
            new = text[:a] + s[:pos] + str(d) + s[pos + 1:] + text[b:]
        out.append((u"D1", k, new if new != text else None))
    for k, m in enumerate(nums):
        u_ = m.group(u"unit")
        if rows_unit.get(m.group(u"id")) == u"円" and u_ in UNIT_NEXT:
            a, b = m.span(u"unit")
            out.append((u"D2", k, text[:a] + UNIT_NEXT[u_] + text[b:]))
        else:
            out.append((u"D2", k, None))
    for k in range(len(nums) - 1):
        m1, m2 = nums[k], nums[k + 1]
        body1 = (m1.group(u"neg") or u"") + m1.group(u"num") + (m1.group(u"unit") or u"")
        body2 = (m2.group(u"neg") or u"") + m2.group(u"num") + (m2.group(u"unit") or u"")
        if body1 == body2 or m1.group(u"id") == m2.group(u"id"):
            out.append((u"D3", k, None))
            continue
        a1, b1 = m1.span(u"id")
        a2, b2 = m2.span(u"id")
        new = text[:a1] + m2.group(u"id") + text[b1:a2] + m1.group(u"id") + text[b2:]
        out.append((u"D3", k, new if new != text else None))
    for k, m in enumerate(nums + words):
        mm = re.search(u"\\[材料:%s\\]" % re.escape(m.group(u"id")), text[m.start():])
        a = m.start() + mm.start()
        b = m.start() + mm.end()
        out.append((u"D4", k, text[:a] + text[b:]))
    for k, m in enumerate(words):
        a, b = m.span(u"word")
        out.append((u"D5", k, text[:a] + u"100円" + text[b:]))
    return out


# ============================================================ 検査の呼び出し(検査の file の関数を importlib で読む)
def load_check():
    spec = importlib.util.spec_from_file_location("universal_check_for_gen", os.path.join(ROOT, CHECK_REL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def defn_of(chk, product):
    d = def_json(product)
    tmp = tempfile.mkdtemp(prefix="um0_def_")
    p = os.path.join(tmp, "d.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=False))
    got, err = chk.load_def(p)
    return got


def spec_of(chk, co, product):
    tmp = tempfile.mkdtemp(prefix="um0_spec_")
    p = os.path.join(tmp, u"s.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(spec_json(co, product), ensure_ascii=False))
    got, err = chk.load_spec(p)
    return got


def judge_mutant(res, ids, counter=None):
    u"""変異した材料(``ids``)を検査がどう扱ったか。``断った``(束ごと)・``止めた``(材料が止まった)・``通した``。"""
    if res[u"束"][u"状態"] != u"受理":
        return u"断った"
    stopped = [x for x in res[u"材料"] if x[u"id"] in ids and x[u"判定"] == u"止める"]
    if stopped:
        if counter is not None:
            for x in stopped:
                counter[u"規則:" + u"+".join(x[u"規則"])] += 1
        return u"止めた"
    return u"通した"


def tally_a(companies, chk=None):
    u"""段 A(席を使わない。正解の束)。数だけ。"""
    chk = chk or load_check()
    out = od()
    total = collections.Counter()
    mut = od((c, collections.Counter()) for c in MUT_CODES + X_CODES)
    ext = collections.Counter()
    for i in companies:
        co = build(i)
        tmp = tempfile.mkdtemp(prefix="um0_a_")
        write_files(co, tmp, u"A")
        defn = defn_of(chk, u"A")
        sp = spec_of(chk, co, u"A")
        src = chk.Source(tmp)
        gold = gold_bundle(co)
        res = chk.check_bundle(sp, defn, gold, src)
        c = collections.Counter()
        stop_rules = collections.Counter()
        for r in res[u"材料"]:
            c[r[u"判定"]] += 1
            if r[u"判定"] == u"止める":
                stop_rules[u"+".join(r[u"規則"])] += 1
        c[u"束ごとの断り"] += 1 if res[u"束"][u"状態"] != u"受理" else 0
        out[i] = {u"通す": c[u"通す"], u"止める": c[u"止める"], u"無いを受ける": c[u"無いを受ける"], u"束ごとの断り": c[u"束ごとの断り"],
                  u"止めた規則": dict(stop_rules), u"K7": res[u"K7"]}
        total.update({u"通す": c[u"通す"], u"止める": c[u"止める"], u"無いを受ける": c[u"無いを受ける"], u"束ごとの断り": c[u"束ごとの断り"]})
        for code, ident, ident2 in mutant_plan(co, gold):
            b = make_mutant(co, gold, code, ident, ident2)
            if b is None:
                mut[code][u"作れなかった"] += 1
                continue
            mut[code][u"作れた"] += 1
            rr = chk.check_bundle(sp, defn, b, src)
            mut[code][judge_mutant(rr, [ident] + ([ident2] if ident2 else []), mut[code])] += 1
            full = chk.check_bundle(sp, defn, b, src, form_only=True)
            if full[u"束"][u"状態"] == u"受理" and all(x[u"判定"] != u"止める" for x in full[u"材料"]):
                mut[code][u"形だけの検査が通した"] += 1
        for code in X_CODES:
            for ident in [m[u"id"] for m in gold[u"材料"]]:
                b = make_extra(co, gold, code, ident)
                if b is None:
                    mut[code][u"作れなかった"] += 1
                    continue
                mut[code][u"作れた"] += 1
                rr = chk.check_bundle(sp, defn, b, src)
                mut[code][judge_mutant(rr, [ident], mut[code])] += 1
    for k in (u"通す", u"止める", u"無いを受ける", u"束ごとの断り"):
        total.setdefault(k, 0)
    for k, row in mut.items():
        for key in (u"作れた", u"作れなかった", u"断った", u"止めた", u"通した") + ((u"形だけの検査が通した",) if k in MUT_CODES else ()):
            row.setdefault(key, 0)          # 0 は 0 と書く(キーが無いのと区別する)
    return {u"会社ごと": out, u"合計": dict(total), u"変異": dict((k, dict(v)) for k, v in mut.items())}


def tally_bc(companies, seat_dir, chk=None):
    u"""段 B・C(席の出力を読む)。数だけ。席の出力が無い社は ``席の出力なし`` に数える。"""
    chk = chk or load_check()
    boxes = collections.Counter()
    c = collections.Counter()
    out = od()
    defA, defB = defn_of(chk, u"A"), defn_of(chk, u"B")
    for i in companies:
        co = build(i)
        gold = _items(gold_bundle(co))
        d = os.path.join(seat_dir, str(i))
        tmp = tempfile.mkdtemp(prefix="um0_bc_")
        write_files(co, tmp, u"A")
        sp = spec_of(chk, co, u"A")
        src = chk.Source(tmp)
        seat_path = os.path.join(d, u"材料_A.json")
        if not os.path.exists(seat_path):
            c[u"席の出力なし"] += 1
            continue
        bundle, err = chk.read_json(seat_path)
        if err:
            bundle = {}
            res = chk.refuse(u"K0", u"束が読めない")
        else:
            res = chk.check_bundle(sp, defA, bundle, src)
        refused = res[u"束"][u"状態"] != u"受理"
        c[u"束が K0 で断られた社"] += 1 if refused else 0
        seat = {}
        if not refused:
            seat = _items(bundle)
        verd = dict((r[u"id"], r) for r in res[u"材料"])
        for ident, g in gold.items():
            s = seat.get(ident)
            same = s is not None and _same_answer(g, s)
            passed = (not refused) and verd.get(ident, {}).get(u"判定") in (u"通す", u"無いを受ける")
            key = (u"正解どおり" if same else u"正解と違う") + u"×" + (u"通した" if passed else u"止めた")
            boxes[key] += 1
            is_t5 = ident in co.p["t5"]
            is_abs = g[u"状態"] == u"無い"
            if is_abs:
                c[u"無いの行"] += 1
                if s is not None and s.get(u"状態") == u"無い":
                    c[u"無いの行で席が無いと書いた"] += 1
            if is_t5:
                c[u"表に無い言い方の行"] += 1
                if same:
                    c[u"表に無い言い方の行で席が正解どおり"] += 1
            if passed and s is not None and s.get(u"状態") == u"在る" and g[u"状態"] == u"在る":
                if s.get(u"数値") != g.get(u"数値"):
                    c[u"通したが数値が違う"] += 1
                elif s.get(u"出どころ") != g.get(u"出どころ"):
                    c[u"位置は違うが通り数値は同じ"] += 1
            if (not passed) and same and not is_t5:
                c[u"正解どおりなのに止めた(表に無い言い方以外)"] += 1
        # 置き場と B
        store = chk.build_store(defA, res, bundle, u"A")
        plan = chk.make_plan(defB, store)
        out[i] = {u"B の計画": dict((k, len(v)) for k, v in plan.items())}
        for k, v in plan.items():
            c[u"B の計画:" + k] += len(v)
        # A の資料
        doc, err = chk.read_text(os.path.join(d, u"資料_A.md"))
        if err is not None:
            c[u"A の資料なし"] += 1
        if err is None:
            r = chk.check_document(defA, store, doc)
            c[u"A の資料を通した"] += 1 if r[u"通った"] else 0
            c[u"A の資料の結ばれていない数"] += r[u"結ばれていない数"]
            if r[u"通った"]:
                rows_unit = dict((x[u"id"], x[u"単位"]) for x in defA.rows)
                for code, k, new in doc_mutants(doc, rows_unit):
                    if new is None:
                        c[u"資料の変異:" + code + u":作れなかった"] += 1
                        continue
                    c[u"資料の変異:" + code + u":作れた"] += 1
                    if chk.check_document(defA, store, new)[u"通った"]:
                        c[u"資料の変異:" + code + u":通した"] += 1
        # B(2 回目): b01 だけ席の答え
        bseat, err = chk.read_json(os.path.join(d, u"材料_B.json"))
        spB = spec_of(chk, co, u"B")
        gb = _items(gold_bundle(co, [u"b01"]))[u"b01"]
        if err is None:
            rb = chk.check_bundle(spB, defB, bseat, src, ids=plan[u"新しく要る"])
            sb = _items(bseat) if rb[u"束"][u"状態"] == u"受理" else {}
            if u"b01" in sb and _same_answer(gb, sb[u"b01"]):
                c[u"b01 の席の答えが正解どおり"] += 1
            storeB = chk.build_store(defB, rb, bseat, u"B", prior=store, ids=plan[u"新しく要る"])
        else:
            storeB = chk.build_store(defB, {u"束": {u"状態": u"断り"}}, {}, u"B", prior=store, ids=plan[u"新しく要る"])
        docB = chk.render_doc(defB, storeB)
        rB = chk.check_document(defB, storeB, docB)
        c[u"B の資料を通した"] += 1 if rB[u"通った"] else 0
        rows_unit_b = dict((x[u"id"], x[u"単位"]) for x in defB.rows)
        for code, k, new in doc_mutants(docB, rows_unit_b):
            if new is None:
                c[u"資料の変異:" + code + u":作れなかった:B"] += 1
                continue
            c[u"資料の変異:" + code + u":作れた:B"] += 1
            if chk.check_document(defB, storeB, new)[u"通った"]:
                c[u"資料の変異:" + code + u":通した:B"] += 1
    for key in (u"束が K0 で断られた社", u"席の出力なし", u"無いの行", u"無いの行で席が無いと書いた", u"表に無い言い方の行", u"表に無い言い方の行で席が正解どおり",
                u"通したが数値が違う", u"位置は違うが通り数値は同じ", u"正解どおりなのに止めた(表に無い言い方以外)", u"A の資料を通した", u"A の資料の結ばれていない数",
                u"B の資料を通した", u"b01 の席の答えが正解どおり", u"A の資料なし"):
        c.setdefault(key, 0)
    for code in DOC_CODES:
        for suffix in (u"", u":B"):
            for what in (u"作れた", u"作れなかった", u"通した"):
                c.setdefault(u"資料の変異:%s:%s%s" % (code, what, suffix) if suffix == u"" else u"資料の変異:%s:%s:B" % (code, what), 0)
    for key in (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた"):
        boxes.setdefault(key, 0)
    return {u"会社ごと": out, u"数": dict(c), u"4 つの枠": dict(boxes)}


def _same_answer(g, s):
    if not isinstance(s, dict) or s.get(u"状態") != g.get(u"状態"):
        return False
    if g[u"状態"] == u"無い":
        return True
    if s.get(u"数値") != g.get(u"数値"):
        return False
    gs, ss = g.get(u"出どころ"), s.get(u"出どころ")
    if not isinstance(ss, dict):
        return False
    if gs[u"種類"] == u"素材の和":
        return ss.get(u"種類") == u"素材の和" and ss.get(u"file") == gs[u"file"] and ss.get(u"列") == gs[u"列"] and ss.get(u"行の並び") == gs[u"行の並び"]
    return ss.get(u"種類") == u"素材" and ss.get(u"file") == gs[u"file"] and ss.get(u"位置") == gs[u"位置"]


def build_record(companies, seat_dir, chk=None):
    u"""記録(数だけ)。本番は ``PROD`` の 12 社で 1 回だけ(席の出力が全部そろってから)。"""
    chk = chk or load_check()
    return od([(u"段 A", tally_a(companies, chk)), (u"段 B・C", tally_bc(companies, seat_dir, chk))])


# ============================================================ 命令
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    opt = {}
    flags = []
    k = 0
    while k < len(argv):
        a = argv[k]
        if a in ("--companies",):
            vals = []
            k += 1
            while k < len(argv) and not argv[k].startswith("--"):
                vals.append(int(argv[k]))
                k += 1
            opt[a] = vals
            continue
        if a.startswith("--") and k + 1 < len(argv) and not argv[k + 1].startswith("--"):
            opt[a] = argv[k + 1]
            k += 2
        else:
            flags.append(a)
            k += 1
    product = opt.get("--product", u"A")
    if "--make" in opt:
        co = build(int(opt["--make"]))
        write_files(co, opt["--out"], product)
        return 0
    if "--gold" in opt:
        co = build(int(opt["--gold"]))
        g = gold_bundle(co) if product == u"A" else gold_bundle(co, [u"b01"])
        with io.open(opt["--out"], "w", encoding="utf-8") as fh:
            fh.write(json.dumps(g, ensure_ascii=False, indent=1) + u"\n")
        return 0
    if "--write-defs" in opt:
        write_defs(opt["--write-defs"])
        return 0
    if "--tally-a" in flags or "--tally-a" in opt:
        res = tally_a(opt.get("--companies", list(DEV)))
    elif "--tally-bc" in flags or "--tally-bc" in opt:
        res = tally_bc(opt.get("--companies", list(DEV)), opt["--seat-dir"])
    elif "--record" in flags or "--record" in opt:
        res = build_record(list(PROD), opt["--seat-dir"])
    else:
        print(u"命令が無い", file=sys.stderr)
        return 2
    body = json.dumps(res, ensure_ascii=False, indent=1) + u"\n"
    if "--out" in opt:
        with io.open(opt["--out"], "w", encoding="utf-8") as fh:
            fh.write(body)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
