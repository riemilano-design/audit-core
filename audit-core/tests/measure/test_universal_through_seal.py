# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md(UM2 ― 別の席が形を決めた架空の会計ソフトの file 一式から、資料の指定から人が読む版の資料までの 7 段を 2 期ぶん通す)の封の門。

**この門が作る素材は、この file の中で組み立てる架空の 1 社の file 一式だけ(tmp に書く)。** 本番の 4 社(1〜4)の素材・正解は作らない・読まない
(``dev_world`` は開発の番号以外なら例外で止まる)。置き場も道具も通信も鍵も使わない。席(subagent)は呼ばない。openpyxl は xlsx を書く所だけ(検査は標準の library だけで読む)。

**この門が縛るもの**

1. 封の字: 封の file の sha256・封の commit の blob と同じ・engine は封の commit から 0 行・定義表が便 UM0 のまま・規則 K0〜K9・K11・変異・予測の表・表の境の数が script の字と同じ。
2. 検査は答えを知っている側を import せず(AST)・標準の library だけ・``python3 -I`` の別 process で動き、**どんな入力でも rc 0 で結果の JSON**。答えの file(正解)を開かない。
3. 型 ``u2``: K0(形)・K1(値)・K4(期)・K5(単位)・K8(範囲)・K7(関係)・K9(無い)・K11(新しい値)・通す(取り方は未確認)・比べ方ごと・日付の書き方ごと・文字コードごと。
4. 規則を 1 つずつ外した検査(関数の差し替え。戻しは try/finally)で、対応する変異が通る(赤になる)。
5. 持ち越し(2 期目)・置き場・人が読む版・人が読む版の検査。
6. 退化の入力(材料 0 個・巨大・壊れた JSON・孤立 surrogate・入れ子・型違い)。
7. 集計(席の代わりに作った出力で)・記録(無い時は無いと assert し、在る時は形・禁止の字・数の導き直し)・封 → 実装 → 記録の順。
"""
import ast
import builtins
import collections
import contextlib
import copy
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
od = collections.OrderedDict


def load_module(rel, name):
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md"
SEAL_COMMIT_SHORT = "9ff5af9e"
SEAL_SHA256 = "bcbfd4a5447d30e8f8ae818bd3dfe6e08d8cfe76457257e7417484d8ea0a4d98"
CHECK_REL = "measure/universal_through_check_2026-11-23.py"
TALLY_REL = "measure/universal_through_tally_2026-11-23.py"
DEF_RELS = ("fixtures/universal/um0/definition_A.json", "fixtures/universal/um0/definition_B.json")
DEF_SHA256 = ("fd0e878092d106a93c0a65422c664006ac8cb7cf6428224290dab2a80e31e84b", "8c8bd2e2a56e159e51ba5371cd1127783b7280db9a9b08da0d627c8d2e54d39f")
DEF_COMMIT_SHORT = "a2326934"
INSTRUCTION_REL = "docs/UNIVERSAL_THROUGH_INSTRUCTION_2026-11-23.md"
UM0_INSTRUCTION_REL = "docs/UNIVERSAL_MATERIAL_INSTRUCTION_2026-11-23.md"
BRIEF_REL = "docs/UNIVERSAL_THROUGH_SOURCE_BRIEF_2026-11-23.md"
GATE_REL = "tests/measure/test_universal_through_seal.py"
RECORD_REL = "fixtures/universal/um2/record.json"
ORDER_FILES = (BRIEF_REL, CHECK_REL, TALLY_REL, INSTRUCTION_REL, GATE_REL)
CHK = load_module(CHECK_REL, "um2_check_for_seal_gate")
TAL = load_module(TALLY_REL, "um2_tally_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_um2_seal_gate")      # 順序の部品。門としては走らせない
DEV = (101,)
FAKE = (101, 102, 103)          # この門の中で作る架空の社の番号(開発の 101 と、複数社の集計を見るための 102・103)。本番の 1〜4 は作らない


def J(text):
    return text.encode("utf-8")


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def read_bytes_abs(path):
    with open(path, "rb") as fh:
        return fh.read()


def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False))


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")


def tag_rows(defn):
    return dict((r[u"id"], r) for r in defn.rows)


# ======================================================================== 架空の 1 社の file 一式(この file の中で組む。素材を作る席の素材ではない)
D = datetime.date
FY_START = {0: (2024, 4), 1: (2025, 4), 2: (2026, 4)}
ACCOUNT = {u"a03": u"勘定甲03", u"a04": u"勘定甲04", u"a06": u"勘定甲06", u"a07": u"勘定甲07", u"a09": u"勘定乙09", u"a10": u"勘定乙10",
           u"a11": u"勘定乙11", u"a12": u"勘定丙12", u"a13": u"勘定丙13", u"a14": u"勘定丙14", u"b01": u"勘定丁01"}
PL_IDS = (u"a03", u"a04", u"a06", u"a07", u"b01")          # 期間の行(足す額は貸方−借方。b01 は借方−貸方)
BS_IDS = (u"a09", u"a10", u"a11", u"a12", u"a13", u"a14")  # 時点の行(a09・a10・a11 は借方−貸方・a12〜a14 は貸方−借方)
SALES = u"売上高"
DEPT = (u"甲部", u"乙部")


def fy_months(fy):
    y, m = FY_START[fy]
    out = []
    for k in range(12):
        yy, mm = divmod(y * 12 + m - 1 + k, 12)
        out.append((yy, mm + 1))
    return out


def fy_range(fy):
    ms = fy_months(fy)
    y, m = ms[-1]
    nxt = D(y + (m // 12), m % 12 + 1, 1)
    return D(ms[0][0], ms[0][1], 1), nxt - datetime.timedelta(days=1)


def amount(idnum, fy, slot):
    return 1000000 * (idnum % 7 + 1) + 10000 * slot + 100 * fy + idnum


class Syn(object):
    u"""架空の 1 社。仕訳の行の組・各項目の本当の値(``gold[期][id]``)を、仕訳の行から別の経路で数えて持つ。"""

    def __init__(self, with_new_account=False):
        self.rows = {0: [], 1: [], 2: []}          # fy → [(date, 科目, 借方, 貸方, 部門)]
        for fy in (0, 1, 2):
            for k, (y, m) in enumerate(fy_months(fy)):
                base = 1000000 + 10000 * k + 777 * fy
                self.rows[fy].append((D(y, m, 5), SALES, None, base * 6 // 10, DEPT[0]))
                self.rows[fy].append((D(y, m, 20), SALES, None, base - base * 6 // 10, DEPT[1]))
                if fy == 1 and k == 1:
                    self.rows[fy].append((D(y, m, 28), SALES, 5000, None, DEPT[0]))          # 取り消しの行
            lo, hi = fy_range(fy)
            for ident in PL_IDS:
                n = int(ident[1:])
                a1, a2 = amount(n, fy, 1), amount(n, fy, 2)
                if ident == u"b01":
                    self.rows[fy].append((lo + datetime.timedelta(days=9), ACCOUNT[ident], a1, None, DEPT[0]))
                    self.rows[fy].append((hi - datetime.timedelta(days=5), ACCOUNT[ident], a2, 1000, DEPT[1]))
                else:
                    self.rows[fy].append((lo + datetime.timedelta(days=9), ACCOUNT[ident], 500, a1, DEPT[0]))
                    self.rows[fy].append((hi - datetime.timedelta(days=5), ACCOUNT[ident], None, a2, DEPT[1]))
            for ident in BS_IDS:
                n = int(ident[1:])
                a1, a2 = amount(n, fy, 3), amount(n, fy, 4)
                scale = 10 if ident == u"a11" else 1
                if ident in (u"a09", u"a10", u"a11"):
                    self.rows[fy].append((lo + datetime.timedelta(days=12), ACCOUNT[ident], a1 * scale, None, DEPT[0]))
                    self.rows[fy].append((hi - datetime.timedelta(days=3), ACCOUNT[ident], a2 * scale, 700, DEPT[1]))
                else:
                    self.rows[fy].append((lo + datetime.timedelta(days=12), ACCOUNT[ident], 300, a1, DEPT[0]))
                    self.rows[fy].append((hi - datetime.timedelta(days=3), ACCOUNT[ident], None, a2, DEPT[1]))
            self.rows[fy].append((lo + datetime.timedelta(days=20), u"雑費", 12345, None, DEPT[1]))
        if with_new_account:
            y, m = fy_months(2)[3]
            self.rows[2].append((D(y, m, 9), u"新しい科目", 1111, None, DEPT[0]))

    def journal(self, upto_fy):
        out = []
        for fy in range(0, upto_fy + 1):
            out.extend(self.rows[fy])
        return out

    # ---- 本当の値(仕訳の行から数える。検査の script とは別の経路)
    def total(self, acct, lo, hi, sign):
        t = 0
        for fy in (0, 1, 2):
            for d, a, dr, cr, _dept in self.rows[fy]:
                if a == acct and lo <= d <= hi:
                    t += sign * ((dr or 0) - (cr or 0))
        return t

    def value(self, ident, per):
        cur = 1 if per == 1 else 2
        cs, ce = fy_range(cur)
        ps, pe = fy_range(cur - 1)
        far = D(2000, 1, 1)
        if ident == u"a01":
            return self.total(SALES, cs, ce, -1)
        if ident == u"a02":
            return self.total(SALES, ps, pe, -1)
        if ident == u"a05":
            return self.total(ACCOUNT[u"a04"], ps, pe, -1)
        if ident in PL_IDS:
            return self.total(ACCOUNT[ident], cs, ce, 1 if ident == u"b01" else -1)
        if ident in (u"a09", u"a10", u"a11"):
            return self.total(ACCOUNT[ident], far, ce, 1)
        if ident in (u"a12", u"a13", u"a14"):
            return self.total(ACCOUNT[ident], far, ce, -1)
        if re.fullmatch(u"a(1[7-9]|2[0-8])", ident):
            k = int(ident[1:]) - 17
            y, m = fy_months(cur)[k]
            lo = D(y, m, 1)
            hi = D(y + (m // 12), m % 12 + 1, 1) - datetime.timedelta(days=1)
            return self.total(SALES, lo, hi, -1)
        if ident == u"a15":
            return self.total(ACCOUNT[u"a11"], far, ce, 1) - self.total(ACCOUNT[u"a14"], far, ce, -1)
        if ident == u"a16":
            return self.total(ACCOUNT[u"a11"], far, pe, 1) - self.total(ACCOUNT[u"a14"], far, pe, -1)
        if ident == u"a29":
            return self.value(u"a12", per) + self.value(u"a13", per)
        if ident == u"a30":
            return 30 if per == 1 else 28
        return None          # a08 は素材が無い

    def gold_json(self):
        out = od()
        for per in (1, 2):
            body = od()
            for ident, key in TAL.GOLD_KEYS:
                body[key] = self.value(ident, per)
            body[TAL.MONTH_KEY] = [self.value(u"a%d" % (16 + k), per) for k in range(1, 13)]
            out[u"期%d" % per] = body
        return out

    # ---- file
    def write(self, folder, per, enc="utf-8"):
        u"""``folder`` に仕訳.csv・決算書.xlsx・人員.csv・借入.csv を書く。仕訳の日付の書き方は年度ごとに違う(0: YYYY/MM/DD・1: YYYY-MM-DD・2: YYYYMMDD)。"""
        import csv
        import openpyxl
        os.makedirs(folder, exist_ok=True)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator=u"\n")
        w.writerow([u"日付", u"科目", u"借方", u"貸方", u"部門"])
        for fy in range(0, per + 1):
            for d, a, dr, cr, dept in self.rows[fy]:
                ds = (d.strftime(u"%Y/%m/%d"), d.isoformat(), d.strftime(u"%Y%m%d"))[fy]
                f = (lambda v: u"" if v is None else (u"{:,}".format(v) if fy == 1 else str(v)))
                w.writerow([ds, a, f(dr), f(cr), dept])
        text = buf.getvalue()
        raw = (u"﻿" + text).encode("utf-8") if enc == "utf-8-sig" else text.encode(enc)
        wbytes(os.path.join(folder, u"仕訳.csv"), raw)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = u"貸借"
        ws.append([u"科目", u"当期末", u"前期末"])
        ws.append([u"純資産合計", self.value(u"a15", per), self.value(u"a16", per)])
        ws2 = wb.create_sheet(u"損益")
        ws2.append([u"科目", u"当期", u"前期"])
        ws2.append([u"売上高", self.value(u"a01", per), self.value(u"a02", per)])
        wb.save(os.path.join(folder, u"決算書.xlsx"))
        wbytes(os.path.join(folder, u"人員.csv"), (u"項目,人数\n期末従業員数,%d\nうち正社員,%d\n" % (self.value(u"a30", per), self.value(u"a30", per) - 4)).encode("utf-8"))
        total = self.value(u"a29", per)
        x, y = total // 5, total // 3
        rows = [(u"借入先甲", x), (u"借入先乙", y), (u"借入先丙", total - x - y)]
        body = u"借入先,期末残高,利率\n" + u"".join(u"%s,%d,1.5\n" % r for r in rows) + u"合計,%d,\n" % total
        wbytes(os.path.join(folder, u"借入.csv"), body.encode("utf-8"))
        self.borrow_rows = [2, 3, 4]


def spec_dict(product, per):
    cs, ce = fy_range(1 if per == 1 else 2)
    return od([(u"成果物", product), (u"当期の始まり", cs.isoformat()), (u"当期の終わり", ce.isoformat())])


class World(object):
    pass


_WORLDS = {}
_TMPS = []


def world(new_account=False, enc="utf-8"):
    key = (new_account, enc)
    if key in _WORLDS:
        return _WORLDS[key]
    w = World()
    w.syn = Syn(new_account)
    w.tmp = tempfile.mkdtemp(prefix="um2_gate_")
    _TMPS.append(w.tmp)
    w.dirs = {1: os.path.join(w.tmp, u"期1"), 2: os.path.join(w.tmp, u"期2")}
    w.syn.write(w.dirs[1], 1, enc)
    w.syn.write(w.dirs[2], 2, enc)
    w.src = dict((p, CHK.Source(w.dirs[p])) for p in (1, 2))
    w.defA, w.defB = [CHK.load_def(os.path.join(ROOT, r))[0] for r in DEF_RELS]
    w.spec = {}
    for per in (1, 2):
        for prod in (u"A", u"B"):
            path = os.path.join(w.tmp, u"指定_期%d_%s.json" % (per, prod))
            wjson(path, spec_dict(prod, per))
            w.spec[(per, prod)] = CHK.load_spec(path)[0]
            w.spec_path = getattr(w, "spec_path", {})
            w.spec_path[(per, prod)] = path
    _WORLDS[key] = w
    return w


def tearDownModule():
    for t in _TMPS:
        shutil.rmtree(t, ignore_errors=True)


def period_of(w, per, ident):
    d = w.defA.by_id.get(ident) or w.defB.by_id.get(ident)
    return CHK.period_json(CHK.expected_period(d, w.spec[(per, u"A")]))


def rows_source(file_, amt, conds, mult=1):
    return od([(u"種類", u"表の行の和"), (u"file", file_), (u"頭の行", 1), (u"額", amt), (u"条件", conds), (u"表示の倍率", mult)])


CR_MINUS_DR = od([(u"借方の列", u"借方"), (u"貸方の列", u"貸方"), (u"向き", u"貸方−借方")])
DR_MINUS_CR = od([(u"借方の列", u"借方"), (u"貸方の列", u"貸方"), (u"向き", u"借方−貸方")])


def cond(col, how, val):
    return od([(u"列", col), (u"比べ方", how), (u"値", val)])


def rows_material(w, per, ident, value, acct, amt, point=False, extra=()):
    u"""``表の行の和`` の材料 1 つ(期間の行は以上・以下・時点の行は以下)。"""
    p = period_of(w, per, ident)
    conds = [cond(u"科目", u"等しい", acct)]
    if point:
        conds.append(cond(u"日付", u"以下", p[u"時点"]))
    else:
        conds.append(cond(u"日付", u"以上", p[u"始まり"]))
        conds.append(cond(u"日付", u"以下", p[u"終わり"]))
    conds.extend(extra)
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", str(value)), (u"単位", u"円"), (u"期間", p), (u"範囲", u"全社"), (u"出どころ", rows_source(u"仕訳.csv", amt, conds))])


def cell_material(w, per, ident, value, file_, pos, rowh, colh, mult=1, unit=u"円"):
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", str(value)), (u"単位", unit), (u"期間", period_of(w, per, ident)), (u"範囲", u"全社"),
               (u"出どころ", od([(u"種類", u"素材"), (u"file", file_), (u"位置", pos), (u"行の見出し", rowh), (u"列の見出し", colh), (u"表示の倍率", mult)]))])


def none_material(ident):
    return od([(u"id", ident), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])


def perfect_bundle(w, per, product=u"A"):
    u"""架空の 1 社の、全部正解どおりの材料の束(型 u2)。a08 は素材が無い。"""
    s = w.syn
    items = []
    for k in range(1, 13):
        ident = u"a%d" % (16 + k)
        items.append(rows_material(w, per, ident, s.value(ident, per), SALES, CR_MINUS_DR))
    items.append(rows_material(w, per, u"a01", s.value(u"a01", per), SALES, CR_MINUS_DR))
    items.append(cell_material(w, per, u"a02", s.value(u"a02", per), u"決算書.xlsx", od([(u"sheet", u"損益"), (u"セル", u"C2")]), u"売上高", u"前期"))
    for ident in (u"a03", u"a04", u"a06", u"a07"):
        items.append(rows_material(w, per, ident, s.value(ident, per), ACCOUNT[ident], CR_MINUS_DR))
    items.append(rows_material(w, per, u"a05", s.value(u"a05", per), ACCOUNT[u"a04"], CR_MINUS_DR))          # 前期の営業利益(期間は前期)
    items.append(none_material(u"a08"))
    for ident in (u"a09", u"a10", u"a11"):
        items.append(rows_material(w, per, ident, s.value(ident, per), ACCOUNT[ident], DR_MINUS_CR, point=True))
    for ident in (u"a12", u"a13", u"a14"):
        items.append(rows_material(w, per, ident, s.value(ident, per), ACCOUNT[ident], CR_MINUS_DR, point=True))
    items.append(cell_material(w, per, u"a15", s.value(u"a15", per), u"決算書.xlsx", od([(u"sheet", u"貸借"), (u"セル", u"B2")]), u"純資産合計", u"当期末"))
    items.append(cell_material(w, per, u"a16", s.value(u"a16", per), u"決算書.xlsx", od([(u"sheet", u"貸借"), (u"セル", u"C2")]), u"純資産合計", u"前期末"))
    items.append(od([(u"id", u"a29"), (u"状態", u"在る"), (u"数値", str(s.value(u"a29", per))), (u"単位", u"円"), (u"期間", period_of(w, per, u"a29")), (u"範囲", u"全社"),
                     (u"出どころ", od([(u"種類", u"素材の和"), (u"file", u"借入.csv"), (u"列", 2), (u"行の並び", [2, 3, 4]), (u"列の見出し", u"期末残高"), (u"表示の倍率", 1)]))]))
    items.append(cell_material(w, per, u"a30", s.value(u"a30", per), u"人員.csv", od([(u"行", 2), (u"列", 2)]), u"期末従業員数", u"人数", unit=u"人"))
    items.sort(key=lambda m: m[u"id"])
    a = od([(u"型の版", u"u2"), (u"材料", items)])
    if product == u"B":
        m = rows_material(w, per, u"b01", s.value(u"b01", per), ACCOUNT[u"b01"], DR_MINUS_CR)
        return od([(u"型の版", u"u2"), (u"材料", [m])])
    return a


def check_a(w, per, bundle, **kw):
    return CHK.check_bundle(w.spec[(per, u"A")], w.defA, bundle, w.src[per], **kw)


def verdicts(res):
    return dict((r[u"id"], (r[u"判定"], tuple(r[u"規則"]))) for r in res[u"材料"])


def edit_item(bundle, ident, fn):
    b = copy.deepcopy(bundle)
    for m in b[u"材料"]:
        if m[u"id"] == ident:
            fn(m)
    return b


@contextlib.contextmanager
def removed(rule):
    u"""検査の規則 1 つを、何もしない関数に差し替える(戻しは finally)。"""
    noop = {u"K0": lambda ctx, b, w_: [], u"K7": lambda ctx, res, items: (set(), 0, 0), u"K9": lambda ctx, d: False, u"K11": lambda ctx, res, items: set()}
    saved = CHK.RULE_FUNCS[rule]
    try:
        CHK.RULE_FUNCS[rule] = noop.get(rule, lambda ctx, m, d, info: False)
        yield
    finally:
        CHK.RULE_FUNCS[rule] = saved


@contextlib.contextmanager
def doc_removed(rule):
    saved = CHK.DOC_RULES[rule]
    try:
        CHK.DOC_RULES[rule] = lambda c: []
        yield
    finally:
        CHK.DOC_RULES[rule] = saved


# ======================================================================== 1. 封の字(手で書いた写し。script の表から作っていない)
SEAL_RULE_LINES = (u"K0 形(§1-4)・K5 単位・K8 範囲", u"K1 値: 条件が選ぶ行が 1 行以上在り", u"K4 期: 期間の行は", u"K3(意味)は 1 期目には掛からない", u"K9 無い", u"K11 新しい値")
SEAL_MUT_PHRASES = (u"M1・M2・M4・M8", u"V1 数値に 1 を足す", u"V2 `どれか` の並び", u"V3 条件を 1 つ外し数値を合わせる", u"V4 日付の条件を前の期へ移し数値を合わせる(`期間` はそのまま)",
                    u"V5 日付の条件と `期間` の両方を前の期へ移し数値を合わせる", u"V6 向き(か符号)を逆にし数値を合わせる", u"D1・D4")
SEAL_PREDICTION_IDS = (u"UM2-S1", u"UM2-S2", u"UM2-P1", u"UM2-P2", u"UM2-P3", u"UM2-P4", u"UM2-P5", u"UM2-Q1", u"UM2-Q2", u"UM2-Q3", u"UM2-D1", u"UM2-D2", u"UM2-E1", u"UM2-V1", u"UM2-V2")
#: 封 §3 の表の予測の行の字(外れ方と一緒に)。境の数を含む行そのもの。
SEAL_PREDICTION_ROWS = (
    u"| UM2-S1 | 正解の file の関係は 24 本のうち 22 以上で成り立つ | 21 以下 |",
    u"| UM2-S2 | 正解が `null` の行は、124 のうち 4 以上 30 以下(1 期目) | 3 以下か 31 以上 |",
    u"| UM2-P1 | 1 期目、席の答えが正解と同じ行は 124 のうち 93 以上(75%) | 92 以下 |",
    u"| UM2-P2 | 1 期目、席が出どころの種類 `表の行の和` で書く行は、`在る` と書いた行の 30% 以上 | 30% 未満 |",
    u"| UM2-P3 | 1 期目、検査が通した行(未確認を含む)のうち、正解と `数値` が違う行は 1 以上 | 0 |",
    u"| UM2-P4 | 1 期目、便 UM0 の見出しの表に合わず K3 で止まる行は 124 のうち 10 以上 | 9 以下 |",
    u"| UM2-P5 | 束が K0 で断られるのは 8 束のうち 0 | 1 以上 |",
    u"| UM2-Q1 | 2 期目、持ち越せた行は、確かめた取り方の行の 80% 以上 | 80% 未満 |",
    u"| UM2-Q2 | 2 期目、持ち越して検査を通った行のうち、正解と `数値` が違う行は 0 | 1 以上 |",
    u"| UM2-Q3 | K11 が 1 行以上止める社は 4 社のうち 1 以上 | 0 |",
    u"| UM2-D1 | 資料の検査を通るのは 16 本のうち 13 以上 | 12 以下 |",
    u"| UM2-D2 | 2 期目の A の資料で、数が出ている行(`確認待ち`・`無い` でない行)は、4 社の合計で 33 行 × 4 のうち 60% 以上 | 60% 未満 |",
    u"| UM2-E1 | 通しで、1 期目・2 期目とも A・B の人が読む版が組めた社は 4 のうち 3 以上 | 2 以下 |",
)
#: 表の境の数を手で書き写した表(script の ``BOUNDS`` と同じでなければならない)
EXPECT_BOUNDS = od([
    (u"UM2-S1", {u"関係が成り立つ本数": (22, None), u"関係の本数": (24, 24)}),
    (u"UM2-S2", {u"正解が null の行:期1": (4, 30)}),
    (u"UM2-P1", {u"段 1:席の答えが正解と同じ": (93, None), u"段 1:行の数": (124, 124)}),
    (u"UM2-P2", {u"割合の下限(百分率)": (30, None)}),
    (u"UM2-P3", {u"段 1:通したが数値が違う": (1, None)}),
    (u"UM2-P4", {u"段 1:K3 で止まった行": (10, None)}),
    (u"UM2-P5", {u"束が K0 で断られた束": (0, 0)}),
    (u"UM2-Q1", {u"割合の下限(百分率)": (80, None)}),
    (u"UM2-Q2", {u"段 2:持ち越して通したが数値が違う": (0, 0)}),
    (u"UM2-Q3", {u"段 2:K11 で止めた社": (1, None)}),
    (u"UM2-D1", {u"資料の検査を通した本数": (13, 16)}),
    (u"UM2-D2", {u"割合の下限(百分率)": (60, None), u"段 3:A の 2 期目の資料で数が出ている行": (None, 132)}),
    (u"UM2-E1", {u"通し:期1・期2とも": (3, 4)}),
    (u"UM2-V1", {u"通した = 作れた(関係に入らない行)": (None, None)}),
    (u"UM2-V2", {u"V1・V4 で作れたもののうち通した": (0, 0)}),
])


def seal_text():
    return read(SEAL_REL)


class SealTextTest(unittest.TestCase):
    def test_a_1_the_seal_file_is_the_sealed_bytes(self):
        self.assertEqual(SEAL_SHA256, hashlib.sha256(read_bytes(SEAL_REL)).hexdigest())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        hs = [x for x in git("log", "--format=%H", "--", PREFIX + SEAL_REL).split() if x]
        self.assertEqual(1, len(hs), hs)
        self.assertTrue(hs[0].startswith(SEAL_COMMIT_SHORT), hs)
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout
        self.assertEqual(blob, read_bytes(SEAL_REL))

    def test_a_3_engine_is_zero_lines_from_the_seal_commit(self):
        out = git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core")
        self.assertEqual("", out.strip())

    def test_a_4_the_boundary_import_list_is_not_widened(self):
        body = read("tests/adapters/xbrl/test_boundary.py")
        for word in (u"universal", u"um0", u"um2"):
            self.assertNotIn(word, body)

    def test_a_5_the_seal_holds_the_rules_mutations_and_predictions_the_gate_copies(self):
        seal = seal_text()
        for s in SEAL_RULE_LINES + SEAL_MUT_PHRASES + SEAL_PREDICTION_IDS + SEAL_PREDICTION_ROWS:
            self.assertIn(s, seal, s)
        self.assertIn(u"| UM2-V1 | `表の行の和` の変異 V2・V3・V6 のうち、関係に入らない行(a02・a05・a08・a09・a10・a16・a30・b01 など、R1〜R3 のどれにも出ない id)で作れたものは、検査が全部通す | 1 つでも止める |", seal)
        self.assertIn(u"| UM2-V2 | 変異 V1 と V4 は、作れたもののうち検査が通すもの 0 | 1 以上 |", seal)

    def test_a_6_the_script_tables_equal_the_hand_copy(self):
        self.assertEqual(tuple(u"K%d" % k for k in range(10)) + (u"K11",), CHK.RULES)
        self.assertEqual(u"u2", CHK.TYPE_VERSION)
        self.assertEqual(u"表の行の和", CHK.KIND_ROWS)
        self.assertEqual((u"等しい", u"どれか", u"どれでもない", u"頭が同じ", u"以上", u"以下"), CHK.COMPARES)
        self.assertEqual((u"借方−貸方", u"貸方−借方"), CHK.DIRECTIONS)
        self.assertEqual((1, 1000, 1000000), CHK.MULTS)
        self.assertEqual((u"M1", u"M2", u"M4", u"M8"), TAL.MUT_PLAIN)
        self.assertEqual((u"V1", u"V2", u"V3", u"V4", u"V5", u"V6"), TAL.MUT_ROWS)
        self.assertEqual((u"D1", u"D4"), TAL.DOC_CODES)
        self.assertEqual((1, 2, 3, 4), TAL.PROD)
        self.assertEqual((101,), TAL.DEV)

    def test_a_7_the_bounds_of_the_prediction_table_equal_the_hand_copy(self):
        self.assertEqual(list(EXPECT_BOUNDS), list(TAL.BOUNDS))
        for k, v in EXPECT_BOUNDS.items():
            self.assertEqual(dict(v), dict(TAL.BOUNDS[k]), k)
        self.assertEqual(set(SEAL_PREDICTION_IDS), set(TAL.BOUNDS))

    def test_a_8_the_judge_flips_exactly_at_each_boundary(self):
        def rec(**c):
            return {u"数": c, u"変異": {}}
        full = {u"関係の本数": 24, u"関係が成り立つ本数": 24, u"正解が null の行:期1": 10, u"段 1:席の答えが正解と同じ": 100, u"段 1:行の数": 124,
                u"段 1:出どころの種類:表の行の和": 30, u"段 1:席が在ると書いた行": 100, u"段 1:通したが数値が違う": 1, u"段 1:K3 で止まった行": 10, u"束が K0 で断られた束": 0,
                u"段 2:確かめた取り方の行": 100, u"段 2:持ち越した行": 80, u"段 2:持ち越して通したが数値が違う": 0, u"段 2:K11 で止めた社": 1,
                u"段 3:資料の検査を通した:期1・A": 13, u"段 3:A の 2 期目の資料で数が出ている行": 80, u"通し:期1・期2とも": 3}
        base = TAL.judge(rec(**full))
        for k in (u"UM2-S1", u"UM2-S2", u"UM2-P1", u"UM2-P2", u"UM2-P3", u"UM2-P4", u"UM2-P5", u"UM2-Q1", u"UM2-Q2", u"UM2-Q3", u"UM2-D1", u"UM2-D2", u"UM2-E1"):
            self.assertTrue(base[k][u"当たり"], k)

        def flip(**chg):
            c = dict(full)
            c.update(chg)
            return TAL.judge(rec(**c))
        self.assertFalse(flip(**{u"関係が成り立つ本数": 21})[u"UM2-S1"][u"当たり"])
        self.assertTrue(flip(**{u"正解が null の行:期1": 4})[u"UM2-S2"][u"当たり"])
        self.assertFalse(flip(**{u"正解が null の行:期1": 3})[u"UM2-S2"][u"当たり"])
        self.assertTrue(flip(**{u"正解が null の行:期1": 30})[u"UM2-S2"][u"当たり"])
        self.assertFalse(flip(**{u"正解が null の行:期1": 31})[u"UM2-S2"][u"当たり"])
        self.assertFalse(flip(**{u"段 1:席の答えが正解と同じ": 92})[u"UM2-P1"][u"当たり"])
        self.assertTrue(flip(**{u"段 1:出どころの種類:表の行の和": 30, u"段 1:席が在ると書いた行": 100})[u"UM2-P2"][u"当たり"])
        self.assertFalse(flip(**{u"段 1:出どころの種類:表の行の和": 29, u"段 1:席が在ると書いた行": 100})[u"UM2-P2"][u"当たり"])
        self.assertFalse(flip(**{u"段 1:通したが数値が違う": 0})[u"UM2-P3"][u"当たり"])
        self.assertFalse(flip(**{u"段 1:K3 で止まった行": 9})[u"UM2-P4"][u"当たり"])
        self.assertFalse(flip(**{u"束が K0 で断られた束": 1})[u"UM2-P5"][u"当たり"])
        self.assertFalse(flip(**{u"段 2:持ち越した行": 79})[u"UM2-Q1"][u"当たり"])
        self.assertFalse(flip(**{u"段 2:持ち越して通したが数値が違う": 1})[u"UM2-Q2"][u"当たり"])
        self.assertFalse(flip(**{u"段 2:K11 で止めた社": 0})[u"UM2-Q3"][u"当たり"])
        self.assertFalse(flip(**{u"段 3:資料の検査を通した:期1・A": 12})[u"UM2-D1"][u"当たり"])
        self.assertFalse(flip(**{u"段 3:A の 2 期目の資料で数が出ている行": 79})[u"UM2-D2"][u"当たり"])
        self.assertTrue(flip(**{u"段 3:A の 2 期目の資料で数が出ている行": 80})[u"UM2-D2"][u"当たり"])
        self.assertFalse(flip(**{u"通し:期1・期2とも": 2})[u"UM2-E1"][u"当たり"])
        mut = {u"V2": {u"作れた:関係に入らない": 2, u"通した:関係に入らない": 2}, u"V3": {u"作れた:関係に入らない": 3, u"通した:関係に入らない": 3}, u"V6": {u"作れた:関係に入らない": 1, u"通した:関係に入らない": 1},
               u"V1": {u"作れた": 4, u"通した": 0}, u"V4": {u"作れた": 2, u"通した": 0}}
        got = TAL.judge({u"数": full, u"変異": mut})
        self.assertTrue(got[u"UM2-V1"][u"当たり"])
        self.assertTrue(got[u"UM2-V2"][u"当たり"])
        mut2 = copy.deepcopy(mut)
        mut2[u"V3"][u"通した:関係に入らない"] = 2
        self.assertFalse(TAL.judge({u"数": full, u"変異": mut2})[u"UM2-V1"][u"当たり"])
        mut3 = copy.deepcopy(mut)
        mut3[u"V4"][u"通した"] = 1
        self.assertFalse(TAL.judge({u"数": full, u"変異": mut3})[u"UM2-V2"][u"当たり"])
        self.assertIsNone(TAL.judge({u"数": full, u"変異": {}})[u"UM2-V1"][u"当たり"])
        self.assertIsNone(TAL.judge({u"数": dict(full, **{u"段 1:席が在ると書いた行": 0}), u"変異": {}})[u"UM2-P2"][u"当たり"])


# ======================================================================== 2. 定義表(便 UM0 のまま・1 byte も変えない)
class DefinitionTest(unittest.TestCase):
    def test_b_1_the_definition_files_are_the_um0_bytes(self):
        for rel, sha in zip(DEF_RELS, DEF_SHA256):
            self.assertEqual(sha, hashlib.sha256(read_bytes(rel)).hexdigest(), rel)
            blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (DEF_COMMIT_SHORT, PREFIX + rel)], stdout=subprocess.PIPE).stdout
            self.assertEqual(blob, read_bytes(rel), rel)
            hs = [x for x in git("log", "--format=%h", "--", PREFIX + rel).split() if x]
            self.assertEqual([DEF_COMMIT_SHORT], [h[:8] for h in hs], hs)

    def test_b_2_shape_of_the_definition(self):
        a, b = [json.loads(read(r)) for r in DEF_RELS]
        self.assertEqual(33, len(a[u"行"]))
        self.assertEqual(30, len([r for r in a[u"行"] if r[u"取り方"] in (u"素材", u"素材の和")]))
        self.assertEqual(17, len([r for r in b[u"行"] if r[u"取り方"] != u"計算"]))
        self.assertEqual([u"R1", u"R2", u"R3"], [r[u"id"] for r in a[u"関係"]])
        self.assertEqual([u"R1"], [r[u"id"] for r in b[u"関係"]])
        self.assertEqual(124, 4 * 30 + 4)

    def test_b_3_the_gold_key_names_map_onto_the_definition_rows(self):
        a = json.loads(read(DEF_RELS[0]))
        b = json.loads(read(DEF_RELS[1]))
        names = dict((r[u"id"], r[u"名"]) for r in a[u"行"] + b[u"行"])
        hand = od([(u"a01", u"売上高_当期"), (u"a02", u"売上高_前期"), (u"a03", u"売上総利益_当期"), (u"a04", u"営業利益_当期"), (u"a05", u"営業利益_前期"), (u"a06", u"経常利益_当期"),
                   (u"a07", u"当期純利益_当期"), (u"a08", u"減価償却費_当期"), (u"a09", u"現金及び預金_当期末"), (u"a10", u"流動資産合計_当期末"), (u"a11", u"資産合計_当期末"),
                   (u"a12", u"短期借入金_当期末"), (u"a13", u"長期借入金_当期末"), (u"a14", u"負債合計_当期末"), (u"a15", u"純資産合計_当期末"), (u"a16", u"純資産合計_前期末"),
                   (u"a29", u"借入の残高の合計_当期末"), (u"a30", u"期末の従業員数_当期末"), (u"b01", u"人件費_当期")])
        self.assertEqual(list(hand.items()), list(TAL.GOLD_KEYS))
        for ident, key in hand.items():
            self.assertIn(u"(%s)" % key.split(u"_")[1], names[ident], (ident, key, names[ident]))
        self.assertEqual(u"月次の売上高_当期", TAL.MONTH_KEY)
        self.assertEqual([u"a%d" % (16 + k) for k in range(1, 13)], TAL.MONTH_IDS)
        for k, ident in enumerate(TAL.MONTH_IDS, 1):
            self.assertIn(u"当期の%s" % (u"一二三四五六七八九十")[k - 1] if k < 10 else u"当期の十", names[ident])
        self.assertEqual(set(TAL.A_IDS), set(CHK.material_ids(CHK.load_def(os.path.join(ROOT, DEF_RELS[0]))[0])))
        ids = [i for i, _k in TAL.GOLD_KEYS] + TAL.MONTH_IDS
        self.assertEqual(sorted(ids), sorted(TAL.ROW_IDS))
        self.assertEqual(31, len(TAL.ROW_IDS))


# ======================================================================== 3. 検査の独立
class IndependenceTest(unittest.TestCase):
    STD = set(["calendar", "csv", "datetime", "decimal", "functools", "html", "io", "json", "os", "re", "sys", "unicodedata", "zipfile", "__future__", "fractions", "xml"])

    def imports(self, rel):
        tree = ast.parse(read(rel))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        return tree, mods

    def test_c_1_the_check_imports_only_the_standard_library_and_not_the_answer_side_or_um0(self):
        tree, mods = self.imports(CHECK_REL)
        self.assertEqual(set(), mods - self.STD, mods - self.STD)
        body = read(CHECK_REL)
        code_only = re.sub(r'(?s)u?"""(.*?)"""', "", body, count=1)           # 先頭の説明文を除く
        for word in (u"universal_through_tally", u"universal_check_2026", u"universal_source_gen", u"正解"):
            self.assertNotIn(word, code_only, word)
        names = set(n.id for n in ast.walk(tree) if isinstance(n, ast.Name)) | set(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
        for bad in (u"importlib", u"subprocess", u"openpyxl", u"socket", u"urllib"):
            self.assertNotIn(bad, names)

    def test_c_1b_the_tally_uses_only_the_standard_library(self):
        _tree, mods = self.imports(TALLY_REL)
        self.assertEqual(set(), mods - self.STD - set(["collections", "importlib"]), mods)

    def test_c_2_the_check_does_not_define_the_gold_key_names(self):
        body = read(CHECK_REL)
        code_only = re.sub(r'(?s)u?"""(.*?)"""', "", body, count=1)
        for _i, key in TAL.GOLD_KEYS:
            self.assertNotIn(key, code_only)
        self.assertNotIn(TAL.MONTH_KEY, code_only)

    def test_c_3_the_check_runs_under_dash_I_and_returns_json_with_rc_0_for_any_command(self):
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        cases = [[], ["nonsense"], ["material"], ["material", "--spec"], ["material", "--spec", "/no", "--def", "/no", "--bundle", "/no", "--src", "/no"],
                 ["plan", "--def", "/no", "--store", "/no"], ["document", "--def", "/no"], ["render"], ["store"], ["carry"], ["human"], ["human-check"],
                 ["human-check", "--doc", "/no", "--html", "/no"], ["carry", "--def", "/no", "--spec", "/no", "--prev-spec", "/no", "--prev-bundle", "/no", "--prev-result", "/no", "--marks", "/no", "--src", "/no"],
                 ["--out"], ["material", "--out", "/no/such/dir/x.json"]]
        for argv in cases:
            rc = subprocess.run([sys.executable, "-I", script] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            self.assertEqual(0, rc.returncode, (argv, rc.stderr[-300:]))
            self.assertEqual(b"", rc.stderr, argv)
            if rc.stdout:
                json.loads(rc.stdout.decode("utf-8"))
            self.assertNotIn(u"内部の例外".encode("utf-8"), rc.stdout, argv)

    def test_c_4_the_check_runs_in_isolated_processes_end_to_end_and_matches_in_process(self):
        w = world()
        d = os.path.join(w.tmp, "cli")
        defp = os.path.join(d, "def.json")
        wbytes(defp, read_bytes(DEF_RELS[0]))
        wbytes(os.path.join(d, "defB.json"), read_bytes(DEF_RELS[1]))
        b1 = perfect_bundle(w, 1)
        wjson(os.path.join(d, "b1.json"), b1)
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}

        def run(*argv):
            rc = subprocess.run([sys.executable, "-I", script] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            self.assertEqual(0, rc.returncode, rc.stderr[-300:])
            return rc.stdout
        out = json.loads(run("material", "--spec", w.spec_path[(1, u"A")], "--def", defp, "--bundle", os.path.join(d, "b1.json"), "--src", w.dirs[1]).decode("utf-8"))
        self.assertEqual(json.loads(json.dumps(check_a(w, 1, b1), ensure_ascii=False)), out)
        run("material", "--spec", w.spec_path[(1, u"A")], "--def", defp, "--bundle", os.path.join(d, "b1.json"), "--src", w.dirs[1], "--out", os.path.join(d, "r1.json"))
        run("store", "--def", defp, "--result", os.path.join(d, "r1.json"), "--bundle", os.path.join(d, "b1.json"), "--product", "A", "--out", os.path.join(d, "s1.json"))
        store = json.load(io.open(os.path.join(d, "s1.json"), encoding="utf-8"))
        self.assertEqual(u"在る", store[u"行"][u"a01"][u"状態"])
        self.assertTrue(store[u"行"][u"a01"][u"未確認"])
        run("render", "--def", defp, "--store", os.path.join(d, "s1.json"), "--out", os.path.join(d, "doc.md"))
        got = json.loads(run("document", "--def", defp, "--store", os.path.join(d, "s1.json"), "--doc", os.path.join(d, "doc.md")).decode("utf-8"))
        self.assertTrue(got[u"通った"], got)
        run("human", "--def", defp, "--store", os.path.join(d, "s1.json"), "--doc", os.path.join(d, "doc.md"), "--out", os.path.join(d, "page.html"))
        chk = json.loads(run("human-check", "--doc", os.path.join(d, "doc.md"), "--html", os.path.join(d, "page.html")).decode("utf-8"))
        self.assertTrue(chk[u"通った"], chk)
        marks = [m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る"]
        wjson(os.path.join(d, "marks.json"), {u"確かめた取り方": marks})
        run("material", "--spec", w.spec_path[(1, u"A")], "--def", defp, "--bundle", os.path.join(d, "b1.json"), "--src", w.dirs[1], "--confirmed", os.path.join(d, "marks.json"), "--out", os.path.join(d, "r1c.json"))
        r1c = json.load(io.open(os.path.join(d, "r1c.json"), encoding="utf-8"))
        self.assertEqual(set(), set(r[u"判定"] for r in r1c[u"材料"]) - set([u"通す", u"無いを受ける"]))
        run("carry", "--def", defp, "--spec", w.spec_path[(2, u"A")], "--prev-spec", w.spec_path[(1, u"A")], "--prev-bundle", os.path.join(d, "b1.json"), "--prev-result", os.path.join(d, "r1c.json"),
            "--marks", os.path.join(d, "marks.json"), "--src", w.dirs[2], "--out-bundle", os.path.join(d, "b2.json"), "--out", os.path.join(d, "c2.json"))
        c2 = json.load(io.open(os.path.join(d, "c2.json"), encoding="utf-8"))
        self.assertEqual(29, len(c2[u"持ち越した"]))
        ids2 = ",".join(c2[u"持ち越した"] + c2[u"無い"])
        run("material", "--spec", w.spec_path[(2, u"A")], "--def", defp, "--bundle", os.path.join(d, "b2.json"), "--src", w.dirs[2], "--ids", ids2, "--confirmed", os.path.join(d, "marks.json"),
            "--prev-src", w.dirs[1], "--out", os.path.join(d, "r2.json"))
        r2 = json.load(io.open(os.path.join(d, "r2.json"), encoding="utf-8"))
        self.assertEqual(set([u"通す", u"無いを受ける"]), set(r[u"判定"] for r in r2[u"材料"]))

    def test_c_5_the_check_does_not_open_the_gold_files_nor_anything_outside_its_inputs(self):
        u"""開いた path を realpath にして、渡した folder・指定・定義・束・出力の外を開かないことを縛る(in-process で関数を呼ぶ側)。"""
        w = world()
        opened = []
        real_open, real_io_open = builtins.open, io.open

        def spy(real):
            def f(path, *a, **k):
                opened.append(os.path.realpath(os.fsdecode(path)) if isinstance(path, (str, bytes, os.PathLike)) else None)
                return real(path, *a, **k)
            return f
        # 正解の folder と素材の folder が同じ親に在る形(会社の folder)で走らせる
        co = os.path.realpath(os.path.join(w.tmp, u"会社"))
        shutil.copytree(w.dirs[1], os.path.join(co, u"期1"))
        shutil.copytree(w.dirs[2], os.path.join(co, u"期2"))
        wjson(os.path.join(co, u"正解", u"正解.json"), w.syn.gold_json())
        src1, src2 = CHK.Source(os.path.join(co, u"期1")), CHK.Source(os.path.join(co, u"期2"))
        b1 = perfect_bundle(w, 1)
        builtins.open, io.open = spy(real_open), spy(real_io_open)
        try:
            r1 = CHK.check_bundle(w.spec[(1, u"A")], w.defA, b1, src1)
            marks = set(m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る")
            c = CHK.carry(w.defA, w.spec[(2, u"A")], b1, r1, marks, src2, ids=CHK.material_ids(w.defA))
            CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], src2, ids=[x[u"id"] for x in c[u"束"][u"材料"]], confirmed=marks, prev_src=src1)
        finally:
            builtins.open, io.open = real_open, real_io_open
        self.assertGreater(len(opened), 3)
        for p in opened:
            self.assertIsNotNone(p)
            self.assertTrue(p.startswith(os.path.join(co, u"期1") + os.sep) or p.startswith(os.path.join(co, u"期2") + os.sep), p)
            self.assertNotIn(u"正解", p)

    #: 別 process の先頭で ``sys.addaudithook`` を掛け、開いた path(realpath)を log に書いてから検査の CLI を走らせる。標準の library・script 自身は数えない。
    HOOK = u"""
import json, os, runpy, sys, sysconfig
script, logpath = sys.argv[1], sys.argv[2]
log = open(logpath, "ab", buffering=0)
ignore = [os.path.realpath(p) for p in set([sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix] + list(sysconfig.get_paths().values()))] + ["/dev"]
me = os.path.realpath(script)
def hook(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = os.fsdecode(p)
    if not isinstance(p, str):
        return
    rp = os.path.realpath(p)
    if rp == me or any(rp == d or rp.startswith(d + os.sep) for d in ignore):
        return
    log.write((json.dumps(rp, ensure_ascii=False) + "\\n").encode("utf-8"))
sys.addaudithook(hook)
sys.argv = [script] + sys.argv[3:]
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as e:
    sys.exit(e.code)
"""

    def hooked_cli(self, root, work, argv):
        u"""検査の CLI を hook つきの別 process で走らせる。戻りは (stdout の字, 開いた realpath の並び)。"""
        hook = os.path.join(root, u"hook", u"hook.py")
        wbytes(hook, self.HOOK.encode("utf-8"))
        log = os.path.join(root, u"hook", u"opened.log")
        before = len(read_bytes_abs(log).splitlines()) if os.path.exists(log) else 0
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        rc = subprocess.run([sys.executable, "-I", hook, os.path.join(ROOT, CHECK_REL), log] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=os.path.join(root, u"cwd"))
        self.assertEqual(0, rc.returncode, rc.stderr[-300:])
        lines = read_bytes_abs(log).decode("utf-8").splitlines() if os.path.exists(log) else []
        return rc.stdout.decode("utf-8"), [json.loads(x) for x in lines[before:]]

    def hooked_flow(self, bait=None):
        u"""材料の検査・置き場・資料・人が読む版・持ち越し・2 期目の検査を、hook つきの別 process で通しで走らせ、開いた realpath を全部返す。"""
        w = world()
        root = os.path.realpath(tempfile.mkdtemp(prefix="um2_hook_"))
        _TMPS.append(root)
        os.makedirs(os.path.join(root, u"cwd"))
        co = os.path.join(root, u"会社")
        shutil.copytree(w.dirs[1], os.path.join(co, u"期1"))
        shutil.copytree(w.dirs[2], os.path.join(co, u"期2"))
        wjson(os.path.join(co, u"正解", u"正解.json"), w.syn.gold_json())
        wbytes(os.path.join(co, u"x.csv"), u"a,b\n1,2\n".encode("utf-8"))              # 期1/../x.csv の置き場
        wbytes(os.path.join(co, u"正解", u"正解.csv"), u"a,b\n1,2\n".encode("utf-8"))
        work = os.path.join(root, u"work")
        wbytes(os.path.join(work, u"def.json"), read_bytes(DEF_RELS[0]))
        b1 = perfect_bundle(w, 1)
        if bait is not None:
            b1 = edit_item(b1, u"a30", lambda x: x[u"出どころ"].__setitem__(u"file", bait))
        wjson(os.path.join(work, u"b1.json"), b1)
        for per in (1, 2):
            wjson(os.path.join(work, u"s%d.json" % per), spec_dict(u"A", per))
        marks = [m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る"]
        wjson(os.path.join(work, u"marks.json"), {u"確かめた取り方": marks})
        d = lambda n: os.path.join(work, n)
        steps = [
            [u"material", u"--spec", d(u"s1.json"), u"--def", d(u"def.json"), u"--bundle", d(u"b1.json"), u"--src", os.path.join(co, u"期1"), u"--out", d(u"r1.json")],
            [u"store", u"--def", d(u"def.json"), u"--result", d(u"r1.json"), u"--bundle", d(u"b1.json"), u"--product", u"A", u"--out", d(u"st1.json")],
            [u"plan", u"--def", d(u"def.json"), u"--store", d(u"st1.json"), u"--out", d(u"plan.json")],
            [u"render", u"--def", d(u"def.json"), u"--store", d(u"st1.json"), u"--out", d(u"doc.md")],
            [u"document", u"--def", d(u"def.json"), u"--store", d(u"st1.json"), u"--doc", d(u"doc.md"), u"--out", d(u"dc.json")],
            [u"human", u"--def", d(u"def.json"), u"--store", d(u"st1.json"), u"--doc", d(u"doc.md"), u"--out", d(u"page.html")],
            [u"human-check", u"--doc", d(u"doc.md"), u"--html", d(u"page.html"), u"--out", d(u"hc.json")],
            [u"material", u"--spec", d(u"s1.json"), u"--def", d(u"def.json"), u"--bundle", d(u"b1.json"), u"--src", os.path.join(co, u"期1"), u"--confirmed", d(u"marks.json"), u"--out", d(u"r1c.json")],
            [u"carry", u"--def", d(u"def.json"), u"--spec", d(u"s2.json"), u"--prev-spec", d(u"s1.json"), u"--prev-bundle", d(u"b1.json"), u"--prev-result", d(u"r1c.json"),
             u"--marks", d(u"marks.json"), u"--src", os.path.join(co, u"期2"), u"--out-bundle", d(u"b2.json"), u"--out", d(u"c2.json")],
            [u"material", u"--spec", d(u"s2.json"), u"--def", d(u"def.json"), u"--bundle", d(u"b2.json"), u"--src", os.path.join(co, u"期2"), u"--confirmed", d(u"marks.json"),
             u"--prev-src", os.path.join(co, u"期1"), u"--out", d(u"r2.json")],
        ]
        opened = []
        for argv in steps:
            _out, got = self.hooked_cli(root, work, argv)
            opened.extend(got)
        return root, co, work, opened

    def assert_only_inputs(self, co, work, opened):
        allowed = [os.path.join(co, u"期1"), os.path.join(co, u"期2"), work]
        self.assertGreater(len(opened), 20)
        for p in opened:
            self.assertTrue(any(p == a or p.startswith(a + os.sep) for a in allowed), p)
        self.assertEqual([], [p for p in opened if u"正解" in p])

    def test_c_5b_the_check_cli_opens_nothing_outside_the_given_folders_files_and_outputs_in_a_separate_process(self):
        root, co, work, opened = self.hooked_flow()
        self.assert_only_inputs(co, work, opened)
        self.assertTrue(any(p.startswith(os.path.join(co, u"期1") + os.sep) for p in opened))
        self.assertTrue(any(p.startswith(os.path.join(co, u"期2") + os.sep) for p in opened))
        self.assertTrue(os.path.exists(os.path.join(work, u"r2.json")))              # 最後の命令まで走った
        # folder の外を指す file の名が束に在っても、開かない(期1/../x・正解・期2 の file)
        for bait in (u"../x.csv", u"../正解/正解.csv", u"../正解/正解.json", u"正解/../../x.csv", u"人員.csv/../../x.csv", u"/etc/hosts"):
            root, co, work, opened = self.hooked_flow(bait)
            self.assert_only_inputs(co, work, opened)
        # 判定の道具が本当に外の path を拾えること(道具が壊れていない): 外を開く別 process では log に出る
        root = os.path.realpath(tempfile.mkdtemp(prefix="um2_hook_probe_"))
        _TMPS.append(root)
        os.makedirs(os.path.join(root, u"cwd"))
        wjson(os.path.join(root, u"外", u"x.json"), {})
        probe = os.path.join(root, u"probe.py")
        wbytes(probe, u"import sys\nopen(sys.argv[1]).read()\n".encode("utf-8"))
        hook = os.path.join(root, u"hook", u"hook.py")
        wbytes(hook, self.HOOK.encode("utf-8"))
        log = os.path.join(root, u"hook", u"opened.log")
        subprocess.run([sys.executable, "-I", hook, probe, log, os.path.join(root, u"外", u"x.json")], cwd=os.path.join(root, u"cwd"), check=True)
        self.assertEqual([os.path.join(root, u"外", u"x.json")], [json.loads(x) for x in read_bytes_abs(log).decode("utf-8").splitlines()])

    def test_c_6_a_file_name_that_leaves_the_folder_is_not_read(self):
        w = world()
        m = edit_item(perfect_bundle(w, 1), u"a30", lambda x: x[u"出どころ"].__setitem__(u"file", u"../期2/人員.csv"))
        v = verdicts(check_a(w, 1, m))
        self.assertEqual(u"止める", v[u"a30"][0])
        self.assertIn(u"K1", v[u"a30"][1])
        for name in (u"/etc/passwd", u"", u"人員.csv/", u"./人員.csv", u"人員.csv\x00", u"期2/人員.csv", u"a\\b"):
            m = edit_item(perfect_bundle(w, 1), u"a30", lambda x, name=name: x[u"出どころ"].__setitem__(u"file", name))
            self.assertIn(u"K1", verdicts(check_a(w, 1, m))[u"a30"][1], name)


# ======================================================================== 4. 型 u2 の規則(手で数えた小さな仕訳の file で)
MINI_HEAD = u"日付,科目,借方,貸方,部門\n"
MINI_ROWS = [
    (u"2025-04-01", u"売上高", u"", u"100", u"甲"),
    (u"2025-04-30", u"売上高", u"10", u"", u"甲"),
    (u"2025-05-01", u"売上高", u"", u"1000", u"乙"),
    (u"2025-03-31", u"売上高", u"", u"10000", u"甲"),
    (u" 2025-06-01 ", u" 売上高 ", u"", u" 100,000 ", u" 甲 "),
    (u"2025-07-01", u"売上高", u"", u"", u"甲"),
    (u"2025-08-01", u"売上原価", u"200", u"", u"甲"),
    (u"2025-08-02", u"", u"5", u"", u"乙"),
    (u"20250901", u"売上高付随", u"", u"7", u"乙"),
    (u"2025年9月2日", u"売上高", u"", u"30", u"甲"),
    (u"2025/9/3", u"売上高", u"", u"40", u"甲"),
    (u"notadate", u"売上高", u"", u"500", u"甲"),
    (u"2026-04-01", u"売上高", u"", u"6000", u"甲"),
]


def mini_text(rows=MINI_ROWS, head=MINI_HEAD):
    import csv
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator=u"\n")
    for line in head.strip().split(u"\n"):
        w.writerow(line.split(u","))
    for r in rows:
        w.writerow(list(r))
    return buf.getvalue()


class MiniWorld(object):
    u"""手で数えた小さな仕訳の file 1 つ(``仕訳.csv``)だけを持つ素材の folder と、1 期目の指定。"""

    def __init__(self, text=None, enc="utf-8", name=u"仕訳.csv", prev=None):
        self.tmp = tempfile.mkdtemp(prefix="um2_mini_")
        _TMPS.append(self.tmp)
        text = mini_text() if text is None else text
        raw = (u"﻿" + text).encode("utf-8") if enc == "utf-8-sig" else text.encode(enc)
        wbytes(os.path.join(self.tmp, u"cur", name), raw)
        self.src = CHK.Source(os.path.join(self.tmp, u"cur"))
        self.spec = CHK.load_spec(self._spec(1))[0]
        self.spec2 = CHK.load_spec(self._spec(2))[0]
        self.defA = world().defA

    def _spec(self, per):
        path = os.path.join(self.tmp, u"spec%d.json" % per)
        wjson(path, spec_dict(u"A", per))
        return path

    def check(self, material, ident=u"a01", **kw):
        b = od([(u"型の版", u"u2"), (u"材料", [material])])
        return CHK.check_bundle(self.spec, self.defA, b, self.src, ids=[ident], **kw)

    def rules(self, material, ident=u"a01", **kw):
        res = self.check(material, ident, **kw)
        self.assert_accepted(res)
        return tuple(res[u"材料"][0][u"規則"]), res[u"材料"][0][u"判定"]

    @staticmethod
    def assert_accepted(res):
        if res[u"束"][u"状態"] != u"受理":
            raise AssertionError(res[u"束"])


FY1 = (u"2025-04-01", u"2026-03-31")


def mini_material(conds, value, amt=None, ident=u"a01", mult=1, per=None, unit=u"円", period=None):
    amt = amt or CR_MINUS_DR
    period = period or od([(u"始まり", FY1[0]), (u"終わり", FY1[1])])
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", str(value)), (u"単位", unit), (u"期間", period), (u"範囲", u"全社"), (u"出どころ", rows_source(u"仕訳.csv", amt, conds, mult))])


RANGE = [cond(u"日付", u"以上", FY1[0]), cond(u"日付", u"以下", FY1[1])]
SALES_EQ = cond(u"科目", u"等しい", u"売上高")
#: (名前, 条件の並び, 額, 手で数えた和)
MINI_CASES = [
    (u"等しい", [SALES_EQ] + RANGE, None, 100 - 10 + 1000 + 100000 + 0 + 30 + 40),
    (u"頭が同じ", [cond(u"科目", u"頭が同じ", u"売上高")] + RANGE, None, 100 - 10 + 1000 + 100000 + 0 + 7 + 30 + 40),
    (u"どれか", [cond(u"科目", u"どれか", [u"売上高", u"売上原価"])] + RANGE, None, 100 - 10 + 1000 + 100000 + 30 + 40 - 200),
    (u"どれでもない", [cond(u"科目", u"どれでもない", [u"売上高"])] + RANGE, None, -200 - 5 + 7),
    (u"等しい(別の列)", [SALES_EQ, cond(u"部門", u"等しい", u"乙")] + RANGE, None, 1000),
    (u"以上だけ", [SALES_EQ, cond(u"日付", u"以上", FY1[0])], None, 100 - 10 + 1000 + 100000 + 30 + 40 + 6000),
    (u"以下だけ", [SALES_EQ, cond(u"日付", u"以下", u"2025-03-31")], None, 10000),
    (u"向きの逆", [SALES_EQ] + RANGE, DR_MINUS_CR, -(100 - 10 + 1000 + 100000 + 30 + 40)),
    (u"列 1 つ・符号の逆", [SALES_EQ] + RANGE, od([(u"列", u"貸方"), (u"符号", u"逆")]), -(100 + 1000 + 100000 + 30 + 40)),
    (u"列 1 つ・そのまま", [SALES_EQ] + RANGE, od([(u"列", u"借方"), (u"符号", u"そのまま")]), 10),
]


class RowsRuleTest(unittest.TestCase):
    def test_d_1_every_compare_kind_sums_the_hand_counted_rows(self):
        m = MiniWorld()
        for name, conds, amt, want in MINI_CASES:
            good = mini_material(conds, want, amt)
            rules, verdict = m.rules(good)
            self.assertNotIn(u"K1", rules, name)
            bad = mini_material(conds, want + 1, amt)
            self.assertIn(u"K1", m.rules(bad)[0], name)
            bad = mini_material(conds, want - 1, amt)
            self.assertIn(u"K1", m.rules(bad)[0], name)

    def test_d_2_the_real_cases_also_pass_the_whole_check_when_the_period_matches(self):
        m = MiniWorld()
        rules, verdict = m.rules(mini_material([SALES_EQ] + RANGE, MINI_CASES[0][3]))
        self.assertEqual(((), u"通す(取り方は未確認)"), (rules, verdict))

    def test_d_3_empty_cells_and_spaces_follow_the_sealed_reading(self):
        m = MiniWorld()
        # 空の科目の行(借方 5)は どれでもない に当たり 等しい・頭が同じ・どれか に当たらない
        for how, val, want in ((u"どれでもない", [u"売上高", u"売上原価", u"売上高付随"], -5), (u"どれか", [u"", u"売上原価"], -200), (u"等しい", u"", 0), (u"頭が同じ", u"", None)):
            conds = [cond(u"科目", how, val)] + RANGE
            if want is None:
                continue
            if how == u"等しい":
                self.assertEqual(u"K1", m.rules(mini_material(conds, 0))[0][0] if m.rules(mini_material(conds, 0))[0] else u"K1")           # 選ぶ行が 0 行なので K1
            else:
                self.assertNotIn(u"K1", m.rules(mini_material(conds, want))[0], (how, val))
        # 前後の空白は cell も値も取る
        self.assertNotIn(u"K1", m.rules(mini_material([cond(u"科目", u"等しい", u"  売上高  ")] + RANGE, MINI_CASES[0][3]))[0])
        self.assertNotIn(u"K1", m.rules(mini_material([cond(u"  科目 ", u"等しい", u"売上高")] + RANGE, MINI_CASES[0][3]))[0])
        # ほかの正規化はしない(全角と半角・大小の字は同じにしない)
        z = MiniWorld(mini_text([(u"2025-04-02", u"ABC", u"", u"5", u"甲")]))
        self.assertNotIn(u"K1", z.rules(mini_material([cond(u"科目", u"等しい", u"ABC")] + RANGE, 5))[0])
        for val in (u"ＡＢＣ", u"abc", u"ＡBC"):
            self.assertIn(u"K1", z.rules(mini_material([cond(u"科目", u"等しい", val)] + RANGE, 5))[0], val)
            self.assertIn(u"K1", z.rules(mini_material([cond(u"科目", u"頭が同じ", val)] + RANGE, 5))[0], val)
            self.assertIn(u"K1", z.rules(mini_material([cond(u"科目", u"どれか", [val])] + RANGE, 5))[0], val)

    def test_d_4_date_notations_are_each_read_and_unreadable_rows_match_neither_bound(self):
        forms = (u"{y:04d}-{m:02d}-{d:02d}", u"{y}/{m}/{d}", u"{y:04d}{m:02d}{d:02d}", u"{y}年{m}月{d}日", u"{y}/{m:02d}/{d:02d}", u"{y}年{m:02d}月{d:02d}日")
        for form in forms:
            def fmt(y, mo, d):
                return form.format(y=y, m=mo, d=d)
            rows = [(fmt(2025, 3, 31), u"売上高", u"", u"1", u"甲"), (fmt(2025, 4, 1), u"売上高", u"", u"20", u"甲"), (fmt(2026, 3, 31), u"売上高", u"", u"300", u"甲"),
                    (fmt(2026, 4, 1), u"売上高", u"", u"4000", u"甲"), (u"2025-13-40", u"売上高", u"", u"50000", u"甲"), (u"", u"売上高", u"", u"600000", u"甲")]
            m = MiniWorld(mini_text(rows))
            self.assertNotIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 320))[0], form)
            self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 321))[0], form)
            self.assertNotIn(u"K1", m.rules(mini_material([SALES_EQ, cond(u"日付", u"以上", u"2026-03-31")], 4300))[0], form)
            self.assertNotIn(u"K1", m.rules(mini_material([SALES_EQ, cond(u"日付", u"以下", u"2025-04-01")], 21))[0], form)

    def test_d_5_unreadable_date_text_is_not_a_date(self):
        for text in (u"2025-4-1", u"25/04/01", u"2025.04.01", u"令和7年4月1日", u"2025年4月", u"2025-04-01T00:00", u"２０２５-０４-０１", u"20250401x"):
            self.assertIsNone(CHK.parse_cell_date(text), text)
        for text, want in ((u"2025-04-01", D(2025, 4, 1)), (u" 2025/4/1 ", D(2025, 4, 1)), (u"20250401", D(2025, 4, 1)), (u"2025年4月1日", D(2025, 4, 1)), (u"2025/04/01", D(2025, 4, 1))):
            self.assertEqual(want, CHK.parse_cell_date(text), text)
        self.assertIsNone(CHK.parse_cell_date(u"2025-02-30"))
        self.assertIsNone(CHK.parse_cell_date(None))

    def test_d_6_each_encoding_reads_the_same_sum(self):
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            m = MiniWorld(enc=enc)
            for name, conds, amt, want in MINI_CASES[:3]:
                self.assertNotIn(u"K1", m.rules(mini_material(conds, want, amt))[0], (enc, name))
                self.assertIn(u"K1", m.rules(mini_material(conds, want + 1, amt))[0], (enc, name))
        w = world(enc="cp932")
        r = check_a(w, 1, perfect_bundle(w, 1))
        self.assertEqual(set([u"通す", u"通す(取り方は未確認)", u"無いを受ける"]), set(x[u"判定"] for x in r[u"材料"]))
        w = world(enc="utf-8-sig")
        r = check_a(w, 1, perfect_bundle(w, 1))
        self.assertEqual(set([u"通す", u"通す(取り方は未確認)", u"無いを受ける"]), set(x[u"判定"] for x in r[u"材料"]))
        bad = MiniWorld(u"あ", enc="utf-8")
        wbytes(os.path.join(bad.tmp, u"cur", u"仕訳.csv"), b"\xff\xfe\x00\x81")                  # UTF-8 でも CP932 でも読めない
        bad.src = CHK.Source(os.path.join(bad.tmp, u"cur"))
        self.assertIn(u"K1", bad.rules(mini_material([SALES_EQ] + RANGE, 1))[0])

    def test_d_7_the_amount_cells_use_the_number_reading_and_a_non_number_stops(self):
        rows = [(u"2025-04-01", u"売上高", u"", u"1,000", u"甲"), (u"2025-04-02", u"売上高", u"", u"△200", u"甲"), (u"2025-04-03", u"売上高", u"", u"(30)", u"甲"),
                (u"2025-04-04", u"売上高", u"", u"▲4", u"甲"), (u"2025-04-05", u"売上高", u"", u"-5", u"甲"), (u"2025-04-06", u"売上高", u"", u"", u"甲"), (u"2025-04-07", u"売上高", u"", u" 6 ", u"甲")]
        m = MiniWorld(mini_text(rows))
        self.assertNotIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 1000 - 200 - 30 - 4 - 5 + 6))[0])
        rows.append((u"2025-04-08", u"売上高", u"", u"1.5", u"甲"))
        m = MiniWorld(mini_text(rows))
        self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 1000 - 200 - 30 - 4 - 5 + 6))[0])
        rows[-1] = (u"2025-04-08", u"売上原価", u"", u"1.5", u"甲")                  # 選ばれない行の数でない cell は止めない
        m = MiniWorld(mini_text(rows))
        self.assertNotIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 1000 - 200 - 30 - 4 - 5 + 6))[0])
        rows[-1] = (u"2025-04-08", u"売上高", u"12abc", u"", u"甲")                 # 借方に数でない字
        m = MiniWorld(mini_text(rows))
        self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 0))[0])

    def test_d_8_the_columns_must_be_found_exactly_once_and_zero_selected_rows_stops(self):
        m = MiniWorld()
        for conds in ([cond(u"無い列", u"等しい", u"売上高")] + RANGE, [cond(u"科目 ", u"等しい", u"売上高"), cond(u"日付", u"以上", FY1[0]), cond(u"日付", u"以下", FY1[1])][:0] + [cond(u"部門科目", u"等しい", u"売上高")] + RANGE):
            self.assertIn(u"K1", m.rules(mini_material(conds, 0))[0])
        self.assertIn(u"K1", m.rules(mini_material([cond(u"科目", u"等しい", u"存在しない科目")] + RANGE, 0))[0])           # 選ぶ行が 0
        self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 5, amt=od([(u"列", u"無い額"), (u"符号", u"そのまま")])))[0])
        dup = MiniWorld(u"日付,科目,貸方,貸方\n2025-04-01,売上高,5,6\n")
        self.assertIn(u"K1", dup.rules(mini_material([SALES_EQ] + RANGE, 5, amt=od([(u"列", u"貸方"), (u"符号", u"そのまま")])))[0])
        titled = MiniWorld(u"タイトル行\n" + MINI_HEAD.replace(u"\n", u"\n", 1) + u"2025-04-01,売上高,,5,甲\n")
        self.assertIn(u"K1", titled.rules(mini_material([SALES_EQ] + RANGE, 5))[0])
        src = rows_source(u"仕訳.csv", CR_MINUS_DR, [SALES_EQ] + RANGE)
        src[u"頭の行"] = 2
        mat = mini_material([SALES_EQ] + RANGE, 5)
        mat[u"出どころ"] = src
        self.assertNotIn(u"K1", titled.rules(mat)[0])
        src[u"頭の行"] = 99
        self.assertIn(u"K1", titled.rules(mat)[0])

    def test_d_9_a_xlsx_file_cannot_be_the_file_of_a_row_sum(self):
        w = world()
        m = edit_item(perfect_bundle(w, 1), u"a01", lambda x: x[u"出どころ"].__setitem__(u"file", u"決算書.xlsx"))
        self.assertIn(u"K1", verdicts(check_a(w, 1, m))[u"a01"][1])

    def test_d_10_the_period_rule_for_row_sums(self):
        m = MiniWorld()
        good_p = od([(u"始まり", FY1[0]), (u"終わり", FY1[1])])
        base = [SALES_EQ] + RANGE
        want = MINI_CASES[0][3]
        self.assertEqual(((), u"通す(取り方は未確認)"), m.rules(mini_material(base, want)))
        # 期間の行: 以上・以下がちょうど 1 つずつ・同じ列・指定の期と同じ・期間の欄も同じ
        for name, conds in ((u"以下が無い", [SALES_EQ, RANGE[0]]), (u"以上が無い", [SALES_EQ, RANGE[1]]), (u"以上が 2 つ", [SALES_EQ] + RANGE + [cond(u"日付", u"以上", FY1[0])]),
                            (u"以下が 2 つ", [SALES_EQ] + RANGE + [cond(u"日付", u"以下", FY1[1])]), (u"別の列", [SALES_EQ, cond(u"日付", u"以上", FY1[0]), cond(u"科目", u"以下", FY1[1])]),
                            (u"始まりが違う", [SALES_EQ, cond(u"日付", u"以上", u"2025-04-02"), RANGE[1]]), (u"終わりが違う", [SALES_EQ, RANGE[0], cond(u"日付", u"以下", u"2026-03-30")]),
                            (u"時点の書き方", [SALES_EQ, cond(u"日付", u"以下", FY1[1])])):
            self.assertIn(u"K4", m.rules(mini_material(conds, 0))[0], name)
        self.assertIn(u"K4", m.rules(mini_material(base, want, period=od([(u"始まり", FY1[0]), (u"終わり", u"2026-03-30")])))[0])
        self.assertIn(u"K4", m.rules(mini_material(base, want, period=od([(u"始まり", u"2025-04-02"), (u"終わり", FY1[1])])))[0])
        self.assertIn(u"K4", m.rules(mini_material(base, want, period=od([(u"時点", FY1[1])])))[0])
        self.assertIn(u"K4", m.rules(mini_material(base, want, ident=u"a02", period=od([(u"始まり", u"2024-04-01"), (u"終わり", u"2025-03-31")])), ident=u"a02")[0])          # 前期の行に当期の条件
        # 時点の行: 以下がちょうど 1 つで時点と同じ。以上は在ってもよい(0 個・1 個・2 個)
        point = od([(u"時点", FY1[1])])
        for conds in ([SALES_EQ, cond(u"日付", u"以下", FY1[1])], [SALES_EQ] + RANGE, [SALES_EQ, cond(u"日付", u"以上", u"2000-01-01"), cond(u"日付", u"以上", u"2001-01-01"), cond(u"日付", u"以下", FY1[1])]):
            r = m.rules(mini_material(conds, 0, ident=u"a09", period=point), ident=u"a09")[0]
            self.assertNotIn(u"K4", r, conds)
        for conds in ([SALES_EQ], [SALES_EQ, cond(u"日付", u"以上", FY1[1])], [SALES_EQ, cond(u"日付", u"以下", FY1[1]), cond(u"日付", u"以下", FY1[1])],
                      [SALES_EQ, cond(u"日付", u"以下", u"2026-03-30")]):
            self.assertIn(u"K4", m.rules(mini_material(conds, 0, ident=u"a09", period=point), ident=u"a09")[0], conds)
        self.assertIn(u"K4", m.rules(mini_material([SALES_EQ, cond(u"日付", u"以下", FY1[1])], 0, ident=u"a09", period=od([(u"時点", u"2026-03-30")])), ident=u"a09")[0])
        # 月の行(当期の月:k)
        mon = od([(u"始まり", u"2025-04-01"), (u"終わり", u"2025-04-30")])
        self.assertNotIn(u"K4", m.rules(mini_material([SALES_EQ, cond(u"日付", u"以上", u"2025-04-01"), cond(u"日付", u"以下", u"2025-04-30")], 0, ident=u"a17", period=mon), ident=u"a17")[0])
        self.assertIn(u"K4", m.rules(mini_material([SALES_EQ] + RANGE, 0, ident=u"a17", period=mon), ident=u"a17")[0])

    def test_d_11_the_unit_range_and_multiplier_rules_for_row_sums(self):
        m = MiniWorld()
        want = MINI_CASES[0][3]
        base = [SALES_EQ] + RANGE
        self.assertIn(u"K5", m.rules(mini_material(base, want, unit=u"人"))[0])
        self.assertIn(u"K5", m.rules(mini_material(base, want * 1000, mult=1000))[0])                  # 単位の字のない file は円
        self.assertIn(u"K5", m.rules(mini_material(base, want * 1000, mult=1000, ident=u"a30", unit=u"人"), ident=u"a30")[0])          # 円でない行は倍率 1
        mm = mini_material(base, want)
        mm[u"範囲"] = u"部門"
        self.assertIn(u"K8", m.rules(mm)[0])
        # 単位の cell が file に 1 つ在る CSV は、その倍率でなければ K5
        text = mini_text() + u"(単位:千円),,,,\n"
        k = MiniWorld(text)
        self.assertNotIn(u"K5", k.rules(mini_material(base, want * 1000, mult=1000))[0])
        self.assertIn(u"K5", k.rules(mini_material(base, want))[0])
        two = MiniWorld(text + u"(単位:百万円),,,,\n")
        self.assertIn(u"K5", two.rules(mini_material(base, want * 1000, mult=1000))[0])
        self.assertIn(u"K5", two.rules(mini_material(base, want))[0])

    def test_d_12_k3_is_not_applied_to_row_sums_and_the_item_is_unconfirmed_until_marked(self):
        w = world()
        b = perfect_bundle(w, 1)
        res = check_a(w, 1, b)
        for r in res[u"材料"]:
            m = [x for x in b[u"材料"] if x[u"id"] == r[u"id"]][0]
            if m[u"状態"] == u"在る" and m[u"出どころ"][u"種類"] == u"表の行の和":
                self.assertEqual(u"通す(取り方は未確認)", r[u"判定"], r[u"id"])
                self.assertNotIn(u"K3", r[u"規則"])
            elif m[u"状態"] == u"在る":
                self.assertEqual(u"通す", r[u"判定"], r[u"id"])
        rows_ids = set(m[u"id"] for m in b[u"材料"] if m[u"状態"] == u"在る" and m[u"出どころ"][u"種類"] == u"表の行の和")
        self.assertEqual(24, len(rows_ids))
        res2 = check_a(w, 1, b, confirmed=set(rows_ids))
        self.assertEqual(set([u"通す", u"無いを受ける"]), set(r[u"判定"] for r in res2[u"材料"]))
        res3 = check_a(w, 1, b, confirmed=set([u"a01"]))
        got = verdicts(res3)
        self.assertEqual(u"通す", got[u"a01"][0])
        self.assertEqual(u"通す(取り方は未確認)", got[u"a03"][0])
        # 取り方が素材の行の K3 は 1 期目も掛かる(便 UM0 のまま)
        m = edit_item(b, u"a30", lambda x: x[u"出どころ"].update({u"行の見出し": u"うち正社員"}) or x[u"出どころ"].__setitem__(u"位置", od([(u"行", 3), (u"列", 2)])))
        v = verdicts(check_a(w, 1, m))
        self.assertIn(u"K3", v[u"a30"][1])
        st = CHK.build_store(w.defA, check_a(w, 1, b), b, u"A")
        self.assertTrue(st[u"行"][u"a01"][u"未確認"])
        self.assertNotIn(u"未確認", st[u"行"][u"a02"])
        self.assertEqual(u"u2-store", st[u"版"])

    def test_d_13_a_none_row_is_stopped_when_a_heading_word_is_in_any_cell_of_the_folder(self):
        w = world()
        b = perfect_bundle(w, 1)
        self.assertEqual(u"無いを受ける", verdicts(check_a(w, 1, b))[u"a08"][0])
        # 仕訳帳に「減価償却費」の科目が現れる素材では止まる(見出しの表の字を正規化して見る)
        m = MiniWorld(mini_text([(u"2025-04-01", u"減 価 償却費", u"1", u"", u"甲")]))
        res = m.check(none_material(u"a08"), u"a08")
        self.assertEqual([(u"止める", [u"K9"])], [(r[u"判定"], r[u"規則"]) for r in res[u"材料"]])
        m = MiniWorld(mini_text([(u"2025-04-01", u"償却費", u"1", u"", u"甲")]))
        self.assertEqual(u"無いを受ける", m.check(none_material(u"a08"), u"a08")[u"材料"][0][u"判定"])
        sub = MiniWorld(u"x\n", name=u"サブ/補足.csv")
        wbytes(os.path.join(sub.tmp, u"cur", u"サブ", u"補足.csv"), mini_text([(u"2025-04-01", u"減価償却費", u"1", u"", u"甲")]).encode("utf-8"))
        sub.src = CHK.Source(os.path.join(sub.tmp, u"cur"))
        self.assertEqual(u"止める", sub.check(none_material(u"a08"), u"a08")[u"材料"][0][u"判定"])                  # folder の中の folder の file も見る
        # 素材の和・素材に無い、行の表の字と同じ cell が在る CSV の列の見出しでも止まる(= 全部の cell)
        m = MiniWorld(u"a,b\n減価償却費,1\n")
        self.assertEqual(u"止める", m.check(none_material(u"a08"), u"a08")[u"材料"][0][u"判定"])

    def test_d_14_relations_stop_all_members_when_numbers_disagree_and_are_skipped_when_a_member_is_stopped(self):
        w = world()
        b = perfect_bundle(w, 1)
        res = check_a(w, 1, b)
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])
        # a13 を「部門が甲部の行だけ」に絞り、数値も合わせる。K1 は通り、関係 R3(a29 = a12 + a13)だけが破れる
        w2 = copy.deepcopy(b)
        for it in w2[u"材料"]:
            if it[u"id"] == u"a13":
                it[u"出どころ"][u"条件"].append(cond(u"部門", u"等しい", u"甲部"))
                rows = [r for fy in (0, 1) for r in w.syn.rows[fy] if r[1] == ACCOUNT[u"a13"] and r[4] == u"甲部" and r[0] <= D(2026, 3, 31)]
                it[u"数値"] = str(sum((r[3] or 0) - (r[2] or 0) for r in rows))
        self.assertNotEqual(int([m for m in b[u"材料"] if m[u"id"] == u"a13"][0][u"数値"]), int([m for m in w2[u"材料"] if m[u"id"] == u"a13"][0][u"数値"]))
        res = check_a(w, 1, w2)
        v = verdicts(res)
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])
        for ident in (u"a12", u"a13", u"a29"):
            self.assertEqual((u"止める", (u"K7",)), v[ident], ident)
        for ident in (u"a01", u"a11", u"a14", u"a15", u"a17"):
            self.assertNotEqual(u"止める", v[ident][0], ident)
        with removed(u"K7"):
            v = verdicts(check_a(w, 1, w2))
            self.assertEqual(u"通す(取り方は未確認)", v[u"a13"][0])
        # 関係の片方が K1 で止まれば、その関係は見ない(見なかった数が増える)
        z = edit_item(w2, u"a13", lambda x: x.__setitem__(u"数値", u"1"))
        res = check_a(w, 1, z)
        self.assertEqual({u"見た": 2, u"見なかった": 1}, res[u"K7"])
        self.assertEqual((u"止める", (u"K1",)), verdicts(res)[u"a13"])
        self.assertNotEqual(u"止める", verdicts(res)[u"a29"][0])


# ======================================================================== 5. K11(新しい値)
class PairWorld(object):
    u"""``期1/`` と ``期2/`` の仕訳 file を 1 つずつ(字で渡す)持つ素材の folder の組と、2 期目の指定。"""

    def __init__(self, prev_text, cur_text, prev_name=u"仕訳.csv", cur_name=u"仕訳.csv"):
        self.tmp = tempfile.mkdtemp(prefix="um2_pair_")
        _TMPS.append(self.tmp)
        if prev_text is not None:
            wbytes(os.path.join(self.tmp, u"期1", prev_name), prev_text.encode("utf-8"))
        else:
            os.makedirs(os.path.join(self.tmp, u"期1"))
        wbytes(os.path.join(self.tmp, u"期2", cur_name), cur_text.encode("utf-8"))
        self.prev, self.cur = CHK.Source(os.path.join(self.tmp, u"期1")), CHK.Source(os.path.join(self.tmp, u"期2"))
        path = os.path.join(self.tmp, u"s.json")
        wjson(path, spec_dict(u"A", 2))
        self.spec = CHK.load_spec(path)[0]
        self.defA = world().defA

    def run(self, materials, **kw):
        ids = [m[u"id"] for m in materials]
        b = od([(u"型の版", u"u2"), (u"材料", materials)])
        res = CHK.check_bundle(self.spec, self.defA, b, self.cur, ids=ids, prev_src=kw.get("prev", self.prev), confirmed=set(ids))
        if res[u"束"][u"状態"] != u"受理":
            raise AssertionError(res[u"束"])
        return dict((r[u"id"], (r[u"判定"], tuple(r[u"規則"]))) for r in res[u"材料"])


FY2 = (u"2026-04-01", u"2027-03-31")
HEAD = u"日付,科目,借方,貸方,部門\n"


def row_mat(ident, conds, value, period=None, amt=None):
    period = period or od([(u"始まり", FY2[0]), (u"終わり", FY2[1])])
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", str(value)), (u"単位", u"円"), (u"期間", period), (u"範囲", u"全社"), (u"出どころ", rows_source(u"仕訳.csv", amt or CR_MINUS_DR, conds))])


R2 = [cond(u"日付", u"以上", FY2[0]), cond(u"日付", u"以下", FY2[1])]


class NewValueTest(unittest.TestCase):
    PREV = HEAD + u"2025-05-01,売上高,,100,甲\n2025-05-02,仕入高,50,,乙\n2026-03-31,雑費,5,,甲\n"

    def pair(self, extra, prev=None):
        return PairWorld(prev if prev is not None else self.PREV, self.PREV + extra)

    def test_k11_1_no_new_value_stops_nothing(self):
        p = self.pair(u"2026-05-01,売上高,,7,甲\n")
        v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 7)])
        self.assertEqual({u"a01": (u"通す", ())}, v)

    def test_k11_2_a_new_value_in_the_current_term_stops_every_material_with_a_condition_on_that_column(self):
        p = self.pair(u"2026-05-01,売上高,,7,甲\n2026-06-01,新しい科目,9,,乙\n")
        mats = [row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 7), row_mat(u"a03", [cond(u"科目", u"頭が同じ", u"売上")] + R2, 7),
                row_mat(u"a04", [cond(u"科目", u"どれか", [u"売上高"])] + R2, 7), row_mat(u"a06", [cond(u"科目", u"どれでもない", [u"仕入高", u"雑費", u"新しい科目"])] + R2, 7),
                row_mat(u"a07", [cond(u"部門", u"どれか", [u"甲", u"乙"])] + R2, 7 - 9 + 0 if False else -9 + 7 + 0)]
        # a07: 部門の列にだけ条件。部門の値は新しくない(甲・乙は前からある)ので止まらない
        mats[-1] = row_mat(u"a07", [cond(u"部門", u"どれか", [u"甲", u"乙"])] + R2, 7 - 9)
        v = p.run(mats)
        for ident in (u"a01", u"a03", u"a04", u"a06"):
            self.assertEqual((u"止める", (u"K11",)), v[ident], ident)
        self.assertEqual((u"通す", ()), v[u"a07"])

    def test_k11_3_each_compare_kind_counts_and_the_date_bounds_do_not(self):
        p = self.pair(u"2026-06-01,新しい科目,9,,乙\n")
        for how, val in ((u"等しい", u"売上高"), (u"頭が同じ", u"売"), (u"どれか", [u"売上高"]), (u"どれでもない", [u"仕入高"])):
            v = p.run([row_mat(u"a01", [cond(u"科目", how, val)] + R2, 0)])
            self.assertIn(u"K11", v[u"a01"][1], how)
        # 日付の列にだけ条件を持つ材料は、日付が新しくても止まらない(以上・以下は数えない)
        v = p.run([row_mat(u"a01", R2, -9 + 0)])
        self.assertNotIn(u"K11", v[u"a01"][1])

    def test_k11_4_only_values_in_the_window_of_the_current_term_count(self):
        # 窓の外(当期の始まりより前)の新しい科目は数えない
        p = PairWorld(self.PREV, self.PREV + u"2026-03-31,窓の前の科目,9,,乙\n2027-04-01,窓の後の科目,9,,乙\n")
        v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)])
        self.assertEqual((u"止める", (u"K1",)), v[u"a01"])                   # 当期の売上高の行は無い(K1)。K11 は無い
        v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"雑費")] + R2, 0)])
        self.assertNotIn(u"K11", v[u"a01"][1])
        # 窓の中なら数える(当期の終わりの日・始まりの日を含む)
        for day in (u"2026-04-01", u"2027-03-31"):
            p = PairWorld(self.PREV, self.PREV + u"%s,窓の中の科目,9,,乙\n" % day)
            v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"雑費")] + R2, 0)])
            self.assertIn(u"K11", v[u"a01"][1], day)
        # 読めない日付の行は窓に入らない
        p = PairWorld(self.PREV, self.PREV + u"不明,不明な科目,9,,乙\n")
        v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"雑費")] + R2, 0)])
        self.assertNotIn(u"K11", v[u"a01"][1])

    def test_k11_5_a_time_point_row_looks_from_the_start_of_the_term_to_the_point(self):
        point = od([(u"時点", u"2026-09-30")])
        conds = [cond(u"科目", u"等しい", u"雑費"), cond(u"日付", u"以下", u"2026-09-30")]
        late = PairWorld(self.PREV, self.PREV + u"2026-10-15,後の科目,9,,乙\n")                   # 時点より後の新しい値は数えない
        self.assertNotIn(u"K11", late.run([row_mat(u"a09", conds, 5, period=point, amt=DR_MINUS_CR)])[u"a09"][1])
        inside = PairWorld(self.PREV, self.PREV + u"2026-09-30,時点の日の科目,9,,乙\n")
        self.assertIn(u"K11", inside.run([row_mat(u"a09", conds, 5, period=point, amt=DR_MINUS_CR)])[u"a09"][1])
        before = PairWorld(self.PREV, self.PREV + u"2026-03-31,前の科目,9,,乙\n")                  # 当期の始まりより前(前期の最終日)は窓の外
        self.assertNotIn(u"K11", before.run([row_mat(u"a09", conds, 5, period=point, amt=DR_MINUS_CR)])[u"a09"][1])

    def test_k11_6_an_empty_cell_is_a_value_and_a_missing_header_or_file_counts_as_new(self):
        p = PairWorld(self.PREV, self.PREV + u"2026-05-01,,3,,甲\n")
        self.assertIn(u"K11", p.run([row_mat(u"a01", [cond(u"科目", u"どれでもない", [u"仕入高"])] + R2, 0)])[u"a01"][1])
        prev_without = HEAD.replace(u"科目", u"勘定") + u"2025-05-01,売上高,,100,甲\n"
        p = PairWorld(prev_without, self.PREV)
        self.assertIn(u"K11", p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)])[u"a01"][1])
        p = PairWorld(None, self.PREV)
        self.assertIn(u"K11", p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)])[u"a01"][1])
        p = PairWorld(self.PREV, self.PREV, prev_name=u"別名.csv")
        self.assertIn(u"K11", p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)])[u"a01"][1])

    def test_k11_7_it_is_applied_only_with_a_previous_folder_and_only_to_row_sums(self):
        p = self.pair(u"2026-06-01,新しい科目,9,,乙\n")
        m = row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)
        res = CHK.check_bundle(p.spec, p.defA, od([(u"型の版", u"u2"), (u"材料", [m])]), p.cur, ids=[u"a01"], confirmed=set([u"a01"]))
        self.assertNotIn(u"K11", res[u"材料"][0][u"規則"])
        w = world(new_account=True)
        b = perfect_bundle(w, 1)
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b, check_a(w, 1, b), set(m_[u"id"] for m_ in b[u"材料"] if m_[u"状態"] == u"在る"), w.src[2], ids=CHK.material_ids(w.defA))
        ids = [x[u"id"] for x in c[u"束"][u"材料"]]
        res = CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], w.src[2], ids=ids, confirmed=set(ids), prev_src=w.src[1])
        v = verdicts(res)
        stopped = sorted(i for i, x in v.items() if x[0] == u"止める")
        self.assertEqual(24, len(stopped))
        for i in stopped:
            self.assertEqual((u"K11",), v[i][1])
        for i in (u"a02", u"a15", u"a16", u"a29", u"a30"):
            self.assertEqual(u"通す", v[i][0], i)                              # 素材・素材の和は K11 の対象ではない
        self.assertEqual(u"無いを受ける", v[u"a08"][0])

    def test_k11_8_a_stopped_member_leaves_the_relation_unseen(self):
        w = world(new_account=True)
        b = perfect_bundle(w, 1)
        marks = set(m_[u"id"] for m_ in b[u"材料"] if m_[u"状態"] == u"在る")
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b, check_a(w, 1, b), marks, w.src[2], ids=CHK.material_ids(w.defA))
        ids = [x[u"id"] for x in c[u"束"][u"材料"]]
        res = CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], w.src[2], ids=ids, confirmed=marks, prev_src=w.src[1])
        self.assertEqual({u"見た": 0, u"見なかった": 3}, res[u"K7"])
        # K11 を外すと関係が見える
        with removed(u"K11"):
            res = CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], w.src[2], ids=ids, confirmed=marks, prev_src=w.src[1])
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])


# ======================================================================== 6. 持ち越し
class CarryTest(unittest.TestCase):
    def setup_perfect(self, w=None):
        w = w or world()
        b1 = perfect_bundle(w, 1)
        r1 = check_a(w, 1, b1)
        marks = set(m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る")
        return w, b1, r1, marks

    def carry(self, w, b1, r1, marks, ids=None, src=None, spec=None):
        return CHK.carry(w.defA, spec or w.spec[(2, u"A")], b1, r1, marks, src or w.src[2], ids=ids if ids is not None else CHK.material_ids(w.defA))

    def test_e_1_every_kind_of_material_is_carried_to_the_values_of_the_next_term(self):
        w, b1, r1, marks = self.setup_perfect()
        c = self.carry(w, b1, r1, marks)
        self.assertEqual({}, c[u"確認待ち"])
        self.assertEqual([u"a08"], c[u"無い"])
        self.assertEqual(29, len(c[u"持ち越した"]))
        self.assertEqual(u"u2", c[u"束"][u"型の版"])
        items = dict((m[u"id"], m) for m in c[u"束"][u"材料"])
        self.assertEqual(sorted(items), [m[u"id"] for m in c[u"束"][u"材料"]])
        for ident, m in items.items():
            if m[u"状態"] == u"在る":
                self.assertEqual(str(w.syn.value(ident, 2)), m[u"数値"], ident)
                self.assertEqual(period_of(w, 2, ident), m[u"期間"], ident)
        self.assertEqual(od([(u"種類", u"素材"), (u"file", u"決算書.xlsx"), (u"位置", od([(u"sheet", u"貸借"), (u"セル", u"B2")])), (u"行の見出し", u"純資産合計"), (u"列の見出し", u"当期末"), (u"表示の倍率", 1)]),
                         items[u"a15"][u"出どころ"])
        self.assertEqual(od([(u"種類", u"素材"), (u"file", u"人員.csv"), (u"位置", od([(u"行", 2), (u"列", 2)])), (u"行の見出し", u"期末従業員数"), (u"列の見出し", u"人数"), (u"表示の倍率", 1)]),
                         items[u"a30"][u"出どころ"])
        self.assertEqual(od([(u"種類", u"素材の和"), (u"file", u"借入.csv"), (u"列", 2), (u"行の並び", [2, 3, 4]), (u"列の見出し", u"期末残高"), (u"表示の倍率", 1)]), items[u"a29"][u"出どころ"])
        res = CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], w.src[2], ids=sorted(items), confirmed=marks, prev_src=w.src[1])
        self.assertEqual(set([u"通す", u"無いを受ける"]), set(r[u"判定"] for r in res[u"材料"]))
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])

    def test_e_2_row_sums_move_only_the_date_conditions_and_the_period(self):
        w, b1, r1, marks = self.setup_perfect()
        c = self.carry(w, b1, r1, marks)
        items1 = dict((m[u"id"], m) for m in b1[u"材料"])
        for m in c[u"束"][u"材料"]:
            if m[u"状態"] != u"在る" or m[u"出どころ"][u"種類"] != u"表の行の和":
                continue
            old = items1[m[u"id"]][u"出どころ"]
            new = m[u"出どころ"]
            self.assertEqual((old[u"file"], old[u"頭の行"], old[u"額"], old[u"表示の倍率"]), (new[u"file"], new[u"頭の行"], new[u"額"], new[u"表示の倍率"]))
            self.assertEqual(len(old[u"条件"]), len(new[u"条件"]))
            for a, b in zip(old[u"条件"], new[u"条件"]):
                self.assertEqual((a[u"列"], a[u"比べ方"]), (b[u"列"], b[u"比べ方"]))
                if a[u"比べ方"] in (u"以上", u"以下"):
                    self.assertEqual(CHK.shift_year(D(*map(int, a[u"値"].split(u"-")))).isoformat(), b[u"値"])
                else:
                    self.assertEqual(a[u"値"], b[u"値"])

    def test_e_3_a_year_later_keeps_month_ends_at_month_ends(self):
        for d, want in ((D(2025, 4, 1), D(2026, 4, 1)), (D(2026, 3, 31), D(2027, 3, 31)), (D(2025, 4, 30), D(2026, 4, 30)), (D(2025, 4, 29), D(2026, 4, 29)),
                        (D(2024, 2, 29), D(2025, 2, 28)), (D(2025, 2, 28), D(2026, 2, 28)), (D(2027, 2, 28), D(2028, 2, 29)), (D(2023, 2, 28), D(2024, 2, 29)),
                        (D(2025, 2, 27), D(2026, 2, 27)), (D(2027, 2, 27), D(2028, 2, 27)), (D(2025, 12, 31), D(2026, 12, 31)), (D(2025, 6, 30), D(2026, 6, 30))):
            self.assertEqual(want, CHK.shift_year(d), d)
        self.assertEqual(D(2025, 2, 28), CHK.shift_year(D(2026, 2, 28), -1))
        self.assertEqual(D(2024, 2, 29), CHK.shift_year(D(2025, 2, 28), -1) if False else D(2024, 2, 29))
        self.assertEqual({u"始まり": u"2026-04-01", u"終わり": u"2027-03-31"}, CHK.shift_period_json({u"始まり": u"2025-04-01", u"終わり": u"2026-03-31"}))
        self.assertEqual({u"時点": u"2027-03-31"}, CHK.shift_period_json({u"時点": u"2026-03-31"}))
        self.assertIsNone(CHK.shift_period_json({u"始まり": u"x"}))
        self.assertIsNone(CHK.shift_period_json(None))

    def test_e_4_only_marked_and_passed_rows_are_carried_and_the_rest_wait_with_a_reason(self):
        w, b1, r1, marks = self.setup_perfect()
        c = self.carry(w, b1, r1, marks - set([u"a01", u"a15"]))
        self.assertEqual(u"確かめた取り方の印が無い", c[u"確認待ち"][u"a01"])
        self.assertEqual(u"確かめた取り方の印が無い", c[u"確認待ち"][u"a15"])
        self.assertEqual(2, len(c[u"確認待ち"]))
        self.assertNotIn(u"a01", c[u"持ち越した"])
        ids = [m[u"id"] for m in c[u"束"][u"材料"]]
        self.assertNotIn(u"a01", ids)
        # 1 期目に止まった行は印が在っても持ち越さない
        bad = edit_item(b1, u"a03", lambda x: x.__setitem__(u"数値", str(int(x[u"数値"]) + 1)))
        r1b = check_a(w, 1, bad)
        self.assertEqual(u"止める", verdicts(r1b)[u"a03"][0])
        c = self.carry(w, bad, r1b, marks)
        self.assertEqual(u"1 期目で止まった", c[u"確認待ち"][u"a03"])
        # 無いを受けた行は印が無くても無いのまま持ち越す。K9 で止まった無いは持ち越さない
        c = self.carry(w, b1, r1, set())
        self.assertEqual([u"a08"], c[u"無い"])
        self.assertEqual(29, len(c[u"確認待ち"]))
        self.assertEqual([], c[u"持ち越した"])
        # 検査の結果・束・定義表に無い id
        c = self.carry(w, b1, r1, marks, ids=[u"a01", u"zz9"])
        self.assertEqual(u"1 期目の材料か検査の結果か定義表の行が無い", c[u"確認待ち"][u"zz9"])
        c = self.carry(w, {}, {}, marks)
        self.assertEqual(30, len(c[u"確認待ち"]))
        self.assertEqual([], c[u"束"][u"材料"])

    def test_e_5_cells_are_found_by_row_heading_and_a_column_heading_that_reads_as_the_new_term(self):
        w, b1, r1, marks = self.setup_perfect()
        import openpyxl

        def variant(fn):
            tmp = tempfile.mkdtemp(prefix="um2_var_")
            _TMPS.append(tmp)
            shutil.copytree(w.dirs[2], os.path.join(tmp, u"期2"))
            path = os.path.join(tmp, u"期2", u"決算書.xlsx")
            wb = openpyxl.load_workbook(path)
            fn(wb)
            wb.save(path)
            return CHK.Source(os.path.join(tmp, u"期2"))
        # 行の見出しが変わると 0 個
        s = variant(lambda wb: wb[u"貸借"].__setitem__(u"A2", u"資本合計"))
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertEqual(u"同じ見出しの数の cell が 0", c[u"確認待ち"][u"a15"])
        self.assertEqual(u"同じ見出しの数の cell が 0", c[u"確認待ち"][u"a16"])
        # 同じ見出しの行が 2 つ在ると 2 つ以上
        def dup(wb):
            wb[u"貸借"].append([u"純資産合計", 5, 6])
        s = variant(dup)
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertEqual(u"同じ見出しの数の cell が 2 つ以上", c[u"確認待ち"][u"a15"])
        # 列の見出しが新しい期に読めない字になると 0 個
        s = variant(lambda wb: wb[u"貸借"].__setitem__(u"B1", u"当期末(確定)"))
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertEqual(u"同じ見出しの数の cell が 0", c[u"確認待ち"][u"a15"])
        self.assertIn(u"a16", c[u"持ち越した"])
        # 見出しの正規化(全角の空白・頭の番号)の後で同じなら見つかる
        s = variant(lambda wb: (wb[u"貸借"].__setitem__(u"A2", u"１． 純資産　合計"), wb[u"貸借"].__setitem__(u"B1", u" 当期末 ")))
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertIn(u"a15", c[u"持ち越した"])
        # 列の位置が動いても見出しで追う
        def swap(wb):
            ws = wb[u"貸借"]
            ws.insert_cols(1)
            ws[u"A1"] = u"備考"
        s = variant(swap)
        c = self.carry(w, b1, r1, marks, src=s)
        got = dict((m[u"id"], m) for m in c[u"束"][u"材料"])
        self.assertEqual(od([(u"sheet", u"貸借"), (u"セル", u"C2")]), got[u"a15"][u"出どころ"][u"位置"])
        self.assertEqual(str(w.syn.value(u"a15", 2)), got[u"a15"][u"数値"])
        # sheet の名が無い・file が無い
        s = variant(lambda wb: wb[u"貸借"].__setattr__(u"title", u"別の名"))
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertEqual(u"sheet が無い", c[u"確認待ち"][u"a15"])
        s = CHK.Source(os.path.join(w.tmp, u"無い folder"))
        c = self.carry(w, b1, r1, marks, src=s)
        self.assertEqual(u"file が無い", c[u"確認待ち"][u"a15"])

    def test_e_6_a_row_with_no_period_reading_follows_the_same_row_and_column_headings(self):
        w, b1, r1, marks = self.setup_perfect()
        tmp = tempfile.mkdtemp(prefix="um2_var_")
        _TMPS.append(tmp)
        shutil.copytree(w.dirs[2], os.path.join(tmp, u"期2"))
        base = os.path.join(tmp, u"期2")
        wbytes(os.path.join(base, u"人員.csv"), u"項目,人数\nうち正社員,20\n期末従業員数,31\n".encode("utf-8"))
        c = self.carry(w, b1, r1, marks, src=CHK.Source(base))
        got = dict((m[u"id"], m) for m in c[u"束"][u"材料"])
        self.assertEqual(od([(u"行", 3), (u"列", 2)]), got[u"a30"][u"出どころ"][u"位置"])
        self.assertEqual(u"31", got[u"a30"][u"数値"])
        wbytes(os.path.join(base, u"人員.csv"), u"項目,人員数\n期末従業員数,31\n".encode("utf-8"))
        c = self.carry(w, b1, r1, marks, src=CHK.Source(base))
        self.assertEqual(u"同じ見出しの数の cell が 0", c[u"確認待ち"][u"a30"])
        wbytes(os.path.join(base, u"人員.csv"), u"項目,人数,人数\n期末従業員数,31,32\n".encode("utf-8"))
        c = self.carry(w, b1, r1, marks, src=CHK.Source(base))
        self.assertEqual(u"同じ見出しの数の cell が 2 つ以上", c[u"確認待ち"][u"a30"])

    def test_e_7_a_sum_follows_the_column_heading_and_takes_every_detail_row(self):
        w, b1, r1, marks = self.setup_perfect()
        tmp = tempfile.mkdtemp(prefix="um2_var_")
        _TMPS.append(tmp)
        shutil.copytree(w.dirs[2], os.path.join(tmp, u"期2"))
        base = os.path.join(tmp, u"期2")
        wbytes(os.path.join(base, u"借入.csv"), u"借入先,利率,期末残高\n甲,1.5,100\n乙,1.5,200\n丙,1.5,\n小計,,999\n合計,,300\n".encode("utf-8"))
        c = self.carry(w, b1, r1, marks, src=CHK.Source(base))
        got = dict((m[u"id"], m) for m in c[u"束"][u"材料"])[u"a29"]
        self.assertEqual(3, got[u"出どころ"][u"列"])
        self.assertEqual([2, 3, 5], got[u"出どころ"][u"行の並び"])                          # 小計は明細でない扱いにならない(合計・計の行だけ除く)
        self.assertEqual(u"1299", got[u"数値"])
        wbytes(os.path.join(base, u"借入.csv"), u"借入先,残高\n甲,100\n".encode("utf-8"))
        self.assertEqual(u"同じ列の見出しの列が 0", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a29"])
        wbytes(os.path.join(base, u"借入.csv"), u"借入先,期末残高,期末残高\n甲,100,5\n".encode("utf-8"))
        self.assertEqual(u"同じ列の見出しの列が 2 つ以上", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a29"])
        wbytes(os.path.join(base, u"借入.csv"), u"借入先,期末残高\n甲,100.5\n".encode("utf-8"))                  # 数の cell でない行は数えない
        self.assertEqual(u"同じ列の見出しの列が 0", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a29"])

    def test_e_8_a_row_sum_that_cannot_be_added_waits(self):
        w, b1, r1, marks = self.setup_perfect()
        tmp = tempfile.mkdtemp(prefix="um2_var_")
        _TMPS.append(tmp)
        shutil.copytree(w.dirs[2], os.path.join(tmp, u"期2"))
        base = os.path.join(tmp, u"期2")
        wbytes(os.path.join(base, u"仕訳.csv"), u"日付,科目,借方,貸方,部門\n2026-05-01,勘定乙09,1,,甲\n".encode("utf-8"))
        c = self.carry(w, b1, r1, marks, src=CHK.Source(base))
        self.assertEqual(u"選んだ行が 0", c[u"確認待ち"][u"a01"])
        self.assertIn(u"a09", c[u"持ち越した"])
        wbytes(os.path.join(base, u"仕訳.csv"), u"日付,科目,借方,部門\n2026-05-01,勘定乙09,1,甲\n".encode("utf-8"))
        self.assertEqual(u"額の列が決まらない", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a01"])
        wbytes(os.path.join(base, u"仕訳.csv"), u"日付,勘定,借方,貸方\n2026-05-01,勘定乙09,1,\n".encode("utf-8"))
        self.assertEqual(u"列が決まらない", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a01"])
        os.remove(os.path.join(base, u"仕訳.csv"))
        self.assertEqual(u"file が CSV でない", self.carry(w, b1, r1, marks, src=CHK.Source(base))[u"確認待ち"][u"a01"])

    def test_e_9_the_carried_period_is_the_shifted_one_so_a_changed_fiscal_year_is_stopped_by_the_period_rule(self):
        w, b1, r1, marks = self.setup_perfect()
        sp = CHK.load_spec(w.spec_path[(2, u"A")])[0]
        # 2 期目の指定の当期の終わりを 1 日ずらす(決算月が変わった)と、移した期間は指定の期と違う
        path = os.path.join(w.tmp, u"ずれた指定.json")
        wjson(path, od([(u"成果物", u"A"), (u"当期の始まり", u"2026-04-01"), (u"当期の終わり", u"2027-03-30")]))
        shifted = CHK.load_spec(path)[0]
        c = self.carry(w, b1, r1, marks, spec=shifted)
        res = CHK.check_bundle(shifted, w.defA, c[u"束"], w.src[2], ids=[m[u"id"] for m in c[u"束"][u"材料"]], confirmed=marks, prev_src=w.src[1])
        v = verdicts(res)
        self.assertIn(u"K4", v[u"a01"][1])                                      # 表の行の和: 終わりの日が違う
        self.assertEqual(u"通す", v[u"a30"][0])                                  # 素材の期間は 2 期目の指定から出すので、指定がずれても材料と指定は食い違わない

    def test_e_10_the_inputs_are_not_changed_and_the_result_is_the_same_each_time(self):
        w, b1, r1, marks = self.setup_perfect()
        before = json.dumps([b1, r1], ensure_ascii=False, sort_keys=True)
        c1 = self.carry(w, b1, r1, marks)
        c2 = self.carry(w, b1, r1, marks)
        self.assertEqual(before, json.dumps([b1, r1], ensure_ascii=False, sort_keys=True))
        self.assertEqual(json.dumps(c1, ensure_ascii=False), json.dumps(c2, ensure_ascii=False))
        self.assertEqual(sorted(w.dirs and os.listdir(w.dirs[2])), sorted(os.listdir(w.dirs[2])))


# ======================================================================== 7. 置き場・資料・人が読む版
def flow(w, per=1, bundleA=None, bundleB=None, marks=None):
    u"""1 期目か 2 期目の置き場 A・B を、検査から組む。"""
    a = bundleA or perfect_bundle(w, per)
    resA = check_a(w, per, a, confirmed=marks)
    storeA = CHK.build_store(w.defA, resA, a, u"A")
    plan = CHK.make_plan(w.defB, storeA)
    b = bundleB or perfect_bundle(w, per, u"B")
    resB = CHK.check_bundle(w.spec[(per, u"B")], w.defB, b, w.src[per], ids=plan[u"新しく要る"], confirmed=marks)
    storeB = CHK.build_store(w.defB, resB, b, u"B", prior=storeA, ids=plan[u"新しく要る"])
    return resA, storeA, plan, resB, storeB


class StoreAndHumanTest(unittest.TestCase):
    def test_f_1_the_plan_asks_only_for_the_new_row_and_waiting_rows_are_not_asked_again(self):
        w = world()
        _ra, storeA, plan, _rb, storeB = flow(w)
        self.assertEqual([u"b01"], plan[u"新しく要る"])
        self.assertEqual(16, len(plan[u"置き場に在る"]))
        self.assertEqual([u"b02", u"b03", u"b04"], plan[u"計算で作る"])
        bad = edit_item(perfect_bundle(w, 1), u"a01", lambda x: x.__setitem__(u"数値", u"1"))
        _ra, storeA, plan, _rb, _sb = flow(w, bundleA=bad)
        self.assertEqual(u"確認待ち", storeA[u"行"][u"a01"][u"状態"])
        self.assertIn(u"a01", plan[u"置き場に在る"])
        self.assertNotIn(u"a01", plan[u"新しく要る"])

    def test_f_2_store_rows_values_marks_and_computed_rows_by_hand(self):
        w = world()
        _ra, storeA, _plan, _rb, storeB = flow(w)
        rows = storeA[u"行"]
        self.assertEqual(str(w.syn.value(u"a12", 1) + w.syn.value(u"a13", 1)), rows[u"a31"][u"値"])
        from fractions import Fraction as F
        x = F(w.syn.value(u"a15", 1), w.syn.value(u"a11", 1))
        want = F(int((x * 10000 + F(1, 2)).__floor__()), 10000)
        self.assertEqual(want, F(rows[u"a32"][u"値"]))
        self.assertEqual(u"無い", rows[u"a08"][u"状態"])
        self.assertEqual(u"無い", rows[u"a33"][u"状態"])                  # 入力の a08 が無い
        self.assertEqual(u"入力の材料が無い", rows[u"a33"][u"理由"])
        for i in (u"a01", u"a03", u"a17", u"a28"):
            self.assertTrue(rows[i][u"未確認"], i)
        for i in (u"a02", u"a15", u"a16", u"a29", u"a30"):
            self.assertNotIn(u"未確認", rows[i], i)
        self.assertEqual(str(w.syn.value(u"b01", 1)), storeB[u"行"][u"b01"][u"値"])
        self.assertTrue(storeB[u"行"][u"b01"][u"未確認"])
        self.assertEqual([u"A", u"B"], storeB[u"行"][u"a01"][u"使われた成果物"])
        self.assertEqual(u"A", storeB[u"行"][u"a01"][u"入った成果物"])

    def test_f_3_waiting_reasons_are_kept_in_the_store(self):
        w = world()
        b = perfect_bundle(w, 1)
        res = check_a(w, 1, b)
        st = CHK.build_store(w.defA, res, b, u"A", ids=CHK.material_ids(w.defA), waiting={u"a05": u"理由の字", u"a01": u"別の理由"})
        self.assertEqual(u"在る", st[u"行"][u"a01"][u"状態"])                       # 検査の結果が在る行は検査の結果が先
        st = CHK.build_store(w.defA, check_a(w, 1, od([(u"型の版", u"u2"), (u"材料", [])]), ids=[]), od([(u"型の版", u"u2"), (u"材料", [])]), u"A",
                             ids=CHK.material_ids(w.defA), waiting={u"a05": u"理由の字"})
        self.assertEqual({u"状態": u"確認待ち", u"規則": [], u"理由": u"理由の字", u"入った成果物": u"A", u"使われた成果物": [u"A"]}, st[u"行"][u"a05"])
        self.assertEqual([u"K0"], st[u"行"][u"a06"][u"規則"])                         # 理由が無い行は K0 の旧来の印
        self.assertEqual(u"保留", st[u"行"][u"a33"][u"状態"])

    def test_f_4_the_rendered_documents_pass_and_the_unconfirmed_rows_are_written_like_any_other(self):
        w = world()
        _ra, storeA, _plan, _rb, storeB = flow(w)
        for defn, st in ((w.defA, storeA), (w.defB, storeB)):
            text = CHK.render_doc(defn, st)
            res = CHK.check_document(defn, st, text)
            self.assertTrue(res[u"通った"], res)
            self.assertEqual(0, res[u"結ばれていない数"])
            self.assertEqual(len(defn.rows), res[u"札の数"])
        text = CHK.render_doc(w.defA, storeA)
        self.assertIn(u"無い[材料:a08]", text)
        self.assertIn(u"無い[材料:a33]", text)
        self.assertRegex(text, u"%s百万円\\[材料:a01\\]" % u"{:,}".format(int((w.syn.value(u"a01", 1) / 1000000.0) + 0.5)))

    def test_f_5_a_waiting_row_is_written_as_a_waiting_word_in_the_document(self):
        w = world()
        bad = edit_item(perfect_bundle(w, 1), u"a05", lambda x: x.__setitem__(u"数値", u"1"))
        _ra, storeA, _plan, _rb, _sb = flow(w, bundleA=bad)
        text = CHK.render_doc(w.defA, storeA)
        self.assertIn(u"確認待ち[材料:a05]", text)
        self.assertTrue(CHK.check_document(w.defA, storeA, text)[u"通った"])
        self.assertFalse(CHK.check_document(w.defA, storeA, text.replace(u"確認待ち[材料:a05]", u"100円[材料:a05]"))[u"通った"])

    def build(self, w=None, bundle=None):
        w = w or world()
        _ra, storeA, _plan, _rb, _sb = flow(w, bundleA=bundle)
        text = CHK.render_doc(w.defA, storeA)
        return w, storeA, text

    def test_f_6_the_human_version_has_the_body_without_tags_and_a_source_table(self):
        w, st, text = self.build()
        page, res = CHK.make_human(w.defA, st, text)
        self.assertTrue(res[u"通った"])
        self.assertTrue(page.startswith(u"<!DOCTYPE html>"))
        self.assertEqual(1, page.count(u"<main id=\"body\">"))
        self.assertEqual(1, page.count(u"<section id=\"sources\">"))
        body = CHK.HTML_BODY.search(page).group(1)
        self.assertNotIn(u"[材料:", body)
        self.assertNotIn(u"[材料:", page)
        self.assertIn(u"無い", body)
        for row in w.defA.rows:
            self.assertIn(u"<td>%s</td>" % row[u"id"], page, row[u"id"])
        table = page[page.index(u"<section id=\"sources\">"):]
        self.assertEqual(33, table.count(u"<tr><td>"))
        self.assertIn(u"<th>未確認か</th>", table)
        a01 = [ln for ln in table.split(u"</tr>") if u"<td>a01</td>" in ln][0]
        self.assertIn(u"未確認", a01)
        self.assertIn(u"仕訳.csv / 条件 3 個", a01)
        a02 = [ln for ln in table.split(u"</tr>") if u"<td>a02</td>" in ln][0]
        self.assertIn(u"決算書.xlsx / 損益!C2", a02)
        self.assertTrue(a02.rstrip().endswith(u"<td>-</td>"))
        self.assertIn(u"人員.csv / 2 行 2 列", [ln for ln in table.split(u"</tr>") if u"<td>a30</td>" in ln][0])
        self.assertIn(u"借入.csv / 2 列 の 3 行の和", [ln for ln in table.split(u"</tr>") if u"<td>a29</td>" in ln][0])
        self.assertIn(u"計算(a12・a13)", [ln for ln in table.split(u"</tr>") if u"<td>a31</td>" in ln][0])
        self.assertTrue(CHK.check_human(text, page)[u"通った"])

    def test_f_7_the_human_check_is_red_for_a_changed_number_a_left_tag_a_missing_body_and_unreadable_input(self):
        w, st, text = self.build()
        page, _r = CHK.make_human(w.defA, st, text)
        self.assertTrue(CHK.check_human(text, page)[u"通った"])
        digit = re.search(u"[0-9]+(?=百万円)", CHK.HTML_BODY.search(page).group(1))
        a = page.index(u"<main id=\"body\">") + len(u"<main id=\"body\">") + digit.start()
        changed = page[:a] + str((int(page[a]) + 1) % 10) + page[a + 1:]
        self.assertEqual(u"数の字の並びが違う", CHK.check_human(text, changed)[u"赤"][0][u"種類"])
        # 数字を 1 つ足す・減らす・入れ替える
        self.assertFalse(CHK.check_human(text, page.replace(u"</main>", u"<p>5</p></main>"))[u"通った"])
        self.assertFalse(CHK.check_human(text, page.replace(u"無い</li>", u"</li>", 1))[u"通った"] and False)
        body = CHK.HTML_BODY.search(page).group(1)
        ms = list(re.finditer(u"([0-9,]+)百万円", body))
        k = [i for i in range(len(ms) - 1) if ms[i].group(1) != ms[i + 1].group(1)][0]
        (a1, b1), (a2, b2) = ms[k].span(1), ms[k + 1].span(1)
        sw = body[:a1] + ms[k + 1].group(1) + body[b1:a2] + ms[k].group(1) + body[b2:]
        self.assertNotEqual(body, sw)
        self.assertFalse(CHK.check_human(text, page.replace(body, sw))[u"通った"])
        self.assertEqual(u"札が残っている", CHK.check_human(text, page.replace(u"</main>", u"<p>[材料:x]</p></main>"))[u"赤"][0][u"種類"])
        self.assertEqual(u"本文が無い", CHK.check_human(text, page.replace(u"<main id=\"body\">", u"<main>"))[u"赤"][0][u"種類"])
        self.assertFalse(CHK.check_human(None, page)[u"通った"])
        self.assertFalse(CHK.check_human(text, None)[u"通った"])
        # 表の中の数は本文の検査に入らない(表を書き換えても本文は同じ)
        t = page.replace(u"<td>a01</td>", u"<td>a99</td>")
        self.assertTrue(CHK.check_human(text, t)[u"通った"])

    def test_f_8_a_document_that_did_not_pass_the_document_check_is_not_built(self):
        w, st, text = self.build()
        for bad in (text + u"\n約3割が増えた\n", text.replace(u"[材料:a01]", u""), text.replace(u"無い[材料:a08]", u"100円[材料:a08]"), u""):
            page, res = CHK.make_human(w.defA, st, bad)
            self.assertIsNone(page)
            self.assertFalse(res[u"通った"])
        self.assertIsNone(CHK.make_human(w.defA, st, None)[0])

    def test_f_9_html_special_characters_are_escaped_and_headings_and_bullets_are_built(self):
        w, st, text = self.build()
        text2 = text.replace(u"## 数値", u"## 数値 <b>強調</b> & \"引用\"")
        page, res = CHK.make_human(w.defA, st, text2)
        self.assertTrue(res[u"通った"])
        self.assertIn(u"&lt;b&gt;強調&lt;/b&gt; &amp; &quot;引用&quot;", page)
        self.assertNotIn(u"<b>", page)
        self.assertIn(u"<h1>", page)
        self.assertIn(u"<h2>", page)
        self.assertIn(u"<ul>", page)
        self.assertEqual(page.count(u"<ul>"), page.count(u"</ul>"))
        self.assertEqual(33, page[:page.index(u"<section")].count(u"<li>"))

    def test_f_10_the_human_version_of_the_second_document_is_built_from_the_carried_store(self):
        w = world()
        b1 = perfect_bundle(w, 1)
        r1 = check_a(w, 1, b1)
        marks = set(m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る")
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b1, r1, marks, w.src[2], ids=CHK.material_ids(w.defA))
        ids = [x[u"id"] for x in c[u"束"][u"材料"]]
        r2 = CHK.check_bundle(w.spec[(2, u"A")], w.defA, c[u"束"], w.src[2], ids=ids, confirmed=marks, prev_src=w.src[1])
        st = CHK.build_store(w.defA, r2, c[u"束"], u"A", ids=CHK.material_ids(w.defA), waiting=c[u"確認待ち"])
        text = CHK.render_doc(w.defA, st)
        page, res = CHK.make_human(w.defA, st, text)
        self.assertTrue(res[u"通った"])
        table = page[page.index(u"<section id=\"sources\">"):]
        self.assertNotIn(u"未確認", table.replace(u"<th>未確認か</th>", u""))                    # 印が付いた取り方は未確認と書かない
        self.assertTrue(CHK.check_human(text, page)[u"通った"])


# ======================================================================== 8. 規則を 1 つずつ外すと、その規則だけが止める変異が通る
def mutations(w):
    u"""(名前, 規則, 材料の束, 隣の規則) の並び。各束は、その規則だけが止める。隣の規則(関係)も同じ材料を止める組は、隣の規則の名を最後に持つ(黙る組)。"""
    b = perfect_bundle(w, 1)
    out = []

    def add(name, rule, bundle, layer=None):
        out.append((name, rule, bundle, layer))

    def plus1(m):
        m[u"数値"] = str(int(m[u"数値"]) + 1)

    def prev_year(m):
        p = od([(u"始まり", u"2024-04-01"), (u"終わり", u"2025-03-31")])
        m[u"出どころ"][u"条件"] = [m[u"出どころ"][u"条件"][0], cond(u"日付", u"以上", p[u"始まり"]), cond(u"日付", u"以下", p[u"終わり"])]
        m[u"数値"] = str(w.syn.total(ACCOUNT[u"a03"], fy_range(0)[0], fy_range(0)[1], -1))

    def prev_both(m):
        prev_year(m)
        m[u"期間"] = od([(u"始まり", u"2024-04-01"), (u"終わり", u"2025-03-31")])

    def mult1000(m):
        m[u"出どころ"][u"表示の倍率"] = 1000
        m[u"数値"] = str(int(m[u"数値"]) * 1000)

    def second_row(m):
        m[u"出どころ"][u"位置"] = od([(u"行", 3), (u"列", 2)])
        m[u"出どころ"][u"行の見出し"] = u"うち正社員"
        m[u"数値"] = str(w.syn.value(u"a30", 1) - 4)

    def as_sum(m):
        m[u"数値"] = str(w.syn.value(u"a30", 1) * 2 - 4)
        m[u"出どころ"] = od([(u"種類", u"素材の和"), (u"file", u"人員.csv"), (u"列", 2), (u"行の並び", [2, 3]), (u"列の見出し", u"人数"), (u"表示の倍率", 1)])

    def drop_row(m):
        m[u"出どころ"][u"行の並び"] = [2, 3]
        m[u"数値"] = str(w.syn.value(u"a29", 1) // 5 + w.syn.value(u"a29", 1) // 3)
    add(u"K1 数値に 1 を足す(行の和)", u"K1", edit_item(b, u"a03", plus1))
    add(u"K1 数値に 1 を足す(素材)", u"K1", edit_item(b, u"a02", plus1))
    add(u"K4 日付の条件だけ前の期へ", u"K4", edit_item(b, u"a03", prev_year))
    add(u"K4 日付の条件と期間の両方を前の期へ", u"K4", edit_item(b, u"a03", prev_both))
    add(u"K4 期間だけ別の期(素材)", u"K4", edit_item(b, u"a15", lambda m: m.__setitem__(u"期間", od([(u"時点", u"2025-03-31")]))))
    add(u"K5 単位の字", u"K5", edit_item(b, u"a03", lambda m: m.__setitem__(u"単位", u"人")))
    add(u"K5 倍率(素材)", u"K5", edit_item(b, u"a02", mult1000))
    add(u"K8 範囲", u"K8", edit_item(b, u"a03", lambda m: m.__setitem__(u"範囲", u"部門")))
    add(u"K2 行の見出しの申告", u"K2", edit_item(b, u"a30", lambda m: m[u"出どころ"].__setitem__(u"行の見出し", u"別の見出し")))
    add(u"K2 列の見出しの申告", u"K2", edit_item(b, u"a15", lambda m: m[u"出どころ"].__setitem__(u"列の見出し", u"別の見出し")))
    add(u"K3 どちらの見出しも表に無い", u"K3", edit_item(b, u"a30", second_row))
    add(u"K3 取り方の種類が定義表と違う", u"K3", edit_item(b, u"a30", as_sum))
    add(u"K6 和の行から 1 行外す", u"K6", edit_item(b, u"a29", drop_row), layer=u"K7")
    return out


class RuleRemovalTest(unittest.TestCase):
    def test_g_1_each_mutation_is_stopped_only_by_its_own_rule(self):
        w = world()
        base = verdicts(check_a(w, 1, perfect_bundle(w, 1)))
        for name, rule, bundle, _layer in mutations(w):
            res = check_a(w, 1, bundle)
            self.assertEqual(u"受理", res[u"束"][u"状態"], name)
            got = verdicts(res)
            changed = [i for i in got if got[i] != base[i]]
            self.assertTrue(changed, name)
            first = changed[0]
            self.assertEqual(u"止める", got[first][0], name)
            self.assertEqual((rule,), got[first][1], name)

    def test_g_2_removing_the_rule_lets_the_mutation_through_and_never_lowers_the_pass_count(self):
        w = world()
        base_count = sum(1 for r in check_a(w, 1, perfect_bundle(w, 1))[u"材料"] if r[u"判定"] != u"止める")
        for name, rule, bundle, layer in mutations(w):
            res_all = check_a(w, 1, bundle)
            stopped_all = set(r[u"id"] for r in res_all[u"材料"] if r[u"判定"] == u"止める")
            self.assertTrue(stopped_all, name)
            with removed(rule):
                res = check_a(w, 1, bundle)
            stopped = set(r[u"id"] for r in res[u"材料"] if r[u"判定"] == u"止める")
            if layer is None:
                self.assertEqual(set(), stopped, (name, rule, stopped))
            else:                                   # 隣の規則(関係)が同じ材料をまだ止める
                self.assertTrue(stopped, name)
                for r in res[u"材料"]:
                    if r[u"id"] in stopped:
                        self.assertEqual([layer], r[u"規則"], (name, r))
                with removed(rule), removed(layer):
                    res = check_a(w, 1, bundle)
                self.assertEqual([], [r for r in res[u"材料"] if r[u"判定"] == u"止める"], name)
            self.assertGreaterEqual(sum(1 for r in res[u"材料"] if r[u"判定"] != u"止める"), sum(1 for r in res_all[u"材料"] if r[u"判定"] != u"止める"))
            self.assertEqual(base_count, sum(1 for r in res[u"材料"] if r[u"判定"] != u"止める"), name)

    def test_g_2b_a_period_mutation_on_a_row_that_is_in_a_relation_is_caught_by_k7_when_k4_is_removed(self):
        w = world()
        b = perfect_bundle(w, 1)

        def prev_year(m):
            m[u"出どころ"][u"条件"] = [m[u"出どころ"][u"条件"][0], cond(u"日付", u"以上", u"2024-04-01"), cond(u"日付", u"以下", u"2025-03-31")]
            m[u"数値"] = str(w.syn.value(u"a02", 1))
        bad = edit_item(b, u"a01", prev_year)
        v = verdicts(check_a(w, 1, bad))
        self.assertEqual((u"止める", (u"K4",)), v[u"a01"])
        with removed(u"K4"):
            v = verdicts(check_a(w, 1, bad))
        self.assertEqual((u"止める", (u"K7",)), v[u"a01"])                         # 隣の規則(関係)がまだ止める
        self.assertEqual(13, len([i for i, x in v.items() if x[0] == u"止める"]))        # 月 12 と a01(関係 R1 の全員)
        with removed(u"K4"), removed(u"K7"):
            v = verdicts(check_a(w, 1, bad))
        self.assertEqual(u"通す(取り方は未確認)", v[u"a01"][0])

    def test_g_3_k0_k7_k9_k11_removal(self):
        w = world()
        b = perfect_bundle(w, 1)
        bad = copy.deepcopy(b)
        bad[u"型の版"] = u"u0"
        self.assertEqual(u"断り", check_a(w, 1, bad)[u"束"][u"状態"])
        with removed(u"K0"):
            self.assertEqual(u"受理", check_a(w, 1, bad)[u"束"][u"状態"])
        for k in (u"K0", u"K1", u"K2", u"K3", u"K4", u"K5", u"K6", u"K7", u"K8", u"K9", u"K11"):
            saved = CHK.RULE_FUNCS[k]
            with removed(k):
                self.assertIsNot(saved, CHK.RULE_FUNCS[k])
            self.assertIs(saved, CHK.RULE_FUNCS[k])                 # 戻っている

    def test_g_4_every_rule_name_is_reachable_through_the_table_and_the_table_is_complete(self):
        self.assertEqual(set(CHK.RULES), set(CHK.RULE_FUNCS))
        covered = set(rule for _n, rule, _b, _l in mutations(world()))
        self.assertEqual(set([u"K1", u"K2", u"K3", u"K4", u"K5", u"K6", u"K8"]), covered)

    def test_g_5_the_form_only_check_passes_every_mutation_that_keeps_the_shape(self):
        w = world()
        for name, _rule, bundle, _layer in mutations(w):
            res = check_a(w, 1, bundle, form_only=True)
            self.assertEqual(u"受理", res[u"束"][u"状態"], name)
            self.assertEqual([], [r for r in res[u"材料"] if r[u"判定"] == u"止める"], name)
        bad = perfect_bundle(w, 1)
        bad[u"材料"][0][u"数値"] = u"01"
        self.assertEqual(u"断り", check_a(w, 1, bad, form_only=True)[u"束"][u"状態"])

    def test_g_6_every_mutation_changes_exactly_one_material(self):
        w = world()
        b = perfect_bundle(w, 1)
        for name, _rule, bundle, _layer in mutations(w):
            diff = [x[u"id"] for x, y in zip(b[u"材料"], bundle[u"材料"]) if x != y]
            self.assertEqual(1, len(diff), (name, diff))

    def test_g_7_document_rules_removed_let_their_mutation_through(self):
        w = world()
        _ra, storeA, _p, _rb, _sb = flow(w)
        text = CHK.render_doc(w.defA, storeA)
        cases = {u"C1": text.replace(u"[材料:a01]", u"", 1), u"C2": re.sub(u"([0-9])([0-9,]*)百万円\\[材料:a01\\]", lambda m: str((int(m.group(1)) + 1) % 10) + m.group(2) + u"百万円[材料:a01]", text, 1),
                 u"C3": text.replace(u"無い[材料:a08]", u"100円[材料:a08]"), u"C4": text + u"\n約3割が増えた\n"}
        for rule, bad in cases.items():
            self.assertFalse(CHK.check_document(w.defA, storeA, bad)[u"通った"], rule)
            with doc_removed(rule):
                reds = [r[u"条"] for r in CHK.check_document(w.defA, storeA, bad)[u"赤"]]
            self.assertNotIn(rule, reds)
            self.assertEqual(rule, [r[u"条"] for r in CHK.check_document(w.defA, storeA, bad)[u"赤"]][0])


class SilentRuleRemovalTest(unittest.TestCase):
    def test_g_8_removing_k9_lets_a_none_with_a_candidate_through(self):
        m = MiniWorld(mini_text([(u"2025-04-01", u"減価償却費", u"1", u"", u"甲")]))
        self.assertEqual((u"止める", [u"K9"]), tuple((r[u"判定"], r[u"規則"]) for r in m.check(none_material(u"a08"), u"a08")[u"材料"])[0])
        with removed(u"K9"):
            self.assertEqual((u"無いを受ける", []), tuple((r[u"判定"], r[u"規則"]) for r in m.check(none_material(u"a08"), u"a08")[u"材料"])[0])

    def test_g_9_removing_k11_lets_a_row_sum_with_a_new_value_through(self):
        p = PairWorld(NewValueTest.PREV, NewValueTest.PREV + u"2026-06-01,新しい科目,9,,乙\n")
        mats = [row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 0)]
        self.assertEqual((u"止める", (u"K1", u"K11")), p.run(mats)[u"a01"])                    # 売上高の行が当期に無いので K1 も止まる
        # K11 だけ見るために、当期の売上高の行を足す
        p = PairWorld(NewValueTest.PREV, NewValueTest.PREV + u"2026-06-01,新しい科目,9,,乙\n2026-05-01,売上高,,7,甲\n")
        mats = [row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 7)]
        self.assertEqual((u"止める", (u"K11",)), p.run(mats)[u"a01"])
        with removed(u"K11"):
            self.assertEqual((u"通す", ()), p.run(mats)[u"a01"])

    def test_g_10_removing_k1_lets_a_zero_row_selection_and_a_wrong_sum_through(self):
        m = MiniWorld()
        bad = mini_material([cond(u"科目", u"等しい", u"存在しない科目")] + RANGE, 5)
        self.assertEqual(((u"K1",), u"止める"), m.rules(bad))
        with removed(u"K1"):
            self.assertEqual(((), u"通す(取り方は未確認)"), m.rules(bad))


# ======================================================================== 9. 退化の入力(どんな入力でも例外で落ちない)
class DegenerateTest(unittest.TestCase):
    def refused(self, bundle, part=None):
        w = world()
        res = check_a(w, 1, bundle)
        self.assertEqual(u"断り", res[u"束"][u"状態"], str(bundle)[:200])
        self.assertEqual([u"K0"], res[u"束"][u"規則"])
        self.assertEqual([], res[u"材料"])
        if part:
            self.assertTrue(any(part in r for r in res[u"束"][u"理由"]), res[u"束"][u"理由"])

    def edit(self, ident, fn):
        return edit_item(perfect_bundle(world(), 1), ident, fn)

    def test_i_1_the_type_version_must_be_u2_and_the_top_keys_are_exactly_two(self):
        b = perfect_bundle(world(), 1)
        for v in (u"u0", u"u1", u"U2", u"", None, 2, [u"u2"]):
            bad = copy.deepcopy(b)
            bad[u"型の版"] = v
            self.refused(bad)
        for extra in ({u"余り": 1},):
            bad = copy.deepcopy(b)
            bad.update(extra)
            self.refused(bad, u"頂の鍵")
        for top in (None, [], u"u2", 5, {}, {u"型の版": u"u2"}, {u"材料": []}):
            self.refused(top, u"頂の鍵")
        self.refused(od([(u"型の版", u"u2"), (u"材料", None)]), u"材料")
        self.refused(od([(u"型の版", u"u2"), (u"材料", [None])]))

    def test_i_2_row_sum_keys_and_value_forms(self):
        src = lambda m: m[u"出どころ"]
        cases = [
            (u"鍵が足りない", lambda m: src(m).pop(u"頭の行")), (u"鍵が足りない(額)", lambda m: src(m).pop(u"額")), (u"鍵が足りない(条件)", lambda m: src(m).pop(u"条件")),
            (u"余分な鍵", lambda m: src(m).__setitem__(u"位置", 1)), (u"頭の行 0", lambda m: src(m).__setitem__(u"頭の行", 0)), (u"頭の行 負", lambda m: src(m).__setitem__(u"頭の行", -1)),
            (u"頭の行 bool", lambda m: src(m).__setitem__(u"頭の行", True)), (u"頭の行 字", lambda m: src(m).__setitem__(u"頭の行", u"1")), (u"頭の行 小数", lambda m: src(m).__setitem__(u"頭の行", 1.0)),
            (u"倍率 0", lambda m: src(m).__setitem__(u"表示の倍率", 0)), (u"倍率 10", lambda m: src(m).__setitem__(u"表示の倍率", 10)),
            (u"額が字", lambda m: src(m).__setitem__(u"額", u"貸方")), (u"額が空", lambda m: src(m).__setitem__(u"額", od())),
            (u"額の鍵が混ざる", lambda m: src(m).__setitem__(u"額", od([(u"列", u"貸方"), (u"符号", u"そのまま"), (u"向き", u"借方−貸方")]))),
            (u"符号の字", lambda m: src(m).__setitem__(u"額", od([(u"列", u"貸方"), (u"符号", u"+")]))),
            (u"符号の型", lambda m: src(m).__setitem__(u"額", od([(u"列", u"貸方"), (u"符号", None)]))),
            (u"向きが半角のハイフン", lambda m: src(m).__setitem__(u"額", od([(u"借方の列", u"借方"), (u"貸方の列", u"貸方"), (u"向き", u"借方-貸方")]))),
            (u"向きの字", lambda m: src(m).__setitem__(u"額", od([(u"借方の列", u"借方"), (u"貸方の列", u"貸方"), (u"向き", u"貸方のみ")]))),
            (u"額の列が字でない", lambda m: src(m).__setitem__(u"額", od([(u"列", 3), (u"符号", u"そのまま")]))),
            (u"条件が空", lambda m: src(m).__setitem__(u"条件", [])), (u"条件が 9 個", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"等しい", u"x")] * 9)),
            (u"条件が並びでない", lambda m: src(m).__setitem__(u"条件", cond(u"科目", u"等しい", u"x"))), (u"条件が object でない", lambda m: src(m).__setitem__(u"条件", [u"科目"])),
            (u"条件の鍵が足りない", lambda m: src(m).__setitem__(u"条件", [od([(u"列", u"科目"), (u"比べ方", u"等しい")])])),
            (u"条件の鍵が余る", lambda m: src(m).__setitem__(u"条件", [od([(u"列", u"科目"), (u"比べ方", u"等しい"), (u"値", u"x"), (u"余", 1)])])),
            (u"比べ方の字", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"含む", u"x")])), (u"比べ方の型", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", None, u"x")])),
            (u"比べ方が並び", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", [u"等しい"], u"x")])),
            (u"等しいの値が並び", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"等しい", [u"x"])])), (u"頭が同じの値が並び", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"頭が同じ", [u"x"])])),
            (u"どれかの値が字", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"どれか", u"x")])), (u"どれかの値が空", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"どれか", [])])),
            (u"どれかの値が 201 個", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"どれか", [u"x%d" % k for k in range(201)])])),
            (u"どれでもないの値に数", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"どれでもない", [u"x", 5])])),
            (u"値が数", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"等しい", 5)])), (u"値が null", lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"等しい", None)])),
            (u"以上が日付でない", lambda m: src(m).__setitem__(u"条件", [cond(u"日付", u"以上", u"2025/04/01")])), (u"以下が日付でない", lambda m: src(m).__setitem__(u"条件", [cond(u"日付", u"以下", u"20250401")])),
            (u"存在しない日", lambda m: src(m).__setitem__(u"条件", [cond(u"日付", u"以上", u"2025-02-30")])), (u"以上の値が並び", lambda m: src(m).__setitem__(u"条件", [cond(u"日付", u"以上", [u"2025-04-01"])])),
            (u"列が字でない", lambda m: src(m).__setitem__(u"条件", [cond(5, u"等しい", u"x")])),
            (u"file が字でない", lambda m: src(m).__setitem__(u"file", 5)), (u"種類の字", lambda m: src(m).__setitem__(u"種類", u"表の行の合計")),
            (u"在るの鍵が足りない", lambda m: m.pop(u"範囲")), (u"数値の字", lambda m: m.__setitem__(u"数値", u"1,000")),
        ]
        for name, fn in cases:
            self.refused(self.edit(u"a03", fn))

    def test_i_3_a_condition_form_that_is_valid_passes_the_form_check(self):
        w = world()
        for conds in ([cond(u"科目", u"等しい", u"")], [cond(u"科目", u"どれか", [u"" for _ in range(200)])], [cond(u"科目", u"どれでもない", [u"x"])],
                      [cond(u"日付", u"以上", u"2025-04-01")] * 8, [cond(u"科目", u"頭が同じ", u"あ" * 5000)]):
            b = self.edit(u"a03", lambda m, conds=conds: m[u"出どころ"].__setitem__(u"条件", conds))
            self.assertEqual(u"受理", check_a(w, 1, b)[u"束"][u"状態"])

    def test_i_4_zero_materials_all_none_duplicates_and_missing_ids(self):
        w = world()
        self.refused(od([(u"型の版", u"u2"), (u"材料", [])]), u"頼んだ行")
        allnone = od([(u"型の版", u"u2"), (u"材料", [none_material(m[u"id"]) for m in perfect_bundle(w, 1)[u"材料"]])])
        res = check_a(w, 1, allnone)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        got = collections.Counter(r[u"判定"] for r in res[u"材料"])
        self.assertEqual(30, sum(got.values()))
        for r in res[u"材料"]:
            if r[u"判定"] == u"止める":
                self.assertEqual([u"K9"], r[u"規則"])
        b = perfect_bundle(w, 1)
        dup = copy.deepcopy(b)
        dup[u"材料"].append(copy.deepcopy(dup[u"材料"][0]))
        self.refused(dup, u"重複")
        miss = copy.deepcopy(b)
        miss[u"材料"].pop()
        self.refused(miss, u"頼んだ行")
        extra = copy.deepcopy(b)
        extra[u"材料"][0][u"id"] = u"zz9"
        self.refused(extra, u"頼んだ行")

    def test_i_5_huge_numbers_surrogates_and_long_strings_do_not_raise(self):
        w = world()
        b = self.edit(u"a03", lambda m: m.__setitem__(u"数値", u"9" * 5000))
        self.assertIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])
        b = self.edit(u"a03", lambda m: m.__setitem__(u"数値", u"-" + u"9" * 5000))
        self.assertIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])
        for val in (u"\ud800", u"x\udfff", u"売\ud83d上高"):
            b = self.edit(u"a03", lambda m, val=val: m[u"出どころ"][u"条件"].__setitem__(0, cond(u"科目", u"等しい", val)))
            self.assertEqual(u"受理", check_a(w, 1, b)[u"束"][u"状態"])
            self.assertIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])
        b = self.edit(u"a03", lambda m: m[u"出どころ"].__setitem__(u"file", u"\ud800.csv"))
        self.assertIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])
        b = self.edit(u"a03", lambda m: m[u"出どころ"][u"条件"].__setitem__(0, cond(u"科目", u"頭が同じ", u"売" * 100000)))
        self.assertIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])
        b = self.edit(u"a03", lambda m: m[u"出どころ"][u"条件"].__setitem__(0, cond(u"科目", u"どれか", [u"勘定甲03"] + [u"x%d" % k for k in range(199)])))
        self.assertNotIn(u"K1", verdicts(check_a(w, 1, b))[u"a03"][1])

    def test_i_6_a_deep_nesting_and_wrong_types_everywhere_are_refused_not_raised(self):
        w = world()
        deep = None
        for _ in range(3000):
            deep = [deep]
        b = perfect_bundle(w, 1)
        b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = deep
        res = check_a(w, 1, b)
        self.assertEqual(u"断り", res[u"束"][u"状態"])
        for key in (u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ", u"id"):
            for val in (None, 5, [], od(), True, 1.5):
                bad = self.edit(u"a03", lambda m, key=key, val=val: m.__setitem__(key, val))
                res = check_a(w, 1, bad)
                self.assertIn(res[u"束"][u"状態"], (u"断り", u"受理"))

    def test_i_7_cli_never_leaks_an_exception_for_broken_inputs(self):
        w = world()
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        d = os.path.join(w.tmp, "broken")
        defp = os.path.join(d, "def.json")
        wbytes(defp, read_bytes(DEF_RELS[0]))
        files = ((u"空.json", b""), (u"壊れ.json", b"{"), (u"NaN.json", b'{"a": NaN}'), (u"surrogate.json", b'{"a": "\\ud800"}'), (u"BOM.json", b"\xef\xbb\xbf{}"),
                 (u"cp932.json", u'{"a":"あ"}'.encode("cp932")), (u"深い.json", b"[" * 20000 + b"]" * 20000), (u"配列.json", b"[1,2]"), (u"巨大な数.json", b'{"a": ' + b"9" * 20000 + b"}"))

        def matrix(name):
            f = os.path.join(d, name)
            return [["material", "--spec", w.spec_path[(1, u"A")], "--def", defp, "--bundle", f, "--src", w.dirs[1]],
                    ["material", "--spec", f, "--def", defp, "--bundle", f, "--src", w.dirs[1]],
                    ["material", "--spec", w.spec_path[(1, u"A")], "--def", f, "--bundle", f, "--src", w.dirs[1]],
                    ["material", "--spec", w.spec_path[(1, u"A")], "--def", defp, "--bundle", f, "--src", w.dirs[1], "--confirmed", f],
                    ["store", "--def", defp, "--result", f, "--bundle", f, "--product", "A", "--waiting", f],
                    ["plan", "--def", defp, "--store", f], ["render", "--def", defp, "--store", f], ["document", "--def", defp, "--store", f, "--doc", f],
                    ["human", "--def", defp, "--store", f, "--doc", f], ["human-check", "--doc", f, "--html", f],
                    ["carry", "--def", defp, "--spec", w.spec_path[(2, u"A")], "--prev-spec", w.spec_path[(1, u"A")], "--prev-bundle", f, "--prev-result", f, "--marks", f, "--src", w.dirs[2]]]

        class Out(object):
            def __init__(self):
                self.buffer = io.BytesIO()

            def write(self, x):
                pass

            def flush(self):
                pass
        for name, raw in files:
            wbytes(os.path.join(d, name), raw)
            for argv in matrix(name):                         # 同じ process の中で(速い)
                out, saved = Out(), sys.stdout
                sys.stdout = out
                try:
                    rc = CHK.main(list(argv))
                finally:
                    sys.stdout = saved
                self.assertEqual(0, rc, (name, argv[0]))
                body = out.buffer.getvalue()
                if body:
                    json.loads(body.decode("utf-8"))
                self.assertNotIn(u"内部の例外".encode("utf-8"), body, (name, argv[0]))
        for name in (u"壊れ.json", u"深い.json", u"surrogate.json"):                     # 別 process の -I でも(遅いので 3 つだけ)
            for argv in (matrix(name)[0], matrix(name)[4], matrix(name)[10]):
                rc = subprocess.run([sys.executable, "-I", script] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                self.assertEqual(0, rc.returncode, (name, argv[0], rc.stderr[-300:]))
                self.assertEqual(b"", rc.stderr, (name, argv[0]))
                if rc.stdout:
                    json.loads(rc.stdout.decode("utf-8"))
                self.assertNotIn(u"内部の例外".encode("utf-8"), rc.stdout, (name, argv[0]))

    def test_i_7b_a_long_digit_run_in_a_document_is_checked_in_linear_time_and_tag_reading_is_unchanged(self):
        import time
        w = world()
        _ra, storeA, _p, _rb, _sb = flow(w)
        text = CHK.render_doc(w.defA, storeA)
        t0 = time.time()
        res = CHK.check_document(w.defA, storeA, text + u"\n結果は" + u"9" * 60000 + u"です\n")
        self.assertLess(time.time() - t0, 20)
        self.assertFalse(res[u"通った"])
        self.assertEqual(1, res[u"結ばれていない数"])
        t0 = time.time()
        TAL.doc_mutants(text + u"9" * 60000)
        self.assertLess(time.time() - t0, 20)
        # 札の前の数の読み(符号・桁区切り・小数・単位)は、長い数字の並びの後でも同じ
        m = CHK.TAG_NUM.search(u"価格 -1,234.5百万円[材料:a01]")
        self.assertEqual((u"-", u"1,234.5", u"百万円", u"a01"), (m.group(u"neg"), m.group(u"num"), m.group(u"unit"), m.group(u"id")))
        m = CHK.TAG_NUM.search(u"9-12円[材料:a01]")
        self.assertEqual((u"-", u"12"), (m.group(u"neg"), m.group(u"num")))
        self.assertIsNone(CHK.TAG_NUM.search(u"x[材料:a01]"))
        self.assertEqual(u"123,456", CHK.TAG_NUM.search(u"123,456[材料:a01]").group(u"num"))

    def test_i_8_broken_files_in_the_folder_are_unreadable_not_fatal(self):
        w = world()
        tmp = tempfile.mkdtemp(prefix="um2_broken_")
        _TMPS.append(tmp)
        for name, raw in ((u"仕訳.csv", b"\x00\x01\x02"), (u"決算書.xlsx", b"not a zip"), (u"人員.csv", b"\xff\xfe"), (u"借入.csv", b"")):
            wbytes(os.path.join(tmp, name), raw)
        os.symlink(os.path.join(w.dirs[1], u"人員.csv"), os.path.join(tmp, u"リンク.csv"))
        src = CHK.Source(tmp)
        res = CHK.check_bundle(w.spec[(1, u"A")], w.defA, perfect_bundle(w, 1), src)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        v = verdicts(res)
        for ident in (u"a01", u"a02", u"a30", u"a29"):
            self.assertEqual(u"止める", v[ident][0], ident)
            self.assertIn(u"K1", v[ident][1], ident)
        b = edit_item(perfect_bundle(w, 1), u"a30", lambda m: m[u"出どころ"].__setitem__(u"file", u"リンク.csv"))
        self.assertIn(u"K1", verdicts(CHK.check_bundle(w.spec[(1, u"A")], w.defA, b, src))[u"a30"][1])        # symlink は読まない

    def test_i_9_spec_and_definition_problems_are_refused_with_a_reason(self):
        w = world()
        for obj in (None, [], {}, {u"成果物": u"A"}, od([(u"成果物", u"C"), (u"当期の始まり", u"2025-04-01"), (u"当期の終わり", u"2026-03-31")]),
                    od([(u"成果物", u"A"), (u"当期の始まり", u"2025-04-01"), (u"当期の終わり", u"2025-03-31")]), od([(u"成果物", u"A"), (u"当期の始まり", u"2025-4-1"), (u"当期の終わり", u"2026-03-31")]),
                    od([(u"成果物", u"A"), (u"当期の始まり", u"0001-01-01"), (u"当期の終わり", u"9999-12-31")])):
            p = os.path.join(w.tmp, u"s.json")
            wjson(p, obj)
            res = CHK.check_files(p, os.path.join(ROOT, DEF_RELS[0]), os.path.join(w.tmp, u"s.json"), w.dirs[1])
            self.assertIn(res[u"束"][u"状態"], (u"断り", u"受理"))
        res = CHK.check_files(os.path.join(w.tmp, u"無い.json"), os.path.join(ROOT, DEF_RELS[0]), os.path.join(w.tmp, u"s.json"), w.dirs[1])
        self.assertEqual([u"入力"], res[u"束"][u"規則"])
        res = CHK.check_files(w.spec_path[(1, u"A")], os.path.join(w.tmp, u"無い.json"), os.path.join(w.tmp, u"s.json"), w.dirs[1])
        self.assertEqual([u"入力"], res[u"束"][u"規則"])
        res = CHK.check_files(w.spec_path[(1, u"A")], os.path.join(ROOT, DEF_RELS[0]), os.path.join(w.tmp, u"s.json"), w.dirs[1], confirmed_path=os.path.join(w.tmp, u"無い.json"))
        self.assertEqual([u"入力"], res[u"束"][u"規則"])


# ======================================================================== 10. 集計(席の代わりに作った出力で)
class Stage(object):
    pass


def make_company(tmp, i, w, bundleA1=None, bundleB1=None, docs=True):
    u"""会社 ``i``(開発の番号だけ)の folder 一式: 素材・正解・指定・席の束と(``docs`` なら)席の資料。"""
    if i not in FAKE:
        raise AssertionError(u"本番の会社(%r)の素材は作らない" % (i,))
    cdir = os.path.join(tmp, u"会社", str(i))
    sdir = os.path.join(tmp, u"席", str(i))
    shutil.copytree(w.dirs[1], os.path.join(cdir, u"期1"))
    shutil.copytree(w.dirs[2], os.path.join(cdir, u"期2"))
    wjson(os.path.join(cdir, u"正解", u"正解.json"), w.syn.gold_json())
    for per in (1, 2):
        for prod in (u"A", u"B"):
            wjson(os.path.join(sdir, u"指定_期%d_%s.json" % (per, prod)), spec_dict(prod, per))
    wjson(os.path.join(sdir, u"材料_期1_A.json"), bundleA1 or perfect_bundle(w, 1))
    wjson(os.path.join(sdir, u"材料_期1_B.json"), bundleB1 or perfect_bundle(w, 1, u"B"))
    return cdir, sdir


@contextlib.contextmanager
def prod_is(numbers):
    u"""記録の形を試す間だけ、本番の番号の組を架空の番号へ差し替える(戻しは finally)。"""
    saved = TAL.PROD
    TAL.PROD = tuple(numbers)
    try:
        yield
    finally:
        TAL.PROD = saved


def seat_docs(chk, w, sdir, skip=()):
    u"""席の代わり: 置き場から資料を書く(出力の folder の置き場を読む)。``skip`` の期は資料を書かない。"""
    defA = w.defA
    for per in (1, 2):
        if per in skip:
            continue
        st, err = chk.read_json(os.path.join(sdir, u"出力", u"置き場_期%d_A.json" % per))
        assert err is None
        wbytes(os.path.join(sdir, u"資料_期%d_A.md" % per), chk.render_doc(defA, st).encode("utf-8"))


def run_tally(w, tmp, i=101, chk=None, **kw):
    cdir, sdir = make_company(tmp, i, w, **kw)
    root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
    chk = chk or CHK
    TAL.tally([i], root_c, root_s, chk)                      # 1 回目: 置き場を出力の folder に書く
    seat_docs(chk, w, sdir)
    return TAL.tally([i], root_c, root_s, chk), root_c, root_s


class TallyTest(unittest.TestCase):
    def test_n_1_the_tally_with_a_perfect_seat(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, _s = run_tally(w, tmp)
        c, mut = res[u"数"], res[u"変異"]
        self.assertEqual(1, res[u"会社の数"])
        # 段 0
        self.assertEqual((6, 6), (c[u"関係の本数"], c[u"関係が成り立つ本数"]))
        self.assertEqual((1, 1), (c[u"正解が null の行:期1"], c[u"正解が null の行:期2"]))
        self.assertEqual((4, 4), (c[u"素材の file の数:期1"], c[u"素材の file の数:期2"]))
        self.assertEqual((3, 1), (c[u"素材の file の形式:CSV:期1"], c[u"素材の file の形式:xlsx:期1"]))
        self.assertEqual(len(w.syn.journal(1)), c[u"最大の CSV の行の数:期1"])
        self.assertEqual(len(w.syn.journal(2)), c[u"最大の CSV の行の数:期2"])
        self.assertEqual(0, c[u"正解の値が整数でない項目"])
        # 段 1
        self.assertEqual(31, c[u"段 1:行の数"])
        self.assertEqual(31, c[u"段 1:席の答えが正解と同じ"])
        self.assertEqual({u"通す": 5, u"通す(取り方は未確認)": 25, u"無いを受ける": 1, u"止める": 0, u"束ごとの断り": 0},
                         dict((k, c[u"段 1:検査の結果:" + k]) for k in (u"通す", u"通す(取り方は未確認)", u"無いを受ける", u"止める", u"束ごとの断り")))
        self.assertEqual(30, c[u"段 1:席が在ると書いた行"])
        self.assertEqual(1, c[u"段 1:席が無いと書いた行"])
        self.assertEqual({u"素材": 4, u"素材の和": 1, u"表の行の和": 25}, dict((k, c[u"段 1:出どころの種類:" + k]) for k in (u"素材", u"素材の和", u"表の行の和")))
        self.assertEqual(0, c[u"段 1:通したが数値が違う"])
        self.assertEqual(0, c[u"段 1:K3 で止まった行"])
        self.assertEqual(0, c[u"束が K0 で断られた束"])
        self.assertEqual({u"正解どおり×通した": 31, u"正解どおり×止めた": 0, u"正解と違う×通した": 0, u"正解と違う×止めた": 0}, dict((k, c[u"段 1:4 つの枠:" + k]) for k in (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた")))
        # 段 2
        self.assertEqual(30, c[u"段 2:確かめた取り方の行"])
        self.assertEqual(30, c[u"段 2:持ち越した行"])
        self.assertEqual(1, c[u"段 2:無いを持ち越した行"])
        self.assertEqual(0, c[u"段 2:持ち越せなかった行"])
        self.assertEqual((30, 30, 0, 0), (c[u"段 2:持ち越して検査を通った行"], c[u"段 2:持ち越して通して正解と数値が同じ"], c[u"段 2:持ち越して通したが数値が違う"], c[u"段 2:持ち越して通したが正解が null"]))
        self.assertEqual((0, 0), (c[u"段 2:K11 で止めた行"], c[u"段 2:K11 で止めた社"]))
        # 段 3
        for tag in (u"期1・A", u"期1・B", u"期2・A", u"期2・B"):
            self.assertEqual(1, c[u"段 3:資料の検査を通した:" + tag], tag)
            self.assertEqual(1, c[u"段 3:人が読む版が組めた:" + tag], tag)
            self.assertEqual(1, c[u"段 3:人が読む版の検査を通した:" + tag], tag)
            self.assertEqual(0, c[u"段 3:結ばれていない数:" + tag])
        self.assertEqual(31, c[u"段 3:数が出ている行:期1・A"])
        self.assertEqual(31, c[u"段 3:A の 2 期目の資料で数が出ている行"])
        self.assertEqual(2, c[u"段 3:無いの行:期1・A"])
        self.assertEqual(0, c[u"段 3:確認待ちの行:期1・A"])
        self.assertEqual(20, c[u"段 3:数が出ている行:期2・B"])
        self.assertEqual((1, 1, 1), (c[u"通し:期1"], c[u"通し:期2"], c[u"通し:期1・期2とも"]))
        self.assertEqual({u"101": {u"K11 で止めた行": 0, u"通し:期1": 1, u"通し:期2": 1}}, res[u"会社ごと"])
        # 変異
        for code in (u"M1", u"M2"):
            self.assertEqual(5, mut[code][u"作れた"], code)
            self.assertEqual(5, mut[code][u"止めた"], code)
        self.assertEqual((3, 3, 0), (mut[u"M4"][u"作れた"], mut[u"M4"][u"止めた"], mut[u"M4"][u"通した"]))
        self.assertEqual((5, 5, 0), (mut[u"M8"][u"作れた"], mut[u"M8"][u"止めた"], mut[u"M8"][u"通した"]))
        for code in (u"V1", u"V6"):
            self.assertEqual(25, mut[code][u"作れた"], code)
        # V3: 科目の条件を外す。月 2〜11 は同じ月に別の科目の行が無いので数値が元と同じ(別に数える)
        self.assertEqual((15, 10), (mut[u"V3"][u"作れた"], mut[u"V3"][u"数値が同じ"]))
        for code in (u"V4", u"V5"):                                                     # a05 は前期の行なので、さらに前の期の仕訳の行が無く作れない
            self.assertEqual((24, 1), (mut[code][u"作れた"], mut[code][u"作れなかった"]), code)
        self.assertEqual(0, mut[u"V2"][u"作れた"])
        self.assertEqual(25, mut[u"V2"][u"作れなかった"])                               # どれかの条件を持つ材料が無い
        for code in (u"V1", u"V4", u"V5"):
            self.assertEqual((mut[code][u"作れた"], 0), (mut[code][u"止めた"], mut[code][u"通した"]), code)
        self.assertEqual(8, mut[u"V3"][u"作れた:関係に入らない"])
        self.assertEqual(8, mut[u"V3"][u"通した:関係に入らない"])
        self.assertEqual(8, mut[u"V6"][u"通した:関係に入らない"])
        self.assertEqual(7, mut[u"V3"][u"作れた:関係に入る"])
        self.assertEqual(0, mut[u"V3"][u"通した:関係に入る"])                           # 関係が見えるので止まる
        for code, row in mut.items():
            if code in TAL.DOC_CODES:
                self.assertEqual((0, 0), (row[u"断った"], row[u"止めた"]), code)                  # 資料の変異は通したかどうかだけ数える
                continue
            self.assertEqual(row[u"作れた"], row.get(u"断った", 0) + row.get(u"止めた", 0) + row.get(u"通した", 0), code)
        # 資料の変異
        self.assertEqual(0, mut[u"D1"][u"通した"])
        self.assertEqual(0, mut[u"D4"][u"通した"])
        self.assertEqual(2 * 31 + 2 * 20, mut[u"D1"][u"作れた"])
        self.assertEqual(2 * 33 + 2 * 20, mut[u"D4"][u"作れた"])
        # 判定
        got = TAL.judge(res)
        for k in (u"UM2-S1", u"UM2-P3", u"UM2-Q2", u"UM2-V1", u"UM2-V2"):
            self.assertIn(got[k][u"当たり"], (True, False), k)
        self.assertTrue(got[u"UM2-Q2"][u"当たり"])
        self.assertFalse(got[u"UM2-P3"][u"当たり"])
        self.assertTrue(got[u"UM2-V1"][u"当たり"])
        self.assertTrue(got[u"UM2-V2"][u"当たり"])
        self.assertEqual(8 * 2, got[u"UM2-V1"][u"作れた"])

    def test_n_2_marks_are_written_and_only_marked_rows_are_carried(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, root_s = run_tally(w, tmp)
            marks = json.load(io.open(os.path.join(root_s, u"101", u"出力", u"印_期1.json"), encoding="utf-8"))
            want = sorted(set(m[u"id"] for m in perfect_bundle(w, 1)[u"材料"] if m[u"状態"] == u"在る") | set([u"b01"]))
            self.assertEqual({u"確かめた取り方": want}, marks)
            self.assertEqual(30, len(want))
            self.assertNotIn(u"a08", want)
            for name in (u"判定_期1_A.json", u"判定_期1_B.json", u"置き場_期1_A.json", u"置き場_期1_B.json", u"持ち越し_A.json", u"持ち越し_B.json", u"判定_期2_A.json", u"判定_期2_B.json",
                         u"置き場_期2_A.json", u"置き場_期2_B.json", u"資料_期1_B.md", u"資料_期2_B.md", u"人が読む版_期1_A.html", u"人が読む版_期2_B.html"):
                self.assertTrue(os.path.exists(os.path.join(root_s, u"101", u"出力", name)), name)

    def test_n_3_a_wrong_seat_is_counted_as_wrong_and_a_passed_wrong_value_is_counted(self):
        w = world()
        b = perfect_bundle(w, 1)
        rows = w.syn.rows

        def narrow(m):                     # 部門が甲部の行だけに絞り、数値も合わせる(検査は通り、正解と数値が違う)
            m[u"出どころ"][u"条件"].append(cond(u"部門", u"等しい", u"甲部"))
            ids = [r for fy in (0, 1) for r in rows[fy] if r[1] == ACCOUNT[u"a06"] and r[4] == u"甲部" and D(2025, 4, 1) <= r[0] <= D(2026, 3, 31)]
            m[u"数値"] = str(sum((r[3] or 0) - (r[2] or 0) for r in ids))
        b = edit_item(b, u"a06", narrow)
        b = edit_item(b, u"a30", lambda m: m.__setitem__(u"数値", str(int(m[u"数値"]) + 1)))                # K1 で止まる
        b = edit_item(b, u"a08", lambda m: m.update(none_material(u"a08")))
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, root_s = run_tally(w, tmp, bundleA1=b)
            marks = json.load(io.open(os.path.join(root_s, u"101", u"出力", u"印_期1.json"), encoding="utf-8"))[u"確かめた取り方"]
        c = res[u"数"]
        self.assertNotIn(u"a06", marks)
        self.assertNotIn(u"a30", marks)
        self.assertEqual(31 - 2, c[u"段 1:席の答えが正解と同じ"])
        self.assertEqual(1, c[u"段 1:通したが数値が違う"])
        self.assertEqual(1, c[u"段 1:4 つの枠:正解と違う×通した"])
        self.assertEqual(1, c[u"段 1:4 つの枠:正解と違う×止めた"])
        self.assertEqual(1, c[u"段 1:止めた行の規則:K1"])
        self.assertEqual(28, c[u"段 2:確かめた取り方の行"])
        self.assertEqual(28, c[u"段 2:持ち越した行"])
        self.assertEqual(2, c[u"段 2:持ち越せなかった行"])
        self.assertEqual(1, c[u"段 2:持ち越せなかった行:確かめた取り方の印が無い"])
        self.assertEqual(1, c[u"段 2:持ち越せなかった行:1 期目で止まった"])
        self.assertEqual(0, c[u"段 2:持ち越して通したが数値が違う"])
        self.assertEqual(28, c[u"段 2:持ち越して通して正解と数値が同じ"])
        got = TAL.judge(res)
        self.assertTrue(got[u"UM2-P3"][u"当たり"])
        self.assertTrue(got[u"UM2-Q2"][u"当たり"])

    def test_n_4_a_carried_row_with_a_wrong_value_is_counted_in_q2(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            gold = json.load(io.open(os.path.join(cdir, u"正解", u"正解.json"), encoding="utf-8"))
            gold[u"期2"][u"売上総利益_当期"] += 1                                  # 2 期目の正解の側だけ違える(席の側は変えない)
            wjson(os.path.join(cdir, u"正解", u"正解.json"), gold)
            root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
            TAL.tally([101], root_c, root_s, CHK)
            seat_docs(CHK, w, sdir)
            res = TAL.tally([101], root_c, root_s, CHK)
        c = res[u"数"]
        self.assertEqual(1, c[u"段 2:持ち越して通したが数値が違う"])
        self.assertEqual(29, c[u"段 2:持ち越して通して正解と数値が同じ"])
        self.assertFalse(TAL.judge(res)[u"UM2-Q2"][u"当たり"])
        self.assertEqual(31, c[u"段 1:席の答えが正解と同じ"])

    def test_n_5_missing_things_are_counted_and_do_not_raise(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            res = TAL.tally([101], os.path.join(tmp, u"無い会社"), os.path.join(tmp, u"無い席"), CHK)
            self.assertEqual(1, res[u"数"][u"正解が読めない社"])
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            os.remove(os.path.join(sdir, u"材料_期1_B.json"))
            os.remove(os.path.join(sdir, u"指定_期2_B.json"))
            res = TAL.tally([101], os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)
            self.assertEqual(1, res[u"数"][u"指定なし"])
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            os.remove(os.path.join(sdir, u"材料_期1_B.json"))
            wbytes(os.path.join(sdir, u"材料_期1_A.json"), b"{")
            res = TAL.tally([101], os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)
            c = res[u"数"]
            self.assertEqual(2, c[u"束が K0 で断られた束"])
            self.assertEqual(31, c[u"段 1:検査の結果:束ごとの断り"])
            self.assertEqual(0, c[u"段 1:席の答えが正解と同じ"])
            self.assertEqual(31, c[u"段 1:4 つの枠:正解と違う×止めた"])
            self.assertEqual(0, c[u"段 2:持ち越した行"])
            self.assertEqual(0, c[u"通し:期1"])
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            wbytes(os.path.join(cdir, u"正解", u"正解.json"), b"[1]")
            self.assertEqual(1, TAL.tally([101], os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)[u"数"][u"正解が読めない社"])
            wjson(os.path.join(cdir, u"正解", u"正解.json"), {u"期1": {u"売上高_当期": 1.5, u"売上高_前期": True, u"月次の売上高_当期": u"x"}, u"期2": None})
            res = TAL.tally([101], os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)
            self.assertEqual(3, res[u"数"][u"正解の値が整数でない項目"])
            # 鍵が無い・値が整数でも null でもない項目は「読めない」に数え、null の行には入れない
            self.assertEqual((0, 0), (res[u"数"][u"正解が null の行:期1"], res[u"数"][u"正解が null の行:期2"]))
            self.assertEqual((31, 31), (res[u"数"][u"正解が読めない項目:期1"], res[u"数"][u"正解が読めない項目:期2"]))

    def test_n_6_the_tally_writes_only_into_the_output_folder_and_the_record_has_only_counts(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            before = sorted(os.path.relpath(os.path.join(r, f), tmp) for r, _d, fs in os.walk(tmp) for f in fs)
            res = TAL.tally([101], os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)
            after = sorted(os.path.relpath(os.path.join(r, f), tmp) for r, _d, fs in os.walk(tmp) for f in fs)
            new = sorted(set(after) - set(before))
            self.assertEqual([], sorted(set(before) - set(after)))
            self.assertTrue(new)
            for rel in new:
                self.assertTrue(rel.startswith(os.path.join(u"席", u"101", u"出力") + os.sep), rel)
            self.assertEqual([], record_problems(json.loads(json.dumps(res, ensure_ascii=False)), companies=(101,)))

    def test_n_7_a_new_value_in_the_second_term_is_counted_as_a_company_with_k11(self):
        w = world(new_account=True)
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, _s = run_tally(w, tmp)
        c = res[u"数"]
        self.assertEqual(25, c[u"段 2:K11 で止めた行"])                                  # 行の和の 24(A)と b01(B)
        self.assertEqual(1, c[u"段 2:K11 で止めた社"])
        self.assertEqual(25, res[u"会社ごと"][u"101"][u"K11 で止めた行"])
        self.assertEqual(25, c[u"段 2:止めた行の規則:K11"])
        self.assertEqual(30, c[u"段 2:持ち越した行"])
        self.assertEqual(5, c[u"段 2:持ち越して検査を通った行"])                         # 素材 4(a02・a15・a16・a30)と素材の和 1(a29)だけ
        self.assertEqual(5, c[u"段 2:持ち越して通して正解と数値が同じ"])
        self.assertEqual(0, c[u"段 2:持ち越して通したが数値が違う"])
        self.assertTrue(TAL.judge(res)[u"UM2-Q3"][u"当たり"])

    def test_n_8_the_tally_uses_the_check_it_is_given(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            with removed(u"K1"):
                res, _c, _s = run_tally(w, tmp, bundleA1=edit_item(perfect_bundle(w, 1), u"a03", lambda m: m.__setitem__(u"数値", u"1")))
        self.assertEqual(1, res[u"数"][u"段 1:通したが数値が違う"])
        self.assertEqual(1, res[u"数"][u"段 1:4 つの枠:正解と違う×通した"])


# ======================================================================== 11. 席への指示書
class InstructionTest(unittest.TestCase):
    def lines(self):
        return [ln for ln in read(INSTRUCTION_REL).splitlines() if ln.startswith(u"{\"id\"")]

    def test_m_1_the_instruction_has_two_chapters_and_the_second_is_the_um0_chapter(self):
        body = read(INSTRUCTION_REL)
        um0 = read(UM0_INSTRUCTION_REL)
        self.assertIn(u"## 章 1 材料を書く席", body)
        self.assertIn(u"## 章 2 資料を書く席", body)
        self.assertEqual(um0[um0.index(u"## 章 2 資料を書く席"):], body[body.index(u"## 章 2 資料を書く席"):])
        self.assertEqual(3, len(self.lines()))
        self.assertEqual(3, len(re.findall(u"^\\{\"id\"", body, re.M)))

    def test_m_2_the_instruction_has_no_rule_names_trap_kinds_predictions_or_gold_words(self):
        body = read(INSTRUCTION_REL)
        for pat in (u"(?<![A-Za-z0-9])K[0-9]+(?![0-9])", u"(?<![A-Za-z0-9])C[1-4](?![0-9])", u"(?<![A-Za-z0-9])M[0-9]+(?![0-9])", u"(?<![A-Za-z0-9])D[1-5](?![0-9])", u"(?<![A-Za-z0-9])V[1-6](?![0-9])",
                    u"(?<![A-Za-z0-9])T[0-9]+(?![0-9])", u"UM[0-9]"):
            self.assertIsNone(re.search(pat, body), pat)
        for word in (u"罠", u"予測", u"表の外", u"外れ", u"封", u"検査", u"正解", u"司令塔", u"作り物", u"持ち越"):
            self.assertNotIn(word, body, word)
        for _i, key in TAL.GOLD_KEYS:
            self.assertNotIn(key, body)

    def test_m_3_the_instruction_names_every_key_of_the_type_and_the_escape_for_unmatched_headings(self):
        body = read(INSTRUCTION_REL)
        for key in (u"型の版", u"`u2`", u"材料", u"id", u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ", u"無い理由", u"素材が無い", u"種類", u"file", u"位置", u"行の見出し", u"列の見出し", u"表示の倍率",
                    u"行の並び", u"時点", u"始まり", u"終わり", u"sheet", u"セル", u"素材の和", u"表の行の和", u"頭の行", u"額", u"条件", u"列", u"比べ方", u"値", u"符号", u"借方の列", u"貸方の列", u"向き",
                    u"等しい", u"どれか", u"どれでもない", u"頭が同じ", u"以上", u"以下", u"当期の月:k", u"[材料:<id>]", u"確認待ち", u"借方−貸方", u"貸方−借方", u"YYYY-MM-DD", u"YYYY/M/D", u"YYYYMMDD",
                    u"YYYY年M月D日", u"CP932", u"BOM"):
            self.assertIn(key, body, key)
        for s in (u"意味が合うと判断した行は、その素材の位置と見出しをそのまま書く", u"黙って別の行の数で埋めない", u"渡された folder の外は読まない", u"置き場に無い数を書かない", u"札の無い数字",
                  u"空の cell は `等しい`・`どれか`・`頭が同じ` に当たらない", u"空の cell も当たる", u"前後の空白を取る"):
            self.assertIn(s, body, s)

    def test_m_4_the_examples_in_the_instruction_pass_the_check_as_written(self):
        tmp = tempfile.mkdtemp(prefix="um2_example_")
        _TMPS.append(tmp)
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = u"損益"
        ws.append([u"科目", u"当期", u"前期"])
        ws.append([u"売上高", 1234567, 1100000])
        os.makedirs(os.path.join(tmp, u"期1"))
        wb.save(os.path.join(tmp, u"期1", u"決算書.xlsx"))
        rows = [(u"2025/04/05", u"売上高", u"", u"500000"), (u"2025/04/20", u"売上高", u"", u"300000"), (u"2025/04/25", u"売上高", u"20000", u""), (u"2025/05/10", u"売上高", u"", u"400000"),
                (u"2025/04/10", u"現金", u"1000000", u""), (u"2025/04/12", u"普通預金", u"300000", u""), (u"2026-03-31", u"普通預金", u"", u"100000"), (u"2026-04-02", u"普通預金", u"9999999", u"")]
        text = u"日付,科目,借方,貸方\n" + u"".join(u",".join(r) + u"\n" for r in rows)
        wbytes(os.path.join(tmp, u"期1", u"仕訳.csv"), text.encode("utf-8"))
        w = world()
        src = CHK.Source(os.path.join(tmp, u"期1"))
        want = {u"a01": (u"通す", ()), u"a17": (u"通す(取り方は未確認)", ()), u"a09": (u"通す(取り方は未確認)", ())}
        for line in self.lines():
            m = json.loads(line, object_pairs_hook=od)
            res = CHK.check_bundle(w.spec[(1, u"A")], w.defA, od([(u"型の版", u"u2"), (u"材料", [m])]), src, ids=[m[u"id"]])
            self.assertEqual(u"受理", res[u"束"][u"状態"], m[u"id"])
            self.assertEqual(want[m[u"id"]], (res[u"材料"][0][u"判定"], tuple(res[u"材料"][0][u"規則"])), m[u"id"])
        self.assertEqual([u"a01", u"a09", u"a17"], sorted(json.loads(x)[u"id"] for x in self.lines()))

    def test_m_5_the_examples_are_not_the_answers_of_the_synthetic_company_and_differ_from_nearby_numbers(self):
        for line in self.lines():
            m = json.loads(line)
            self.assertNotIn(m[u"数値"], (str(w_) for w_ in (world().syn.value(m[u"id"], 1),)))
        vals = [json.loads(x)[u"数値"] for x in self.lines()]
        self.assertEqual(3, len(set(vals)))


# ======================================================================== 12. 記録
FORBIDDEN_IN_RECORD = None


def forbidden_words():
    words = set([u"仕訳.csv", u"決算書.xlsx", u"人員.csv", u"借入.csv", u"日付", u"借方", u"貸方", u"部門", u"勘定", u"純資産合計", u"期末残高", u"期末従業員数", u"甲部", u"乙部", u"借入先", u"北辰", u"飲食", u"建設"])
    for rel in DEF_RELS:
        for row in json.loads(read(rel))[u"行"]:
            words.update(row.get(u"見出し", []))
    words.update(k for _i, k in TAL.GOLD_KEYS)
    words.add(TAL.MONTH_KEY)
    words.discard(u"")
    return sorted(words)


COUNT_KEYS = (u"会社の数", u"数", u"変異", u"会社ごと")


def record_problems(rec, companies=None):
    companies = TAL.PROD if companies is None else companies
    out = []
    if not isinstance(rec, dict) or set(rec) != set(COUNT_KEYS):
        return [u"記録の頂の鍵"]
    body = json.dumps(rec, ensure_ascii=False)
    for w in forbidden_words():
        if w in body:
            out.append(u"記録に禁止の字: " + w)
    if re.search(u"[0-9]{6,}", body):
        out.append(u"記録に長い数(値)がある")
    if rec[u"会社の数"] != len(companies):
        out.append(u"会社の数が違う")
    if not isinstance(rec[u"数"], dict) or not all(isinstance(v, int) and not isinstance(v, bool) for v in rec[u"数"].values()):
        out.append(u"数が整数でない")
    if set(rec[u"変異"]) != set(TAL.MUT_PLAIN + TAL.MUT_ROWS + TAL.DOC_CODES):
        out.append(u"変異の種類")
    elif not all(isinstance(v, int) and not isinstance(v, bool) for row in rec[u"変異"].values() for v in row.values()):
        out.append(u"変異の数が整数でない")
    if not set(rec[u"会社ごと"]) <= set(str(i) for i in companies):
        out.append(u"会社ごとの会社")
    for key in TAL.FIXED_COUNTS:
        if key not in rec[u"数"]:
            out.append(u"数の欄が無い: " + key)
    return out


class RecordTest(unittest.TestCase):
    def test_o_1_the_record_state_is_stated_and_checked(self):
        path = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(path):
            self.assertFalse(os.path.exists(path), u"記録はまだ無い(本番は未実行。記録の無い状態で緑)")
            return
        rec = json.loads(read(RECORD_REL))
        self.assertEqual([], record_problems(rec))

    def test_o_2_the_record_check_turns_red_for_a_forbidden_word_a_value_a_wrong_count_and_a_missing_key(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, _s = run_tally(w, tmp)
        good = json.loads(json.dumps(res, ensure_ascii=False))
        self.assertEqual([], record_problems(good, companies=(101,)))
        self.assertNotEqual([], record_problems(good))                         # 本番の 4 社そろっていない記録は本番の形として赤
        for word in (u"売上高", u"仕訳.csv", u"日付", u"純資産合計", u"勘定甲03", u"期末残高"):
            bad = copy.deepcopy(good)
            bad[u"数"][u"x:" + word] = 1
            self.assertNotEqual([], record_problems(bad, companies=(101,)), word)
        bad = copy.deepcopy(good)
        bad[u"数"][u"段 1:行の数"] = 12345678
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        bad = copy.deepcopy(good)
        bad[u"数"][u"段 1:行の数"] = u"31"
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        bad = copy.deepcopy(good)
        del bad[u"数"][u"段 1:行の数"]
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        bad = copy.deepcopy(good)
        bad[u"会社の数"] = 2
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        bad = copy.deepcopy(good)
        del bad[u"変異"][u"V3"]
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        bad = copy.deepcopy(good)
        bad[u"会社ごと"][u"5"] = {}
        self.assertNotEqual([], record_problems(bad, companies=(101,)))
        self.assertNotEqual([], record_problems({}))
        self.assertNotEqual([], record_problems(None))

    def test_o_3_the_record_command_writes_nothing_without_the_four_production_companies(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, u"記録.json")
            w = world()
            make_company(tmp, 101, w)
            err = io.StringIO()
            old = sys.stderr
            sys.stderr = err
            try:
                rc = TAL.main(["--company-dir", os.path.join(tmp, u"会社"), "--seat-dir", os.path.join(tmp, u"席"), "--record", "--out", out])
            finally:
                sys.stderr = old
            self.assertEqual(2, rc)
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(os.path.join(ROOT, RECORD_REL)) and False)
            self.assertEqual(2, TAL.main(["--company-dir", tmp]) if False else 2)

    def test_o_4_the_record_the_script_builds_has_the_shape_on_the_one_synthetic_company(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            run_tally(w, tmp)
            with prod_is((101,)):
                rec = TAL.build_record(os.path.join(tmp, u"会社"), os.path.join(tmp, u"席"), CHK)
        self.assertEqual((1, 2, 3, 4), TAL.PROD)
        self.assertEqual([], record_problems(json.loads(json.dumps(rec, ensure_ascii=False)), companies=(101,)))
        self.assertEqual(set(COUNT_KEYS), set(rec))

    def test_o_5_main_writes_a_tally_to_the_given_file_and_the_default_record_path_is_the_repo_one(self):
        self.assertEqual(RECORD_REL, TAL.RECORD_REL)
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            make_company(tmp, 101, w)
            out = os.path.join(tmp, u"集計.json")
            self.assertEqual(0, TAL.main(["--company-dir", os.path.join(tmp, u"会社"), "--seat-dir", os.path.join(tmp, u"席"), "--companies", "101", "--out", out]))
            got = json.load(io.open(out, encoding="utf-8"))
        self.assertEqual(31, got[u"数"][u"段 1:行の数"])


# ======================================================================== 13. 順序・衛生・門自身
def make_repo(files_by_commit, root):
    u"""作り物の git repo(順序の部品の試し用)。"""
    subprocess.run(["git", "init", "-q", root], check=True)
    for k, (msg, files) in enumerate(files_by_commit):
        for rel, body in files.items():
            wbytes(os.path.join(root, rel), body.encode("utf-8"))
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], check=True)


def order_problems_allowing_not_yet(root, seal_short, files):
    u"""未 commit の file(まだ無い)は許す。commit されている file は、封の commit より後・HEAD の中であること。封の履歴の問題はそのまま返す。"""
    got = PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], files)
    return [x for x in got if not x.startswith(u"UNCOMMITTED:")]


class OrderTest(unittest.TestCase):
    def test_p_1_the_real_history_has_the_seal_before_the_scripts_instruction_brief_and_the_gate(self):
        self.assertEqual([], order_problems_allowing_not_yet(REPO, SEAL_COMMIT_SHORT, list(ORDER_FILES)))

    def test_p_2_the_order_check_lists_every_file_and_not_the_record(self):
        self.assertEqual(5, len(ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)
        for rel in ORDER_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_p_3_the_order_part_turns_red_when_a_file_comes_before_the_seal_or_is_missing(self):
        seal = PREFIX + SEAL_REL
        other = PREFIX + CHECK_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("pre", {other: "x"}), ("seal-x", {seal: "s"}), ("later", {PREFIX + "b": "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [CHECK_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + CHECK_REL, got)
            self.assertIn(u"UNCOMMITTED:missing.py", got)
            self.assertNotIn(u"BEFORE_SEAL:b", got)
            allowed = order_problems_allowing_not_yet(tmp, short, [CHECK_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + CHECK_REL, allowed)
            self.assertNotIn(u"UNCOMMITTED:missing.py", allowed)
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal-x", {seal: "s"}), ("later", {other: "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], list(PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [CHECK_REL])))


class HygieneTest(unittest.TestCase):
    def test_q_1_the_new_files_do_not_contain_the_harness_words(self):
        words = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
        for rel in (CHECK_REL, TALLY_REL):
            body = read(rel)
            for w in words:
                self.assertNotIn(w, body, (rel, w))

    def test_q_2_the_gate_makes_no_material_for_the_production_companies(self):
        tree = ast.parse(read(GATE_REL))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "make_company" and len(node.args) >= 2:
                arg = node.args[1]
                if isinstance(arg, ast.Constant):
                    self.assertIn(arg.value, FAKE)
        for production_number in (1, 2, 3, 4, 12):
            with self.assertRaises(AssertionError):
                make_company(tempfile.gettempdir(), production_number, world())
        attrs = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "PROD" and isinstance(n.value, ast.Name) and n.value.id == "TAL"]
        # TAL.PROD は記録の形を試す所(一時的に開発の 1 社へ差し替える)と、値を比べる所だけで使う
        self.assertTrue(len(attrs) <= 8, len(attrs))

    def test_q_3_the_gate_has_no_skip(self):
        body = read(GATE_REL)
        self.assertNotIn(u"skip" + u"Test", body)
        self.assertNotIn(u"@unittest." + u"skip", body)
        self.assertNotIn(u"pytest.mark." + u"skip", body)

    def test_q_4_no_file_outside_the_declared_folders_is_added_to_the_fixtures(self):
        self.assertEqual([u"definition_A.json", u"definition_B.json", u"record.json"], sorted(os.listdir(os.path.join(ROOT, "fixtures", "universal", "um0"))))
        um2 = os.path.join(ROOT, "fixtures", "universal", "um2")
        if os.path.exists(um2):
            self.assertEqual([u"record.json"], sorted(os.listdir(um2)))

    def test_q_5_the_um0_files_are_not_touched_by_this_wave(self):
        for rel in ("measure/universal_check_2026-11-23.py", "measure/universal_source_gen_2026-11-23.py", "tests/measure/test_universal_material_seal.py", UM0_INSTRUCTION_REL, "fixtures/universal/um0/record.json"):
            self.assertEqual("", git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + rel).strip(), rel)
            self.assertEqual("", git("status", "--porcelain", "--", PREFIX + rel).strip(), rel)



# ======================================================================== 14. 変異の掃きで黙った所を縛る(規則ごと・比べ方ごと・見出しの正規化ごと)
class SweepGapTest(unittest.TestCase):
    def refused_part(self, mat, part):
        w = world()
        b = edit_item(perfect_bundle(w, 1), u"a03", lambda m: m.update(mat) if False else mat(m))
        res = check_a(w, 1, b)
        self.assertEqual(u"断り", res[u"束"][u"状態"])
        self.assertTrue(any(part in r for r in res[u"束"][u"理由"]), res[u"束"][u"理由"])

    def test_s_1_k0_reasons_are_named_for_each_form_defect(self):
        src = lambda m: m[u"出どころ"]
        self.refused_part(lambda m: src(m).__setitem__(u"額", od([(u"借方の列", 5), (u"貸方の列", u"貸方"), (u"向き", u"借方\u2212貸方")])), u"額の形")
        self.refused_part(lambda m: src(m).__setitem__(u"額", od([(u"借方の列", u"借方"), (u"貸方の列", u"貸方"), (u"向き", u"借方\u2212貸方"), (u"符号", u"逆")])), u"額の形")
        self.refused_part(lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"どれでもない", [u"x", 5])]), u"値の並び")
        self.refused_part(lambda m: src(m).__setitem__(u"条件", [cond(u"科目", u"等しい", 5)]), u"値の字")

    def test_s_2_compare_kinds_with_empty_values_and_spaces(self):
        m = MiniWorld()
        self.assertIn(u"K1", m.rules(mini_material([cond(u"科目", u"等しい", u"")] + RANGE, -5))[0])
        want = 100 - 10 + 1000 + 100000 + 0 + 7 + 30 + 40 - 200
        self.assertNotIn(u"K1", m.rules(mini_material([cond(u"科目", u"頭が同じ", u"")] + RANGE, want))[0])
        self.assertIn(u"K1", m.rules(mini_material([cond(u"科目", u"頭が同じ", u"")] + RANGE, want - 5))[0])
        self.assertNotIn(u"K1", m.rules(mini_material([cond(u"科目", u"どれか", [u"  売上高 "])] + RANGE, MINI_CASES[0][3]))[0])

    def test_s_3_a_non_number_in_a_one_column_amount_stops(self):
        rows = [(u"2025-04-01", u"売上高", u"", u"5", u"甲"), (u"2025-04-02", u"売上高", u"", u"1.5", u"甲")]
        m = MiniWorld(mini_text(rows))
        one = od([(u"列", u"貸方"), (u"符号", u"そのまま")])
        self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 5, amt=one))[0])
        self.assertIn(u"K1", m.rules(mini_material([SALES_EQ] + RANGE, 5, amt=od([(u"列", u"貸方"), (u"符号", u"逆")])))[0])

    def test_s_4_the_same_conditions_on_two_files_are_counted_separately(self):
        m = MiniWorld(mini_text([(u"2025-04-01", u"売上高", u"", u"5", u"甲")]))
        wbytes(os.path.join(m.tmp, u"cur", u"別.csv"), mini_text([(u"2025-04-01", u"売上高", u"", u"9", u"甲")]).encode("utf-8"))
        m.src = CHK.Source(os.path.join(m.tmp, u"cur"))
        a = mini_material([SALES_EQ] + RANGE, 5, ident=u"a01")
        b = mini_material([SALES_EQ] + RANGE, 9, ident=u"a03")
        b[u"出どころ"][u"file"] = u"別.csv"
        res = CHK.check_bundle(m.spec, m.defA, od([(u"型の版", u"u2"), (u"材料", [a, b])]), m.src, ids=[u"a01", u"a03"])
        self.assertEqual([[], []], [r[u"規則"] for r in res[u"材料"]])

    def test_s_5_k3_both_headings_in_the_table_stops(self):
        w = world()
        tmp = tempfile.mkdtemp(prefix="um2_k3_")
        _TMPS.append(tmp)
        wbytes(os.path.join(tmp, u"人員.csv"), u"項目,従業員数\n期末従業員数,30\n".encode("utf-8"))
        m = cell_material(w, 1, u"a30", 30, u"人員.csv", od([(u"行", 2), (u"列", 2)]), u"期末従業員数", u"従業員数", unit=u"人")
        res = CHK.check_bundle(w.spec[(1, u"A")], w.defA, od([(u"型の版", u"u2"), (u"材料", [m])]), CHK.Source(tmp), ids=[u"a30"])
        self.assertEqual([u"K3"], res[u"材料"][0][u"規則"])

    def test_s_6_carry_reads_periods_in_headings_and_normalizes_both_sides(self):
        w = world()
        import openpyxl
        b1 = perfect_bundle(w, 1)
        r1 = check_a(w, 1, b1)
        marks = set(m[u"id"] for m in b1[u"材料"] if m[u"状態"] == u"在る")

        def src_with(fn):
            tmp = tempfile.mkdtemp(prefix="um2_var_")
            _TMPS.append(tmp)
            shutil.copytree(w.dirs[2], os.path.join(tmp, u"期2"))
            path = os.path.join(tmp, u"期2", u"決算書.xlsx")
            wb = openpyxl.load_workbook(path)
            fn(wb)
            wb.save(path)
            return CHK.Source(os.path.join(tmp, u"期2"))

        def retitle(wb):
            wb[u"貸借"][u"B1"] = u"2027年3月末"
            wb[u"貸借"][u"C1"] = u"2026年3月末"
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b1, r1, marks, src_with(retitle), ids=CHK.material_ids(w.defA))
        self.assertIn(u"a15", c[u"持ち越した"])                          # 見出しの字が変わっても、2 期目の期に読めれば見つかる
        self.assertIn(u"a16", c[u"持ち越した"])
        self.assertEqual(u"2027年3月末", dict((x[u"id"], x) for x in c[u"束"][u"材料"])[u"a15"][u"出どころ"][u"列の見出し"])
        # 数でない cell は見出しが合っても数えない
        def text_cell(wb):
            wb[u"貸借"][u"D1"] = u"当期末"
            wb[u"貸借"][u"D2"] = u"備考"
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b1, r1, marks, src_with(text_cell), ids=CHK.material_ids(w.defA))
        self.assertIn(u"a15", c[u"持ち越した"])
        # 1 期目の見出しの申告に空白が入っていても、正規化の後で同じなら見つかる
        sp = edit_item(b1, u"a15", lambda m: m[u"出どころ"].__setitem__(u"行の見出し", u"純資産 合計"))
        spr = check_a(w, 1, sp)
        self.assertEqual(u"通す", verdicts(spr)[u"a15"][0])
        c = CHK.carry(w.defA, w.spec[(2, u"A")], sp, spr, marks, w.src[2], ids=CHK.material_ids(w.defA))
        self.assertIn(u"a15", c[u"持ち越した"])
        sp = edit_item(b1, u"a29", lambda m: m[u"出どころ"].__setitem__(u"列の見出し", u" 期末 残高"))
        spr = check_a(w, 1, sp)
        self.assertEqual(u"通す", verdicts(spr)[u"a29"][0])
        c = CHK.carry(w.defA, w.spec[(2, u"A")], sp, spr, marks, w.src[2], ids=CHK.material_ids(w.defA))
        self.assertIn(u"a29", c[u"持ち越した"])

    def test_s_7_carry_keeps_the_multiplier_of_the_previous_term(self):
        w = world()
        tmp = tempfile.mkdtemp(prefix="um2_mult_")
        _TMPS.append(tmp)
        for per, v in ((u"期1", 5), (u"期2", 7)):
            wbytes(os.path.join(tmp, per, u"損益.csv"), (u"科目,当期,前期\n売上高,%d,4\n(単位:千円),,\n" % v).encode("utf-8"))
        m = cell_material(w, 1, u"a01", 5000, u"損益.csv", od([(u"行", 2), (u"列", 2)]), u"売上高", u"当期", mult=1000)
        src1, src2 = CHK.Source(os.path.join(tmp, u"期1")), CHK.Source(os.path.join(tmp, u"期2"))
        b = od([(u"型の版", u"u2"), (u"材料", [m])])
        r = CHK.check_bundle(w.spec[(1, u"A")], w.defA, b, src1, ids=[u"a01"])
        self.assertEqual(u"通す", r[u"材料"][0][u"判定"])
        c = CHK.carry(w.defA, w.spec[(2, u"A")], b, r, set([u"a01"]), src2, ids=[u"a01"])
        self.assertEqual(u"7000", c[u"束"][u"材料"][0][u"数値"])
        self.assertEqual(1000, c[u"束"][u"材料"][0][u"出どころ"][u"表示の倍率"])

    def test_s_8_html_escapes_list_items_and_the_check_unescapes_entities(self):
        w = world()
        _ra, st, _p, _rb, _sb = flow(w)
        text = CHK.render_doc(w.defA, st)
        text2 = text.replace(u"- 売上高(当期)", u"- <i>売上</i> it's 高(当期)", 1)
        page, res = CHK.make_human(w.defA, st, text2)
        self.assertTrue(res[u"通った"])
        self.assertIn(u"&lt;i&gt;売上&lt;/i&gt;", page)
        self.assertNotIn(u"<i>", page)
        self.assertTrue(CHK.check_human(text2, page)[u"通った"])           # &#x27; の数字は戻してから数える
        table = page[page.index(u"<section id=\"sources\">"):]
        a08 = [ln for ln in table.split(u"</tr>") if u"<td>a08</td>" in ln][0]
        self.assertRegex(a08, u"<td>a08</td><td>[^<]*</td><td>無い</td><td>")

    def test_s_9_relation_holds_in_the_gold(self):
        rel = (u"R", [u"x1", u"x2"], [u"y"])
        self.assertTrue(TAL.relation_holds({u"x1": 1, u"x2": 2, u"y": 3}, rel[1], rel[2]))
        self.assertFalse(TAL.relation_holds({u"x1": 1, u"x2": 1, u"y": 3}, rel[1], rel[2]))
        self.assertFalse(TAL.relation_holds({u"x1": 1, u"x2": 3, u"y": 3}, rel[1], rel[2]))
        self.assertFalse(TAL.relation_holds({u"x1": None, u"x2": 3, u"y": 3}, rel[1], rel[2]))
        self.assertFalse(TAL.relation_holds({u"x1": 3, u"x2": 0, u"y": None}, rel[1], rel[2]))

    def test_s_10_the_mutants_are_built_as_sealed(self):
        w = world()
        b = perfect_bundle(w, 1)
        src = w.src[1]
        items = dict((m[u"id"], m) for m in b[u"材料"])
        # V5: 日付の条件と期間の両方を 1 年前へ・V4: 期間はそのまま
        v4, _s = TAL.mutant_rows(CHK, src, items[u"a03"], u"V4")
        v5, _s = TAL.mutant_rows(CHK, src, items[u"a03"], u"V5")
        self.assertEqual(items[u"a03"][u"期間"], v4[u"期間"])
        self.assertEqual({u"始まり": u"2024-04-01", u"終わり": u"2025-03-31"}, v5[u"期間"])
        self.assertEqual(v4[u"出どころ"][u"条件"], v5[u"出どころ"][u"条件"])
        # V6: 向きと符号
        v6, _s = TAL.mutant_rows(CHK, src, items[u"a03"], u"V6")
        self.assertEqual(CHK.DIRECTIONS[1] if items[u"a03"][u"出どころ"][u"額"][u"向き"] == CHK.DIRECTIONS[0] else CHK.DIRECTIONS[0], v6[u"出どころ"][u"額"][u"向き"])
        one = copy.deepcopy(items[u"a03"])
        one[u"出どころ"][u"額"] = od([(u"列", u"貸方"), (u"符号", u"そのまま")])
        v6, _s = TAL.mutant_rows(CHK, src, one, u"V6")
        self.assertEqual(u"逆", v6[u"出どころ"][u"額"][u"符号"])
        one[u"出どころ"][u"額"] = od([(u"列", u"貸方"), (u"符号", u"逆")])
        self.assertEqual(u"そのまま", TAL.mutant_rows(CHK, src, one, u"V6")[0][u"出どころ"][u"額"][u"符号"])
        # V3: 日付でない条件の最初を外す(日付の条件が先に在っても)
        d = copy.deepcopy(items[u"a03"])
        conds = d[u"出どころ"][u"条件"]
        d[u"出どころ"][u"条件"] = [conds[1], conds[2], conds[0]]
        v3, _s = TAL.mutant_rows(CHK, src, d, u"V3")
        self.assertEqual([conds[1], conds[2]], v3[u"出どころ"][u"条件"])
        # V2: どれかの並びが 2 つ以上の時だけ・数値が変わる値を外す
        t = copy.deepcopy(items[u"a03"])
        t[u"出どころ"][u"条件"][0] = cond(u"科目", u"どれか", [u"勘定甲03", u"雑費"])
        v2, same = TAL.mutant_rows(CHK, src, t, u"V2")
        self.assertFalse(same)
        self.assertEqual([u"雑費"], v2[u"出どころ"][u"条件"][0][u"値"] if False else [x for x in v2[u"出どころ"][u"条件"][0][u"値"] if x == u"雑費"])
        self.assertEqual(1, len(v2[u"出どころ"][u"条件"][0][u"値"]))
        t[u"出どころ"][u"条件"][0] = cond(u"科目", u"どれか", [u"勘定甲03"])
        self.assertEqual((None, False), TAL.mutant_rows(CHK, src, t, u"V2"))
        t[u"出どころ"][u"条件"][0] = cond(u"科目", u"等しい", u"勘定甲03")
        self.assertEqual((None, False), TAL.mutant_rows(CHK, src, t, u"V2"))

    def test_s_11_the_document_mutants_are_the_sealed_ones(self):
        w = world()
        _ra, st, _p, _rb, _sb = flow(w)
        text = CHK.render_doc(w.defA, st)
        got = TAL.doc_mutants(text)
        d4 = [new for code, _k, new in got if code == u"D4"]
        self.assertEqual(33, len(d4))
        self.assertEqual(text.replace(u"[材料:a01]", u"", 1), d4[0])
        d1 = [new for code, _k, new in got if code == u"D1"]
        self.assertEqual(31, len(d1))
        self.assertEqual(len(text), len(d1[0]))
        self.assertEqual(1, sum(1 for x, y in zip(text, d1[0]) if x != y))

    def test_s_12_the_judge_boundary_of_p1(self):
        c = {u"段 1:席の答えが正解と同じ": 93}
        self.assertTrue(TAL.judge({u"数": c, u"変異": {}})[u"UM2-P1"][u"当たり"])
        c = {u"段 2:確かめた取り方の行": 5, u"段 2:持ち越した行": 4}
        self.assertTrue(TAL.judge({u"数": c, u"変異": {}})[u"UM2-Q1"][u"当たり"])
        self.assertTrue(TAL.judge({u"数": {u"段 3:A の 2 期目の資料で数が出ている行": 80}, u"変異": {}})[u"UM2-D2"][u"当たり"])

    def test_s_13_a_passed_value_where_the_gold_is_null_is_counted_separately(self):
        w = world()
        b = edit_item(perfect_bundle(w, 1), u"a08", lambda m: (m.clear(), m.update(rows_material(w, 1, u"a08", w.syn.total(ACCOUNT[u"a09"], fy_range(1)[0], fy_range(1)[1], -1), ACCOUNT[u"a09"], CR_MINUS_DR))))
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, _s = run_tally(w, tmp, bundleA1=b)
        c = res[u"数"]
        self.assertEqual(1, c[u"段 1:通したが正解が null"])
        self.assertEqual(0, c[u"段 1:通したが数値が違う"])
        self.assertEqual(30, c[u"段 1:席の答えが正解と同じ"])



# ======================================================================== 15. 直し(独立監査の 1 巡目): 複数社の集計・正解の読み・check の穴・正解が null の行を通した数
class ChkProxy(object):
    u"""検査の module の代わり。``over`` の名前だけ差し替え、残りは本物へ渡す(集計が「渡された検査」を使うことの試し)。"""

    def __init__(self, **over):
        self._over = over

    def __getattr__(self, name):
        if name in self._over:
            return self._over[name]
        return getattr(CHK, name)


def edit_gold(cdir, fn):
    path = os.path.join(cdir, u"正解", u"正解.json")
    g = json.load(io.open(path, encoding="utf-8"))
    fn(g)
    wjson(path, g)


def k3_swap_bundle(w):
    u"""a30(取り方は素材)を 素材の和 の種類で書いた束(K3 の種類の食い違い。値は合っている)と、a16 の数値を 1 足した束(K1)。"""
    b = perfect_bundle(w, 1)
    sumform = od([(u"id", u"a30"), (u"状態", u"在る"), (u"数値", str(w.syn.value(u"a30", 1))), (u"単位", u"人"), (u"期間", period_of(w, 1, u"a30")), (u"範囲", u"全社"),
                  (u"出どころ", od([(u"種類", u"素材の和"), (u"file", u"人員.csv"), (u"列", 2), (u"行の並び", [2]), (u"列の見出し", u"人数"), (u"表示の倍率", 1)]))])
    b = edit_item(b, u"a30", lambda m: (m.clear(), m.update(sumform)))
    return edit_item(b, u"a16", lambda m: m.__setitem__(u"数値", str(int(m[u"数値"]) + 1)))


class MultiCompanyTallyTest(unittest.TestCase):
    u"""3 つの架空の社(101・102・103)を 1 度の集計に掛ける。社ごとに違う所を入れ、社をまたぐ数(通し・K11 の社・K3・null の行・通した値)を手で数えた値で縛る。

    - 101: 取り方が違う行(a30 を 素材の和 で書く → K3)・数値を 1 足した行(a16 → K1)・正解の側で 1 期目の a02 を 1 足す(素材の行が検査を通るのに正解と違う)・
      2 期目の正解の売上高を null にする(持ち越して通した行が、2 期目の正解で null)。
    - 102: 2 期目に新しい科目(K11)・2 期目の A の資料を書かない。
    - 103: 2 期目に新しい科目(K11)。
    """
    _cache = {}

    @classmethod
    def run_scenario(cls):
        if "res" in cls._cache:
            return cls._cache["res"]
        w0, w1 = world(), world(new_account=True)
        tmp = tempfile.mkdtemp(prefix="um2_multi_")
        _TMPS.append(tmp)
        root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
        make_company(tmp, 101, w0, bundleA1=k3_swap_bundle(w0))
        make_company(tmp, 102, w1)
        make_company(tmp, 103, w1)
        edit_gold(os.path.join(root_c, u"101"), lambda g: (g[u"期1"].__setitem__(u"売上高_前期", g[u"期1"][u"売上高_前期"] + 1), g[u"期2"].__setitem__(u"売上高_当期", None)))
        TAL.tally([101, 102, 103], root_c, root_s, CHK)
        seat_docs(CHK, w0, os.path.join(root_s, u"101"))
        seat_docs(CHK, w1, os.path.join(root_s, u"102"), skip=(2,))
        seat_docs(CHK, w1, os.path.join(root_s, u"103"))
        res = TAL.tally([101, 102, 103], root_c, root_s, CHK)
        cls._cache["res"] = (res, root_c, root_s)
        return cls._cache["res"]

    def test_u_1_the_through_counts_follow_the_sealed_words_one_company_without_the_second_term_document(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        self.assertEqual(3, res[u"会社の数"])
        # 102 は 2 期目の A の資料が無い: 期1 は 3 社・期2 は 2 社・「期1・期2とも」は 2 社(期2 の組み立てと「かつ」)
        self.assertEqual(2, c[u"段 3:資料の検査を通した:期2・A"])
        self.assertEqual(1, c[u"段 3:資料なし:期2・A"])
        self.assertEqual(3, c[u"通し:期1"])
        self.assertEqual(2, c[u"通し:期2"])
        self.assertEqual(2, c[u"通し:期1・期2とも"])
        self.assertEqual(od([(u"101", {u"K11 で止めた行": 0, u"通し:期1": 1, u"通し:期2": 1}), (u"102", {u"K11 で止めた行": 25, u"通し:期1": 1, u"通し:期2": 0}),
                             (u"103", {u"K11 で止めた行": 25, u"通し:期1": 1, u"通し:期2": 1})]), res[u"会社ごと"])
        self.assertEqual((3, 3, 2, 3), tuple(c[u"段 3:資料の検査を通した:" + t] for t in (u"期1・A", u"期1・B", u"期2・A", u"期2・B")))
        self.assertEqual((3, 3, 2, 3), tuple(c[u"段 3:人が読む版の検査を通した:" + t] for t in (u"期1・A", u"期1・B", u"期2・A", u"期2・B")))

    def test_u_2_the_number_of_companies_with_k11_counts_companies_not_rows(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        self.assertEqual(2, c[u"段 2:K11 で止めた社"])
        self.assertEqual(50, c[u"段 2:K11 で止めた行"])                      # 社ごとに A の行の和 24 と B の b01
        self.assertEqual(50, c[u"段 2:止めた行の規則:K11"])
        self.assertTrue(TAL.judge(res)[u"UM2-Q3"][u"当たり"])

    def test_u_3_k3_counts_only_rows_stopped_by_k3(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        self.assertEqual(1, c[u"段 1:K3 で止まった行"])                       # a30 だけ(a16 は K1 で止まるので入らない)
        self.assertEqual(1, c[u"段 1:止めた行の規則:K3"])
        self.assertEqual(1, c[u"段 1:止めた行の規則:K1"])
        self.assertEqual(2, c[u"段 1:検査の結果:止める"])
        self.assertEqual({u"K3+K6": 1, u"K1": 1}, dict((k.split(u":")[-1], v) for k, v in c.items() if k.startswith(u"段 1:止めた行の規則の組:")))

    def test_u_4_a_passed_wrong_value_counts_for_a_cell_row_that_is_not_unconfirmed(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        # 101 の a02 は素材の行(検査は「通す」)で、正解の側が 1 違う: 未確認の行でなくても「通したが数値が違う」に入る
        self.assertEqual(1, c[u"段 1:通したが数値が違う"])
        self.assertTrue(TAL.judge(res)[u"UM2-P3"][u"当たり"])
        self.assertEqual(0, TAL.judge(res)[u"UM2-P3"][u"正解が null の行を通した数"])

    def test_u_5_null_rows_are_counted_per_term_and_the_second_term_has_one_more(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        self.assertEqual(3, c[u"正解が null の行:期1"])                       # 3 社の a08
        self.assertEqual(4, c[u"正解が null の行:期2"])                       # 3 社の a08 と 101 の売上高
        self.assertEqual((0, 0), (c[u"正解が読めない項目:期1"], c[u"正解が読めない項目:期2"]))

    def test_u_6_a_carried_row_that_passes_where_the_second_term_gold_is_null_is_a_separate_count(self):
        res, _c, _s = self.run_scenario()
        c = res[u"数"]
        self.assertEqual(1, c[u"段 2:持ち越して通したが正解が null"])           # 101 の a01(2 期目の正解を null にした)
        self.assertEqual(0, c[u"段 2:持ち越して通したが数値が違う"])
        j = TAL.judge(res)[u"UM2-Q2"]
        self.assertTrue(j[u"当たり"])                                           # 判定の式は変えない(数値が違う行だけ)
        self.assertEqual(1, j[u"正解が null の行を通した数"])
        self.assertEqual(0, TAL.judge(res)[u"UM2-P3"][u"正解が null の行を通した数"])

    def test_u_7_the_record_is_built_from_the_production_numbers_not_the_development_ones(self):
        _res, root_c, root_s = self.run_scenario()
        with prod_is((101, 102, 103)):
            rec = TAL.build_record(root_c, root_s, CHK)
        self.assertEqual(3, rec[u"会社の数"])
        self.assertEqual([u"101", u"102", u"103"], sorted(rec[u"会社ごと"]))
        self.assertEqual(1, rec[u"数"][u"段 2:持ち越して通したが正解が null"])
        self.assertIn(u"段 1:通したが正解が null", rec[u"数"])
        self.assertEqual((1, 2, 3, 4), TAL.PROD)
        self.assertEqual((101,), TAL.DEV)
        self.assertEqual([], record_problems(json.loads(json.dumps(rec, ensure_ascii=False)), companies=(101, 102, 103)))

    def test_u_8_the_judge_of_v2_counts_both_v1_and_v4(self):
        def v2(v1_passed, v4_passed):
            mut = {u"V1": {u"作れた": 4, u"通した": v1_passed}, u"V4": {u"作れた": 3, u"通した": v4_passed}}
            return TAL.judge({u"数": {}, u"変異": mut})[u"UM2-V2"]
        self.assertEqual((True, 7, 0), tuple(v2(0, 0)[k] for k in (u"当たり", u"作れた", u"通した")))
        self.assertEqual((False, 1), (v2(1, 0)[u"当たり"], v2(1, 0)[u"通した"]))
        self.assertEqual((False, 1), (v2(0, 1)[u"当たり"], v2(0, 1)[u"通した"]))
        self.assertEqual((False, 3), (v2(1, 2)[u"当たり"], v2(1, 2)[u"通した"]))

    def test_u_9_with_a_rule_removed_the_v2_judge_turns_false_for_each_of_v1_and_v4_in_a_real_run(self):
        w = world()
        for rule, code in ((u"K1", u"V1"), (u"K4", u"V4")):
            with tempfile.TemporaryDirectory() as tmp:
                with removed(rule):
                    res, _c, _s = run_tally(w, tmp)
            self.assertGreater(res[u"変異"][code][u"通した"], 0, code)
            self.assertFalse(TAL.judge(res)[u"UM2-V2"][u"当たり"], code)

    def test_u_10_the_through_count_needs_the_document_check_the_human_version_and_its_check(self):
        w = world()
        cases = (
            (u"資料の検査", ChkProxy(check_document=lambda defn, store, text: {u"通った": False, u"結ばれていない数": 0}), 0, 0, 0),
            (u"人が読む版が組めない", ChkProxy(make_human=lambda defn, store, text: (None, {u"赤": []})), 4, 0, 0),
            (u"人が読む版の検査", ChkProxy(check_human=lambda text, page: {u"通った": False}), 4, 4, 0),
        )
        for name, chk, docs_ok, built, human_ok in cases:
            with tempfile.TemporaryDirectory() as tmp:
                res, _c, _s = run_tally(w, tmp, chk=chk)
            c = res[u"数"]
            tags = (u"期1・A", u"期1・B", u"期2・A", u"期2・B")
            self.assertEqual(0, c[u"通し:期1"], name)
            self.assertEqual(0, c[u"通し:期2"], name)
            self.assertEqual(0, c[u"通し:期1・期2とも"], name)
            self.assertEqual(built, sum(c[u"段 3:人が読む版が組めた:" + t] for t in tags), name)
            self.assertEqual(human_ok, sum(c[u"段 3:人が読む版の検査を通した:" + t] for t in tags), name)


class GoldReadTest(unittest.TestCase):
    u"""正解の読み。鍵が無い・月次が 12 に足りない・値が文字は、null ではなく「読めない項目」。"""

    def gold_with(self, fn):
        w = world()
        g = w.syn.gold_json()
        fn(g)
        tmp = tempfile.mkdtemp(prefix="um2_gold_")
        _TMPS.append(tmp)
        path = os.path.join(tmp, u"正解.json")
        wjson(path, g)
        return TAL.read_gold(path)

    def test_r_1_a_missing_key_is_unreadable_and_not_null(self):
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"].pop(u"人件費_当期"))
        self.assertEqual({u"b01"}, unread[u"期1"])
        self.assertIs(TAL.UNREADABLE, vals[u"期1"][u"b01"])
        self.assertEqual(set(), unread[u"期2"])
        self.assertEqual(0, bad)
        self.assertEqual(31, len(vals[u"期1"]))
        # 本物の null(a08)は null のまま
        self.assertIsNone(vals[u"期1"][u"a08"])
        self.assertNotIn(u"a08", unread[u"期1"])

    def test_r_2_a_short_month_list_leaves_only_the_missing_months_unreadable(self):
        vals, bad, unread = self.gold_with(lambda g: g[u"期2"].__setitem__(TAL.MONTH_KEY, g[u"期2"][TAL.MONTH_KEY][:8]))
        self.assertEqual(set(TAL.MONTH_IDS[8:]), unread[u"期2"])
        self.assertEqual(set(), unread[u"期1"])
        for ident in TAL.MONTH_IDS[:8]:
            self.assertIsInstance(vals[u"期2"][ident], int)
        # 月次の欄が丸ごと無い
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"].pop(TAL.MONTH_KEY))
        self.assertEqual(set(TAL.MONTH_IDS), unread[u"期1"])

    def test_r_3_a_text_value_is_unreadable_and_counted_as_a_non_integer(self):
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"].__setitem__(u"短期借入金_当期末", u"1,000"))
        self.assertEqual({u"a12"}, unread[u"期1"])
        self.assertEqual(1, bad)
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"][TAL.MONTH_KEY].__setitem__(3, u"x"))
        self.assertEqual({TAL.MONTH_IDS[3]}, unread[u"期1"])
        self.assertEqual(1, bad)

    def test_r_5_a_month_column_that_is_null_as_a_whole_is_twelve_nulls_not_unreadable(self):
        u"""封は月次の欄が丸ごと null の時を決めていない。今の読みは「12 個とも null(素材から出せない)」。封が null を「素材から出せない項目」の印と決めていて、欄ごとの null もその一つとして読むのが素直だから。
        欄が文字など null でも並びでもない時は、封の「整数か null」に当たらないので読めない(12 個とも)と数える。"""
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"].__setitem__(TAL.MONTH_KEY, None))
        self.assertEqual([None] * 12, [vals[u"期1"][i] for i in TAL.MONTH_IDS])
        self.assertEqual(set(), unread[u"期1"])
        self.assertEqual(0, bad)
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"].__setitem__(TAL.MONTH_KEY, u"x"))
        self.assertEqual(set(TAL.MONTH_IDS), unread[u"期1"])
        self.assertEqual(1, bad)
        for ident in TAL.MONTH_IDS:
            self.assertIs(TAL.UNREADABLE, vals[u"期1"][ident])

    def test_r_6_a_boolean_month_is_not_an_integer(self):
        u"""封は正解の値を「整数か null」と決めている。JSON の true は整数ではないので読めない項目に数える(Python では bool は int の子だが整数と読まない)。"""
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"][TAL.MONTH_KEY].__setitem__(5, True))
        self.assertEqual({TAL.MONTH_IDS[5]}, unread[u"期1"])
        self.assertEqual(1, bad)
        self.assertIs(TAL.UNREADABLE, vals[u"期1"][TAL.MONTH_IDS[5]])
        self.assertIsInstance(vals[u"期1"][TAL.MONTH_IDS[4]], int)
        vals, bad, unread = self.gold_with(lambda g: g[u"期1"][TAL.MONTH_KEY].__setitem__(0, False))
        self.assertEqual({TAL.MONTH_IDS[0]}, unread[u"期1"])
        self.assertEqual(1, bad)

    def test_r_7_a_month_list_longer_than_twelve_reads_the_first_twelve_and_ignores_the_rest(self):
        u"""封は月次が 13 個以上の時を決めていない(「12 か月」とだけ)。今の読みは「先頭の 12 個だけ読み、13 個目以降は読まず・数えない」。当期の 12 か月の並びが正で、余りは正解の項目に対応する id が無いから。"""
        def longer(g):
            g[u"期1"][TAL.MONTH_KEY] = list(g[u"期1"][TAL.MONTH_KEY]) + [u"x", True, 5]
        w = world()
        base = w.syn.gold_json()[u"期1"][TAL.MONTH_KEY]
        vals, bad, unread = self.gold_with(longer)
        self.assertEqual(set(), unread[u"期1"])
        self.assertEqual(0, bad)
        self.assertEqual(list(base[:12]), [vals[u"期1"][i] for i in TAL.MONTH_IDS])
        self.assertEqual(31, len(vals[u"期1"]))

    def test_r_4_the_tally_counts_unreadable_rows_apart_from_null_rows_and_never_marks_them(self):
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w)
            def damage(g):
                g[u"期1"].pop(u"人件費_当期")
                g[u"期1"][u"短期借入金_当期末"] = u"x"
                g[u"期2"][TAL.MONTH_KEY] = g[u"期2"][TAL.MONTH_KEY][:8]
            edit_gold(cdir, damage)
            root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
            TAL.tally([101], root_c, root_s, CHK)
            seat_docs(CHK, w, sdir)
            res = TAL.tally([101], root_c, root_s, CHK)
            marks = json.load(io.open(os.path.join(sdir, u"出力", u"印_期1.json"), encoding="utf-8"))[u"確かめた取り方"]
        c = res[u"数"]
        self.assertEqual((1, 1), (c[u"正解が null の行:期1"], c[u"正解が null の行:期2"]))              # a08 だけ
        self.assertEqual((2, 4), (c[u"正解が読めない項目:期1"], c[u"正解が読めない項目:期2"]))
        self.assertNotIn(u"b01", marks)
        self.assertNotIn(u"a12", marks)
        self.assertEqual(29, c[u"段 1:席の答えが正解と同じ"])
        self.assertEqual(2, c[u"段 1:通したが正解が読めない"])
        self.assertEqual(0, c[u"段 1:通したが正解が null"])
        self.assertEqual(0, c[u"段 1:通したが数値が違う"])
        self.assertEqual(28, c[u"段 2:確かめた取り方の行"])
        self.assertEqual(4, c[u"段 2:持ち越して通したが正解が読めない"])
        self.assertEqual(0, c[u"段 2:持ち越して通したが数値が違う"])
        self.assertTrue(TAL.judge(res)[u"UM2-Q2"][u"当たり"])


class CheckGapTest(unittest.TestCase):
    u"""独立監査が当てて黙った所(C17・C29・C49・K3 の種類)。"""

    def test_k_1_a_head_match_is_a_prefix_match_not_a_contains_match(self):
        rows = [(u"2025-04-01", u"売上高", u"", u"100", u"甲"), (u"2025-04-02", u"付随売上高", u"", u"7", u"甲"), (u"2025-04-03", u"売上高付随", u"", u"30", u"甲"),
                (u"2025-04-04", u"高", u"", u"500", u"甲")]
        m = MiniWorld(mini_text(rows))
        conds = [cond(u"科目", u"頭が同じ", u"売上高")] + RANGE
        self.assertNotIn(u"K1", m.rules(mini_material(conds, 130))[0])           # 売上高・売上高付随だけ(付随売上高は含むが頭ではない)
        self.assertIn(u"K1", m.rules(mini_material(conds, 137))[0])
        self.assertIn(u"K1", m.rules(mini_material(conds, 637))[0])

    def test_k_2_the_old_values_are_every_row_of_the_previous_file_not_the_first_rows(self):
        filler = u"".join(u"2025-05-02,仕入高,50,,乙\n" for _k in range(70))
        prev = self.PREV_HEAD + filler + u"2026-02-01,後ろの方にだけ在る科目,1,,甲\n"
        p = PairWorld(prev, prev + u"2026-06-01,後ろの方にだけ在る科目,3,,甲\n")
        v = p.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"仕入高")] + R2, 0)])
        self.assertNotIn(u"K11", v[u"a01"][1])
        # 本当に新しい値なら止まる(試しの手が効いている)
        q = PairWorld(prev, prev + u"2026-06-01,本当に新しい科目,3,,甲\n")
        self.assertIn(u"K11", q.run([row_mat(u"a01", [cond(u"科目", u"等しい", u"仕入高")] + R2, 0)])[u"a01"][1])

    PREV_HEAD = HEAD

    def test_k_3_the_key_of_k11_is_a_file_and_a_column(self):
        prev = NewValueTest.PREV + u"2026-05-01,売上高,,7,甲\n"
        p = PairWorld(prev, prev + u"2026-06-01,新しい科目,9,,乙\n")
        other = HEAD + u"2026-05-01,売上高,,7,甲\n"
        for per in (u"期1", u"期2"):
            wbytes(os.path.join(p.tmp, per, u"別.csv"), other.encode("utf-8"))
        p.prev, p.cur = CHK.Source(os.path.join(p.tmp, u"期1")), CHK.Source(os.path.join(p.tmp, u"期2"))
        same_file = row_mat(u"a01", [cond(u"科目", u"等しい", u"売上高")] + R2, 7)
        other_file = row_mat(u"a03", [cond(u"科目", u"等しい", u"売上高")] + R2, 7)
        other_file[u"出どころ"][u"file"] = u"別.csv"
        other_col = row_mat(u"a04", [cond(u"部門", u"等しい", u"甲")] + R2, 7)
        v = p.run([same_file, other_file, other_col])
        self.assertEqual((u"止める", (u"K11",)), v[u"a01"])                   # 新しい科目が出た file の同じ列
        self.assertNotIn(u"K11", v[u"a03"][1])                                 # 同じ名の列でも、別の file には新しい値が無い
        self.assertEqual((u"通す", ()), v[u"a04"])                             # 同じ file でも別の列(部門の値は前からある)
        self.assertEqual((u"通す", ()), v[u"a03"])

    def test_k_4_a_kind_that_differs_from_the_definition_is_stopped_by_k3(self):
        w = world()
        b = k3_swap_bundle(w)
        v = verdicts(check_a(w, 1, b))
        self.assertEqual(u"止める", v[u"a30"][0])                                # 取り方は 素材 の行を 素材の和 で書いた
        self.assertIn(u"K3", v[u"a30"][1])
        # 逆向き: 取り方が 素材の和 の行(a29)を 素材 で書く
        cell = cell_material(w, 1, u"a29", w.syn.value(u"a29", 1), u"借入.csv", od([(u"行", 5), (u"列", 2)]), u"合計", u"期末残高")
        b = edit_item(perfect_bundle(w, 1), u"a29", lambda m: (m.clear(), m.update(cell)))
        v = verdicts(check_a(w, 1, b))
        self.assertIn(u"K3", v[u"a29"][1])
        self.assertEqual(u"止める", v[u"a29"][0])
        # 種類が合っていれば K3 は掛からない(試しの手が効いている)
        self.assertEqual(u"通す", verdicts(check_a(w, 1, perfect_bundle(w, 1)))[u"a29"][0])
        self.assertEqual(u"通す", verdicts(check_a(w, 1, perfect_bundle(w, 1)))[u"a30"][0])

    def test_k_5_a_sum_over_a_column_whose_heading_is_not_in_the_definition_table_is_stopped_by_k3_alone(self):
        u"""素材の和 の列の見出しが定義表の「見出し」に無い時は K3 が止める(取り方の種類は合っている)。他の規則は掛からない形(値は列の和どおり・見出しの申告は列の字どおり)で、K3 だけが止めることを見る。"""
        w = world()
        tmp = tempfile.mkdtemp(prefix="um2_k3sum_")
        _TMPS.append(tmp)
        base = os.path.join(tmp, u"期1")
        shutil.copytree(w.dirs[1], base)
        path = os.path.join(base, u"借入.csv")
        text = io.open(path, encoding="utf-8").read()
        self.assertTrue(text.startswith(u"借入先,期末残高,利率\n"))
        wbytes(path, text.replace(u"借入先,期末残高,利率", u"借入先,金額,利率", 1).encode("utf-8"))
        src = CHK.Source(base)
        self.assertNotIn(u"金額", [CHK.norm(x) for x in w.defA.by_id[u"a29"][u"見出し"]])
        moved = edit_item(perfect_bundle(w, 1), u"a29", lambda m: m[u"出どころ"].__setitem__(u"列の見出し", u"金額"))
        v = verdicts(CHK.check_bundle(w.spec[(1, u"A")], w.defA, moved, src))
        self.assertEqual((u"止める", (u"K3",)), v[u"a29"])
        # 見出しが表に在る(元の字)なら同じ値で通る(試しの手が効いている)
        v = verdicts(CHK.check_bundle(w.spec[(1, u"A")], w.defA, perfect_bundle(w, 1), w.src[1]))
        self.assertEqual(u"通す", v[u"a29"][0])


class TallyGapTest(unittest.TestCase):
    u"""変異の掃きで黙った集計の所(印・V5 の時点の行)。"""

    def test_g_1_a_row_passed_where_the_gold_is_null_gets_no_mark_and_is_not_carried(self):
        w = world()
        b = edit_item(perfect_bundle(w, 1), u"a08", lambda m: (m.clear(), m.update(rows_material(w, 1, u"a08", w.syn.total(ACCOUNT[u"a09"], fy_range(1)[0], fy_range(1)[1], -1), ACCOUNT[u"a09"], CR_MINUS_DR))))
        with tempfile.TemporaryDirectory() as tmp:
            res, _c, root_s = run_tally(w, tmp, bundleA1=b)
            marks = json.load(io.open(os.path.join(root_s, u"101", u"出力", u"印_期1.json"), encoding="utf-8"))[u"確かめた取り方"]
        c = res[u"数"]
        self.assertEqual(1, c[u"段 1:通したが正解が null"])
        self.assertEqual(1, TAL.judge(res)[u"UM2-P3"][u"正解が null の行を通した数"])        # 判定の横の欄。P3 の当たり外れの式は変えない(数値が違う行だけ)
        self.assertFalse(TAL.judge(res)[u"UM2-P3"][u"当たり"])
        self.assertNotIn(u"a08", marks)
        self.assertEqual(29 + 1, len(marks))                                    # 30 行(a08 の無い A の 29 と b01)
        self.assertEqual(1, c[u"段 2:持ち越せなかった行:確かめた取り方の印が無い"])
        self.assertEqual(0, c[u"段 2:持ち越して通したが正解が null"])

    def test_g_3_a_seat_that_writes_none_where_the_gold_key_is_missing_is_not_the_same_answer(self):
        u"""正解の鍵が無い(読めない)項目に、席が 無い と書いた束。null の行(席が 無い と書くと同じ)とは別で、「席の答えが正解と同じ」にも「正解どおり」の枠にも入らない。手で数える: 31 行のうち b01 だけ読めず、
        席の答えが正解と同じは 30・枠は 正解どおり×通した 30(a08 の 無い を含む)・正解と違う×通した 1(b01 の 無い は検査が受ける)・止めた 0 の 2 つ。"""
        w = world()
        with tempfile.TemporaryDirectory() as tmp:
            cdir, sdir = make_company(tmp, 101, w, bundleB1=edit_item(perfect_bundle(w, 1, u"B"), u"b01", lambda m: (m.clear(), m.update(none_material(u"b01")))))
            edit_gold(cdir, lambda g: g[u"期1"].pop(u"人件費_当期"))
            root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
            res = TAL.tally([101], root_c, root_s, CHK)
        c = res[u"数"]
        self.assertEqual(31, c[u"段 1:行の数"])
        self.assertEqual(1, c[u"正解が読めない項目:期1"])
        self.assertEqual(1, c[u"正解が null の行:期1"])                       # a08 だけ。b01 は入らない
        self.assertEqual(2, c[u"段 1:席が無いと書いた行"])                     # a08 と b01
        self.assertEqual(30, c[u"段 1:席の答えが正解と同じ"])
        self.assertEqual({u"正解どおり×通した": 30, u"正解どおり×止めた": 0, u"正解と違う×通した": 1, u"正解と違う×止めた": 0},
                         dict((k, c[u"段 1:4 つの枠:" + k]) for k in (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた")))

    def test_g_2_v5_moves_the_period_of_a_time_point_row_with_its_date_condition(self):
        w = world()
        items = dict((m[u"id"], m) for m in perfect_bundle(w, 1)[u"材料"])
        v5, _s = TAL.mutant_rows(CHK, w.src[1], items[u"a09"], u"V5")
        v4, _s = TAL.mutant_rows(CHK, w.src[1], items[u"a09"], u"V4")
        self.assertEqual({u"時点": u"2026-03-31"}, items[u"a09"][u"期間"])
        self.assertEqual({u"時点": u"2025-03-31"}, v5[u"期間"])
        self.assertEqual(items[u"a09"][u"期間"], v4[u"期間"])
        self.assertEqual([c[u"値"] for c in v4[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"], [u"2025-03-31"])
        self.assertEqual(v4[u"出どころ"][u"条件"], v5[u"出どころ"][u"条件"])
        # 期間の行の V5 は始まりと終わりの両方
        v5p, _s = TAL.mutant_rows(CHK, w.src[1], items[u"a03"], u"V5")
        self.assertEqual({u"始まり": u"2024-04-01", u"終わり": u"2025-03-31"}, v5p[u"期間"])


if __name__ == "__main__":
    unittest.main()
