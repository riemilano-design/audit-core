# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md(便 UM1)の「答えを知っている側」。

開発の写しを作る・確かめた取り方の表を作る・席に渡す folder を作る・正解の束を作る・規則の持ち越しの束を作る・変異を作って
**確かめる側(``universal_ledger_check_2026-11-23.py``)を別 process(``python3 -I``)で**両方の通りに掛ける・段 A・段 B の集計・記録を書く。
確かめる側を import しない(決めた約束の側。この script が正解の取り方・分類の字・変異を持つ)。path は全部引数で受ける。
素材の全体は、司令塔が監査 GO と commit の後に ``--src`` で渡した時だけ開く(この script の関数は、渡された path を ``mode=ro`` で開くだけ)。

    python3 universal_ledger_ref_2026-11-23.py build-dev --src <素材> --dst <開発の写し>
    python3 universal_ledger_ref_2026-11-23.py table --db <素材か写し> --spec <指定.json> --out <表>
    python3 universal_ledger_ref_2026-11-23.py gold --db <素材か写し> --spec <指定.json> --out <束>
    python3 universal_ledger_ref_2026-11-23.py carry --db <素材か写し> --table <表> --spec <指定.json> --out <束>
    python3 universal_ledger_ref_2026-11-23.py seat-folder --dest <folder> --material <素材か写し> --spec <指定.json> --instruction <指示書> --def <定義表> --reading <読込みの定義>
    python3 universal_ledger_ref_2026-11-23.py mutate --gold <束> --db <素材か写し> --spec <指定.json> --def <定義表> --outdir <folder>
    python3 universal_ledger_ref_2026-11-23.py tally-a --check <検査> --db .. --def .. --reading .. --table .. --workdir <folder> --spec NAME=PATH [--spec ..] --out <file>
    python3 universal_ledger_ref_2026-11-23.py tally-b --check <検査> --db .. --def .. --reading .. --table .. --workdir <folder> --seat <folder> [--seat ..] [--dirty NAME,..] --out <file>
    python3 universal_ledger_ref_2026-11-23.py source-facts --src <素材> --dev <写し> --from <日> --to <日> --out <file>
    python3 universal_ledger_ref_2026-11-23.py record --a <段 A> --b <段 B か ``-``> --table-sha <字> [--facts <source-facts の出力>] [--retakes <席の取り直しの数>] --out <記録>
"""
from __future__ import print_function

import argparse
import collections
import copy
import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import pathlib

od = collections.OrderedDict
SIGN_DEBIT_CREDIT, SIGN_CREDIT_DEBIT = u"借方−貸方", u"貸方−借方"
CLOSE = (u"Year-End Close - P&L to Income Summary", u"Year-End Close - Income Summary to Retained Earnings")
DEPRECIATION = u"Depreciation"
NONE_REASON = u"素材が無い"
SEAT_FILE = u"材料.json"
SEAT_SOURCE = u"素材.sqlite"
MUTATIONS = tuple(u"N%d" % k for k in range(1, 13))
#: 指定の名 → (当期の始まり, 当期の終わり)。D1 は開発、S1〜S5 は本番だけ(封 §1-2)
DESIGNATIONS = od([(u"D1", (u"2024-01-01", u"2024-12-31")), (u"S1", (u"2025-01-01", u"2025-12-31")),
                   (u"S2", (u"2026-01-01", u"2026-12-31")), (u"S3", (u"2025-04-01", u"2026-03-31")),
                   (u"S4", (u"2025-07-01", u"2026-06-30")), (u"S5", (u"2025-10-01", u"2026-09-30"))])
RELATIONS = od([(u"R1", ([u"c%02d" % k for k in range(9, 21)], [u"c01"])), (u"R2", ([u"c23"], [u"c25", u"c26"])),
                (u"R3", ([u"c01", u"c05"], [u"c03", u"c04", u"c06"]))])
A5_IDS = (u"c02", u"c07", u"c08", u"c21", u"c22", u"c24", u"c27")
A6_IDS = tuple([u"c01", u"c03", u"c04", u"c05", u"c06"] + [u"c%02d" % k for k in range(9, 21)] + [u"c23", u"c25", u"c26"])
SUB, TYP, NUM, JT, DATE = u"科目の小分類", u"科目の大分類", u"科目番号", u"仕訳の種類", u"日付"


def C(col, op, val):
    return (col, op, val)


def _gold_table():
    g = od()

    def add(i, per, dirn, cats, jt):
        g[i] = {u"期": per, u"向き": dirn, u"cats": cats, u"jt": jt}
    rev = [C(SUB, u"どれか", [u"Operating Revenue", u"Contra Revenue"])]
    add(u"c01", u"当期", SIGN_CREDIT_DEBIT, rev, u"close")
    add(u"c02", u"前期", SIGN_CREDIT_DEBIT, rev, u"close")
    add(u"c03", u"当期", SIGN_DEBIT_CREDIT, [C(SUB, u"等しい", u"COGS")], u"close")
    add(u"c04", u"当期", SIGN_DEBIT_CREDIT, [C(SUB, u"等しい", u"Operating Expense")], u"close")
    add(u"c05", u"当期", SIGN_CREDIT_DEBIT, [C(SUB, u"どれか", [u"Other Income", u"Other Income or Expense", u"Other Expense"])], u"close")
    ni = [C(TYP, u"どれか", [u"Revenue", u"Expense"])]
    add(u"c06", u"当期", SIGN_CREDIT_DEBIT, ni, u"close")
    add(u"c07", u"前期", SIGN_CREDIT_DEBIT, ni, u"close")
    add(u"c08", u"当期", SIGN_CREDIT_DEBIT, [C(SUB, u"等しい", u"Contra Fixed Asset")], u"dep")
    for k in range(1, 13):
        add(u"c%02d" % (8 + k), u"当期の月:%d" % k, SIGN_CREDIT_DEBIT, rev, u"close")
    add(u"c21", u"当期末", SIGN_DEBIT_CREDIT, [C(NUM, u"等しい", 1010)], None)
    add(u"c22", u"当期末", SIGN_DEBIT_CREDIT, [C(SUB, u"どれか", [u"Current Asset", u"Contra Current Asset"])], None)
    add(u"c23", u"当期末", SIGN_DEBIT_CREDIT, [C(TYP, u"等しい", u"Asset")], None)
    add(u"c24", u"当期末", SIGN_CREDIT_DEBIT, [C(NUM, u"等しい", 2110)], None)
    add(u"c25", u"当期末", SIGN_CREDIT_DEBIT, [C(TYP, u"等しい", u"Liability")], None)
    add(u"c26", u"当期末", SIGN_CREDIT_DEBIT, [C(TYP, u"どれか", [u"Equity", u"Revenue", u"Expense"])], None)
    add(u"c27", u"前期末", SIGN_CREDIT_DEBIT, [C(TYP, u"どれか", [u"Equity", u"Revenue", u"Expense"])], None)
    add(u"c28", u"当期", None, None, None)          # 当たる科目なし
    add(u"c29", u"当期末", None, None, None)        # 当たる科目なし
    add(u"c30", u"当期", SIGN_CREDIT_DEBIT, [C(NUM, u"等しい", 7010)], u"close")
    return g


GOLD = _gold_table()
IDS = list(GOLD)


# ============================================================ 日付・期
def pdate(s):
    return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def add_months(d, n):
    y, m = divmod(d.year * 12 + (d.month - 1) + n, 12)
    m += 1
    nxt = datetime.date(y + (m // 12), (m % 12) + 1, 1)
    last = (nxt - datetime.timedelta(days=1)).day
    return datetime.date(y, m, min(d.day, last))


def load_spec(path):
    with open(path, "rb") as fh:
        o = json.loads(fh.read().decode("utf-8"))
    assert set(o) == {u"成果物", u"当期の始まり", u"当期の終わり"} and o[u"成果物"] == u"C"
    return pdate(o[u"当期の始まり"]), pdate(o[u"当期の終わり"])


def period_of(kind, cs, ce):
    pe = cs - datetime.timedelta(days=1)
    ps = add_months(cs, -12)
    if kind == u"当期":
        return (u"期間", cs, ce)
    if kind == u"前期":
        return (u"期間", ps, pe)
    if kind == u"当期末":
        return (u"時点", ce)
    if kind == u"前期末":
        return (u"時点", pe)
    k = int(kind.split(u":")[1])
    f = add_months(cs, k - 1)
    first = datetime.date(f.year, f.month, 1)
    return (u"期間", first, add_months(first, 1) - datetime.timedelta(days=1))


def shifted_kind(kind):
    u"""もう一方の期(N4・N5)。"""
    if kind == u"当期":
        return u"前期"
    if kind == u"前期":
        return u"当期"
    if kind == u"当期末":
        return u"前期末"
    if kind == u"前期末":
        return u"当期末"
    k = int(kind.split(u":")[1])
    return u"当期の月:%d" % (k + 1 if k < 12 else 11)


def period_field(p):
    if p[0] == u"期間":
        return od([(u"始まり", p[1].isoformat()), (u"終わり", p[2].isoformat())])
    return od([(u"時点", p[1].isoformat())])


def date_conds(p):
    if p[0] == u"期間":
        return [C(DATE, u"以上", p[1].isoformat()), C(DATE, u"以下", p[2].isoformat())]
    return [C(DATE, u"以下", p[1].isoformat())]


def fmt_cents(n):
    return u"%s%d.%02d" % (u"-" if n < 0 else u"", abs(n) // 100, abs(n) % 100)


def parse_cents(t):
    neg = t.startswith(u"-")
    n = int((t[1:] if neg else t).replace(u".", u""))
    return -n if neg else n


# ============================================================ 素材(答えを知っている側の読み方 = SQL の集計)
BASE = (u"FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        u"LEFT JOIN JournalEntry j ON g.VoucherType = 'JournalEntry' AND j.JournalEntryID = g.SourceDocumentID")
COLSQL = {DATE: u"g.PostingDate", NUM: u"a.AccountNumber", TYP: u"a.AccountType", SUB: u"a.AccountSubType",
          u"伝票の種類": u"g.VoucherType", JT: u"NULLIF(j.EntryType, '')"}
DEB = u"CAST(ROUND(g.Debit * 100) AS INTEGER)"
CRE = u"CAST(ROUND(g.Credit * 100) AS INTEGER)"


def ro_connect(path):
    return sqlite3.connect(pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro", uri=True)


class Sel(object):
    def __init__(self, path):
        self.con = ro_connect(path)
        self.cache = {}

    def close(self):
        self.con.close()

    @staticmethod
    def where(conds):
        parts, args = [], []
        for col, op, val in conds:
            c = COLSQL[col]
            ph = u",".join(u"?" * len(val)) if isinstance(val, list) else u"?"
            if op == u"以上":
                parts.append(c + u" >= ?")
            elif op == u"以下":
                parts.append(c + u" <= ?")
            elif op == u"等しい":
                parts.append(c + u" = ?")
            elif op == u"どれか":
                parts.append(u"%s IN (%s)" % (c, ph))
            elif op == u"どれでもない":
                parts.append(u"(%s IS NULL OR %s NOT IN (%s))" % (c, c, ph))
            else:
                raise ValueError(op)
            args.extend(val if isinstance(val, list) else [val])
        return (u" WHERE " + u" AND ".join(parts)) if parts else u"", args

    def _key(self, tag, conds):
        return (tag, json.dumps(conds, sort_keys=True, ensure_ascii=True))

    def agg(self, conds):
        k = self._key("agg", conds)
        if k not in self.cache:
            w, a = self.where(conds)
            self.cache[k] = self.con.execute(u"SELECT count(*), coalesce(sum(%s),0), coalesce(sum(%s),0) %s%s" % (DEB, CRE, BASE, w), a).fetchone()
        return self.cache[k]

    def accounts(self, conds):
        k = self._key("acc", conds)
        if k not in self.cache:
            w, a = self.where(conds)
            self.cache[k] = sorted(r[0] for r in self.con.execute(u"SELECT DISTINCT a.AccountNumber %s%s" % (BASE, w), a))
        return self.cache[k]

    def diff(self, a, b):
        u"""条件 a を満たし条件 b を満たさない行の数。"""
        k = self._key("diff", [a, b])
        if k not in self.cache:
            wa, aa = self.where(a)
            wb, ab = self.where(b)
            ea = wa[len(u" WHERE "):] if wa else u"1"
            eb = wb[len(u" WHERE "):] if wb else u"1"
            self.cache[k] = self.con.execute(u"SELECT count(*) %s WHERE (%s) AND NOT COALESCE((%s), 0)" % (BASE, ea, eb), aa + ab).fetchone()[0]
        return self.cache[k]

    def same_rows(self, a, b):
        return self.diff(a, b) == 0 and self.diff(b, a) == 0

    def values(self, col, period):
        k = self._key("val", [col, period_field(period)])
        if k not in self.cache:
            w, a = self.where(date_conds(period))
            self.cache[k] = sorted(r[0] for r in self.con.execute(u"SELECT DISTINCT %s %s%s" % (COLSQL[col], BASE, w), a) if r[0] is not None)
        return self.cache[k]

    def signed(self, conds, direction):
        n, db, cr = self.agg(conds)
        return (db - cr if direction == SIGN_DEBIT_CREDIT else cr - db), n


# ============================================================ 材料・束
def cond_dict(c):
    return od([(u"列", c[0]), (u"比べ方", c[1]), (u"値", c[2])])


def gold_conds(i, period):
    g = GOLD[i]
    conds = list(g[u"cats"])
    if g[u"jt"] == u"close":
        conds.append(C(JT, u"どれでもない", list(CLOSE)))
    elif g[u"jt"] == u"dep":
        conds.append(C(JT, u"等しい", DEPRECIATION))
    return conds + date_conds(period)


def make_material(i, kind_period, direction, conds, cents):
    return od([(u"id", i), (u"状態", u"在る"), (u"数値", fmt_cents(cents)), (u"単位", u"通貨"), (u"期間", period_field(kind_period)),
               (u"範囲", u"全社"),
               (u"出どころ", od([(u"種類", u"表の行の和"), (u"表", u"仕訳の行"), (u"向き", direction), (u"条件", [cond_dict(c) for c in conds])]))])


def none_material(i):
    return od([(u"id", i), (u"状態", u"無い"), (u"無い理由", NONE_REASON)])


def conds_of(m):
    return [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]


def gold_bundle(sel, cs, ce):
    items = []
    for i in IDS:
        g = GOLD[i]
        p = period_of(g[u"期"], cs, ce)
        if g[u"cats"] is None:
            items.append(none_material(i))
            continue
        conds = gold_conds(i, p)
        s, n = sel.signed(conds, g[u"向き"])
        items.append(make_material(i, p, g[u"向き"], conds, s) if n >= 1 else none_material(i))
    return od([(u"型の版", u"u1"), (u"材料", items)])


def make_table(sel, cs, ce):
    u"""確かめた取り方の表(開発の写しだけから)。前期・前期末・月の行は、当期の同じ名の行と同じ。"""
    same = {u"c02": u"c01", u"c07": u"c06", u"c27": u"c26"}
    for k in range(9, 21):
        same[u"c%02d" % k] = u"c01"
    rows = od()
    for i in IDS:
        src = same.get(i, i)
        g = GOLD[src]
        if g[u"cats"] is None:
            rows[i] = od([(u"向き", SIGN_CREDIT_DEBIT), (u"科目", []), (u"仕訳の種類の条件", None)])
            continue
        p = period_of(GOLD[src][u"期"], cs, ce)
        conds = gold_conds(src, p)
        jc = None
        if g[u"jt"] == u"close":
            jc = od([(u"比べ方", u"どれでもない"), (u"値", list(CLOSE))])
        elif g[u"jt"] == u"dep":
            jc = od([(u"比べ方", u"等しい"), (u"値", DEPRECIATION)])
        rows[i] = od([(u"向き", g[u"向き"]), (u"科目", sel.accounts(conds)), (u"仕訳の種類の条件", jc)])
    return od([(u"表の版", u"t1"), (u"行", rows)])


def carry_bundle(sel, table, cs, ce):
    u"""規則の持ち越し(席を使わない)。科目が空の id は ``無い``。選ぶ行が 0 行でも ``無い``。"""
    items = []
    for i in IDS:
        r = table[u"行"][i]
        p = period_of(GOLD[i][u"期"], cs, ce)
        if not r[u"科目"]:
            items.append(none_material(i))
            continue
        conds = [C(NUM, u"どれか", list(r[u"科目"]))]
        if r[u"仕訳の種類の条件"] is not None:
            conds.append(C(JT, r[u"仕訳の種類の条件"][u"比べ方"], r[u"仕訳の種類の条件"][u"値"]))
        conds += date_conds(p)
        s, n = sel.signed(conds, r[u"向き"])
        items.append(make_material(i, p, r[u"向き"], conds, s) if n >= 1 else none_material(i))
    return od([(u"型の版", u"u1"), (u"材料", items)])


def relation_status(bundle):
    u"""関係 R1〜R3 が成り立つか(``無い`` は 0)。戻りは {名: True/False}。"""
    val = {}
    for m in bundle[u"材料"]:
        val[m[u"id"]] = parse_cents(m[u"数値"]) if m[u"状態"] == u"在る" else 0
    return od((k, sum(val[x] for x in l) == sum(val[x] for x in r)) for k, (l, r) in RELATIONS.items())


# ============================================================ 変異 N1〜N12
def reeval(sel, m):
    s, _n = sel.signed(conds_of(m), m[u"出どころ"][u"向き"])
    m[u"数値"] = fmt_cents(s)
    return m


def mutate_item(sel, bundle, idx, name, cs, ce, kinds):
    u"""``bundle[材料][idx]`` に変異 1 つ。戻りは変えた材料の dict か、作れなければ None。"""
    items = bundle[u"材料"]
    m = copy.deepcopy(items[idx])
    i = m[u"id"]
    kind = kinds[i]
    period = period_of(kind, cs, ce)
    ok = m[u"状態"] == u"在る"
    if name == u"N9":
        if ok:
            return None
        accs = sel.values(NUM, period)
        if not accs:
            return None
        conds = date_conds(period) + [C(NUM, u"等しい", min(accs))]
        s, _n = sel.signed(conds, SIGN_DEBIT_CREDIT)
        return make_material(i, period, SIGN_DEBIT_CREDIT, conds, s)
    if not ok:
        return None
    src = m[u"出どころ"]
    conds = conds_of(m)
    if name == u"N1":
        m[u"数値"] = fmt_cents(parse_cents(m[u"数値"]) + 1)
        return m
    if name == u"N2":
        accs = sel.accounts(conds)
        if len(accs) < 2:
            return None
        src[u"条件"].append(cond_dict(C(NUM, u"どれでもない", [min(accs)])))
        return reeval(sel, m)
    if name == u"N3":
        for c in src[u"条件"]:
            if c[u"比べ方"] in (u"どれか", u"等しい"):
                cur = list(c[u"値"]) if c[u"比べ方"] == u"どれか" else [c[u"値"]]
                cand = [v for v in sel.values(c[u"列"], period) if v not in cur]
                if not cand:
                    return None
                c[u"比べ方"] = u"どれか"
                c[u"値"] = cur + [min(cand)]
                return reeval(sel, m)
        return None
    if name in (u"N4", u"N5"):
        np_ = period_of(shifted_kind(kind), cs, ce)
        for c in src[u"条件"]:
            if c[u"列"] == DATE:
                if c[u"比べ方"] == u"以上":
                    c[u"値"] = np_[1].isoformat()
                else:
                    c[u"値"] = (np_[2] if np_[0] == u"期間" else np_[1]).isoformat()
        if name == u"N5":
            m[u"期間"] = period_field(np_)
        return reeval(sel, m)
    if name == u"N6":
        if period[0] != u"時点":
            return None
        start = cs if kind == u"当期末" else add_months(cs, -12)
        src[u"条件"].append(cond_dict(C(DATE, u"以上", start.isoformat())))
        return reeval(sel, m)
    if name == u"N7":
        keep = [c for c in src[u"条件"] if not (c[u"列"] == JT and c[u"比べ方"] == u"どれでもない")]
        if len(keep) == len(src[u"条件"]):
            return None
        src[u"条件"] = keep
        return reeval(sel, m)
    if name == u"N8":
        return none_material(i)
    if name == u"N10":
        src[u"向き"] = SIGN_CREDIT_DEBIT if src[u"向き"] == SIGN_DEBIT_CREDIT else SIGN_DEBIT_CREDIT
        return reeval(sel, m)
    if name == u"N11":
        for j in range(idx + 1, len(items)):
            o = items[j]
            if o[u"状態"] == u"在る" and o[u"数値"] != m[u"数値"]:
                m[u"出どころ"] = copy.deepcopy(o[u"出どころ"])
                m[u"数値"] = o[u"数値"]
                return m
        return None
    if name == u"N12":
        for c in src[u"条件"]:
            if c[u"列"] == DATE and c[u"比べ方"] == u"以下":
                c[u"値"] = (pdate(c[u"値"]) - datetime.timedelta(days=1)).isoformat()
        return reeval(sel, m)
    raise ValueError(name)


def make_mutations(sel, bundle, cs, ce):
    u"""戻りは [(変異の名, id, 変えた束 か None, 数値が元と同じか)]。作れなかった組も含む。"""
    kinds = dict((i, GOLD[i][u"期"]) for i in IDS)
    out = []
    for idx, m0 in enumerate(bundle[u"材料"]):
        for name in MUTATIONS:
            nm = mutate_item(sel, bundle, idx, name, cs, ce, kinds)
            if nm is None:
                out.append((name, m0[u"id"], None, False))
                continue
            nb = copy.deepcopy(bundle)
            nb[u"材料"][idx] = nm
            if json.dumps(nb, ensure_ascii=False) == json.dumps(bundle, ensure_ascii=False):
                out.append((name, m0[u"id"], None, False))
                continue
            same = m0[u"状態"] == u"在る" and nm[u"状態"] == u"在る" and nm[u"数値"] == m0[u"数値"]
            out.append((name, m0[u"id"], nb, same))
    return out


# ============================================================ file
def wjson(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8"))


def rjson(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ============================================================ 開発の写し(司令塔の下調べの script と同じ結果になる形)
DEV_Y0, DEV_Y1 = u"2024-01-01", u"2024-12-31"
DEV_WHERE = od([
    (u"Account", u"1"), (u"CostCenter", u"1"), (u"Warehouse", u"1"), (u"Customer", u"1"), (u"Supplier", u"1"),
    (u"GLEntry", u"FiscalYear=2024"),
    (u"JournalEntry", u"PostingDate between '%s' and '%s'" % (DEV_Y0, DEV_Y1)),
    (u"Budget", u"FiscalYear=2024"), (u"BudgetLine", u"FiscalYear=2024"),
    (u"PayrollPeriod", u"FiscalYear=2024"),
    (u"PayrollRegister", u"PayrollPeriodID in (select PayrollPeriodID from s.PayrollPeriod where FiscalYear=2024)"),
    (u"PayrollRegisterLine", u"PayrollRegisterID in (select PayrollRegisterID from s.PayrollRegister where PayrollPeriodID in (select PayrollPeriodID from s.PayrollPeriod where FiscalYear=2024))"),
    (u"PayrollLiabilityRemittance", u"RemittanceDate between '%s' and '%s'" % (DEV_Y0, DEV_Y1)),
    (u"DebtAgreement", u"OriginationDate<='%s'" % DEV_Y1),
    (u"DebtScheduleLine", u"PaymentDate<='%s' and DebtAgreementID in (select DebtAgreementID from s.DebtAgreement where OriginationDate<='%s')" % (DEV_Y1, DEV_Y1)),
    (u"FixedAsset", u"InServiceDate<='%s'" % DEV_Y1),
    (u"FixedAssetEvent", u"EventDate between '%s' and '%s'" % (DEV_Y0, DEV_Y1)),
    (u"Employee", u"HireDate<='%s'" % DEV_Y1),
])


def build_dev(src, dst):
    u"""開発の写し(会計年度 2024)を作る。戻りは {表: 行の数}。``src`` は素材(読むだけで開く)。"""
    if os.path.exists(dst):
        os.remove(dst)
    d = sqlite3.connect(dst)
    try:
        d.execute("attach database ? as s", (pathlib.Path(os.path.abspath(src)).as_uri() + "?mode=ro",))
    except sqlite3.OperationalError:
        d.close()
        raise
    for t, w in DEV_WHERE.items():
        d.execute('create table "%s" as select * from s."%s" where %s' % (t, t, w))
    d.execute("update Employee set TerminationDate=null, TerminationReason=null, EmploymentStatus=null, IsActive=null where TerminationDate>'%s'" % DEV_Y1)
    d.execute("update FixedAsset set DisposalDate=null, Status=null where DisposalDate>'%s'" % DEV_Y1)
    d.commit()
    counts = od()
    for t in DEV_WHERE:
        counts[t] = d.execute('select count(*) from "%s"' % t).fetchone()[0]
    d.close()
    return counts


# ============================================================ 検査を別 process で
def run_check(check, mode, spec, defn, reading, db, bundle_dir, out, table=None):
    cmd = [sys.executable, "-I", check, mode, "--spec", spec, "--def", defn, "--reading", reading, "--src", db,
           "--bundle-dir", bundle_dir, "--out", out]
    if table is not None:
        cmd += ["--table", table]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("check rc %d: %s" % (r.returncode, r.stderr.decode("utf-8", "replace")[:300]))
    return rjson(out)[u"束の結果"]


def verdict_of(res, i):
    u"""束の結果のうち id の判定(``通す``・``無いを受ける``・``止める``・``断り``)と規則。"""
    if res[u"束"][u"状態"] != u"受理":
        return u"断り", list(res[u"束"][u"規則"])
    for r in res[u"材料"]:
        if r[u"id"] == i:
            return r[u"判定"], list(r[u"規則"])
    return u"断り", [u"id が無い"]


def passed(v):
    return v in (u"通す", u"無いを受ける")


def tally_rules(results):
    c = collections.Counter()
    for res in results:
        if res[u"束"][u"状態"] != u"受理":
            c[u"断り"] += 1
            continue
        for r in res[u"材料"]:
            if r[u"判定"] == u"止める":
                for k in r[u"規則"]:
                    c[k] += 1
    return dict(c)


# ============================================================ 段 A
def tally_a(args):
    os.makedirs(args.workdir, exist_ok=True)
    out = od()
    mut_total = od((n, od([(u"作れた", 0), (u"表なしが通した", 0), (u"表つきが通した", 0), (u"数値が元と同じ", 0)])) for n in MUTATIONS)
    a5 = od([(u"作れた", 0), (u"表なしが通した", 0)])
    a6 = od([(u"数値が違う作れた", 0), (u"表なしが通した", 0)])
    unmade = collections.Counter()
    gold_rows = od([(u"在る", 0), (u"無い", 0)])
    verdicts = od([(u"表なし", collections.Counter()), (u"表つき", collections.Counter())])
    rules = od([(u"表なし", collections.Counter()), (u"表つき", collections.Counter())])
    k3rows = collections.Counter()
    rel_hold = 0
    rel_total = 0
    carry_same = carry_same_num = carry_diff = 0
    per_designation = od()
    sel = Sel(args.db)
    try:
        for ent in args.spec:
            name, path = ent.split("=", 1)
            cs, ce = load_spec(path)
            g = gold_bundle(sel, cs, ce)
            cb = carry_bundle(sel, rjson(args.table), cs, ce)
            gdir = os.path.join(args.workdir, "gold_" + name)
            shutil.rmtree(gdir, ignore_errors=True)
            wjson(os.path.join(gdir, "gold.json"), g)
            wjson(os.path.join(gdir, "carry.json"), cb)
            for m in g[u"材料"]:
                gold_rows[m[u"状態"]] += 1
            for k, ok in relation_status(g).items():
                rel_total += 1
                rel_hold += 1 if ok else 0
            plain = run_check(args.check, "without-table", path, args.def_, args.reading, args.db, gdir, os.path.join(args.workdir, "gold_%s_plain.json" % name))
            tabled = run_check(args.check, "with-table", path, args.def_, args.reading, args.db, gdir, os.path.join(args.workdir, "gold_%s_tabled.json" % name), table=args.table)
            for label, res in ((u"表なし", plain[u"gold.json"]), (u"表つき", tabled[u"gold.json"])):
                for r in res[u"材料"]:
                    verdicts[label][r[u"判定"]] += 1
                    for k in r[u"規則"]:
                        rules[label][k] += 1
            for r in tabled[u"gold.json"][u"材料"]:
                if u"K3" in r:
                    k3rows[u"余り"] += r[u"K3"][u"余り"]
                    k3rows[u"漏れ"] += r[u"K3"][u"漏れ"]
            for m, c in zip(g[u"材料"], cb[u"材料"]):
                if m[u"状態"] != c[u"状態"]:
                    carry_diff += 1
                    continue
                if m[u"状態"] == u"無い":
                    carry_same += 1
                    carry_same_num += 1
                    continue
                numeq = m[u"数値"] == c[u"数値"]
                idseq = sel.same_rows(conds_of(m), conds_of(c))
                carry_same_num += 1 if numeq else 0
                if numeq and idseq:
                    carry_same += 1
                else:
                    carry_diff += 1
            # 変異
            muts = make_mutations(sel, g, cs, ce)
            mdir = os.path.join(args.workdir, "mut_" + name)
            shutil.rmtree(mdir, ignore_errors=True)
            index = od()
            for n, i, nb, same in muts:
                if nb is None:
                    unmade[n] += 1
                    continue
                fn = "%s_%s.json" % (n, i)
                wjson(os.path.join(mdir, fn), nb)
                index[fn] = (n, i, same)
            mp = run_check(args.check, "without-table", path, args.def_, args.reading, args.db, mdir, os.path.join(args.workdir, "mut_%s_plain.json" % name))
            mt = run_check(args.check, "with-table", path, args.def_, args.reading, args.db, mdir, os.path.join(args.workdir, "mut_%s_tabled.json" % name), table=args.table)
            for fn, (n, i, same) in index.items():
                pp = passed(verdict_of(mp[fn], i)[0])
                pt = passed(verdict_of(mt[fn], i)[0])
                t = mut_total[n]
                t[u"作れた"] += 1
                t[u"表なしが通した"] += 1 if pp else 0
                t[u"表つきが通した"] += 1 if pt else 0
                t[u"数値が元と同じ"] += 1 if same else 0
                orig = next(x for x in g[u"材料"] if x[u"id"] == i)
                if i in A5_IDS and n in (u"N2", u"N3", u"N10") and orig[u"状態"] == u"在る":
                    a5[u"作れた"] += 1
                    a5[u"表なしが通した"] += 1 if pp else 0
                if i in A6_IDS and n in (u"N2", u"N3", u"N7", u"N10") and orig[u"状態"] == u"在る" and not same:
                    a6[u"数値が違う作れた"] += 1
                    a6[u"表なしが通した"] += 1 if pp else 0
            per_designation[name] = od([(u"在る", sum(1 for m in g[u"材料"] if m[u"状態"] == u"在る")),
                                        (u"関係が成り立つ", sum(1 for ok in relation_status(g).values() if ok))])
    finally:
        sel.close()
    out[u"正解の束"] = od([(u"束の数", len(args.spec)), (u"行の数", sum(gold_rows.values())), (u"状態", dict(gold_rows)),
                         (u"関係が成り立つ本数", rel_hold), (u"関係の本数", rel_total), (u"指定ごと", per_designation)])
    out[u"検査の結果"] = od((k, od([(u"判定", dict(verdicts[k])), (u"止めた規則", dict(rules[k]))])) for k in verdicts)
    out[u"K3の行"] = dict(k3rows)
    out[u"規則の持ち越し"] = od([(u"正解と同じ行", carry_same), (u"正解と違う行", carry_diff), (u"数値だけ同じ行", carry_same_num)])
    out[u"変異"] = od((n, od(list(mut_total[n].items()) + [(u"作れなかった", unmade[n])])) for n in MUTATIONS)
    out[u"A5"] = a5
    out[u"A6"] = a6
    wjson(args.out, out)


# ============================================================ 段 B
def seat_designation(spec_path):
    cs, ce = load_spec(spec_path)
    for k, (a, b) in DESIGNATIONS.items():
        if pdate(a) == cs and pdate(b) == ce:
            return k
    return None


def tally_b(args):
    os.makedirs(args.workdir, exist_ok=True)
    dirty = set(x for x in (args.dirty or u"").split(u",") if x)
    sel = Sel(args.db)
    seats = od()
    for folder in args.seat:
        name = os.path.basename(os.path.normpath(folder))
        d = seat_designation(os.path.join(folder, u"指定.json"))
        seats[name] = {u"folder": folder, u"指定": d}
    by_d = collections.defaultdict(list)
    for n, s in seats.items():
        by_d[s[u"指定"]].append(n)
    rows = []                                   # 1 行 1 要素
    refused = 0
    gold_by = {}
    try:
        for d, names in by_d.items():
            cs, ce = [pdate(x) for x in DESIGNATIONS[d]]
            g = gold_bundle(sel, cs, ce)
            gold_by[d] = g
            bdir = os.path.join(args.workdir, "seat_" + d)
            shutil.rmtree(bdir, ignore_errors=True)
            os.makedirs(bdir)
            spec_path = os.path.join(args.workdir, "spec_%s.json" % d)
            wjson(spec_path, od([(u"成果物", u"C"), (u"当期の始まり", DESIGNATIONS[d][0]), (u"当期の終わり", DESIGNATIONS[d][1])]))
            for n in names:
                p = os.path.join(seats[n][u"folder"], SEAT_FILE)
                if os.path.exists(p):
                    shutil.copyfile(p, os.path.join(bdir, n + ".json"))
                else:
                    with open(os.path.join(bdir, n + ".json"), "wb") as fh:
                        fh.write(b"")
            plain = run_check(args.check, "without-table", spec_path, args.def_, args.reading, args.db, bdir, os.path.join(args.workdir, "seat_%s_plain.json" % d))
            tabled = run_check(args.check, "with-table", spec_path, args.def_, args.reading, args.db, bdir, os.path.join(args.workdir, "seat_%s_tabled.json" % d), table=args.table)
            for n in names:
                fn = n + ".json"
                bundle = None
                if plain[fn][u"束"][u"状態"] == u"受理":
                    bundle = rjson(os.path.join(bdir, fn))
                if bundle is None:
                    refused += 1
                    for m in g[u"材料"]:
                        rows.append(od([(u"席", n), (u"指定", d), (u"id", m[u"id"]), (u"状態の一致", False), (u"正解どおり", False), (u"数値の違い", False), (u"行の集まりだけ違う", False),
                                        (u"表なし", u"断り"), (u"表つき", u"断り"), (u"答え", None), (u"_conds", None)]))
                    continue
                answers = dict((x[u"id"], x) for x in bundle[u"材料"])
                for m in g[u"材料"]:
                    a = answers[m[u"id"]]
                    same_state = a[u"状態"] == m[u"状態"]
                    right = same_state
                    numdiff = False
                    setdiff = False
                    key = None
                    key = [u"在る", a[u"数値"]] if a[u"状態"] == u"在る" else [u"無い"]
                    if same_state and a[u"状態"] == u"在る":
                        numeq = a[u"数値"] == m[u"数値"]
                        seteq = sel.same_rows(conds_of(a), conds_of(m))
                        right = numeq and seteq
                        numdiff = not numeq
                        setdiff = numeq and not seteq
                    rows.append(od([(u"席", n), (u"指定", d), (u"id", m[u"id"]), (u"状態の一致", same_state), (u"正解どおり", right),
                                    (u"数値の違い", numdiff), (u"行の集まりだけ違う", setdiff),
                                    (u"表なし", verdict_of(plain[fn], m[u"id"])[0]), (u"表つき", verdict_of(tabled[fn], m[u"id"])[0]),
                                    (u"答え", key), (u"_conds", conds_of(a) if a[u"状態"] == u"在る" else None)]))
    finally:
        sel.close()

    def summarize(rs):
        s = od()
        s[u"行"] = len(rs)
        s[u"正解どおり"] = sum(1 for r in rs if r[u"正解どおり"])
        s[u"数値は同じで行の集まりだけ違う"] = sum(1 for r in rs if r[u"行の集まりだけ違う"])
        for label in (u"表なし", u"表つき"):
            ps = [r for r in rs if r[label] in (u"通す", u"無いを受ける")]
            s[label] = od([(u"通した", len(ps)), (u"止めた", sum(1 for r in rs if r[label] == u"止める")),
                           (u"断り", sum(1 for r in rs if r[label] == u"断り")),
                           (u"通した行のうち数値が違う", sum(1 for r in ps if r[u"数値の違い"])),
                           (u"通した行のうち状態が違う", sum(1 for r in ps if not r[u"状態の一致"])),
                           (u"通した行のうち行の集まりだけ違う", sum(1 for r in ps if r[u"行の集まりだけ違う"])),
                           (u"正しい材料を止めた", sum(1 for r in rs if r[label] == u"止める" and r[u"正解どおり"]))])
        return s
    sel0 = Sel(args.db)
    out = od()
    out[u"席"] = od((n, od([(u"指定", s[u"指定"])])) for n, s in seats.items())
    out[u"席の数"] = len(seats)
    out[u"全部"] = summarize(rows)
    out[u"汚れた席の数"] = len(dirty & set(seats))
    out[u"汚れを除く"] = summarize([r for r in rows if r[u"席"] not in dirty])
    out[u"束が K0 で断られた数"] = refused
    out[u"指定ごと"] = od((d, summarize([r for r in rows if r[u"指定"] == d])) for d in DESIGNATIONS if d in by_d)
    calendar_rows = [r for r in rows if r[u"指定"] in (u"S1", u"S2")]
    shifted_rows = [r for r in rows if r[u"指定"] in (u"S3", u"S4", u"S5")]
    out[u"暦年の指定の率"] = od([(u"行", len(calendar_rows)), (u"正解どおり", sum(1 for r in calendar_rows if r[u"正解どおり"]))])
    out[u"ずらした指定の率"] = od([(u"行", len(shifted_rows)), (u"正解どおり", sum(1 for r in shifted_rows if r[u"正解どおり"]))])
    out[u"id ごと"] = od((i, od([(u"行", sum(1 for r in rows if r[u"id"] == i)), (u"正解どおり", sum(1 for r in rows if r[u"id"] == i and r[u"正解どおり"]))])) for i in IDS)
    out[u"c08"] = od([(u"行", sum(1 for r in rows if r[u"id"] == u"c08")), (u"正解どおり", sum(1 for r in rows if r[u"id"] == u"c08" and r[u"正解どおり"]))])
    out[u"ずらした指定の c26"] = od([(u"行", sum(1 for r in shifted_rows if r[u"id"] == u"c26")), (u"正解どおり", sum(1 for r in shifted_rows if r[u"id"] == u"c26" and r[u"正解どおり"]))])
    cn = [r for r in rows if r[u"id"] in (u"c28", u"c29")]
    out[u"c28・c29"] = od([(u"行", len(cn)), (u"席が無いと書いた", sum(1 for r in cn if r[u"答え"] == [u"無い"]))])
    agree = 0
    for d, names in by_d.items():
        for i in IDS:
            rs = [r for r in rows if r[u"指定"] == d and r[u"id"] == i and r[u"答え"] is not None]
            if len(names) < 3 or len(rs) != len(names) or any(r[u"答え"] != rs[0][u"答え"] for r in rs):
                continue
            if rs[0][u"答え"][0] == u"在る" and not all(sel0.same_rows(rs[0][u"_conds"], r[u"_conds"]) for r in rs[1:]):
                continue
            agree += 1
    sel0.close()
    out[u"3 席が 3 つとも同じ行"] = agree
    wjson(args.out, out)


# ============================================================ 素材の全体の数(段 A)
def source_facts(args):
    con = ro_connect(args.src)
    dev = ro_connect(args.dev)
    out = od()
    out[u"貸借が合わない伝票"] = con.execute(
        "select count(*) from (select 1 from GLEntry group by VoucherType, VoucherNumber having sum(CAST(ROUND(Debit*100) AS INTEGER)) != sum(CAST(ROUND(Credit*100) AS INTEGER)))").fetchone()[0]
    idle = set(r[0] for r in dev.execute("select AccountID from Account where AccountID not in (select AccountID from GLEntry)"))
    moved = set(r[0] for r in con.execute("select distinct AccountID from GLEntry where PostingDate between ? and ?", (args.from_, args.to)))
    out[u"開発の年に動きが無かった科目"] = len(idle)
    out[u"うち指定の間に行が在る科目"] = len(idle & moved)
    wjson(args.out, out)
    con.close()
    dev.close()


# ============================================================ 席に渡す folder
def seat_folder(args):
    os.makedirs(args.dest, exist_ok=True)
    cs, ce = load_spec(args.spec)
    shutil.copyfile(args.instruction, os.path.join(args.dest, u"指示書.md"))
    shutil.copyfile(args.def_, os.path.join(args.dest, u"definition_C.json"))
    shutil.copyfile(args.reading, os.path.join(args.dest, u"reading_def.json"))
    shutil.copyfile(args.spec, os.path.join(args.dest, u"指定.json"))
    target = os.path.join(args.dest, SEAT_SOURCE)
    if os.path.exists(target):
        os.remove(target)
    try:
        os.link(args.material, target)
    except OSError:
        shutil.copyfile(args.material, target)


# ============================================================ 記録(数だけ)
FORBIDDEN_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def write_record(args):
    u"""記録(数だけ)。``--facts`` は ``source-facts`` の出力(素材の全体の数)で、段 A の ``素材の全体`` に入る(無ければ None)。
    ``--retakes`` は席の取り直しの数(道具の故障で席が何も書かずに終わった時の取り直し。封 §1-9)で、段 B の ``席の取り直しの数`` に入る(段 B を渡す時は必須・渡さない時は渡せない)。"""
    a = rjson(args.a)
    a[u"素材の全体"] = rjson(args.facts) if getattr(args, "facts", u"-") != u"-" else None
    b = rjson(args.b) if args.b != u"-" else None
    retakes = getattr(args, "retakes", None)
    assert (b is None) == (retakes is None), u"段 B を渡す時は --retakes も渡す(渡さない時は --retakes も渡さない)"
    if b is not None:
        assert retakes >= 0
        b[u"席の取り直しの数"] = retakes
    rec = od([(u"便", u"UM1"), (u"封", u"0d2156e4"), (u"段 A", a), (u"段 B", b), (u"確かめた取り方の表の SHA-256", args.table_sha)])
    body = json.dumps(rec, ensure_ascii=False, indent=1)
    assert not FORBIDDEN_RE.search(body)
    wjson(args.out, rec)


# ============================================================ 命令
def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("build-dev"); s.add_argument("--src", required=True); s.add_argument("--dst", required=True)
    s = sub.add_parser("table"); s.add_argument("--db", required=True); s.add_argument("--spec", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("gold"); s.add_argument("--db", required=True); s.add_argument("--spec", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("carry"); s.add_argument("--db", required=True); s.add_argument("--table", required=True); s.add_argument("--spec", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("seat-folder"); s.add_argument("--dest", required=True); s.add_argument("--material", required=True); s.add_argument("--spec", required=True)
    s.add_argument("--instruction", required=True); s.add_argument("--def", dest="def_", required=True); s.add_argument("--reading", required=True)
    s = sub.add_parser("mutate"); s.add_argument("--gold", required=True); s.add_argument("--db", required=True); s.add_argument("--spec", required=True)
    s.add_argument("--def", dest="def_", required=True); s.add_argument("--outdir", required=True)
    for nm in ("tally-a", "tally-b"):
        s = sub.add_parser(nm)
        for k in ("--check", "--db", "--reading", "--table", "--workdir", "--out"):
            s.add_argument(k, required=True)
        s.add_argument("--def", dest="def_", required=True)
        if nm == "tally-a":
            s.add_argument("--spec", action="append", required=True)
        else:
            s.add_argument("--seat", action="append", required=True)
            s.add_argument("--dirty")
    s = sub.add_parser("source-facts"); s.add_argument("--src", required=True); s.add_argument("--dev", required=True)
    s.add_argument("--from", dest="from_", required=True); s.add_argument("--to", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("record"); s.add_argument("--a", required=True); s.add_argument("--b", required=True); s.add_argument("--table-sha", required=True); s.add_argument("--out", required=True)
    s.add_argument("--facts", default=u"-"); s.add_argument("--retakes", type=int, default=None)
    args = p.parse_args(argv)
    if args.cmd == "build-dev":
        for t, n in build_dev(args.src, args.dst).items():
            print(t, n)
    elif args.cmd in ("table", "gold", "carry"):
        cs, ce = load_spec(args.spec)
        sel = Sel(args.db)
        try:
            if args.cmd == "table":
                wjson(args.out, make_table(sel, cs, ce))
                print(sha256_file(args.out))
            elif args.cmd == "gold":
                wjson(args.out, gold_bundle(sel, cs, ce))
            else:
                wjson(args.out, carry_bundle(sel, rjson(args.table), cs, ce))
        finally:
            sel.close()
    elif args.cmd == "seat-folder":
        seat_folder(args)
    elif args.cmd == "mutate":
        cs, ce = load_spec(args.spec)
        sel = Sel(args.db)
        try:
            g = rjson(args.gold)
            index = od()
            for n, i, nb, same in make_mutations(sel, g, cs, ce):
                if nb is not None:
                    fn = "%s_%s.json" % (n, i)
                    wjson(os.path.join(args.outdir, fn), nb)
                    index[fn] = od([(u"変異", n), (u"id", i), (u"数値が元と同じ", same)])
            wjson(os.path.join(os.path.dirname(os.path.normpath(args.outdir)), os.path.basename(os.path.normpath(args.outdir)) + "_index.json"), index)
        finally:
            sel.close()
    elif args.cmd == "tally-a":
        tally_a(args)
    elif args.cmd == "tally-b":
        tally_b(args)
    elif args.cmd == "source-facts":
        source_facts(args)
    elif args.cmd == "record":
        write_record(args)
    else:
        p.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
