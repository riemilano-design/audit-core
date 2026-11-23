# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md(便 UM1)の「確かめる側」。**答えを読まない側。**

答えを知っている側(``universal_ledger_ref_2026-11-23.py``)を import しない。読むのは指定・定義表・読込みの定義・材料の束・素材の file(SQLite。
``file:...?mode=ro`` で開く)・(表つきの時だけ)確かめた取り方の表。使う library は標準だけ(``python3 -I`` で動く)。
**どんな入力でも例外で落ちず、rc 0 で結果の JSON を返す。** 材料の束の字は SQL の文に入れない(列の名は決まった表から引き、値は束縛で渡す)。

    python3 -I universal_ledger_check_2026-11-23.py without-table --spec <指定.json> --def <定義表> --reading <読込みの定義> --src <素材.sqlite> (--bundle <束> | --bundle-dir <folder>) [--out <file>]
    python3 -I universal_ledger_check_2026-11-23.py with-table    --spec <指定.json> --def <定義表> --reading <読込みの定義> --src <素材.sqlite> --table <確かめた取り方の表> (--bundle <束> | --bundle-dir <folder>) [--out <file>]

``--bundle-dir`` は folder の中の ``*.json`` を 1 つずつ、**同じ検査の process の中で**(素材を 1 回だけ読み込んで)検査する(変異の束を何百も掛けるため。1 つずつの結果は別々)。

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- K0 は id が定義表とちょうど同じ(重複なし)で、並びが字の昇順であること(封 §1-5)を見る。単位・範囲の字の一致は K5・K8 が見る(K0 は字であることだけ)。
- 数値の字は ``-?[0-9]+\\.[0-9]{2}`` の全体一致(ASCII。末尾の改行は受けない)。``-0.00`` と先頭の 0(``007.00``)は、封が禁じていないので形の上で受ける(申告。封の字は「10 進の字で小数 2 桁ちょうど」)。
- 数値の字は 60 字までを受け、61 字からは K0 で断る。封に無い守り(申告。長い字の数を 10 進に直す手間を避けるため。境目は 60 字は受ける・61 字は断る)。
- 日付の字は ASCII の ``YYYY-MM-DD`` で実在の日。科目番号の値は 64 bit の整数(bool は整数でない)。字の値は UTF-8 に直せる字(孤立 surrogate は K0)。
- K3・K9・K10 に使う「その材料の期」は、材料の ``期間`` の欄でなく、定義表の ``期`` と指定から出した期(材料の欄と違えば K4 が止める)。
- K7 は ``無い`` の行を止めない(0 として数えるだけ。止めるのは ``在る`` の材料)。申告。
- K10 の「行が在る」は、仕訳の種類・伝票の種類を問わない 1 行以上。科目の分類が素材の科目表に無い科目は「入りうる」とする(止める側)。
- K7 は、ほかの規則を 1 つも受けなかった ``在る`` の材料と、無いを受けた材料(0)だけを使う。関係の材料のうち 1 つでもそろわなければ見ない。
  関係が崩れたら、その関係の ``在る`` の材料のうち、ほかの規則を受けていないものに K7 を付ける。
- 額は 1 行ごとに借方・貸方を 100 倍して最も近い整数へ(半分は 0 から遠い方へ)丸め、整数で足す。
"""
from __future__ import print_function

import datetime
import decimal
import json
import os
import re
import sqlite3
import sys
import pathlib
from decimal import Decimal, ROUND_HALF_UP

RULES = ("K0", "K1", "K3", "K4", "K5", "K7", "K8", "K9", "K10")
STATE_OK, STATE_NONE = u"在る", u"無い"
NONE_REASON = u"素材が無い"
COLS = {u"日付": "d", u"科目番号": "acct", u"科目の大分類": "atype", u"科目の小分類": "asub",
        u"伝票の種類": "vtype", u"仕訳の種類": "jtype"}
DIRS = (u"借方−貸方", u"貸方−借方")
OPS_LIST = (u"どれか", u"どれでもない")
BIGCTX = decimal.Context(prec=500, rounding=ROUND_HALF_UP)
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
NUM_RE = re.compile(r"-?[0-9]+\.[0-9]{2}")
I64 = (-(1 << 63), (1 << 63) - 1)


# ============================================================ 読む・字
def dump_json(obj):
    try:
        body = json.dumps(obj, ensure_ascii=False, indent=1)
        body.encode("utf-8")
        return body
    except (UnicodeEncodeError, ValueError):
        return json.dumps(obj, ensure_ascii=True, indent=1)


def read_json(path):
    u"""(object, None) か (None, 理由)。NaN・Infinity は読まない。"""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")

        def bad(_c):
            raise ValueError(_c)
        return json.loads(text, parse_constant=bad), None
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None, type(exc).__name__


def parse_date(s):
    if not isinstance(s, str) or not DATE_RE.fullmatch(s):
        return None
    try:
        return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


def good_text(s):
    try:
        s.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False


def is_int(x):
    return type(x) is int and I64[0] <= x <= I64[1]


def cents_of(x):
    u"""借方・貸方の 1 つの値 → 最小の通貨の単位(整数)。数でなければ ValueError。"""
    if x is None:
        return 0
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("amount")
    if isinstance(x, float) and (x != x or x in (float("inf"), float("-inf"))):
        raise ValueError("amount")
    return int(Decimal(x * 100).to_integral_value(rounding=ROUND_HALF_UP, context=BIGCTX))


def num_to_cents(text):
    neg = text.startswith("-")
    body = text[1:] if neg else text
    n = int(body.replace(".", ""))
    return -n if neg else n


# ============================================================ 日付・期
def add_months(d, n):
    y, m = divmod(d.year * 12 + (d.month - 1) + n, 12)
    m += 1
    last = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return datetime.date(y, m, min(d.day, last))


def month_first(y, m):
    return datetime.date(y, m, 1)


def month_last(y, m):
    return add_months(datetime.date(y, m, 1), 1) - datetime.timedelta(days=1)


class Spec(object):
    pass


def load_spec(path):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None, u"指定が読めない"
    if set(obj) != {u"成果物", u"当期の始まり", u"当期の終わり"}:
        return None, u"指定の鍵"
    if obj[u"成果物"] != u"C":
        return None, u"指定の成果物"
    cs, ce = parse_date(obj[u"当期の始まり"]), parse_date(obj[u"当期の終わり"])
    if cs is None or ce is None or cs > ce:
        return None, u"指定の日"
    try:
        sp = Spec()
        sp.cs, sp.ce = cs, ce
        sp.pe = cs - datetime.timedelta(days=1)
        sp.ps = add_months(cs, -12)
    except (OverflowError, ValueError):
        return None, u"指定の日"
    return sp, None


def expected_period(kind, sp):
    u"""``(u"期間", 始まり, 終わり)`` か ``(u"時点", 日)``。読めなければ None。"""
    try:
        if kind == u"当期":
            return (u"期間", sp.cs, sp.ce)
        if kind == u"前期":
            return (u"期間", sp.ps, sp.pe)
        if kind == u"当期末":
            return (u"時点", sp.ce)
        if kind == u"前期末":
            return (u"時点", sp.pe)
        if isinstance(kind, str) and kind.startswith(u"当期の月:"):
            k = kind[len(u"当期の月:"):]
            if k.isascii() and k.isdigit() and 1 <= int(k) <= 12:
                f = add_months(sp.cs, int(k) - 1)
                return (u"期間", month_first(f.year, f.month), month_last(f.year, f.month))
    except (OverflowError, ValueError):
        return None
    return None


# ============================================================ 定義表
class Def(object):
    pass


def load_def(path):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None, u"定義表が読めない"
    rows = obj.get(u"行")
    if not isinstance(rows, list) or not all(isinstance(r, dict) and isinstance(r.get(u"id"), str) for r in rows):
        return None, u"定義表の行"
    ids = [r[u"id"] for r in rows]
    if len(set(ids)) != len(ids):
        return None, u"定義表の id"
    d = Def()
    d.rows = rows
    d.by_id = dict((r[u"id"], r) for r in rows)
    d.ids = ids
    rel = obj.get(u"関係")
    d.relations = [x for x in rel if isinstance(x, dict)] if isinstance(rel, list) else []
    return d, None


# ============================================================ 素材(読込みの定義で結んだ 1 つの表「仕訳の行」)
def _ident(x):
    if not isinstance(x, str) or not IDENT.match(x):
        raise ValueError("ident")
    return u'"%s"' % x


class Ledger(object):
    u"""素材の SQLite を ``mode=ro`` で開き、読込みの定義で結んだ行を、作業用の表(メモリ)に 1 回だけ写す。"""

    def __init__(self, path, rd):
        self.cache = {}
        t = rd[u"表"]
        gl, ac, je = t[u"元帳"], t[u"科目"], t[u"振替伝票"]
        g = dict((k, _ident(v)) for k, v in gl[u"列"].items())
        a = dict((k, _ident(v)) for k, v in ac[u"列"].items())
        j = dict((k, _ident(v)) for k, v in je[u"列"].items())
        voucher = rd[u"結び方"][u"振替伝票の字"]
        if not isinstance(voucher, str):
            raise ValueError("voucher")
        sql = (u'SELECT g.%s, g.%s, a.%s, a.%s, a.%s, g.%s, j.%s, g.%s, g.%s FROM %s g JOIN %s a ON a.%s = g.%s '
               u'LEFT JOIN %s j ON g.%s = ? AND j.%s = g.%s' % (
                   g[u"行の番号"], g[u"日付"], a[u"科目番号"], a[u"大分類"], a[u"小分類"], g[u"伝票の種類"], j[u"仕訳の種類"],
                   g[u"借方"], g[u"貸方"], _ident(gl[u"表"]), _ident(ac[u"表"]), a[u"鍵"], g[u"科目"],
                   _ident(je[u"表"]), g[u"伝票の種類"], j[u"鍵"], g[u"元の書類の番号"]))
        sql_acct = u"SELECT %s, %s, %s FROM %s" % (a[u"科目番号"], a[u"大分類"], a[u"小分類"], _ident(ac[u"表"]))
        uri = pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro"
        src = sqlite3.connect(uri, uri=True)
        try:
            self.mem = sqlite3.connect(":memory:")
            self.mem.execute("CREATE TABLE l(rid INTEGER, d TEXT, acct INTEGER, atype TEXT, asub TEXT, vtype TEXT, jtype TEXT, deb INTEGER, cre INTEGER)")

            def gen():
                for r in src.execute(sql, (voucher,)):
                    yield (r[0], r[1], r[2], r[3], r[4], r[5], (r[6] if r[6] != u"" else None), cents_of(r[7]), cents_of(r[8]))
            self.mem.executemany("INSERT INTO l VALUES (?,?,?,?,?,?,?,?,?)", gen())
            self.mem.execute("CREATE INDEX l_d ON l(d)")
            self.mem.execute("CREATE INDEX l_a ON l(acct)")
            self.classes = {}
            for n, ty, sub in src.execute(sql_acct):
                self.classes[n] = (ty, sub)
        finally:
            src.close()

    @staticmethod
    def where(conds):
        parts, args = [], []
        for col, op, val in conds:
            c = COLS[col]
            if op == u"以上":
                parts.append("%s >= ?" % c)
                args.append(val)
            elif op == u"以下":
                parts.append("%s <= ?" % c)
                args.append(val)
            elif op == u"等しい":
                parts.append("%s = ?" % c)
                args.append(val)
            elif op == u"どれか":
                parts.append("%s IN (%s)" % (c, ",".join("?" * len(val))))
                args.extend(val)
            elif op == u"どれでもない":
                parts.append("(%s IS NULL OR %s NOT IN (%s))" % (c, c, ",".join("?" * len(val))))
                args.extend(val)
            else:
                raise ValueError("op")
        return (" WHERE " + " AND ".join(parts)) if parts else "", args

    def select(self, conds):
        u"""条件(列・比べ方・値)の全部を満たす行。戻りは (行の数, 借方の和, 貸方の和)。"""
        key = ("sel", json.dumps(conds, sort_keys=True, ensure_ascii=True))
        if key not in self.cache:
            w, args = self.where(conds)
            self.cache[key] = self.mem.execute("SELECT count(*), coalesce(sum(deb),0), coalesce(sum(cre),0) FROM l" + w, args).fetchone()
        return self.cache[key]

    def diff(self, a, b):
        u"""条件 a を満たし条件 b を満たさない行の数。"""
        key = ("diff", json.dumps([a, b], sort_keys=True, ensure_ascii=True))
        if key not in self.cache:
            wa, aa = self.where(a)
            wb, ab = self.where(b)
            ea = wa[len(" WHERE "):] if wa else "1"
            eb = wb[len(" WHERE "):] if wb else "1"
            self.cache[key] = self.mem.execute("SELECT count(*) FROM l WHERE (%s) AND NOT COALESCE((%s), 0)" % (ea, eb), aa + ab).fetchone()[0]
        return self.cache[key]

    def accounts_in(self, period):
        key = ("acct", period)
        if key in self.cache:
            return self.cache[key]
        if period[0] == u"期間":
            rows = self.mem.execute("SELECT DISTINCT acct FROM l WHERE d >= ? AND d <= ?", (period[1].isoformat(), period[2].isoformat()))
        else:
            rows = self.mem.execute("SELECT DISTINCT acct FROM l WHERE d <= ?", (period[1].isoformat(),))
        res = frozenset(r[0] for r in rows if r[0] is not None)
        self.cache[key] = res
        return res


def load_reading(path):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None, u"読込みの定義が読めない"
    try:
        t = obj[u"表"]
        for k, cols in ((u"元帳", (u"行の番号", u"日付", u"科目", u"借方", u"貸方", u"伝票の種類", u"元の書類の番号")),
                        (u"科目", (u"鍵", u"科目番号", u"大分類", u"小分類")), (u"振替伝票", (u"鍵", u"仕訳の種類"))):
            _ident(t[k][u"表"])
            for c in cols:
                _ident(t[k][u"列"][c])
        if not isinstance(obj[u"結び方"][u"振替伝票の字"], str):
            return None, u"読込みの定義の形"
    except (KeyError, TypeError, ValueError):
        return None, u"読込みの定義の形"
    return obj, None


# ============================================================ 確かめた取り方の表
class Table(object):
    pass


def load_table(path, ids):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict) or not isinstance(obj.get(u"行"), dict):
        return None, u"表が読めない"
    t = Table()
    t.rows = {}
    for i in ids:
        r = obj[u"行"].get(i)
        if not isinstance(r, dict) or r.get(u"向き") not in DIRS:
            return None, u"表の行"
        acc = r.get(u"科目")
        if not isinstance(acc, list) or not all(is_int(x) for x in acc):
            return None, u"表の科目"
        jc = r.get(u"仕訳の種類の条件")
        if jc is not None:
            if not isinstance(jc, dict) or jc.get(u"比べ方") not in (u"等しい", u"どれか", u"どれでもない"):
                return None, u"表の仕訳の種類"
            v = jc.get(u"値")
            if jc[u"比べ方"] == u"等しい":
                ok = isinstance(v, str) and good_text(v)
            else:
                ok = isinstance(v, list) and 1 <= len(v) <= 200 and all(isinstance(x, str) and good_text(x) for x in v)
            if not ok:
                return None, u"表の仕訳の種類"
        t.rows[i] = {u"向き": r[u"向き"], u"科目": sorted(set(acc)), u"仕訳の種類の条件": jc}
    t.covered = frozenset(a for r in t.rows.values() for a in r[u"科目"])
    return t, None


# ============================================================ K0 形
def k0_condition(c):
    if not isinstance(c, dict) or set(c) != {u"列", u"比べ方", u"値"}:
        return False
    col, op, val = c[u"列"], c[u"比べ方"], c[u"値"]
    if not isinstance(col, str) or col not in COLS or not isinstance(op, str):
        return False
    if col == u"日付":
        return op in (u"以上", u"以下") and parse_date(val) is not None
    if op not in (u"等しい",) + OPS_LIST:
        return False

    def one(x):
        if col == u"科目番号":
            return is_int(x)
        return isinstance(x, str) and good_text(x)
    if op == u"等しい":
        return one(val)
    return isinstance(val, list) and 1 <= len(val) <= 200 and all(one(x) for x in val)


def k0_item(m):
    u"""材料 1 つの形の理由(空なら形は合う)。"""
    if not isinstance(m, dict):
        return u"材料が辞書でない"
    st = m.get(u"状態")
    if st == STATE_NONE:
        if set(m) != {u"id", u"状態", u"無い理由"}:
            return u"無いの鍵"
        if m[u"無い理由"] != NONE_REASON:
            return u"無い理由の字"
        return u""
    if st != STATE_OK:
        return u"状態の字"
    if set(m) != {u"id", u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ"}:
        return u"在るの鍵"
    v = m[u"数値"]
    if not isinstance(v, str) or not NUM_RE.fullmatch(v) or len(v) > 60:
        return u"数値の字"
    if not isinstance(m[u"単位"], str) or not good_text(m[u"単位"]) or not isinstance(m[u"範囲"], str) or not good_text(m[u"範囲"]):
        return u"単位・範囲の字"
    p = m[u"期間"]
    if not isinstance(p, dict) or not (
            (set(p) == {u"時点"} and parse_date(p[u"時点"]) is not None)
            or (set(p) == {u"始まり", u"終わり"} and parse_date(p[u"始まり"]) is not None and parse_date(p[u"終わり"]) is not None)):
        return u"期間の形"
    s = m[u"出どころ"]
    if not isinstance(s, dict) or set(s) != {u"種類", u"表", u"向き", u"条件"}:
        return u"出どころの鍵"
    if s[u"種類"] != u"表の行の和" or s[u"表"] != u"仕訳の行" or s[u"向き"] not in DIRS:
        return u"出どころの字"
    conds = s[u"条件"]
    if not isinstance(conds, list) or not 1 <= len(conds) <= 8 or not all(k0_condition(c) for c in conds):
        return u"条件の形"
    return u""


def k0_bundle(ctx, bundle, wanted):
    u"""束の形の理由の並び(空なら受理)。"""
    if not isinstance(bundle, dict) or set(bundle) != {u"型の版", u"材料"}:
        return [u"頂の鍵"]
    if bundle[u"型の版"] != u"u1":
        return [u"型の版"]
    items = bundle[u"材料"]
    if not isinstance(items, list):
        return [u"材料が並びでない"]
    if len(items) != len(wanted):
        return [u"材料の数"]
    ids = []
    for m in items:
        i = m.get(u"id") if isinstance(m, dict) else None
        if not isinstance(i, str):
            return [u"id の字"]
        ids.append(i)
    if len(set(ids)) != len(ids):
        return [u"id の重なり"]
    if set(ids) != set(wanted):
        return [u"id が定義表と違う"]
    if ids != sorted(ids):
        return [u"id の並び"]
    for m in items:
        why = k0_item(m)
        if why:
            return [why]
    return []


# ============================================================ 規則
def conds_of(m):
    return [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]


def signed(n_db_cr, direction):
    _n, db, cr = n_db_cr[0], n_db_cr[1], n_db_cr[2]
    return db - cr if direction == u"借方−貸方" else cr - db


def rule_k1(ctx, m, d, info):
    n, db, cr = ctx.led.select(info[u"conds"])
    if n < 1:
        return True
    return signed((n, db, cr), m[u"出どころ"][u"向き"]) != num_to_cents(m[u"数値"])


def carry_conds(ctx, i, period):
    r = ctx.table.rows[i]
    if not r[u"科目"]:
        return None
    conds = [(u"科目番号", u"どれか", list(r[u"科目"]))]
    jc = r[u"仕訳の種類の条件"]
    if jc is not None:
        conds.append((u"仕訳の種類", jc[u"比べ方"], jc[u"値"]))
    if period[0] == u"期間":
        conds.append((u"日付", u"以上", period[1].isoformat()))
        conds.append((u"日付", u"以下", period[2].isoformat()))
    else:
        conds.append((u"日付", u"以下", period[1].isoformat()))
    return conds


def rule_k3(ctx, m, d, info):
    period = info[u"period"]
    if period is None:
        return True
    i = m[u"id"]
    cc = carry_conds(ctx, i, period)
    mine_c = info[u"conds"]
    if cc is None:
        cc = [(u"科目番号", u"どれか", [])]
    info[u"k3"] = {u"余り": ctx.led.diff(mine_c, cc), u"漏れ": ctx.led.diff(cc, mine_c)}
    return info[u"k3"][u"余り"] != 0 or info[u"k3"][u"漏れ"] != 0 or m[u"出どころ"][u"向き"] != ctx.table.rows[i][u"向き"]



def rule_k4(ctx, m, d, info):
    period = info[u"period"]
    if period is None:
        return True
    ups = [v for (c, o, v) in info[u"conds"] if c == u"日付" and o == u"以上"]
    dns = [v for (c, o, v) in info[u"conds"] if c == u"日付" and o == u"以下"]
    p = m[u"期間"]
    if period[0] == u"期間":
        return not (ups == [period[1].isoformat()] and dns == [period[2].isoformat()]
                    and p == {u"始まり": period[1].isoformat(), u"終わり": period[2].isoformat()})
    return not (not ups and dns == [period[1].isoformat()] and p == {u"時点": period[1].isoformat()})


def rule_k5(ctx, m, d, info):
    return m[u"単位"] != d.get(u"単位")


def rule_k8(ctx, m, d, info):
    return m[u"範囲"] != d.get(u"範囲")


def rule_k10(ctx, i, period):
    u"""確かめていない科目が「入りうる」なら True。"""
    if period is None:
        return True
    present = ctx.led.accounts_in(period)
    unc = present - ctx.table.covered
    if not unc:
        return False
    mine = ctx.table.rows[i][u"科目"]
    if not mine:
        return True
    cl = ctx.led.classes
    mine_cls = set(cl[a] for a in mine if a in cl)
    all_cls = set(cl[a] for a in ctx.table.covered if a in cl)
    all_sub = set(c[1] for c in all_cls)
    for u in unc:
        if u not in cl:
            return True
        t, s = cl[u]
        if s in all_sub:
            if (t, s) in mine_cls:
                return True
        elif t in set(c[0] for c in mine_cls):
            return True
    return False


def rule_k9(ctx, i, period):
    u"""``無い`` と書いた行の取り方を、その期に当てはめて 1 行でも選ばれれば True。"""
    if period is None:
        return False
    cc = carry_conds(ctx, i, period)
    if cc is None:
        return False
    return ctx.led.select(cc)[0] >= 1


def rule_k7(ctx, results, bundle_items):
    u"""関係。戻りは (止める id の集合, 見た数, 見なかった数)。"""
    usable = {}
    for r in results:
        if r[u"状態"] == STATE_OK and not r[u"規則"]:
            usable[r[u"id"]] = int(num_to_cents(bundle_items[r[u"id"]][u"数値"]))
        elif r[u"状態"] == STATE_NONE and r[u"判定"] == u"無いを受ける":
            usable[r[u"id"]] = 0
    stop, seen, unseen = set(), 0, 0
    for rel in ctx.defn.relations:
        left, right = rel.get(u"左"), rel.get(u"右")
        if not (isinstance(left, list) and isinstance(right, list)) or not all(isinstance(x, str) for x in left + right):
            unseen += 1
            continue
        allids = left + right
        if not allids or not all(i in usable for i in allids):
            unseen += 1
            continue
        seen += 1
        if sum(usable[i] for i in left) != sum(usable[i] for i in right):
            stop.update(allids)
    return stop, seen, unseen


#: 差し替えられる規則の関数(変異の門が 1 つずつ差し替える。戻しは try/finally)
RULE_FUNCS = {u"K0": k0_bundle, u"K1": rule_k1, u"K3": rule_k3, u"K4": rule_k4, u"K5": rule_k5,
              u"K7": rule_k7, u"K8": rule_k8, u"K9": rule_k9, u"K10": rule_k10}


class Ctx(object):
    pass


def refuse(rule, reason):
    return {u"束": {u"状態": u"断り", u"規則": [rule], u"理由": [reason]}, u"材料": [], u"K7": {u"見た": 0, u"見なかった": 0},
            u"K3の行": {u"余り": 0, u"漏れ": 0}}


def check_bundle(ctx, bundle):
    u"""材料の検査。例外を出さない。"""
    try:
        return _check_bundle(ctx, bundle)
    except RecursionError:
        return refuse(u"K0", u"入れ子が深い")
    except Exception as exc:                     # noqa: BLE001
        return refuse(u"入力", u"内部の例外: " + type(exc).__name__)


def _check_bundle(ctx, bundle):
    wanted = list(ctx.defn.ids)
    reasons = RULE_FUNCS[u"K0"](ctx, bundle, wanted)
    if reasons:
        return refuse(u"K0", reasons[0])
    items = bundle[u"材料"]
    results, by_id = [], {}
    k3sum = {u"余り": 0, u"漏れ": 0}
    for m in items:
        by_id[m[u"id"]] = m
        i = m[u"id"]
        d = ctx.defn.by_id[i]
        period = expected_period(d.get(u"期"), ctx.spec)
        if m[u"状態"] == STATE_NONE:
            stops = []
            if ctx.table is not None:
                if RULE_FUNCS[u"K9"](ctx, i, period):
                    stops.append(u"K9")
                if RULE_FUNCS[u"K10"](ctx, i, period):
                    stops.append(u"K10")
            results.append({u"id": i, u"状態": STATE_NONE, u"判定": u"止める" if stops else u"無いを受ける", u"規則": stops})
            continue
        info = {u"conds": conds_of(m), u"period": period}
        order = (u"K1", u"K4", u"K5", u"K8") if ctx.table is None else (u"K1", u"K3", u"K4", u"K5", u"K8")
        stops = []
        for name in order:
            try:
                hit = RULE_FUNCS[name](ctx, m, d, info)
            except Exception:                    # noqa: BLE001
                hit = True
            if hit:
                stops.append(name)
        if ctx.table is not None:
            try:
                hit = RULE_FUNCS[u"K10"](ctx, i, period)
            except Exception:                    # noqa: BLE001
                hit = True
            if hit:
                stops.append(u"K10")
        row = {u"id": i, u"状態": STATE_OK, u"判定": u"通す", u"規則": stops}
        if u"k3" in info:
            row[u"K3"] = info[u"k3"]
            k3sum[u"余り"] += info[u"k3"][u"余り"]
            k3sum[u"漏れ"] += info[u"k3"][u"漏れ"]
        results.append(row)
    stop7, seen, unseen = RULE_FUNCS[u"K7"](ctx, results, by_id)
    for r in results:
        if r[u"状態"] == STATE_OK and r[u"id"] in stop7 and not r[u"規則"]:
            r[u"規則"] = [u"K7"]
    for r in results:
        if r[u"状態"] == STATE_OK:
            r[u"規則"] = [x for x in RULES if x in r[u"規則"]]
            r[u"判定"] = u"止める" if r[u"規則"] else u"通す"
    return {u"束": {u"状態": u"受理", u"規則": [], u"理由": []}, u"材料": results,
            u"K7": {u"見た": seen, u"見なかった": unseen}, u"K3の行": k3sum}


def make_ctx(spec_path, def_path, reading_path, src_path, table_path):
    u"""(ctx, None) か (None, 断りの辞書)。"""
    sp, err = load_spec(spec_path)
    if sp is None:
        return None, refuse(u"入力", err)
    defn, err = load_def(def_path)
    if defn is None:
        return None, refuse(u"入力", err)
    rd, err = load_reading(reading_path)
    if rd is None:
        return None, refuse(u"入力", err)
    ctx = Ctx()
    ctx.spec, ctx.defn, ctx.table = sp, defn, None
    if table_path is not None:
        ctx.table, err = load_table(table_path, defn.ids)
        if ctx.table is None:
            return None, refuse(u"入力", err)
    try:
        ctx.led = Ledger(src_path, rd)
    except Exception as exc:                     # noqa: BLE001
        return None, refuse(u"入力", u"素材が読めない: " + type(exc).__name__)
    return ctx, None


def run_bundles(ctx, paths):
    out = {}
    for p in paths:
        bundle, err = read_json(p)
        name = os.path.basename(p)
        out[name] = refuse(u"K0", u"束が読めない: " + err) if err else check_bundle(ctx, bundle)
    return out


# ============================================================ 命令
def parse_args(argv):
    opts, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and i + 1 < len(argv):
            opts[a] = argv[i + 1]
            i += 2
        else:
            return None
    return opts


def run(argv):
    if not argv or argv[0] not in ("without-table", "with-table"):
        return {u"断り": u"命令の名"}
    opts = parse_args(argv[1:])
    need = ["--spec", "--def", "--reading", "--src"] + (["--table"] if argv[0] == "with-table" else [])
    if opts is None or not all(k in opts for k in need) or ("--bundle" in opts) == ("--bundle-dir" in opts):
        return {u"断り": u"命令の形"}
    ctx, bad = make_ctx(opts["--spec"], opts["--def"], opts["--reading"], opts["--src"], opts.get("--table"))
    if ctx is None:
        return bad
    if "--bundle" in opts:
        return run_bundles(ctx, [opts["--bundle"]])[os.path.basename(opts["--bundle"])]
    try:
        names = sorted(n for n in os.listdir(opts["--bundle-dir"]) if n.endswith(".json"))
    except OSError:
        return {u"断り": u"folder が読めない"}
    return {u"束の結果": run_bundles(ctx, [os.path.join(opts["--bundle-dir"], n) for n in names])}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out_path = None
    if u"--out" in argv:
        k = argv.index(u"--out")
        if k + 1 < len(argv):
            out_path = argv[k + 1]
            del argv[k:k + 2]
    try:
        res = run(argv)
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, KeyboardInterrupt):
            raise
        res = {u"内部の例外": type(exc).__name__}
    body = dump_json(res)
    if out_path:
        try:
            with open(out_path, "wb") as fh:
                fh.write(body.encode("utf-8", "backslashreplace"))
        except OSError:
            sys.stdout.buffer.write(dump_json({u"断り": u"出力先に書けない"}).encode("utf-8", "backslashreplace") + b"\n")
    else:
        sys.stdout.buffer.write(body.encode("utf-8", "backslashreplace") + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
