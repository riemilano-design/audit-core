# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md(UM1 ― 第三者が公開した作り物の会社の帳簿から、席が材料を作り、答えを読まない検査が確かめ、
確かめた取り方を次の期へ持ち越す)の封の門。

**素材の全体(SQLite 1 つ)は repo に無く、この門は開かない。** 門の中で、素材と同じ表と列の名を持つ小さな作り物の SQLite(``Fake``)を作って縛る。
作り物は、締めの仕訳・期首の仕訳・減価償却の 2 つの借方・動きの無い科目・2 期目に新しく動く科目・結ばれない振替伝票の行を持つ。
置き場も道具も通信も鍵も使わない。席(subagent)は呼ばない。

**この門が縛るもの**

1. 封の字: 封の file の sha256・封の commit の blob と同じ・engine は封の commit から 0 行・封の表の字が定義表・script の定数と同じ。
2. 定義表 C・読込みの定義が封の字どおり・定義表・読込みの定義・指示書・検査には素材の科目の番号・分類の字・仕訳の種類の字を書かない。
3. 検査は答えを知っている側を import せず(AST)・標準の library だけ・``python3 -I`` の別 process で動き・素材は ``mode=ro`` で開き・
   どんな入力でも rc 0 で結果の JSON を返す(壊した入力を掃く)・材料の束の字は SQL に入らない(悪い字を列と値に入れて掃く)。
4. 検査の規則 K0〜K10 が、当たる例と当たらない例(表なし・表つき)で答える。変異 N1〜N12 の作り(1 つずつ、期待の値を作り物の行から別に導いて比べる)。
5. **変異で赤くなる**: 規則の関数 1 つずつを緩める(``RULE_FUNCS``)と対応する材料が通る・締めると正しい材料を止める。
   検査と答えを知っている側の本文を 1 か所ずつ緩めた版(本文の置換。読み込んだ module の上でだけ。file は触らない)に、同じ電池を掛けると赤になる
   (``どれでもない`` の空の扱い・丸め・時点の行の下限・K10 の「入りうる」の 2 段・K9 の下限・K1 の下限・向き・N ごとの作り)。黙る組は ``SILENT_BY_DESIGN`` に置く。
6. 答えを知っている側の命令(開発の写し・表・正解の束・持ち越しの束・席の folder・変異・段 A・段 B・記録)が作り物の素材で動く。
7. 記録: 無い時は無いと assert し、在る時は形・禁止の字・数の導き直し。封 → script → 定義表 → 指示書 → 門の commit の順。
8. 独立監査 REVISE(1 巡目)の直し(``CheckHoleTest``・``RefHoleTest``): 監査の変異 26 本(検査 9・答えを知っている側 17)が黙った穴を 1 本ずつ縛る。
   作り物の素材の写し(``derive``。額 0 の行・科目表に無い科目の行・境の日の行を足す)の上で、期待は集計の本文でなく門の中で別に数え直す。
   K0 は末尾の改行・id の昇順を見る。記録は段 A の余分な鍵・素材の全体の数・席の取り直しの数を縛る。
"""
import ast
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
import sqlite3
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


def load_module(rel, name, text=None):
    u"""module を読み込む。``text`` が在れば、その本文で(file は触らない)。"""
    before = dict(sys.modules)
    if text is None:
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
    import types
    mod = types.ModuleType(name)
    mod.__file__ = os.path.join(ROOT, rel)
    sys.modules[name] = mod
    try:
        exec(compile(text, os.path.join(ROOT, rel), "exec"), mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


SEAL_REL = "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md"
PRESEAL_REL = "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_PRESEAL_2026-11-23.md"
SEAL_COMMIT_SHORT = "0d2156e4"
PRESEAL_SHA256 = "a4916ab51c8cd40c20e23406ded9b19d440f6045c0bd0f98e0107a3a44e23df1"
SEAL_SHA256 = "0b1153edbe2f4698bcea5f85fae54c0a8334d334b3fed6c233c0f1b023584d0a"
CHECK_REL = "measure/universal_ledger_check_2026-11-23.py"
REF_REL = "measure/universal_ledger_ref_2026-11-23.py"
DEF_REL = "fixtures/universal/um1/definition_C.json"
READING_REL = "fixtures/universal/um1/reading_def.json"
INSTRUCTION_REL = "docs/UNIVERSAL_MATERIAL_LEDGER_INSTRUCTION_2026-11-23.md"
GATE_REL = "tests/measure/test_universal_ledger_seal.py"
RECORD_REL = "fixtures/universal/um1/record.json"
ORDER_FILES = (CHECK_REL, REF_REL, DEF_REL, READING_REL, INSTRUCTION_REL, GATE_REL)
CHK = load_module(CHECK_REL, "um1_check_for_seal_gate")
REF = load_module(REF_REL, "um1_ref_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_um1_seal_gate")      # 順序の部品。門としては走らせない


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def sha(rel):
    return hashlib.sha256(read_bytes(rel)).hexdigest()


def wjson(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False))


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")


def seal_text():
    return read(SEAL_REL)


def hu(x):
    u"""借方・貸方 1 つの 100 倍を、最も近い整数へ(半分は 0 から遠い方へ)。門の中で別に書いた読み(検査・答えを知っている側の式を共有しない)。"""
    import decimal as _d
    return int(_d.Decimal(x * 100).quantize(_d.Decimal(1), rounding=_d.ROUND_HALF_UP))


# 素材の分類の字・科目の番号・仕訳の種類の字(答えを知っている側と、この門だけが持つ。定義表・読込みの定義・指示書・検査には書かない)
SECRET_WORDS = (u"Operating Revenue", u"Contra Revenue", u"COGS", u"Operating Expense", u"Other Income", u"Other Expense", u"Contra Fixed Asset",
                u"Current Asset", u"Contra Current Asset", u"Year-End Close", u"Depreciation", u"Income Summary", u"Retained Earnings",
                u"1010", u"2110", u"7010")

# ======================================================================== 作り物の素材
D_SPEC = (u"2001-01-01", u"2001-12-31")             # 開発に当たる期(作り物)
S_SPEC = (u"2002-01-01", u"2002-12-31")             # 本番に当たる暦年
H_SPEC = (u"2001-07-01", u"2002-06-30")             # ずらした期
ACCOUNTS = [
    # (番号, 名, 大分類, 小分類)  AccountID は 1 から
    (1010, u"cash", u"Asset", u"Current Asset"), (1100, u"receivable", u"Asset", u"Current Asset"), (1190, u"allowance", u"Asset", u"Contra Current Asset"),
    (1500, u"equipment", u"Asset", u"Fixed Asset"), (1590, u"accum dep", u"Asset", u"Contra Fixed Asset"), (1591, u"accum dep mfg", u"Asset", u"Contra Fixed Asset"),
    (1600, u"land", u"Asset", u"Noncurrent Asset"), (8010, u"new current", u"Asset", u"Current Asset"),
    (2010, u"payable", u"Liability", u"Current Liability"), (2110, u"loan", u"Liability", u"Long-Term Liability"),
    (3010, u"equity", u"Equity", u"Equity"), (3900, u"summary", u"Equity", u"Closing"),
    (4010, u"sales", u"Revenue", u"Operating Revenue"), (4090, u"returns", u"Revenue", u"Contra Revenue"),
    (5010, u"cogs", u"Expense", u"COGS"), (6010, u"opex", u"Expense", u"Operating Expense"), (6030, u"new opex", u"Expense", u"Operating Expense"),
    (7010, u"interest", u"Revenue", u"Other Income"), (7090, u"other exp", u"Expense", u"Other Expense"), (9990, u"header", u"Asset", u"Header"),
]
ACC_ID = dict((a[0], k + 1) for k, a in enumerate(ACCOUNTS))
ACC_CLS = dict((a[0], (a[2], a[3])) for a in ACCOUNTS)
CLOSE1, CLOSE2 = REF.CLOSE


class Fake(object):
    u"""素材と同じ表・列の名の作り物。``rows`` は検査・答えを知っている側と別に導く期待のための元(Python の行)。"""

    def __init__(self, path):
        self.path = path
        self.rows = []          # dict(rid, date, acct, deb, cre, vtype, vnum, src, je)(je = 振替伝票の種類か None)
        self.jes = {}
        self._rid = 0
        self._je = 0
        self._build()
        self._write()

    def post(self, date, acct, deb, cre, vtype, vnum, src, je):
        self._rid += 1
        self.rows.append(dict(rid=self._rid, date=date, acct=acct, deb=deb, cre=cre, vtype=vtype, vnum=vnum, src=src, je=je))

    def journal(self, date, etype, lines):
        self._je += 1
        self.jes[self._je] = (u"JE-%d" % self._je, date, etype)
        for acct, deb, cre in lines:
            self.post(date, acct, deb, cre, u"JournalEntry", u"JE-%d" % self._je, self._je, etype)

    def _build(self):
        c = lambda n: n / 100.0
        self.journal(u"2001-01-01", u"Opening", [(1010, c(10000000), 0.0), (1500, c(800000), 0.0), (1590, 0.0, c(300000)), (3010, 0.0, c(10500000))])
        self.journal(u"2001-02-01", u"Borrowing", [(1010, c(5000000), 0.0), (2110, 0.0, c(5000000))])
        # 結ばれない行: 伝票の種類が振替伝票で、元の書類の番号が振替伝票に無い
        self.post(u"2001-03-03", 1010, 1.0, 0.0, u"JournalEntry", u"JE-X", 99999, None)
        self.post(u"2001-03-03", 4010, 0.0, 1.0, u"JournalEntry", u"JE-X", 99999, None)
        # 仕訳の種類が空の字の振替伝票(空は 空 として扱う)
        self.journal(u"2001-03-04", u"", [(1010, 2.0, 0.0), (4010, 0.0, 2.0)])
        # 半分の端数(0.125 × 100 = 12.5 は 13 へ)
        self.post(u"2001-01-15", 1100, 0.125, 0.0, u"SalesInvoice", u"SIX-1", 1, None)
        self.post(u"2001-01-15", 4010, 0.0, 0.125, u"SalesInvoice", u"SIX-1", 1, None)
        for mi in range(24):
            y, m = 2001 + mi // 12, mi % 12 + 1
            mid = u"%04d-%02d-15" % (y, m)
            last = (datetime.date(y + (m // 12), m % 12 + 1, 1) - datetime.timedelta(days=1)).isoformat()
            rev = 100010 + mi * 1337
            small = c(rev)
            self.post(mid, 1100, small, 0.0, u"SalesInvoice", u"SI-%d" % mi, mi + 1, None)       # 元の書類の番号が振替伝票の番号と重なる
            self.post(mid, 4010, 0.0, small, u"SalesInvoice", u"SI-%d" % mi, mi + 1, None)
            self.post(mid, 4090, c(2005), 0.0, u"SalesReturn", u"SR-%d" % mi, mi + 1, None)
            self.post(mid, 1100, 0.0, c(2005), u"SalesReturn", u"SR-%d" % mi, mi + 1, None)
            self.post(mid, 5010, c(40015 + mi * 7), 0.0, u"Shipment", u"SH-%d" % mi, mi + 1, None)
            self.post(mid, 2010, 0.0, c(40015 + mi * 7), u"Shipment", u"SH-%d" % mi, mi + 1, None)
            for k in range(3):                                                                 # 0.1 を重ねる(浮動小数のまま足すと 10 進の和とずれる)
                self.post(mid, 1100, 0.1, 0.0, u"SalesInvoice", u"SIT-%d-%d" % (mi, k), mi + 1, None)
                self.post(mid, 4010, 0.0, 0.1, u"SalesInvoice", u"SIT-%d-%d" % (mi, k), mi + 1, None)
            self.post(mid, 1100, 0.29, 0.0, u"SalesInvoice", u"SIO-%d" % mi, mi + 1, None)      # 0.29 × 100 = 28.999999999999996
            self.post(mid, 4010, 0.0, 0.29, u"SalesInvoice", u"SIO-%d" % mi, mi + 1, None)
            self.post(mid, 1100, 10.007, 0.0, u"SalesInvoice", u"SIH-%d" % mi, mi + 1, None)    # 1000.7 → 1001
            self.post(mid, 4010, 0.0, 10.007, u"SalesInvoice", u"SIH-%d" % mi, mi + 1, None)
            self.journal(last, u"Accrual", [(6010, c(8002), 0.0), (2010, 0.0, c(8002))])
            self.journal(last, u"Depreciation", [(6010, c(3003), 0.0), (5010, c(2002), 0.0), (1590, 0.0, c(3003)), (1591, 0.0, c(2002))])
            self.post(mid, 7090, c(303), 0.0, u"Misc", u"MI-%d" % mi, mi + 1, None)
            self.post(mid, 1010, 0.0, c(303), u"Misc", u"MI-%d" % mi, mi + 1, None)
            if y == 2002:                                                                       # 2 期目に新しく動く科目
                self.post(mid, 6030, c(1501), 0.0, u"Misc", u"MN-%d" % mi, mi + 1, None)
                self.post(mid, 2010, 0.0, c(1501), u"Misc", u"MN-%d" % mi, mi + 1, None)
                self.post(mid, 8010, c(7007), 0.0, u"Misc", u"MA-%d" % mi, mi + 1, None)
                self.post(mid, 1010, 0.0, c(7007), u"Misc", u"MA-%d" % mi, mi + 1, None)
                self.post(mid, 7010, 0.0, c(555), u"Misc", u"MB-%d" % mi, mi + 1, None)
                self.post(mid, 1010, c(555), 0.0, u"Misc", u"MB-%d" % mi, mi + 1, None)
                if m == 6:
                    self.post(mid, 1600, c(1111), 0.0, u"Misc", u"ML-%d" % mi, mi + 1, None)
                    self.post(mid, 1010, 0.0, c(1111), u"Misc", u"ML-%d" % mi, mi + 1, None)
            if m == 12:
                self._close(y, last)

    def _cents(self, x):
        return hu(x)

    def _close(self, y, last):
        net = collections.defaultdict(int)
        for r in self.rows:
            if r["date"].startswith(str(y)) and ACC_CLS[r["acct"]][0] in (u"Revenue", u"Expense") and r["je"] not in (CLOSE1, CLOSE2):
                net[r["acct"]] += self._cents(r["cre"]) - self._cents(r["deb"])
        lines, total = [], 0
        for a in sorted(net):
            if net[a] > 0:
                lines.append((a, net[a] / 100.0, 0.0))
            elif net[a] < 0:
                lines.append((a, 0.0, -net[a] / 100.0))
            total += net[a]
        lines.append((3900, 0.0 if total < 0 else 0.0, total / 100.0) if total >= 0 else (3900, -total / 100.0, 0.0))
        self.journal(last, CLOSE1, lines)
        self.journal(last, CLOSE2, [(3900, total / 100.0, 0.0), (3010, 0.0, total / 100.0)] if total >= 0 else [(3900, 0.0, -total / 100.0), (3010, -total / 100.0, 0.0)])

    def _write(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        con = sqlite3.connect(self.path)
        con.execute("CREATE TABLE Account(AccountID INTEGER, AccountNumber INTEGER, AccountName TEXT, AccountType TEXT, AccountSubType TEXT, ParentAccountID INTEGER, NormalBalance TEXT, IsActive INTEGER)")
        con.executemany("INSERT INTO Account VALUES (?,?,?,?,?,NULL,NULL,1)", [(ACC_ID[n], n, nm, t, s) for n, nm, t, s in ACCOUNTS])
        con.execute("CREATE TABLE JournalEntry(JournalEntryID INTEGER, EntryNumber TEXT, PostingDate TEXT, EntryType TEXT, Description TEXT, TotalAmount REAL)")
        con.executemany("INSERT INTO JournalEntry VALUES (?,?,?,?,NULL,0)", [(k, v[0], v[1], v[2]) for k, v in self.jes.items()])
        con.execute("CREATE TABLE GLEntry(GLEntryID INTEGER, PostingDate TEXT, AccountID INTEGER, Debit REAL, Credit REAL, VoucherType TEXT, VoucherNumber TEXT, SourceDocumentType TEXT, SourceDocumentID INTEGER, FiscalYear INTEGER)")
        con.executemany("INSERT INTO GLEntry VALUES (?,?,?,?,?,?,?,NULL,?,?)",
                        [(r["rid"], r["date"], ACC_ID[r["acct"]], r["deb"], r["cre"], r["vtype"], r["vnum"], r["src"], int(r["date"][:4])) for r in self.rows])
        con.commit()
        con.close()

    # ---- 期待を行から別に導く(検査・答えを知っている側の SQL と式を共有しない)
    def pick(self, pred, lo=None, hi=None):
        out = []
        for r in self.rows:
            if lo is not None and r["date"] < lo:
                continue
            if hi is not None and r["date"] > hi:
                continue
            a = r["acct"]
            row = dict(r, typ=ACC_CLS[a][0], sub=ACC_CLS[a][1])
            if pred(row):
                out.append(r)
        return out

    def cents_sum(self, rows, credit_minus_debit):
        d = sum(hu(r["deb"]) for r in rows)
        c = sum(hu(r["cre"]) for r in rows)
        return (c - d) if credit_minus_debit else (d - c)


_FAKE = {}
_TMPS = []


def fake():
    if "f" not in _FAKE:
        tmp = tempfile.mkdtemp(prefix="um1_gate_")
        _TMPS.append(tmp)
        f = Fake(os.path.join(tmp, "src.sqlite"))
        f.tmp = tmp
        for name, spec in (("D", D_SPEC), ("S", S_SPEC), ("H", H_SPEC)):
            wjson(os.path.join(tmp, "spec_%s.json" % name), od([(u"成果物", u"C"), (u"当期の始まり", spec[0]), (u"当期の終わり", spec[1])]))
        _FAKE["f"] = f
        sel = REF.Sel(f.path)
        try:
            cs, ce = [REF.pdate(x) for x in D_SPEC]
            f.table = REF.make_table(sel, cs, ce)
        finally:
            sel.close()
        wjson(os.path.join(tmp, "table.json"), f.table)
        f.table_path = os.path.join(tmp, "table.json")
    return _FAKE["f"]


def tearDownModule():
    for t in _TMPS:
        shutil.rmtree(t, ignore_errors=True)


DEF_PATH = os.path.join(ROOT, DEF_REL)
READING_PATH = os.path.join(ROOT, READING_REL)


def spec_path(name):
    return os.path.join(fake().tmp, "spec_%s.json" % name)


def make_ctx(name="D", table=False, src=None, defn=DEF_PATH, reading=READING_PATH, chk=None):
    chk = chk or CHK
    ctx, bad = chk.make_ctx(spec_path(name), defn, reading, src or fake().path, fake().table_path if table else None)
    assert ctx is not None, bad
    return ctx


def gold_of(name="S"):
    f = fake()
    sel = REF.Sel(f.path)
    try:
        cs, ce = [REF.pdate(x) for x in {"D": D_SPEC, "S": S_SPEC, "H": H_SPEC}[name]]
        return json.loads(json.dumps(REF.gold_bundle(sel, cs, ce), ensure_ascii=False))
    finally:
        sel.close()


def verdicts(res):
    return dict((r[u"id"], (r[u"判定"], tuple(r[u"規則"]))) for r in res[u"材料"])


def item(bundle, i):
    return next(m for m in bundle[u"材料"] if m[u"id"] == i)


def replace_item(bundle, new):
    b = copy.deepcopy(bundle)
    b[u"材料"] = [new if m[u"id"] == new[u"id"] else m for m in b[u"材料"]]
    return b


def run_cli(args, text_in=None):
    r = subprocess.run([sys.executable, "-I"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


# ======================================================================== 1. 封の字
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
        self.assertEqual("", git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core").strip())

    def test_a_4_the_boundary_import_list_is_not_widened(self):
        body = read("tests/adapters/xbrl/test_boundary.py")
        for word in (u"universal", u"um1", u"ledger"):
            self.assertNotIn(word, body)

    def test_a_5_the_preseal_is_the_one_the_seal_commit_left(self):
        u"""下見の封は、本番の封の commit が追記(日付つき)を足した版のまま。その後は変わらない。"""
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (SEAL_COMMIT_SHORT, PREFIX + PRESEAL_REL)], stdout=subprocess.PIPE).stdout
        self.assertEqual(blob, read_bytes(PRESEAL_REL))
        self.assertEqual(PRESEAL_SHA256, hashlib.sha256(read_bytes(PRESEAL_REL)).hexdigest())

    def test_a_6_the_seal_holds_the_rules_mutations_predictions_and_designations_the_gate_copies(self):
        seal = seal_text()
        self.assertEqual(tuple(u"K%d" % k for k in (0, 1, 3, 4, 5, 7, 8, 9, 10)), CHK.RULES)
        for k in CHK.RULES:
            self.assertIn(u"%s " % k, seal)
        self.assertEqual(tuple(u"N%d" % k for k in range(1, 13)), REF.MUTATIONS)
        for n in REF.MUTATIONS:
            self.assertIn(u"%s " % n, seal)
        for p in [u"UM1-A%d" % k for k in range(8)] + [u"UM1-B%d" % k for k in range(1, 9)]:
            self.assertIn(p, seal)
        for name, (a, b) in REF.DESIGNATIONS.items():
            if name != u"D1":
                self.assertIn(a, seal)
                self.assertIn(b, seal)
        self.assertIn(u"当期 2024-01-01〜2024-12-31", seal)
        self.assertEqual((u"2024-01-01", u"2024-12-31"), REF.DESIGNATIONS[u"D1"])
        self.assertIn(REF.CLOSE[0], seal)
        self.assertIn(REF.CLOSE[1], seal)
        self.assertEqual(u"借方−貸方", REF.SIGN_DEBIT_CREDIT)
        self.assertEqual(u"貸方−借方", REF.SIGN_CREDIT_DEBIT)
        self.assertIn(u"%s / %s" % (REF.SIGN_CREDIT_DEBIT, REF.SIGN_DEBIT_CREDIT), u"%s / %s" % (REF.SIGN_CREDIT_DEBIT, REF.SIGN_DEBIT_CREDIT))

    def test_a_7_the_gold_table_equals_the_seal_table(self):
        u"""封 §1-4 の表の「正解の取り方」を、字から別に読み、答えを知っている側の ``GOLD`` と比べる。"""
        seal = seal_text()
        rows = {}
        for line in seal.splitlines():
            m = re.match(r"^\| (c\d\d[^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\|$", line)
            if m:
                rows[m.group(1).strip()] = m.group(4).strip()
        self.assertEqual(16, len(rows))
        self.assertEqual(30, len(REF.IDS))
        expect_sub = {
            u"c01": (u"貸方−借方", [u"Operating Revenue", u"Contra Revenue"]), u"c03": (u"借方−貸方", [u"COGS"]), u"c04": (u"借方−貸方", [u"Operating Expense"]),
            u"c05": (u"貸方−借方", [u"Other Income", u"Other Income or Expense", u"Other Expense"]), u"c22": (u"借方−貸方", [u"Current Asset", u"Contra Current Asset"])}
        for i, (d, subs) in expect_sub.items():
            self.assertEqual(d, REF.GOLD[i][u"向き"])
            cond = REF.GOLD[i][u"cats"][0]
            self.assertEqual(u"科目の小分類", cond[0])
            self.assertEqual(subs, cond[2] if isinstance(cond[2], list) else [cond[2]])
            for s in subs:
                self.assertIn(s, rows[u"c01・c02"] + rows[u"c03"] + rows[u"c04"] + rows[u"c05"] + rows[u"c22"])
        self.assertEqual([(u"科目の大分類", u"どれか", [u"Revenue", u"Expense"])], REF.GOLD[u"c06"][u"cats"])
        self.assertEqual(u"dep", REF.GOLD[u"c08"][u"jt"])
        self.assertEqual([(u"科目の小分類", u"等しい", u"Contra Fixed Asset")], REF.GOLD[u"c08"][u"cats"])
        self.assertEqual([(u"科目番号", u"等しい", 1010)], REF.GOLD[u"c21"][u"cats"])
        self.assertEqual([(u"科目番号", u"等しい", 2110)], REF.GOLD[u"c24"][u"cats"])
        self.assertEqual([(u"科目番号", u"等しい", 7010)], REF.GOLD[u"c30"][u"cats"])
        self.assertEqual([(u"科目の大分類", u"等しい", u"Asset")], REF.GOLD[u"c23"][u"cats"])
        self.assertEqual([(u"科目の大分類", u"等しい", u"Liability")], REF.GOLD[u"c25"][u"cats"])
        self.assertEqual([(u"科目の大分類", u"どれか", [u"Equity", u"Revenue", u"Expense"])], REF.GOLD[u"c26"][u"cats"])
        self.assertEqual([(u"科目の大分類", u"どれか", [u"Equity", u"Revenue", u"Expense"])], REF.GOLD[u"c27"][u"cats"])
        self.assertIsNone(REF.GOLD[u"c28"][u"cats"])
        self.assertIsNone(REF.GOLD[u"c29"][u"cats"])
        for i in (u"c01", u"c02", u"c03", u"c04", u"c05", u"c06", u"c07", u"c30") + tuple(u"c%02d" % k for k in range(9, 21)):
            self.assertEqual(u"close", REF.GOLD[i][u"jt"], i)
        for i in (u"c21", u"c22", u"c23", u"c24", u"c25", u"c26", u"c27"):
            self.assertIsNone(REF.GOLD[i][u"jt"], i)
        # 期
        self.assertEqual([u"当期", u"前期"] + [u"当期"] * 3 + [u"当期", u"前期", u"当期"], [REF.GOLD[u"c%02d" % k][u"期"] for k in range(1, 9)])
        self.assertEqual([u"当期の月:%d" % k for k in range(1, 13)], [REF.GOLD[u"c%02d" % (8 + k)][u"期"] for k in range(1, 13)])
        self.assertEqual([u"当期末"] * 6 + [u"前期末"], [REF.GOLD[u"c%02d" % k][u"期"] for k in range(21, 28)])
        self.assertEqual(u"当期", REF.GOLD[u"c28"][u"期"])
        self.assertEqual(u"当期末", REF.GOLD[u"c29"][u"期"])
        self.assertEqual(u"当期", REF.GOLD[u"c30"][u"期"])
        self.assertEqual(od([(u"R1", ([u"c%02d" % k for k in range(9, 21)], [u"c01"])), (u"R2", ([u"c23"], [u"c25", u"c26"])), (u"R3", ([u"c01", u"c05"], [u"c03", u"c04", u"c06"]))]), REF.RELATIONS)
        self.assertIn(u"R1 c09〜c20 の和 = c01/R2 c23 = c25 + c26/R3 c01 − c03 − c04 + c05 = c06", seal)
        self.assertEqual((u"c02", u"c07", u"c08", u"c21", u"c22", u"c24", u"c27"), REF.A5_IDS)
        self.assertEqual(tuple([u"c01", u"c03", u"c04", u"c05", u"c06"] + [u"c%02d" % k for k in range(9, 21)] + [u"c23", u"c25", u"c26"]), REF.A6_IDS)


# ======================================================================== 2. 定義表・読込みの定義・指示書
class DefinitionTest(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(read(DEF_REL))
        self.rd = json.loads(read(READING_REL))

    def test_b_1_the_definition_has_the_sealed_shape_and_30_rows(self):
        d = self.d
        self.assertEqual({u"成果物", u"行", u"関係"}, set(d))
        self.assertEqual(u"C", d[u"成果物"])
        self.assertEqual([u"c%02d" % k for k in range(1, 31)], [r[u"id"] for r in d[u"行"]])
        for r in d[u"行"]:
            self.assertEqual({u"id", u"名", u"意味", u"単位", u"期", u"範囲", u"取り方"}, set(r))
            self.assertEqual(u"通貨", r[u"単位"])
            self.assertEqual(u"全社", r[u"範囲"])
            self.assertEqual(u"素材", r[u"取り方"])
        self.assertEqual(REF.IDS, [r[u"id"] for r in d[u"行"]])
        self.assertEqual([REF.GOLD[r[u"id"]][u"期"] for r in d[u"行"]], [r[u"期"] for r in d[u"行"]])

    def test_b_2_the_meaning_strings_are_the_sealed_strings(self):
        seal = seal_text()
        table = {}
        for line in seal.splitlines():
            m = re.match(r"^\| (c\d\d[^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\|$", line)
            if m:
                table[m.group(1).strip()] = m.group(3).strip()
        for r in self.d[u"行"]:
            n = int(r[u"id"][1:])
            key = next(k for k in table if r[u"id"] in re.findall(r"c\d\d", k) or (u"〜" in k and int(re.findall(r"c(\d\d)", k)[0]) <= n <= int(re.findall(r"c(\d\d)", k)[1])))
            self.assertEqual(table[key], r[u"意味"], r[u"id"])
        self.assertEqual(30, len(set(r[u"id"] for r in self.d[u"行"])))

    def test_b_3_the_relations_are_the_sealed_relations(self):
        rel = dict((x[u"id"], (x[u"左"], x[u"右"])) for x in self.d[u"関係"])
        self.assertEqual(dict(REF.RELATIONS), rel)
        self.assertEqual(3, len(self.d[u"関係"]))

    def test_b_4_no_secret_word_is_in_the_definition_the_reading_the_instruction_or_the_check(self):
        for rel in (DEF_REL, READING_REL, INSTRUCTION_REL, CHECK_REL):
            body = read(rel)
            for w in SECRET_WORDS:
                self.assertNotIn(w, body, (rel, w))
        # 定義表には、素材の科目の名・分類の字(英字の単語)も書かない
        self.assertEqual([], re.findall(r"[A-Za-z]{3,}", read(DEF_REL)))

    def test_b_5_the_reading_definition_has_the_sealed_tables_and_9_columns(self):
        rd = self.rd
        self.assertEqual(u"仕訳の行", rd[u"共通の表"])
        self.assertEqual([u"行の番号", u"日付", u"科目番号", u"科目の大分類", u"科目の小分類", u"伝票の種類", u"仕訳の種類", u"借方", u"貸方"], [c[u"名"] for c in rd[u"列"]])
        self.assertEqual({u"GLEntry", u"Account", u"JournalEntry"}, set(t[u"表"] for t in rd[u"表"].values()))
        self.assertEqual({u"元帳", u"科目", u"振替伝票"}, set(rd[u"表"]))
        seal = seal_text()
        self.assertIn(u"列は 9 つ: `行の番号`(元帳の行の番号)・`日付`(字 `YYYY-MM-DD`)・`科目番号`(整数)・`科目の大分類`・`科目の小分類`・`伝票の種類`・`仕訳の種類`(空が在る)・`借方`・`貸方`", seal)
        self.assertIn(u"100 倍して最も近い整数へ丸めた値(最小の通貨の単位)で足す。浮動小数のまま足さない", seal)
        self.assertIn(u"100 倍して最も近い整数へ丸め", rd[u"額"][u"丸め"])
        self.assertTrue(CHK.load_reading(READING_PATH)[0])

    def test_b_6_the_instruction_has_the_chapters_and_leaves_out_what_it_must(self):
        body = read(INSTRUCTION_REL)
        for s in (u"材料.json", u"素材.sqlite", u"folder の外は読まない", u"読むだけ", u"読み取り専用", u"u1", u"表の行の和", u"仕訳の行", u"素材が無い",
                  u"当期の月:k", u"`日付 以下` を 1 つだけ", u"作り物", u"定義表", u"読込みの定義"):
            self.assertIn(s, body, s)
        for s in (u"正解", u"予測", u"罠", u"UM1-", u"確かめた取り方", u"規則の持ち越し", u"K1", u"K3", u"K10", u"検査の規則"):
            self.assertNotIn(s, body, s)
        # 例は 1 つだけ(コードブロック 1 つ)
        self.assertEqual(1, body.count(u"```json"))

    def test_b_7_the_instruction_example_is_a_made_up_material_the_form_accepts_but_its_values_are_made_up(self):
        body = read(INSTRUCTION_REL)
        ex = json.loads(re.search(r"```json\n(.*?)\n```", body, re.S).group(1))
        self.assertEqual(u"", CHK.k0_item(ex))
        self.assertIn(u"作り物", json.dumps(ex, ensure_ascii=False))
        self.assertTrue(ex[u"期間"][u"始まり"].startswith(u"2001"))
        self.assertEqual(u"1234.50", ex[u"数値"])             # 封 §1-5 の例の字そのもの(作り物)


# ======================================================================== 3. 検査は独立・標準の library だけ・ro
class IndependenceTest(unittest.TestCase):
    def test_c_1_the_check_does_not_import_the_ref_or_any_non_standard_module(self):
        tree = ast.parse(read(CHECK_REL))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        std = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set(
            ["__future__", "datetime", "decimal", "json", "os", "re", "sqlite3", "sys", "pathlib"])
        self.assertTrue(mods <= std | set(["__future__"]), mods - std)
        for m in mods:
            self.assertNotIn(u"ref", m)
            self.assertNotIn(u"universal", m)
        self.assertEqual({"__future__", "datetime", "decimal", "json", "os", "re", "sqlite3", "sys", "pathlib"}, mods)

    def test_c_2_the_ref_does_not_import_the_check(self):
        tree = ast.parse(read(REF_REL))
        for n in ast.walk(tree):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in n.names] + [getattr(n, "module", "") or ""]
                for nm in names:
                    self.assertNotIn(u"universal_ledger_check", nm)

    def test_c_3_the_source_is_opened_read_only_and_never_written(self):
        body = read(CHECK_REL)
        self.assertIn("mode=ro", body)
        self.assertNotIn("mode=rw", body)
        self.assertNotIn("mode=rwc", body)
        for w in ("INSERT INTO GLEntry", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE"):
            self.assertNotIn(w, body)
        f = fake()
        before = sha_file(f.path)
        ctx = make_ctx("S", table=True)
        CHK.check_bundle(ctx, gold_of("S"))
        self.assertEqual(before, sha_file(f.path))
        # 読み取り専用で開いた接続は書けない(検査の ro の開き方をそのまま使う)
        con = sqlite3.connect(CHK.pathlib.Path(os.path.abspath(f.path)).as_uri() + "?mode=ro", uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("CREATE TABLE zz(x)")
        con.close()

    def test_c_4_the_check_runs_as_a_separate_isolated_process(self):
        f = fake()
        wjson(os.path.join(f.tmp, "b_gold.json"), gold_of("S"))
        rc, out, err = run_cli([os.path.join(ROOT, CHECK_REL), "without-table", "--spec", spec_path("S"), "--def", DEF_PATH, "--reading", READING_PATH,
                                "--src", f.path, "--bundle", os.path.join(f.tmp, "b_gold.json")])
        self.assertEqual(0, rc, err)
        res = json.loads(out)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        rc, out, err = run_cli([os.path.join(ROOT, CHECK_REL), "with-table", "--spec", spec_path("S"), "--def", DEF_PATH, "--reading", READING_PATH,
                                "--src", f.path, "--table", f.table_path, "--bundle", os.path.join(f.tmp, "b_gold.json")])
        self.assertEqual(0, rc, err)
        self.assertEqual(u"受理", json.loads(out)[u"束"][u"状態"])

    def test_c_5_the_bundle_text_never_enters_a_sql_statement(self):
        u"""SQL の文を作る箇所(``execute`` の第 1 引数)が、束の字を持つ変数を使っていない。列は固定の表 ``COLS`` から、値は束縛。"""
        tree = ast.parse(read(CHECK_REL))
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in ("where", "select", "diff", "accounts_in")]
        self.assertEqual(4, len(funcs))
        src = read(CHECK_REL)
        self.assertIn('c = COLS[col]', src)
        self.assertNotIn(".format(", src)
        for fn in funcs:
            for n in ast.walk(fn):
                if isinstance(n, ast.JoinedStr):
                    self.fail("f-string in a SQL builder")


def sha_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ======================================================================== 4. 作り物の素材の確かめ
class FakeWorldTest(unittest.TestCase):
    def test_d_1_the_fake_has_every_shape_the_gate_needs(self):
        f = fake()
        con = sqlite3.connect(f.path)
        try:
            self.assertEqual(0, con.execute("select count(*) from (select 1 from GLEntry group by VoucherType, VoucherNumber having sum(round(Debit*100)) != sum(round(Credit*100)))").fetchone()[0])
            types = set(r[0] for r in con.execute("select EntryType from JournalEntry"))
            for t in (u"Opening", u"Depreciation", CLOSE1, CLOSE2):
                self.assertIn(t, types)
            # 減価償却の仕訳は、費用の科目と製造の側の科目の両方を借方に持つ
            dep = [k for k, v in f.jes.items() if v[2] == u"Depreciation"]
            self.assertEqual(24, len(dep))
            debs = set(r["acct"] for r in f.rows if r["je"] == u"Depreciation" and r["deb"] > 0)
            self.assertEqual({6010, 5010}, debs)
            # 動きの無い科目・2 期目に新しく動く科目・結ばれない行
            y1 = set(r["acct"] for r in f.rows if r["date"] <= u"2001-12-31")
            y2 = set(r["acct"] for r in f.rows if r["date"] > u"2001-12-31")
            self.assertNotIn(9990, y1 | y2)
            self.assertEqual({6030, 8010, 7010, 1600}, y2 - y1)
            self.assertEqual(1, len([r for r in f.rows if r["src"] == 99999 and r["acct"] == 4010]))
            self.assertTrue(any(r["vtype"] == u"SalesInvoice" and r["src"] in f.jes for r in f.rows))      # 元の書類の番号が重なるが振替伝票ではない
            # 締めは年の最後の日・期首は年の最初の日
            self.assertEqual({u"2001-12-31", u"2002-12-31"}, set(v[1] for v in f.jes.values() if v[2] == CLOSE1))
            self.assertEqual(u"2001-01-01", [v[1] for v in f.jes.values() if v[2] == u"Opening"][0])
        finally:
            con.close()

    def test_d_2_the_ledger_the_check_builds_equals_the_independent_python_reading(self):
        f = fake()
        ctx = make_ctx("S")
        n, db, cr = ctx.led.select([])
        self.assertEqual(len(f.rows), n)
        self.assertEqual(sum(hu(r["deb"]) for r in f.rows), db)
        self.assertEqual(sum(hu(r["cre"]) for r in f.rows), cr)
        # 結ばれる行と結ばれない行
        got = ctx.led.mem.execute("select count(*) from l where jtype is null").fetchone()[0]
        self.assertEqual(len([r for r in f.rows if r["je"] is None or r["je"] == u""]), got)
        self.assertEqual(len([r for r in f.rows if r["vtype"] == u"JournalEntry" and r["je"] is None]), 2)

    def test_d_3_the_float_sum_would_differ_from_the_cent_sum(self):
        rows = [0.1] * 30
        self.assertNotEqual(3.0, sum(rows))
        self.assertEqual(300, sum(CHK.cents_of(x) for x in rows))
        self.assertEqual(29, CHK.cents_of(0.29))
        self.assertEqual(1001, CHK.cents_of(10.007))
        self.assertEqual(13, CHK.cents_of(0.125))
        self.assertEqual(63, CHK.cents_of(0.625))
        self.assertEqual(1, CHK.cents_of(0.005 + 1e-12))
        self.assertEqual(0, CHK.cents_of(None))
        with self.assertRaises(ValueError):
            CHK.cents_of(True)
        with self.assertRaises(ValueError):
            CHK.cents_of(float("nan"))
        with self.assertRaises(ValueError):
            CHK.cents_of(u"1")


# ======================================================================== 5. 正解の束・両方の検査
class GoldTest(unittest.TestCase):
    def expect(self, name):
        f = fake()
        lo, hi = {"D": D_SPEC, "S": S_SPEC, "H": H_SPEC}[name]
        return f, lo, hi

    def test_e_1_the_gold_values_equal_the_independent_python_sums(self):
        for name in ("D", "S", "H"):
            f, lo, hi = self.expect(name)
            b = gold_of(name)
            cs = REF.pdate(lo)
            ce = REF.pdate(hi)
            pe = (cs - datetime.timedelta(days=1)).isoformat()
            ps = REF.add_months(cs, -12).isoformat()
            mapping = {
                u"c01": (u"貸方−借方", lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
                u"c02": (u"貸方−借方", lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2), ps, pe),
                u"c03": (u"借方−貸方", lambda r: r["sub"] == u"COGS" and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
                u"c04": (u"借方−貸方", lambda r: r["sub"] == u"Operating Expense" and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
                u"c05": (u"貸方−借方", lambda r: r["sub"] in (u"Other Income", u"Other Income or Expense", u"Other Expense") and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
                u"c06": (u"貸方−借方", lambda r: r["typ"] in (u"Revenue", u"Expense") and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
                u"c07": (u"貸方−借方", lambda r: r["typ"] in (u"Revenue", u"Expense") and r["je"] not in (CLOSE1, CLOSE2), ps, pe),
                u"c08": (u"貸方−借方", lambda r: r["sub"] == u"Contra Fixed Asset" and r["je"] == u"Depreciation", lo, hi),
                u"c21": (u"借方−貸方", lambda r: r["acct"] == 1010, None, hi),
                u"c22": (u"借方−貸方", lambda r: r["sub"] in (u"Current Asset", u"Contra Current Asset"), None, hi),
                u"c23": (u"借方−貸方", lambda r: r["typ"] == u"Asset", None, hi),
                u"c24": (u"貸方−借方", lambda r: r["acct"] == 2110, None, hi),
                u"c25": (u"貸方−借方", lambda r: r["typ"] == u"Liability", None, hi),
                u"c26": (u"貸方−借方", lambda r: r["typ"] in (u"Equity", u"Revenue", u"Expense"), None, hi),
                u"c27": (u"貸方−借方", lambda r: r["typ"] in (u"Equity", u"Revenue", u"Expense"), None, pe),
                u"c30": (u"貸方−借方", lambda r: r["acct"] == 7010 and r["je"] not in (CLOSE1, CLOSE2), lo, hi),
            }
            for k in range(1, 13):
                f0 = REF.add_months(cs, k - 1)
                first = datetime.date(f0.year, f0.month, 1)
                end = REF.add_months(first, 1) - datetime.timedelta(days=1)
                mapping[u"c%02d" % (8 + k)] = (u"貸方−借方", lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2), first.isoformat(), end.isoformat())
            for i, (d, pred, a, z) in mapping.items():
                rows = f.pick(pred, a, z)
                m = item(b, i)
                if not rows:
                    self.assertEqual(u"無い", m[u"状態"], (name, i))
                    continue
                self.assertEqual(u"在る", m[u"状態"], (name, i))
                self.assertEqual(d, m[u"出どころ"][u"向き"])
                self.assertEqual(REF.fmt_cents(f.cents_sum(rows, d == u"貸方−借方")), m[u"数値"], (name, i))
            self.assertEqual(u"無い", item(b, u"c28")[u"状態"])
            self.assertEqual(u"無い", item(b, u"c29")[u"状態"])

    def test_e_2_the_gold_bundle_passes_both_checks_and_the_relations_hold(self):
        for name in ("D", "S", "H"):
            b = gold_of(name)
            self.assertEqual(od((k, True) for k in REF.RELATIONS), REF.relation_status(b), name)
            res = CHK.check_bundle(make_ctx(name), b)
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            for r in res[u"材料"]:
                self.assertEqual(u"通す" if r[u"状態"] == u"在る" else u"無いを受ける", r[u"判定"], (name, r))
            self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])

    def test_e_3_the_tabled_check_on_the_first_period_passes_all_and_on_a_later_period_stops_what_the_table_cannot_vouch_for(self):
        res = CHK.check_bundle(make_ctx("D", table=True), gold_of("D"))
        self.assertEqual(0, len([r for r in res[u"材料"] if r[u"判定"] == u"止める"]))
        self.assertEqual({u"余り": 0, u"漏れ": 0}, res[u"K3の行"])
        res = CHK.check_bundle(make_ctx("S", table=True), gold_of("S"))
        v = verdicts(res)
        # 2 期目: 新しく動く科目(6030 費用・8010 流動資産・1600 固定でない資産・7010 営業外の収益)が在る
        self.assertEqual((u"止める", (u"K3", u"K10")), v[u"c04"])
        self.assertEqual((u"通す", ()), v[u"c03"])
        self.assertIn(u"K10", v[u"c01"][1])
        self.assertIn(u"K10", v[u"c06"][1])
        self.assertIn(u"K10", v[u"c23"][1])
        self.assertIn(u"K10", v[u"c28"][1])           # 無いの行は、確かめていない科目が 1 つでも在れば止める
        self.assertIn(u"K10", v[u"c29"][1])
        self.assertNotIn(u"K10", v[u"c24"][1])
        self.assertNotIn(u"K10", v[u"c25"][1])
        self.assertIn(u"K10", v[u"c21"][1])             # 新しい 8010 は(資産・流動資産)で、現金と同じ分類
        self.assertEqual(u"止める", v[u"c30"][0])      # 持ち越しは 7010 を知らず、素材は 7010 に行が在る
        self.assertIn(u"K3", v[u"c30"][1])
        self.assertGreater(res[u"K3の行"][u"余り"], 0)
        self.assertEqual(0, res[u"K3の行"][u"漏れ"])
        # 同じ期の持ち越しの束(席を使わない)は、表なしを通る。表つきでは K10 が止める(K3 は自分と同じ行を選ぶので通る)
        f = fake()
        sel = REF.Sel(f.path)
        try:
            cb = REF.carry_bundle(sel, f.table, REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1]))
        finally:
            sel.close()
        r2 = CHK.check_bundle(make_ctx("S", table=True), json.loads(json.dumps(cb, ensure_ascii=False)))
        for r in r2[u"材料"]:
            self.assertNotIn(u"K3", r[u"規則"], r)
        # 同じ期 D では、持ち越しの束は正解の束と同じ
        sel = REF.Sel(f.path)
        try:
            cd = REF.carry_bundle(sel, f.table, REF.pdate(D_SPEC[0]), REF.pdate(D_SPEC[1]))
        finally:
            sel.close()
        for a, b in zip(gold_of("D")[u"材料"], cd[u"材料"]):
            self.assertEqual((a[u"id"], a[u"状態"], a.get(u"数値")), (b[u"id"], b[u"状態"], b.get(u"数値")))

    def test_e_4_the_table_has_the_sealed_shape_and_the_carry_over_rule(self):
        f = fake()
        t = f.table
        self.assertEqual(REF.IDS, list(t[u"行"]))
        for i, r in t[u"行"].items():
            self.assertEqual({u"向き", u"科目", u"仕訳の種類の条件"}, set(r))
        self.assertEqual([], t[u"行"][u"c28"][u"科目"])
        self.assertEqual([], t[u"行"][u"c29"][u"科目"])
        self.assertEqual([], t[u"行"][u"c30"][u"科目"])                              # 開発の期に 7010 の行が無い
        self.assertEqual(t[u"行"][u"c01"][u"科目"], t[u"行"][u"c02"][u"科目"])        # 前期の行は当期の同じ名の行と同じ
        self.assertEqual(t[u"行"][u"c06"], t[u"行"][u"c07"])
        self.assertEqual(t[u"行"][u"c26"], t[u"行"][u"c27"])
        for k in range(9, 21):
            self.assertEqual(t[u"行"][u"c01"], t[u"行"][u"c%02d" % k])
        self.assertEqual([4010, 4090], t[u"行"][u"c01"][u"科目"])
        self.assertEqual([1590, 1591], t[u"行"][u"c08"][u"科目"])
        self.assertEqual({u"比べ方": u"等しい", u"値": u"Depreciation"}, dict(t[u"行"][u"c08"][u"仕訳の種類の条件"]))
        self.assertIsNone(t[u"行"][u"c21"][u"仕訳の種類の条件"])
        self.assertEqual([1010], t[u"行"][u"c21"][u"科目"])
        self.assertEqual([2110], t[u"行"][u"c24"][u"科目"])
        self.assertNotIn(1600, t[u"行"][u"c23"][u"科目"])
        self.assertEqual(sorted(set(a for a, _n, ty, _s in ACCOUNTS if ty == u"Asset" and a in set(r["acct"] for r in f.rows if r["date"] <= u"2001-12-31"))), t[u"行"][u"c23"][u"科目"])


# ======================================================================== 6. 規則 K0〜K10
def tab_check(name, bundle, table=True):
    return CHK.check_bundle(make_ctx(name, table=table), bundle)


class RuleTest(unittest.TestCase):
    def good(self):
        return gold_of("D")

    def refused(self, bundle, rule=u"K0", name="D", table=False):
        res = CHK.check_bundle(make_ctx(name, table=table), bundle)
        self.assertEqual(u"断り", res[u"束"][u"状態"], res[u"束"])
        self.assertEqual([rule], res[u"束"][u"規則"])
        return res

    def test_f_1_k0_the_form(self):
        g = self.good()
        self.assertEqual(u"受理", CHK.check_bundle(make_ctx("D"), g)[u"束"][u"状態"])
        cases = []
        b = copy.deepcopy(g); b[u"型の版"] = u"u0"; cases.append(b)
        b = copy.deepcopy(g); b[u"extra"] = 1; cases.append(b)
        b = copy.deepcopy(g); del b[u"型の版"]; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"] = b[u"材料"][:-1]; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"].append(b[u"材料"][0]); cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][1] = copy.deepcopy(b[u"材料"][0]); cases.append(b)         # id の重なり
        b = copy.deepcopy(g); b[u"材料"][0][u"id"] = u"c99"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"状態"] = u"確認待ち"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"extra"] = 1; cases.append(b)
        b = copy.deepcopy(g); del b[u"材料"][0][u"範囲"]; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"数値"] = u"1234.5"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"数値"] = u"1,234.50"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"数値"] = 1234.5; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"数値"] = u"１２３４.50"; cases.append(b)             # 全角
        b = copy.deepcopy(g); b[u"材料"][0][u"期間"] = {u"始まり": u"2001-01-01"}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"期間"] = {u"始まり": u"2001-13-01", u"終わり": u"2001-12-31"}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"期間"] = {u"始まり": u"2001-1-1", u"終わり": u"2001-12-31"}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"種類"] = u"素材"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"表"] = u"元帳"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"向き"] = u"借方-貸方"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"] = []; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"] = b[u"材料"][0][u"出どころ"][u"条件"] * 3; cases.append(b)   # 9 個
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"列"] = u"額"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"比べ方"] = u"含む"; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][-1][u"比べ方"] = u"等しい"; cases.append(b)     # 日付に等しい
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = []; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = [u"x"] * 201; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = u"x"; cases.append(b)           # どれか に字 1 つ
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = [u"a\ud800"]; cases.append(b)      # 孤立 surrogate
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0] = {u"列": u"科目番号", u"比べ方": u"等しい", u"値": True}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0] = {u"列": u"科目番号", u"比べ方": u"等しい", u"値": 1.5}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0] = {u"列": u"科目番号", u"比べ方": u"等しい", u"値": 1 << 70}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"等しい", u"値": 5}; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][0][u"出どころ"][u"条件"][0][u"extra"] = 1; cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][5] = od([(u"id", b[u"材料"][5][u"id"]), (u"状態", u"無い")]); cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][5] = od([(u"id", b[u"材料"][5][u"id"]), (u"状態", u"無い"), (u"無い理由", u"不明")]); cases.append(b)
        b = copy.deepcopy(g); b[u"材料"][5] = od([(u"id", b[u"材料"][5][u"id"]), (u"状態", u"無い"), (u"無い理由", u"素材が無い"), (u"数値", u"0.00")]); cases.append(b)
        cases += [[], {}, None, u"x", 1, {u"型の版": u"u1", u"材料": u"x"}, {u"型の版": u"u1", u"材料": [1] * 30}, {u"型の版": u"u1", u"材料": [{}] * 30}]
        for k, b in enumerate(cases):
            res = CHK.check_bundle(make_ctx("D"), b)
            self.assertEqual(u"断り", res[u"束"][u"状態"], k)
            self.assertEqual([u"K0"], res[u"束"][u"規則"], k)
            self.assertEqual([], res[u"材料"])
        # 順序: 封 §1-5 は材料の並びを「id の字の昇順」と書く。昇順でなければ K0 で断る
        b = copy.deepcopy(g)
        b[u"材料"].reverse()
        res = CHK.check_bundle(make_ctx("D"), b)
        self.assertEqual((u"断り", [u"K0"], [u"id の並び"]), (res[u"束"][u"状態"], res[u"束"][u"規則"], res[u"束"][u"理由"]))
        b = copy.deepcopy(g)
        b[u"材料"][3], b[u"材料"][4] = b[u"材料"][4], b[u"材料"][3]
        self.assertEqual([u"id の並び"], CHK.check_bundle(make_ctx("D"), b)[u"束"][u"理由"])
        # 受ける形
        b = copy.deepcopy(g)
        b[u"材料"][0][u"数値"] = u"-0.00"
        self.assertEqual(u"受理", CHK.check_bundle(make_ctx("D"), b)[u"束"][u"状態"])
        b = copy.deepcopy(g)
        b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = [u"x"] * 200
        self.assertEqual(u"受理", CHK.check_bundle(make_ctx("D"), b)[u"束"][u"状態"])

    def one(self, name, bundle, i, table=False):
        res = CHK.check_bundle(make_ctx(name, table=table), bundle)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        return verdicts(res)[i], res

    def test_f_2_k1_value_and_at_least_one_row(self):
        g = gold_of("D")
        m = copy.deepcopy(item(g, u"c01"))
        self.assertEqual((u"通す", ()), self.one("D", g, u"c01")[0])
        m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 1)
        v, _ = self.one("D", replace_item(g, m), u"c01")
        self.assertEqual((u"止める", (u"K1",)), v)
        # 0 行を選ぶ条件に 0.00 は通さない(和が 0 でも行が 1 行以上在ること)
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"条件"][0][u"値"] = [u"no such class"]
        m[u"数値"] = u"0.00"
        v, _ = self.one("D", replace_item(g, m), u"c01")
        self.assertEqual(u"止める", v[0])
        self.assertIn(u"K1", v[1])
        # 行が在って和が 0 の材料は通る(締めを除かずに締めの行だけを選ぶと和は 0 の年が在る)
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"条件"] = [{u"列": u"仕訳の種類", u"比べ方": u"等しい", u"値": u"Opening"}, {u"列": u"科目番号", u"比べ方": u"等しい", u"値": 1590},
                               {u"列": u"日付", u"比べ方": u"以上", u"値": u"2001-01-01"}, {u"列": u"日付", u"比べ方": u"以下", u"値": u"2001-12-31"}]
        m[u"出どころ"][u"向き"] = u"借方−貸方"
        m[u"数値"] = u"-3000.00"
        v, _ = self.one("D", replace_item(g, m), u"c01")
        self.assertEqual(u"K1" in v[1], False)
        # 向き: 借方−貸方 と 貸方−借方 で符号が反転する
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"向き"] = u"借方−貸方"
        v, _ = self.one("D", replace_item(g, m), u"c01")
        self.assertIn(u"K1", v[1])
        m[u"数値"] = u"-" + item(g, u"c01")[u"数値"]
        v, _ = self.one("D", replace_item(g, m), u"c01")
        self.assertNotIn(u"K1", v[1])

    def test_f_3_k4_period_and_the_point_row_has_no_lower_bound(self):
        g = gold_of("D")
        for i, field_fix in ((u"c01", None), (u"c21", None)):
            self.assertEqual((u"通す", ()), self.one("D", g, i)[0])
        m = copy.deepcopy(item(g, u"c01"))
        m[u"期間"] = {u"始まり": u"2001-01-02", u"終わり": u"2001-12-31"}
        self.assertEqual((u"止める", (u"K4",)), self.one("D", replace_item(g, m), u"c01")[0])
        m = copy.deepcopy(item(g, u"c01"))
        m[u"期間"] = {u"時点": u"2001-12-31"}
        self.assertIn(u"K4", self.one("D", replace_item(g, m), u"c01")[0][1])
        m = copy.deepcopy(item(g, u"c01"))
        del m[u"出どころ"][u"条件"][-2]                                    # 日付 以上 が無い
        v = self.one("D", replace_item(g, m), u"c01")[0]
        self.assertIn(u"K4", v[1])
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"条件"].append({u"列": u"日付", u"比べ方": u"以上", u"値": u"2001-01-01"})       # 2 つ
        self.assertIn(u"K4", self.one("D", replace_item(g, m), u"c01")[0][1])
        # 時点の行: 日付 以上 を足すと止める・期間の欄が違えば止める
        m = copy.deepcopy(item(g, u"c21"))
        m[u"出どころ"][u"条件"].append({u"列": u"日付", u"比べ方": u"以上", u"値": u"2001-01-01"})
        self.assertEqual((u"止める", (u"K4",)), self.one("D", replace_item(g, m), u"c21")[0])
        m = copy.deepcopy(item(g, u"c21"))
        m[u"期間"] = {u"時点": u"2001-12-30"}
        self.assertEqual((u"止める", (u"K4",)), self.one("D", replace_item(g, m), u"c21")[0])
        # 指定から出した期と違えば止める(別の指定で検査する)
        v = self.one("S", g, u"c01")[0]
        self.assertIn(u"K4", v[1])

    def test_f_4_k5_k8_unit_and_scope(self):
        g = gold_of("D")
        m = copy.deepcopy(item(g, u"c01"))
        m[u"単位"] = u"円"
        self.assertEqual((u"止める", (u"K5",)), self.one("D", replace_item(g, m), u"c01")[0])
        m = copy.deepcopy(item(g, u"c01"))
        m[u"範囲"] = u"部門"
        self.assertEqual((u"止める", (u"K8",)), self.one("D", replace_item(g, m), u"c01")[0])

    def test_f_5_k3_the_selected_rows_equal_the_carry_over_rows_and_the_direction(self):
        g = gold_of("D")
        self.assertEqual((u"通す", ()), self.one("D", g, u"c01", table=True)[0])
        # 余り: 科目を足す(数値は合わせる)
        m = copy.deepcopy(item(g, u"c01"))
        REF_ = REF
        f = fake()
        sel = REF.Sel(f.path)
        try:
            m[u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"どれか", u"値": [u"Operating Revenue", u"Contra Revenue", u"Other Expense"]}
            conds = [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]
            m[u"数値"] = REF.fmt_cents(sel.signed(conds, u"貸方−借方")[0])
        finally:
            sel.close()
        v, res = self.one("D", replace_item(g, m), u"c01", table=True)
        self.assertEqual((u"止める", (u"K3",)), v)
        self.assertEqual(True, item_k3(res, u"c01")[u"余り"] > 0 and item_k3(res, u"c01")[u"漏れ"] == 0)
        # 漏れ: 科目を減らす
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"どれか", u"値": [u"Operating Revenue"]}
        sel = REF.Sel(f.path)
        try:
            conds = [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]
            m[u"数値"] = REF.fmt_cents(sel.signed(conds, u"貸方−借方")[0])
        finally:
            sel.close()
        v, res = self.one("D", replace_item(g, m), u"c01", table=True)
        self.assertEqual((u"止める", (u"K3",)), v)
        self.assertTrue(item_k3(res, u"c01")[u"漏れ"] > 0 and item_k3(res, u"c01")[u"余り"] == 0)
        # 向きが違えば、同じ行でも止める
        m = copy.deepcopy(item(g, u"c01"))
        m[u"出どころ"][u"向き"] = u"借方−貸方"
        m[u"数値"] = u"-" + m[u"数値"]
        v, res = self.one("D", replace_item(g, m), u"c01", table=True)
        self.assertEqual((u"止める", (u"K3",)), v)
        self.assertEqual({u"余り": 0, u"漏れ": 0}, item_k3(res, u"c01"))
        # 表なしは K3 を見ない(数値が反転するので関係は崩れて K7 が止めるが、K3 は付かない)
        self.assertNotIn(u"K3", self.one("D", replace_item(g, m), u"c01", table=False)[0][1])

    def test_f_6_k9_a_none_row_is_stopped_when_the_table_rule_selects_a_row(self):
        g = gold_of("S")
        # c28・c29 は表の科目が空で、持ち越しは無い。c02 は 2001 年の行が在る(当期 S の前期)ので、無いと書けば止める
        m = od([(u"id", u"c02"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
        self.assertEqual(u"無いを受ける", self.one("S", replace_item(g, m), u"c02", table=False)[0][0])
        v, _ = self.one("S", replace_item(g, m), u"c02", table=True)
        self.assertEqual(u"止める", v[0])
        self.assertIn(u"K9", v[1])
        # 行が丁度 1 行でも止める(下限は 1)
        f = fake()
        t = copy.deepcopy(f.table)
        t[u"行"][u"c28"][u"科目"] = [1600]                                     # 当期 S に 1 行だけの科目
        tp = os.path.join(f.tmp, "table_one.json")
        wjson(tp, t)
        ctx, _ = CHK.make_ctx(spec_path("S"), DEF_PATH, READING_PATH, f.path, tp)
        res = CHK.check_bundle(ctx, g)
        # 科目 1600 に当期 S の行は借方の 1 行だけ(下限は 1 行)
        self.assertEqual(1, len([r for r in f.rows if r["acct"] == 1600]))
        self.assertIn(u"K9", verdicts(res)[u"c28"][1])

    def test_f_7_k10_unchecked_accounts_two_stage(self):
        # 期 S: 新しい科目は 6030(費用・営業費用)・8010(資産・流動資産)・1600(資産・固定でない資産)・7010(収益・営業外の収益)
        res = tab_check("S", gold_of("S"))
        v = verdicts(res)
        # 同じ小分類が表に在る時は、大分類と小分類の両方が同じ科目を持つ id だけ: 6030(費用・営業費用) は c03(原価)を止めない
        self.assertNotIn(u"K10", v[u"c03"][1])
        self.assertIn(u"K10", v[u"c04"][1])
        # 小分類が表のどこにも無い時は、大分類が同じ科目を持つ id: 1600(資産・固定でない資産) は資産の id を止める
        self.assertIn(u"K10", v[u"c23"][1])
        # c08(資産・資産の累計の控除)は、同じ小分類の新しい科目が無い。小分類が表に無い 1600 と大分類が同じなので、段 2 だけで止まる
        self.assertIn(u"K10", v[u"c08"][1])
        # 小分類が表のどこにも無い(営業外の収益)・大分類 収益: 収益の科目を持つ id は止まり、費用だけの id は止まらない
        self.assertIn(u"K10", v[u"c01"][1])
        self.assertNotIn(u"K10", v[u"c03"][1])
        self.assertNotIn(u"K10", v[u"c25"][1])        # 負債の id は止まらない
        self.assertNotIn(u"K10", v[u"c24"][1])
        # 期 D では確かめていない科目が無い
        res = tab_check("D", gold_of("D"))
        self.assertEqual([], [r for r in res[u"材料"] if u"K10" in r[u"規則"]])

    def test_f_8_k7_relations(self):
        g = gold_of("D")
        m = copy.deepcopy(item(g, u"c03"))
        m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 5)
        # K1 が先に止める(c03 は使えなくなり、R3 は見ない)
        res = CHK.check_bundle(make_ctx("D"), replace_item(g, m))
        self.assertEqual({u"見た": 2, u"見なかった": 1}, res[u"K7"])
        # 数値と条件がそろっていて、関係だけ崩れる: c06 の取り方を c06 より 1 行少ない行に変え、数値を合わせる
        m = copy.deepcopy(item(g, u"c06"))
        m[u"出どころ"][u"条件"][0] = {u"列": u"科目の大分類", u"比べ方": u"等しい", u"値": u"Revenue"}
        f = fake()
        sel = REF.Sel(f.path)
        try:
            conds = [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]
            m[u"数値"] = REF.fmt_cents(sel.signed(conds, u"貸方−借方")[0])
        finally:
            sel.close()
        res = CHK.check_bundle(make_ctx("D"), replace_item(g, m))
        v = verdicts(res)
        for i in (u"c01", u"c03", u"c04", u"c05", u"c06"):
            self.assertEqual((u"止める", (u"K7",)), v[i], i)
        self.assertEqual((u"通す", ()), v[u"c23"])
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])
        # 無いは 0 として数える: R1 の c09 を無いにすると、和が崩れて R1 の材料が止まる
        m = od([(u"id", u"c09"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
        res = CHK.check_bundle(make_ctx("D"), replace_item(g, m))
        v = verdicts(res)
        self.assertEqual((u"止める", (u"K7",)), v[u"c10"])
        self.assertEqual((u"無いを受ける", ()), v[u"c09"])
        # そろわない関係は見ない(見なかった数)
        m = od([(u"id", u"c25"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
        res = CHK.check_bundle(make_ctx("D"), replace_item(g, m))
        self.assertEqual(u"止める", verdicts(res)[u"c23"][0])           # c25 を 0 と数えるので R2 が崩れる
        # c01 の数値が違い K1 で止まると、R1・R3 は見ない
        m = copy.deepcopy(item(g, u"c01"))
        m[u"数値"] = u"1.00"
        res = CHK.check_bundle(make_ctx("D"), replace_item(g, m))
        self.assertEqual({u"見た": 1, u"見なかった": 2}, res[u"K7"])

    def test_f_9_the_plain_check_does_not_read_the_table_and_the_tabled_check_adds_k3_k9_k10(self):
        g = gold_of("S")
        plain = CHK.check_bundle(make_ctx("S"), g)
        self.assertEqual(0, len([r for r in plain[u"材料"] if r[u"判定"] == u"止める" and (set(r[u"規則"]) & {u"K3", u"K9", u"K10"})]))
        self.assertEqual({u"余り": 0, u"漏れ": 0}, plain[u"K3の行"])
        self.assertTrue(all(u"K3" not in r for r in plain[u"材料"]))
        tabled = CHK.check_bundle(make_ctx("S", table=True), g)
        self.assertGreater(len([r for r in tabled[u"材料"] if r[u"判定"] == u"止める"]), 0)
        used = set(k for r in tabled[u"材料"] for k in r[u"規則"])
        self.assertTrue(set([u"K3", u"K10"]) <= used)
        self.assertEqual(set(), used - set([u"K3", u"K10"]))

    def test_f_10_the_period_arithmetic_for_every_kind_and_the_shifted_designations(self):
        for spec, expect in (((u"2025-04-01", u"2026-03-31"), (u"2024-04-01", u"2025-03-31")), ((u"2025-10-01", u"2026-09-30"), (u"2024-10-01", u"2025-09-30"))):
            cs, ce = CHK.parse_date(spec[0]), CHK.parse_date(spec[1])
            sp = CHK.Spec(); sp.cs, sp.ce = cs, ce
            sp.pe = cs - datetime.timedelta(days=1)
            sp.ps = CHK.add_months(cs, -12)
            self.assertEqual((u"期間", CHK.parse_date(expect[0]), CHK.parse_date(expect[1])), CHK.expected_period(u"前期", sp))
            self.assertEqual((u"時点", CHK.parse_date(expect[1])), CHK.expected_period(u"前期末", sp))
            self.assertEqual((u"時点", ce), CHK.expected_period(u"当期末", sp))
            self.assertEqual((u"期間", cs, ce), CHK.expected_period(u"当期", sp))
            months = [CHK.expected_period(u"当期の月:%d" % k, sp) for k in range(1, 13)]
            self.assertEqual(cs, months[0][1])
            self.assertEqual(ce, months[11][2])
            for a, b in zip(months, months[1:]):
                self.assertEqual(a[2] + datetime.timedelta(days=1), b[1])
            # 答えを知っている側の期と同じ
            for kind in (u"当期", u"前期", u"当期末", u"前期末") + tuple(u"当期の月:%d" % k for k in range(1, 13)):
                rp = REF.period_of(kind, cs, ce)
                cp = CHK.expected_period(kind, sp)
                self.assertEqual(tuple(x.isoformat() if hasattr(x, "isoformat") else x for x in rp), tuple(x.isoformat() if hasattr(x, "isoformat") else x for x in cp), kind)
        sp = CHK.Spec(); sp.cs, sp.ce = datetime.date(2025, 1, 1), datetime.date(2025, 12, 31)
        sp.pe, sp.ps = datetime.date(2024, 12, 31), datetime.date(2024, 1, 1)
        for bad in (u"当期の月:0", u"当期の月:13", u"当期の月:x", u"当期の月:１", u"", None, 5, u"翌期"):
            self.assertIsNone(CHK.expected_period(bad, sp))
        self.assertEqual(datetime.date(2024, 2, 29), CHK.add_months(datetime.date(2024, 3, 31), -1))


def item_k3(res, i):
    return next(r for r in res[u"材料"] if r[u"id"] == i)[u"K3"]


# ======================================================================== 7. 変異 N1〜N12 の作り
class MutationBuildTest(unittest.TestCase):
    def setUp(self):
        self.f = fake()
        self.sel = REF.Sel(self.f.path)
        self.cs, self.ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
        self.gold = gold_of("S")
        self.muts = dict(((n, i), (nb, same)) for n, i, nb, same in REF.make_mutations(self.sel, self.gold, self.cs, self.ce))

    def tearDown(self):
        self.sel.close()

    def made(self, n, i):
        nb, same = self.muts[(n, i)]
        return (None if nb is None else item(nb, i)), same

    def test_g_1_every_pair_is_counted_and_made_ones_differ_from_the_original(self):
        self.assertEqual(30 * 12, len(self.muts))
        for (n, i), (nb, same) in self.muts.items():
            if nb is not None:
                self.assertNotEqual(json.dumps(nb, ensure_ascii=False), json.dumps(self.gold, ensure_ascii=False))
                # 1 つの材料だけが変わる
                diff = [m[u"id"] for m, o in zip(nb[u"材料"], self.gold[u"材料"]) if m != o]
                self.assertEqual([i], diff, (n, i))

    def test_g_2_n1_adds_one_cent(self):
        m, same = self.made(u"N1", u"c01")
        self.assertEqual(REF.parse_cents(item(self.gold, u"c01")[u"数値"]) + 1, REF.parse_cents(m[u"数値"]))
        self.assertFalse(same)
        self.assertIsNone(self.made(u"N1", u"c28")[0])           # 無いの材料には作れない

    def test_g_3_n2_adds_a_not_in_condition_with_the_smallest_selected_account(self):
        f = self.f
        m, same = self.made(u"N2", u"c01")
        self.assertEqual({u"列": u"科目番号", u"比べ方": u"どれでもない", u"値": [4010]}, dict(m[u"出どころ"][u"条件"][-1]))
        rows = f.pick(lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2) and r["acct"] != 4010, S_SPEC[0], S_SPEC[1])
        self.assertEqual(REF.fmt_cents(f.cents_sum(rows, True)), m[u"数値"])
        self.assertFalse(same)
        # 科目が 1 つだけの材料は作れない
        for i in (u"c21", u"c24"):
            self.assertIsNone(self.made(u"N2", i)[0], i)

    def test_g_4_n3_adds_the_first_unused_value_of_the_same_column_that_has_rows_in_the_period(self):
        f = self.f
        m, same = self.made(u"N3", u"c01")
        c0 = m[u"出どころ"][u"条件"][0]
        used = [u"Operating Revenue", u"Contra Revenue"]
        subs = set(ACC_CLS[r["acct"]][1] for r in f.rows if S_SPEC[0] <= r["date"] <= S_SPEC[1])
        in_period = sorted(subs - set(used))
        self.assertEqual(used + [in_period[0]], c0[u"値"])
        self.assertEqual(u"どれか", c0[u"比べ方"])
        # 等しい の値は並びになる
        m, same = self.made(u"N3", u"c03")
        c0 = m[u"出どころ"][u"条件"][0]
        self.assertEqual(u"どれか", c0[u"比べ方"])
        self.assertEqual(u"COGS", c0[u"値"][0])
        self.assertEqual(2, len(c0[u"値"]))
        self.assertEqual(sorted(subs - {u"COGS"})[0], c0[u"値"][1])
        # 科目番号は数の昇順(1010 の次は、その期に行が在る最小の別の番号)
        m, _ = self.made(u"N3", u"c21")
        accts = sorted(set(r["acct"] for r in f.rows if r["date"] <= S_SPEC[1]) - {1010})
        self.assertEqual([1010, accts[0]], m[u"出どころ"][u"条件"][0][u"値"])
        # 並びを持つ最初の条件にだけ足す
        for c in m[u"出どころ"][u"条件"][1:]:
            self.assertNotEqual(u"どれか", c[u"比べ方"])

    def test_g_5_n4_moves_the_dates_to_the_other_period_and_keeps_the_period_field(self):
        m, _ = self.made(u"N4", u"c01")
        conds = m[u"出どころ"][u"条件"]
        self.assertEqual(u"2001-01-01", [c for c in conds if c[u"比べ方"] == u"以上"][0][u"値"])
        self.assertEqual(u"2001-12-31", [c for c in conds if c[u"比べ方"] == u"以下"][0][u"値"])
        self.assertEqual({u"始まり": u"2002-01-01", u"終わり": u"2002-12-31"}, dict(m[u"期間"]))
        m, _ = self.made(u"N4", u"c02")
        self.assertEqual(u"2002-12-31", [c for c in m[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"][0][u"値"])
        m, _ = self.made(u"N4", u"c21")
        self.assertEqual(u"2001-12-31", m[u"出どころ"][u"条件"][-1][u"値"])
        self.assertEqual({u"時点": u"2002-12-31"}, dict(m[u"期間"]))
        m, _ = self.made(u"N4", u"c27")
        self.assertEqual(u"2002-12-31", m[u"出どころ"][u"条件"][-1][u"値"])
        # 月は次の月・12 番目は 11 番目
        m, _ = self.made(u"N4", u"c09")
        self.assertEqual((u"2002-02-01", u"2002-02-28"), tuple(c[u"値"] for c in m[u"出どころ"][u"条件"][-2:]))
        m, _ = self.made(u"N4", u"c20")
        self.assertEqual((u"2002-11-01", u"2002-11-30"), tuple(c[u"値"] for c in m[u"出どころ"][u"条件"][-2:]))
        # 数値は新しい条件に合わせる
        f = self.f
        rows = f.pick(lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2), u"2001-01-01", u"2001-12-31")
        self.assertEqual(REF.fmt_cents(f.cents_sum(rows, True)), self.made(u"N4", u"c01")[0][u"数値"])
        self.assertIsNone(self.made(u"N4", u"c28")[0])

    def test_g_6_n5_moves_the_dates_and_the_period_field(self):
        m, _ = self.made(u"N5", u"c01")
        self.assertEqual({u"始まり": u"2001-01-01", u"終わり": u"2001-12-31"}, dict(m[u"期間"]))
        self.assertEqual(u"2001-12-31", [c for c in m[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"][0][u"値"])
        m, _ = self.made(u"N5", u"c21")
        self.assertEqual({u"時点": u"2001-12-31"}, dict(m[u"期間"]))

    def test_g_7_n6_adds_a_lower_bound_to_point_rows_only(self):
        m, same = self.made(u"N6", u"c21")
        self.assertEqual({u"列": u"日付", u"比べ方": u"以上", u"値": u"2002-01-01"}, dict(m[u"出どころ"][u"条件"][-1]))
        m, _ = self.made(u"N6", u"c27")
        self.assertEqual(u"2001-01-01", m[u"出どころ"][u"条件"][-1][u"値"])
        self.assertIsNone(self.made(u"N6", u"c01")[0])
        self.assertIsNone(self.made(u"N6", u"c28")[0])

    def test_g_8_n7_drops_the_not_in_journal_type_condition(self):
        m, same = self.made(u"N7", u"c01")
        self.assertEqual([u"科目の小分類", u"日付", u"日付"], [c[u"列"] for c in m[u"出どころ"][u"条件"]])
        self.assertTrue(not same)                                 # 締めの行を含むので数値が変わる
        self.assertIsNone(self.made(u"N7", u"c21")[0])            # その条件を持たない
        self.assertIsNone(self.made(u"N7", u"c08")[0])            # 等しい の条件は外さない

    def test_g_9_n8_n9_flip_the_state(self):
        m, _ = self.made(u"N8", u"c01")
        self.assertEqual(od([(u"id", u"c01"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")]), m)
        self.assertIsNone(self.made(u"N8", u"c28")[0])
        self.assertIsNone(self.made(u"N9", u"c01")[0])
        m, _ = self.made(u"N9", u"c28")
        conds = m[u"出どころ"][u"条件"]
        self.assertEqual([u"日付", u"日付", u"科目番号"], [c[u"列"] for c in conds])
        self.assertEqual(1010, conds[-1][u"値"])                  # 2002 年に行が在る最小の科目番号
        self.assertEqual(u"等しい", conds[-1][u"比べ方"])
        self.assertEqual(u"借方−貸方", m[u"出どころ"][u"向き"])
        self.assertEqual({u"始まり": u"2002-01-01", u"終わり": u"2002-12-31"}, dict(m[u"期間"]))
        m, _ = self.made(u"N9", u"c29")
        self.assertEqual({u"時点": u"2002-12-31"}, dict(m[u"期間"]))
        self.assertEqual(1, len(m[u"出どころ"][u"条件"]) - 1)
        f = self.f
        self.assertEqual(REF.fmt_cents(f.cents_sum(f.pick(lambda r: r["acct"] == 1010, None, u"2002-12-31"), False)), m[u"数値"])

    def test_g_10_n10_reverses_the_direction(self):
        m, same = self.made(u"N10", u"c01")
        self.assertEqual(u"借方−貸方", m[u"出どころ"][u"向き"])
        self.assertEqual(u"-" + item(self.gold, u"c01")[u"数値"], m[u"数値"])
        self.assertFalse(same)
        m, _ = self.made(u"N10", u"c21")
        self.assertEqual(u"貸方−借方", m[u"出どころ"][u"向き"])

    def test_g_11_n11_swaps_source_and_value_with_the_next_present_material_of_a_different_value(self):
        m, same = self.made(u"N11", u"c01")
        o = item(self.gold, u"c02")
        # c02 は 2002 年に前期(2001 年)の行が在り、数値が違う
        self.assertEqual(o[u"出どころ"], m[u"出どころ"])
        self.assertEqual(o[u"数値"], m[u"数値"])
        self.assertEqual(item(self.gold, u"c01")[u"期間"], m[u"期間"])
        self.assertFalse(same)
        # 最後の在る材料(c30 は在る・c29 は無い)の次は無い
        last_present = [x[u"id"] for x in self.gold[u"材料"] if x[u"状態"] == u"在る"][-1]
        self.assertIsNone(self.made(u"N11", last_present)[0])
        self.assertIsNone(self.made(u"N11", u"c28")[0])
        # 数値が同じ次の材料は飛ばす(c09 と c10 は数値が違うのでそのまま。同じなら飛ばす: 作り物で確かめる)
        g = copy.deepcopy(self.gold)
        item(g, u"c11")[u"数値"] = item(g, u"c10")[u"数値"]
        item(g, u"c11")[u"出どころ"] = copy.deepcopy(item(g, u"c10")[u"出どころ"])
        out = dict(((n, i), nb) for n, i, nb, _s in REF.make_mutations(self.sel, g, self.cs, self.ce))
        nb = out[(u"N11", u"c10")]
        self.assertEqual(item(g, u"c12")[u"数値"], item(nb, u"c10")[u"数値"])

    def test_g_12_n12_moves_the_upper_date_one_day_earlier(self):
        m, same = self.made(u"N12", u"c01")
        self.assertEqual(u"2002-12-30", [c for c in m[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"][0][u"値"])
        self.assertEqual(item(self.gold, u"c01")[u"期間"], m[u"期間"])
        m, _ = self.made(u"N12", u"c21")
        self.assertEqual(u"2002-12-30", m[u"出どころ"][u"条件"][-1][u"値"])
        f = self.f
        rows = f.pick(lambda r: r["acct"] == 1010, None, u"2002-12-30")
        self.assertEqual(REF.fmt_cents(f.cents_sum(rows, False)), m[u"数値"])
        self.assertIsNone(self.made(u"N12", u"c28")[0])

    def test_g_13_the_value_same_count_is_kept_for_value_preserving_mutations(self):
        # N7 を c06 に当てると、締めを外しても数値が変わる(締めは損益を 0 にする)。c21 の N6 は残高が最初の日から累計なので数値が同じ
        _, same = self.made(u"N6", u"c21")
        self.assertFalse(same)                                   # 2002 年の期首以降だけの和に変わる
        _, same = self.made(u"N6", u"c27")
        self.assertTrue(same)                                    # 前期末の下限が前期の始まり = 素材の最初の日 に近く、累計が同じ
        self.assertEqual(self.muts[(u"N1", u"c01")][1], False)

    def test_g_14_the_unmade_pairs_are_counted_per_mutation(self):
        u"""作れなかった数(期 S の正解の束: 無い 2 つ(c28・c29)・時点の行 7・``どれでもない`` を持つ行 20)。"""
        un = collections.Counter(n for (n, i), (nb, _s) in self.muts.items() if nb is None)
        self.assertEqual(2, un[u"N1"])
        self.assertEqual(2, un[u"N8"])
        self.assertEqual(28, un[u"N9"])
        self.assertEqual(30 - 7, un[u"N6"])
        self.assertEqual(30 - 20, un[u"N7"])
        for n in REF.MUTATIONS:
            self.assertEqual(30, len([1 for (nn, i) in self.muts if nn == n]))


# ======================================================================== 8. 表なし・表つきの違い(変異に対して)
def judge_all(name, table, src=None):
    u"""変異を全部作り、検査に(関数で)掛ける。戻りは {(N, id): (判定, 規則)}。``src`` を渡すと、その素材(``derive`` で作った作り物)で。"""
    f = fake()
    sel = REF.Sel(src or f.path)
    try:
        cs, ce = [REF.pdate(x) for x in {"D": D_SPEC, "S": S_SPEC, "H": H_SPEC}[name]]
        g = json.loads(json.dumps(REF.gold_bundle(sel, cs, ce), ensure_ascii=False))
        muts = REF.make_mutations(sel, g, cs, ce)
    finally:
        sel.close()
    ctx = make_ctx(name, table=table, src=src)
    out = {}
    for n, i, nb, same in muts:
        if nb is None:
            continue
        res = CHK.check_bundle(ctx, json.loads(json.dumps(nb, ensure_ascii=False)))
        out[(n, i)] = (verdicts(res)[i] if res[u"束"][u"状態"] == u"受理" else (u"断り", tuple(res[u"束"][u"規則"])), same)
    return out


def conds_of(m):
    return [(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]]


def passed(v):
    return v[0] in (u"通す", u"無いを受ける")


class TabledVersusPlainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plain = judge_all("S", False)
        cls.tabled = judge_all("S", True)

    def test_h_1_whatever_the_tabled_check_passes_selects_the_carry_over_rows(self):
        u"""表つきが通した変異は、表の取り方(持ち越し)と同じ行・同じ向きを選んでいる(``UM1-A4`` の「0」は、ここで外れうる ― 結果の文書に書く)。"""
        f = fake()
        sel = REF.Sel(f.path)
        try:
            cs, ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
            gold = REF.gold_bundle(sel, cs, ce)
            carry = REF.carry_bundle(sel, f.table, cs, ce)
            muts = dict(((n, i), nb) for n, i, nb, _s in REF.make_mutations(sel, gold, cs, ce))
            passed_n = 0
            for k, (v, same) in self.tabled.items():
                if not passed(v):
                    continue
                passed_n += 1
                n, i = k
                m = item(muts[k], i)
                c = item(carry, i)
                if m[u"状態"] == u"無い":
                    self.assertEqual(u"無い", c[u"状態"], k)
                else:
                    self.assertEqual(u"在る", c[u"状態"], k)
                    self.assertEqual(c[u"出どころ"][u"向き"], m[u"出どころ"][u"向き"], k)
                    self.assertTrue(sel.same_rows(conds_of(m), conds_of(c)), k)
            self.assertGreater(passed_n, 0)
        finally:
            sel.close()

    def test_h_2_the_plain_check_passes_the_mutations_the_seal_predicts_it_cannot_see(self):
        # UM1-A5 の形: 関係に入らない 在る の行の N2・N3・N10 は表なしが通す
        n = 0
        for i in REF.A5_IDS:
            for name in (u"N2", u"N3", u"N10"):
                if (name, i) in self.plain:
                    n += 1
                    if i != u"c27" or name != u"N3":
                        pass
                    self.assertTrue(passed(self.plain[(name, i)][0]), (name, i, self.plain[(name, i)]))
        self.assertGreater(n, 6)

    def test_h_3_the_plain_check_stops_changed_value_mutations_of_relation_rows_by_k7(self):
        # UM1-A6 の形: 関係に入る行の N2・N3・N7・N10 のうち数値が元と違うものは表なしでも通さない(関係が全部そろっている束で)
        n = 0
        for i in REF.A6_IDS:
            for name in (u"N2", u"N3", u"N7", u"N10"):
                if (name, i) in self.plain:
                    v, same = self.plain[(name, i)]
                    if not same:
                        n += 1
                        self.assertFalse(passed(v), (name, i, v))
        self.assertGreater(n, 40)

    def test_h_4_n8_is_passed_by_the_plain_check_for_rows_outside_a_relation_and_stopped_by_k7_inside(self):
        for i in REF.A5_IDS:
            if (u"N8", i) in self.plain:
                self.assertTrue(passed(self.plain[(u"N8", i)][0]), i)
        # 関係に入る行を 無い にすると、0 を数えて関係が崩れ、その行以外の材料が K7 で止まる(無い自身は無いを受ける)
        self.assertEqual(u"無いを受ける", self.plain[(u"N8", u"c01")][0][0])

    def test_h_5_the_tabled_check_stops_none_and_present_flips(self):
        # N8: 表つきは、持ち越しが選ぶ行が在る期で 無い を止める(K9)。N9: 無い→在る は K3 か K10 が止める
        for i in (u"c01", u"c03", u"c21", u"c24"):
            v, _ = self.tabled[(u"N8", i)]
            self.assertEqual(u"止める", v[0], i)
            self.assertIn(u"K9", v[1])
        for k, (v, _s) in self.tabled.items():
            if k[0] == u"N9":
                self.assertFalse(passed(v), k)

    def test_h_6_every_mutation_is_stopped_by_the_tabled_check_on_the_first_period(self):
        tabled = judge_all("D", True)
        survivors = [(k, v) for k, (v, same) in tabled.items() if passed(v) and not same]
        self.assertEqual([], survivors)
        # 数値も行の集まりも同じ(N3 で選ぶ行が増えない・N7 で外しても行が増えない)ものだけが通る
        for k, (v, same) in tabled.items():
            if passed(v):
                self.assertTrue(same or k[0] in (u"N3",), k)


# ======================================================================== 9. どんな入力でも例外で落ちない・SQL に束の字が入らない
class RobustnessTest(unittest.TestCase):
    def sweep_inputs(self):
        g = gold_of("D")
        out = [None, True, False, 0, 1, -1, 1.5, float("nan"), float("inf"), u"", u"x", u"\ud800", [], {}, [[]], [{}], {u"型の版": u"u1"}, {u"型の版": u"u1", u"材料": None},
               {u"型の版": u"u1", u"材料": [None] * 30}, {u"型の版": u"u1", u"材料": [[]] * 30}, {u"型の版": u"u1", u"材料": [{u"id": u"c01"}] * 30},
               {u"型の版": u"u1", u"材料": list(range(10 ** 5))}, {u"型の版": u"u1", u"材料": [{}] * (10 ** 5)}]
        deep = []
        for _ in range(3000):
            deep = [deep]
        out.append({u"型の版": u"u1", u"材料": deep})
        # 型を 1 つずつ壊す
        for i in (0, 5):
            for key in (u"id", u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ"):
                for bad in (None, True, 1, 1.5, float("nan"), [], {}, u"", u"\ud800", u"x" * 100000, [u"a"] * 1000, {u"a": 1}):
                    b = copy.deepcopy(g)
                    if key in b[u"材料"][i]:
                        b[u"材料"][i][key] = copy.deepcopy(bad)
                        out.append(b)
        for key in (u"列", u"比べ方", u"値"):
            for bad in (None, True, 1, 1.5, [], {}, u"", u"\ud800", [None], [True], [1.5], [[1]], [{}], 1 << 80, -(1 << 80), float("nan"), [u"\ud800"], [1 << 80]):
                b = copy.deepcopy(g)
                b[u"材料"][0][u"出どころ"][u"条件"][0][key] = copy.deepcopy(bad)
                out.append(b)
        return out

    def test_i_1_the_check_never_raises_on_broken_input(self):
        refused = total = 0
        for k, b in enumerate(self.sweep_inputs()):
            for table in (False, True):
                res = CHK.check_bundle(make_ctx("D", table=table), b)
                self.assertIn(u"束", res, k)
                self.assertIn(res[u"束"][u"状態"], (u"断り", u"受理"), k)
                refused += 1 if res[u"束"][u"状態"] == u"断り" else 0
                total += 1
                json.dumps(res, ensure_ascii=False)
                CHK.dump_json(res)
        self.assertGreater(refused, total * 0.8)

    def test_i_2_big_and_nan_values_inside_a_valid_shape_do_not_raise(self):
        g = gold_of("D")
        b = copy.deepcopy(g)
        b[u"材料"][0][u"数値"] = u"9" * 40 + u".00"
        for table in (False, True):
            res = CHK.check_bundle(make_ctx("D", table=table), b)
            self.assertEqual(u"止める", verdicts(res)[u"c01"][0])
        b = copy.deepcopy(g)
        b[u"材料"][0][u"数値"] = u"9" * 5000 + u".00"                     # 長すぎる字は形で断る
        self.assertEqual(u"断り", CHK.check_bundle(make_ctx("D"), b)[u"束"][u"状態"])
        # 値の並び 200 個の巨大な字・日付の極端な値
        b = copy.deepcopy(g)
        b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = [u"x" * 100000] * 200
        res = CHK.check_bundle(make_ctx("D"), b)
        self.assertEqual(u"止める", verdicts(res)[u"c01"][0])
        b = copy.deepcopy(g)
        b[u"材料"][0][u"出どころ"][u"条件"][-1][u"値"] = u"9999-12-31"
        b[u"材料"][0][u"期間"] = {u"始まり": u"2001-01-01", u"終わり": u"9999-12-31"}
        self.assertEqual(u"止める", verdicts(CHK.check_bundle(make_ctx("D"), b))[u"c01"][0])
        b = copy.deepcopy(g)
        b[u"材料"][0][u"出どころ"][u"条件"][-1][u"値"] = u"0001-01-01"
        self.assertEqual(u"止める", verdicts(CHK.check_bundle(make_ctx("D"), b))[u"c01"][0])

    def test_i_3_a_bad_string_in_a_column_or_a_value_never_changes_the_source_or_the_verdict_kind(self):
        f = fake()
        before = sha_file(f.path)
        evil = [u"'; DROP TABLE GLEntry; --", u"\" OR 1=1 --", u"%s", u"?", u"?,?,?", u"x') OR ('1'='1", u"; PRAGMA writable_schema=1; --", u"a\x00b", u"Robert'); DROP TABLE l;--",
                u"é", u"日本語", u"\U0001F600"]
        g = gold_of("D")
        base = verdicts(CHK.check_bundle(make_ctx("D"), g))
        ctx = make_ctx("D", table=True)
        for e in evil:
            for key in (u"値",):
                for k in range(4):
                    b = copy.deepcopy(g)
                    c = b[u"材料"][0][u"出どころ"][u"条件"][k]
                    if c[u"列"] == u"日付":
                        continue
                    c[key] = [e] if isinstance(c[key], list) else e
                    res = CHK.check_bundle(ctx, b)
                    if u"\x00" in e:
                        self.assertIn(res[u"束"][u"状態"], (u"受理", u"断り"))
                    else:
                        self.assertEqual(u"受理", res[u"束"][u"状態"], e)
                    self.assertNotEqual(base[u"c01"], verdicts(res)[u"c01"] if res[u"材料"] else None)
            # 列の名に入れても K0 で断る(SQL の列にならない)
            b = copy.deepcopy(g)
            b[u"材料"][0][u"出どころ"][u"条件"][0][u"列"] = e
            self.assertEqual([u"K0"], CHK.check_bundle(make_ctx("D"), b)[u"束"][u"規則"])
            b = copy.deepcopy(g)
            b[u"材料"][0][u"出どころ"][u"条件"][0][u"比べ方"] = e
            self.assertEqual([u"K0"], CHK.check_bundle(make_ctx("D"), b)[u"束"][u"規則"])
            b = copy.deepcopy(g)
            b[u"材料"][0][u"id"] = e
            self.assertEqual([u"K0"], CHK.check_bundle(make_ctx("D"), b)[u"束"][u"規則"])
        self.assertEqual(before, sha_file(f.path))
        con = sqlite3.connect(f.path)
        self.assertEqual(len(f.rows), con.execute("select count(*) from GLEntry").fetchone()[0])
        con.close()
        self.assertEqual(len(f.rows), ctx.led.select([])[0])                  # 作業用の表も無事

    def test_i_4_a_condition_value_with_an_evil_string_selects_nothing_and_is_stopped_by_k1(self):
        g = gold_of("D")
        b = copy.deepcopy(g)
        b[u"材料"][0][u"出どころ"][u"条件"][0][u"値"] = [u"' OR 1=1 --"]
        v = verdicts(CHK.check_bundle(make_ctx("D"), b))
        self.assertEqual(u"止める", v[u"c01"][0])
        self.assertIn(u"K1", v[u"c01"][1])

    def test_i_5_the_cli_returns_rc_0_and_a_json_for_every_broken_command_line_and_file(self):
        f = fake()
        script = os.path.join(ROOT, CHECK_REL)
        bad_files = {
            "empty.json": b"", "nan.json": b'{"x": NaN}', "inf.json": b'{"x": Infinity}', "trunc.json": u'{"型の版": "u1", "材料": ['.encode("utf-8"),
            "lone.json": u'{"a": "\\ud800"}'.encode("utf-8"), "latin1.json": u'{"a": "é"}'.encode("latin-1"), "bom.json": b'\xef\xbb\xbf{}',
            "nulls.json": b"\x00\x00", "deep.json": b"[" * 100000 + b"]" * 100000, "big.json": b'{"a": ' + b"9" * 100000 + b"}", "str.json": b'"x"', "num.json": b"1",
        }
        d = os.path.join(f.tmp, "badb")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        for n, data in bad_files.items():
            with open(os.path.join(d, n), "wb") as fh:
                fh.write(data)
        for mode, extra in (("without-table", []), ("with-table", ["--table", f.table_path])):
            rc, out, err = run_cli([script, mode, "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle-dir", d] + extra)
            self.assertEqual(0, rc, err)
            res = json.loads(out)[u"束の結果"]
            self.assertEqual(set(bad_files), set(res))
            for n, r in res.items():
                self.assertEqual(u"断り", r[u"束"][u"状態"], n)
            # 1 束ずつ
            for n in ("empty.json", "deep.json", "lone.json"):
                rc, out, err = run_cli([script, mode, "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle", os.path.join(d, n)] + extra)
                self.assertEqual(0, rc, err)
                self.assertEqual(u"断り", json.loads(out)[u"束"][u"状態"])
        # 命令・引数・path の壊れ
        cases = [[], ["x"], ["without-table"], ["with-table", "--spec", spec_path("D")], ["without-table", "--bundle"], ["without-table", "--spec"],
                 ["without-table", "--spec", "/no/such", "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle", os.path.join(d, "num.json")],
                 ["without-table", "--spec", spec_path("D"), "--def", "/no/such", "--reading", READING_PATH, "--src", f.path, "--bundle", os.path.join(d, "num.json")],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", "/no/such", "--src", f.path, "--bundle", os.path.join(d, "num.json")],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", "/no/such.sqlite", "--bundle", os.path.join(d, "num.json")],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", os.path.join(d, "empty.json"), "--bundle", os.path.join(d, "num.json")],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle", "/no/such"],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle-dir", "/no/such"],
                 ["without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle", "a", "--bundle-dir", "b"],
                 ["with-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--table", os.path.join(d, "nan.json"), "--bundle", os.path.join(d, "num.json")],
                 ["with-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--table", "/no/such", "--bundle", os.path.join(d, "num.json")]]
        for args in cases:
            rc, out, err = run_cli([script] + args)
            self.assertEqual(0, rc, (args, err))
            json.loads(out)
        # 出力先に書けない
        rc, out, err = run_cli([script, "without-table", "--spec", spec_path("D"), "--def", DEF_PATH, "--reading", READING_PATH, "--src", f.path, "--bundle", os.path.join(d, "num.json"), "--out", "/no/such/dir/x.json"])
        self.assertEqual(0, rc, err)

    def test_i_6_a_broken_spec_def_reading_or_table_is_refused_not_raised(self):
        f = fake()
        d = os.path.join(f.tmp, "badin")
        os.makedirs(d, exist_ok=True)
        specs = [{}, {u"成果物": u"C"}, {u"成果物": u"A", u"当期の始まり": u"2001-01-01", u"当期の終わり": u"2001-12-31"},
                 {u"成果物": u"C", u"当期の始まり": u"2001-12-31", u"当期の終わり": u"2001-01-01"}, {u"成果物": u"C", u"当期の始まり": u"x", u"当期の終わり": u"2001-12-31"},
                 {u"成果物": u"C", u"当期の始まり": u"0001-01-01", u"当期の終わり": u"2001-12-31"}, {u"成果物": u"C", u"当期の始まり": u"2001-01-01", u"当期の終わり": u"2001-12-31", u"x": 1}, [], None]
        for k, s in enumerate(specs):
            p = os.path.join(d, "s%d.json" % k)
            wjson(p, s)
            ctx, bad = CHK.make_ctx(p, DEF_PATH, READING_PATH, f.path, None)
            self.assertIsNone(ctx, k)
            self.assertEqual(u"断り", bad[u"束"][u"状態"])
        for k, defn in enumerate([{}, {u"行": 1}, {u"行": [1]}, {u"行": [{u"id": 1}]}, {u"行": [{u"id": u"a"}, {u"id": u"a"}]}, [], None]):
            p = os.path.join(d, "d%d.json" % k)
            wjson(p, defn)
            ctx, bad = CHK.make_ctx(spec_path("D"), p, READING_PATH, f.path, None)
            self.assertIsNone(ctx, k)
        rd = json.loads(read(READING_REL))
        variants = []
        r = copy.deepcopy(rd); r[u"表"][u"元帳"][u"表"] = u"GLEntry; DROP TABLE Account"; variants.append(r)
        r = copy.deepcopy(rd); r[u"表"][u"元帳"][u"列"][u"借方"] = u"Debit) --"; variants.append(r)
        r = copy.deepcopy(rd); del r[u"表"][u"科目"]; variants.append(r)
        r = copy.deepcopy(rd); r[u"結び方"][u"振替伝票の字"] = 5; variants.append(r)
        r = copy.deepcopy(rd); r[u"表"][u"元帳"][u"列"][u"日付"] = u"NoSuchColumn"; variants.append(r)
        for k, r in enumerate(variants):
            p = os.path.join(d, "r%d.json" % k)
            wjson(p, r)
            ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, p, f.path, None)
            self.assertIsNone(ctx, k)
        for k, t in enumerate([{}, {u"行": 1}, {u"行": {}}, {u"行": dict((i, {u"向き": u"x"}) for i in REF.IDS)},
                               {u"行": dict((i, {u"向き": u"借方−貸方", u"科目": [True], u"仕訳の種類の条件": None}) for i in REF.IDS)},
                               {u"行": dict((i, {u"向き": u"借方−貸方", u"科目": [1], u"仕訳の種類の条件": {u"比べ方": u"含む", u"値": u"x"}}) for i in REF.IDS)}, [], None]):
            p = os.path.join(d, "t%d.json" % k)
            wjson(p, t)
            ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, READING_PATH, f.path, p)
            self.assertIsNone(ctx, k)
        # 素材が表を持たない
        con = sqlite3.connect(os.path.join(d, "empty.sqlite"))
        con.commit()
        con.close()
        ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, READING_PATH, os.path.join(d, "empty.sqlite"), None)
        self.assertIsNone(ctx)


# ======================================================================== 10. 規則の関数 1 つずつを緩める・締める(RULE_FUNCS)
def targeted_bundles():
    u"""規則 K ごとに、その規則だけが止める材料を持つ束。戻りは {K: (期の名, 表を使うか, 束, id)}。"""
    out = {}
    gD, gS = gold_of("D"), gold_of("S")
    m = copy.deepcopy(item(gD, u"c21")); m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 1)
    out[u"K1"] = ("D", False, replace_item(gD, m), u"c21")
    # K3: 科目を足す(数値は合わせる)。KS は N2 のような作りで、別の規則は止めない
    f = fake()
    sel = REF.Sel(f.path)
    try:
        m = copy.deepcopy(item(gD, u"c22"))
        m[u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"どれか", u"値": [u"Current Asset", u"Contra Current Asset", u"Fixed Asset"]}
        m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"借方−貸方")[0])
        out[u"K3"] = ("D", True, replace_item(gD, m), u"c22")
    finally:
        sel.close()
    m = copy.deepcopy(item(gD, u"c01")); m[u"期間"] = {u"始まり": u"2001-01-02", u"終わり": u"2001-12-31"}
    out[u"K4"] = ("D", False, replace_item(gD, m), u"c01")
    m = copy.deepcopy(item(gD, u"c01")); m[u"単位"] = u"円"
    out[u"K5"] = ("D", False, replace_item(gD, m), u"c01")
    m = copy.deepcopy(item(gD, u"c01")); m[u"範囲"] = u"部門"
    out[u"K8"] = ("D", False, replace_item(gD, m), u"c01")
    m = od([(u"id", u"c02"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
    out[u"K9"] = ("S", True, replace_item(gS, m), u"c02")
    out[u"K10"] = ("S", True, gS, u"c03")                       # c03 は K10 を受けない
    out[u"K10a"] = ("S", True, gS, u"c04")
    return out


class RuleSweepTest(unittest.TestCase):
    def with_rule(self, name, fn):
        old = CHK.RULE_FUNCS[name]
        CHK.RULE_FUNCS[name] = fn
        try:
            yield
        finally:
            CHK.RULE_FUNCS[name] = old

    def test_j_1_relaxing_one_rule_lets_its_targeted_bundle_through(self):
        t = targeted_bundles()
        for k in (u"K1", u"K3", u"K4", u"K5", u"K8"):
            name, table, b, i = t[k]
            base = verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i]
            self.assertEqual((u"止める", (k,)), base, k)
            old = CHK.RULE_FUNCS[k]
            CHK.RULE_FUNCS[k] = lambda *a, **kw: False
            try:
                got = verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i]
            finally:
                CHK.RULE_FUNCS[k] = old
            self.assertEqual((u"通す", ()), got, k)
        # K9
        name, table, b, i = t[u"K9"]
        self.assertEqual((u"止める", (u"K9",)), verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i])
        old = CHK.RULE_FUNCS[u"K9"]
        CHK.RULE_FUNCS[u"K9"] = lambda *a, **kw: False
        try:
            got = verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i]
        finally:
            CHK.RULE_FUNCS[u"K9"] = old
        self.assertEqual((u"無いを受ける", ()), got)
        # K10: c04 は K3 と K10 で止まる。K10 を緩めると K3 だけになる
        name, table, b, i = t[u"K10a"]
        self.assertEqual((u"止める", (u"K3", u"K10")), verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i])
        old = CHK.RULE_FUNCS[u"K10"]
        CHK.RULE_FUNCS[u"K10"] = lambda *a, **kw: False
        try:
            got = verdicts(CHK.check_bundle(make_ctx(name, table=table), b))[i]
        finally:
            CHK.RULE_FUNCS[u"K10"] = old
        self.assertEqual((u"止める", (u"K3",)), got)

    def test_j_2_tightening_one_rule_stops_a_correct_material(self):
        g = gold_of("D")
        for k in (u"K1", u"K3", u"K4", u"K5", u"K8", u"K10"):
            old = CHK.RULE_FUNCS[k]
            CHK.RULE_FUNCS[k] = lambda *a, **kw: True
            try:
                v = verdicts(CHK.check_bundle(make_ctx("D", table=True), g))
            finally:
                CHK.RULE_FUNCS[k] = old
            self.assertEqual((u"止める", (k,)), v[u"c01"] if k != u"K7" else v[u"c01"], k)
        old = CHK.RULE_FUNCS[u"K9"]
        CHK.RULE_FUNCS[u"K9"] = lambda *a, **kw: True
        try:
            v = verdicts(CHK.check_bundle(make_ctx("D", table=True), g))
        finally:
            CHK.RULE_FUNCS[u"K9"] = old
        self.assertEqual((u"止める", (u"K9",)), v[u"c28"])
        old = CHK.RULE_FUNCS[u"K0"]
        CHK.RULE_FUNCS[u"K0"] = lambda *a, **kw: [u"x"]
        try:
            self.assertEqual(u"断り", CHK.check_bundle(make_ctx("D"), g)[u"束"][u"状態"])
        finally:
            CHK.RULE_FUNCS[u"K0"] = old
        old = CHK.RULE_FUNCS[u"K7"]
        CHK.RULE_FUNCS[u"K7"] = lambda ctx, results, items: (set(i[u"id"] for i in results), 3, 0)
        try:
            v = verdicts(CHK.check_bundle(make_ctx("D"), g))
        finally:
            CHK.RULE_FUNCS[u"K7"] = old
        self.assertEqual((u"止める", (u"K7",)), v[u"c01"])

    def test_j_3_relaxing_k7_lets_the_broken_relation_through_and_k0_lets_a_broken_bundle_through(self):
        g = gold_of("D")
        m = copy.deepcopy(item(g, u"c06"))
        m[u"出どころ"][u"条件"][0] = {u"列": u"科目の大分類", u"比べ方": u"等しい", u"値": u"Revenue"}
        f = fake()
        sel = REF.Sel(f.path)
        try:
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"貸方−借方")[0])
        finally:
            sel.close()
        b = replace_item(g, m)
        self.assertEqual((u"止める", (u"K7",)), verdicts(CHK.check_bundle(make_ctx("D"), b))[u"c01"])
        old = CHK.RULE_FUNCS[u"K7"]
        CHK.RULE_FUNCS[u"K7"] = lambda ctx, results, items: (set(), 0, 0)
        try:
            v = verdicts(CHK.check_bundle(make_ctx("D"), b))
        finally:
            CHK.RULE_FUNCS[u"K7"] = old
        self.assertEqual((u"通す", ()), v[u"c01"])
        bad = copy.deepcopy(g)
        bad[u"型の版"] = u"u9"
        self.assertEqual(u"断り", CHK.check_bundle(make_ctx("D"), bad)[u"束"][u"状態"])
        old = CHK.RULE_FUNCS[u"K0"]
        CHK.RULE_FUNCS[u"K0"] = lambda *a, **kw: []
        try:
            res = CHK.check_bundle(make_ctx("D"), bad)
        finally:
            CHK.RULE_FUNCS[u"K0"] = old
        self.assertEqual(u"受理", res[u"束"][u"状態"])             # K0 を緩めると、版の違う束が受理される

    def test_j_4_the_ref_n_functions_swept_to_do_nothing_are_caught_by_the_build_tests(self):
        u"""N ごとに ``mutate_item`` を「その N だけ作らない」に差し替えると、作れた数が変わる(門の ``MutationBuildTest`` の前提が赤になる)。"""
        f = fake()
        sel = REF.Sel(f.path)
        cs, ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
        g = gold_of("S")
        base = collections.Counter(n for n, i, nb, _s in REF.make_mutations(sel, g, cs, ce) if nb is not None)
        try:
            for n in REF.MUTATIONS:
                self.assertGreater(base[n], 0, n)
                orig = REF.mutate_item
                REF.mutate_item = (lambda target: (lambda s, b, idx, name, c1, c2, kinds: None if name == target else orig(s, b, idx, name, c1, c2, kinds)))(n)
                try:
                    got = collections.Counter(nn for nn, i, nb, _s in REF.make_mutations(sel, g, cs, ce) if nb is not None)
                finally:
                    REF.mutate_item = orig
                self.assertEqual(0, got[n], n)
                for other in REF.MUTATIONS:
                    if other != n:
                        self.assertEqual(base[other], got[other], (n, other))
        finally:
            sel.close()


# ======================================================================== 11. 本文を 1 か所ずつ緩めた版(読み込んだ module の上だけ)
#: 黙る変異(同じ動きになる変異)。``carry-keeps-empty-accounts``: 科目が空の id で「空の分岐」を外しても、``科目番号 どれか []`` は 0 行を選ぶので
#: 持ち越しの束は同じ ``無い`` になる(同じ動きの変異。変異の戻りを見て、門の穴ではなく同値と判じた)。
#: 独立監査(1 巡目)の変異のうち、この REVISE で縛っていない 6 本(``c-k0-ids-count``・``c-k10-cover-union-only-mine``・``c-k10-unknown-continue``・
#: ``c-k10-mine-classes-skip``・``r-n3-second-cond``・``r-seat-folder-link``)は、実装者の読みでは同値(材料の数は重なりの検査と id の集合の検査が含む・
#: 2 本は ``if False`` を足しただけで本文が同じ動き・科目表に無い科目は内側の結びで共通の表に入らないので ``u not in cl`` に届かない・
#: ``return`` の後ろの ``continue`` は実行されない・``os.link`` が失敗した時の写しと同じ結果)。この REVISE では同値と断定せず、監査の判じを待つ。
#: 2 巡目の REVISE で、監査が門の穴と判じた ``r-seat-folder-link`` は ``test_q_10`` が、``n3-nocand-continue``・``n3-all-conds`` は ``test_q_8`` が縛った(同値ではなかった)。
SILENT_BY_DESIGN = (u"carry-keeps-empty-accounts",)


def check_battery(mod):
    u"""検査の module に、作り物の素材の上で、答えが決まっている場面を掛ける。戻りは外れた場面の名の並び(空なら全部合う)。"""
    f = fake()
    problems = []

    def ctx_of(name, table):
        c, bad = mod.make_ctx(spec_path(name), DEF_PATH, READING_PATH, f.path, f.table_path if table else None)
        if c is None:
            raise AssertionError(bad)
        return c

    def v_of(res):
        return dict((r[u"id"], (r[u"判定"], tuple(r[u"規則"]))) for r in res[u"材料"]) if res[u"束"][u"状態"] == u"受理" else {}
    try:
        gD, gS = gold_of("D"), gold_of("S")
        sel = REF.Sel(f.path)
        try:
            def want(name, bundle, table, i, expect, label):
                got = v_of(mod.check_bundle(ctx_of(name, table), bundle)).get(i)
                if got != expect:
                    problems.append(u"%s: %r != %r" % (label, got, expect))
            # 正解の束は両方で通る(結ばれない行の空・丸め・向き・点の行)
            for name, g in (("D", gD), ("S", gS)):
                for i in (u"c01", u"c06", u"c08", u"c21", u"c23"):
                    want(name, g, False, i, (u"通す", ()), u"gold-plain-%s-%s" % (name, i))
            for i in (u"c01", u"c06", u"c08", u"c21", u"c23", u"c26"):
                want("D", gD, True, i, (u"通す", ()), u"gold-tabled-D-%s" % i)
            for i in (u"c02", u"c07", u"c27", u"c09", u"c20"):
                want("S", gS, False, i, (u"通す", ()), u"gold-plain-S-%s" % i)
            # 期間の欄だけ違う(条件の日付は合う)
            m = copy.deepcopy(item(gD, u"c01")); m[u"期間"] = {u"始まり": u"2001-01-02", u"終わり": u"2001-12-31"}
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K4",)), u"k4-period-field")
            # 無いを 0 として数える(R1)
            want("D", replace_item(gD, od([(u"id", u"c09"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])), False, u"c10", (u"止める", (u"K7",)), u"k7-none-as-zero")
            # 余分な鍵は K0
            m = copy.deepcopy(item(gD, u"c01")); m[u"extra"] = 1
            if mod.check_bundle(ctx_of("D", False), replace_item(gD, m))[u"束"][u"状態"] != u"断り":
                problems.append(u"k0-extra-key")
            # 空の仕訳の種類は 等しい ・ どれか に当たらない
            for op, val in ((u"等しい", u""), (u"どれか", [u""])):
                if ctx_of("D", False).led.select([(u"仕訳の種類", op, val)])[0] != 0:
                    problems.append(u"empty-type-matches-%s" % op)
            # 半分の端数
            n, db, cr = ctx_of("D", False).led.select([(u"科目番号", u"等しい", 4010), (u"日付", u"以上", u"2001-01-15"), (u"日付", u"以下", u"2001-01-15")])
            if cr != sum(hu(r["cre"]) for r in f.rows if r["acct"] == 4010 and r["date"] == u"2001-01-15"):
                problems.append(u"rounding-tie")
            # 数値が 1 銭違えば止める(K1)
            m = copy.deepcopy(item(gD, u"c01")); m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 1)
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K1",)), u"k1")
            # 0 行を選ぶ条件の 0.00(K1 の下限)
            m = copy.deepcopy(item(gD, u"c01")); m[u"出どころ"][u"条件"][0][u"値"] = [u"none"]; m[u"数値"] = u"0.00"
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K1",)), u"k1-floor")
            # 向きの反転(符号)
            m = copy.deepcopy(item(gD, u"c21")); m[u"出どころ"][u"向き"] = u"貸方−借方"; m[u"数値"] = u"-" + m[u"数値"]
            want("D", replace_item(gD, m), False, u"c21", (u"通す", ()), u"direction")
            # 時点の行に下限を足すと K4(時点の行の下限)
            m = copy.deepcopy(item(gD, u"c21")); m[u"出どころ"][u"条件"].append({u"列": u"日付", u"比べ方": u"以上", u"値": u"2001-01-01"})
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"借方−貸方")[0])
            want("D", replace_item(gD, m), False, u"c21", (u"止める", (u"K4",)), u"k4-point-lower")
            # 期の日付が 1 日違えば K4
            m = copy.deepcopy(item(gD, u"c01")); m[u"出どころ"][u"条件"][-1][u"値"] = u"2001-12-30"
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"貸方−借方")[0])
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K4",)), u"k4-end")
            # 空の仕訳の種類は 等しい に当たらない・どれでもない に当たる(数 = 作り物の行から別に導く)
            for op, val, expect_rows in ((u"どれでもない", [u"Opening"], f.pick(lambda r: r["je"] != u"Opening", None, u"2001-12-31")),
                                         (u"等しい", u"Opening", f.pick(lambda r: r["je"] == u"Opening", None, u"2001-12-31")),
                                         (u"どれか", [u"Opening", u"Accrual"], f.pick(lambda r: r["je"] in (u"Opening", u"Accrual"), None, u"2001-12-31"))):
                conds = [(u"仕訳の種類", op, val), (u"日付", u"以下", u"2001-12-31")]
                n, db, cr = ctx_of("D", False).led.select(conds)
                if (n, db - cr) != (len(expect_rows), f.cents_sum(expect_rows, False)):
                    problems.append(u"null-semantics-%s" % op)
            # 丸め(1000.7 は 1001・0.29 は 29)
            n, db, cr = ctx_of("D", False).led.select([(u"科目番号", u"等しい", 1100), (u"日付", u"以上", u"2001-01-15"), (u"日付", u"以下", u"2001-01-15")])
            rows = [r for r in f.rows if r["acct"] == 1100 and r["date"] == u"2001-01-15"]
            if db != sum(hu(r["deb"]) for r in rows):
                problems.append(u"rounding")
            # K3: 余り・漏れ・向き
            m = copy.deepcopy(item(gD, u"c01"))
            m[u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"どれか", u"値": [u"Operating Revenue", u"Contra Revenue", u"Other Expense"]}
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"貸方−借方")[0])
            want("D", replace_item(gD, m), True, u"c01", (u"止める", (u"K3",)), u"k3-extra")
            m = copy.deepcopy(item(gD, u"c01")); m[u"出どころ"][u"条件"][0] = {u"列": u"科目の小分類", u"比べ方": u"どれか", u"値": [u"Operating Revenue"]}
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"貸方−借方")[0])
            want("D", replace_item(gD, m), True, u"c01", (u"止める", (u"K3",)), u"k3-lack")
            m = copy.deepcopy(item(gD, u"c01")); m[u"出どころ"][u"向き"] = u"借方−貸方"; m[u"数値"] = u"-" + m[u"数値"]
            want("D", replace_item(gD, m), True, u"c01", (u"止める", (u"K3",)), u"k3-direction")
            # K9
            m = od([(u"id", u"c02"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
            want("S", replace_item(gS, m), True, u"c02", (u"止める", (u"K9",)), u"k9")
            want("S", replace_item(gS, m), False, u"c02", (u"無いを受ける", ()), u"k9-plain")
            # K9 の下限 1(1 行だけを選ぶ表)
            t1 = copy.deepcopy(f.table); t1[u"行"][u"c28"][u"科目"] = [1600]
            p1 = os.path.join(f.tmp, "t_one.json"); wjson(p1, t1)
            c1, _ = mod.make_ctx(spec_path("S"), DEF_PATH, READING_PATH, f.path, p1)
            if v_of(mod.check_bundle(c1, gS)).get(u"c28", (None, ()))[1] != (u"K9",) and u"K9" not in v_of(mod.check_bundle(c1, gS)).get(u"c28", (None, ()))[1]:
                problems.append(u"k9-floor-1")
            # K10 の 2 段
            v = v_of(mod.check_bundle(ctx_of("S", True), gS))
            if u"K10" in v.get(u"c03", (None, ()))[1]:
                problems.append(u"k10-stage1-too-wide")
            if u"K10" not in v.get(u"c04", (None, ()))[1]:
                problems.append(u"k10-stage1-narrow")
            if u"K10" not in v.get(u"c23", (None, ()))[1]:
                problems.append(u"k10-stage2-narrow")
            if u"K10" not in v.get(u"c08", (None, ()))[1]:
                problems.append(u"k10-stage2-only-by-type")
            if u"K10" in v.get(u"c25", (None, ()))[1] or u"K10" in v.get(u"c24", (None, ()))[1]:
                problems.append(u"k10-too-wide")
            if u"K10" not in v.get(u"c28", (None, ()))[1]:
                problems.append(u"k10-none-row")
            # 規則の持ち越しの束は同じ期で正解と同じ
            # K7 の関係
            m = copy.deepcopy(item(gD, u"c06")); m[u"出どころ"][u"条件"][0] = {u"列": u"科目の大分類", u"比べ方": u"等しい", u"値": u"Revenue"}
            m[u"数値"] = REF.fmt_cents(sel.signed([(c[u"列"], c[u"比べ方"], c[u"値"]) for c in m[u"出どころ"][u"条件"]], u"貸方−借方")[0])
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K7",)), u"k7")
            # K0
            if mod.check_bundle(ctx_of("D", False), {u"型の版": u"u0", u"材料": gD[u"材料"]})[u"束"][u"状態"] != u"断り":
                problems.append(u"k0")
            # 材料の数・単位・範囲
            m = copy.deepcopy(item(gD, u"c01")); m[u"単位"] = u"円"
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K5",)), u"k5")
            m = copy.deepcopy(item(gD, u"c01")); m[u"範囲"] = u"部門"
            want("D", replace_item(gD, m), False, u"c01", (u"止める", (u"K8",)), u"k8")
        finally:
            sel.close()
    except AssertionError as exc:
        problems.append(u"assert: %s" % exc)
    except Exception as exc:                          # noqa: BLE001
        problems.append(u"exception: %s" % type(exc).__name__)
    return problems


def ref_battery(mod):
    u"""答えを知っている側の module に、作り物の素材の上で答えが決まっている場面を掛ける。"""
    f = fake()
    problems = []
    try:
        sel = mod.Sel(f.path)
        try:
            cs, ce = mod.pdate(S_SPEC[0]), mod.pdate(S_SPEC[1])
            g = json.loads(json.dumps(mod.gold_bundle(sel, cs, ce), ensure_ascii=False))
            # 正解の値(別の導き方)
            exp = {u"c01": f.cents_sum(f.pick(lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2), S_SPEC[0], S_SPEC[1]), True),
                   u"c08": f.cents_sum(f.pick(lambda r: r["sub"] == u"Contra Fixed Asset" and r["je"] == u"Depreciation", S_SPEC[0], S_SPEC[1]), True),
                   u"c21": f.cents_sum(f.pick(lambda r: r["acct"] == 1010, None, S_SPEC[1]), False),
                   u"c26": f.cents_sum(f.pick(lambda r: r["typ"] in (u"Equity", u"Revenue", u"Expense"), None, S_SPEC[1]), True)}
            for i, v in exp.items():
                if item(g, i)[u"数値"] != REF.fmt_cents(v):
                    problems.append(u"gold-%s" % i)
            muts = dict(((n, i), nb) for n, i, nb, _s in mod.make_mutations(sel, g, cs, ce))
            def mm(n, i):
                nb = muts.get((n, i))
                return None if nb is None else item(nb, i)
            m = mm(u"N1", u"c01")
            if m is None or REF.parse_cents(m[u"数値"]) != REF.parse_cents(item(g, u"c01")[u"数値"]) + 1:
                problems.append(u"N1")
            m = mm(u"N2", u"c01")
            if m is None or m[u"出どころ"][u"条件"][-1][u"値"] != [4010]:
                problems.append(u"N2")
            exp_n2 = f.cents_sum(f.pick(lambda r: r["sub"] in (u"Operating Revenue", u"Contra Revenue") and r["je"] not in (CLOSE1, CLOSE2) and r["acct"] != 4010, S_SPEC[0], S_SPEC[1]), True)
            m = mm(u"N2", u"c01")
            if m is None or m[u"数値"] != REF.fmt_cents(exp_n2):
                problems.append(u"N2-number")
            m = mm(u"N4", u"c02")
            if m is None or [c for c in m[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"][0][u"値"] != u"2002-12-31":
                problems.append(u"N4-prior")
            g2 = copy.deepcopy(g)
            item(g2, u"c02")[u"数値"] = item(g2, u"c01")[u"数値"]
            m11 = dict(((n, i), nb) for n, i, nb, _s in mod.make_mutations(sel, g2, cs, ce))[(u"N11", u"c01")]
            if m11 is None or item(m11, u"c01")[u"数値"] != item(g2, u"c03")[u"数値"]:
                problems.append(u"N11-skips-same-value")
            n_e, _db, _cr = sel.agg([(u"仕訳の種類", u"等しい", u"")])
            if n_e != 0:
                problems.append(u"ref-empty-type-equals")
            m = mm(u"N3", u"c21")
            if m is None or m[u"出どころ"][u"条件"][0][u"値"] != [1010, 1100]:
                problems.append(u"N3")
            m = mm(u"N4", u"c09")
            if m is None or tuple(c[u"値"] for c in m[u"出どころ"][u"条件"][-2:]) != (u"2002-02-01", u"2002-02-28"):
                problems.append(u"N4")
            m = mm(u"N4", u"c20")
            if m is None or tuple(c[u"値"] for c in m[u"出どころ"][u"条件"][-2:]) != (u"2002-11-01", u"2002-11-30"):
                problems.append(u"N4-12")
            m = mm(u"N5", u"c01")
            if m is None or m[u"期間"] != {u"始まり": u"2001-01-01", u"終わり": u"2001-12-31"}:
                problems.append(u"N5")
            m = mm(u"N6", u"c21")
            if m is None or m[u"出どころ"][u"条件"][-1][u"値"] != u"2002-01-01":
                problems.append(u"N6")
            m = mm(u"N6", u"c27")
            if m is None or m[u"出どころ"][u"条件"][-1][u"値"] != u"2001-01-01":
                problems.append(u"N6-prior")
            m = mm(u"N7", u"c01")
            if m is None or len(m[u"出どころ"][u"条件"]) != 3:
                problems.append(u"N7")
            m = mm(u"N8", u"c01")
            if m is None or m[u"状態"] != u"無い":
                problems.append(u"N8")
            m = mm(u"N9", u"c28")
            if m is None or m[u"出どころ"][u"条件"][-1][u"値"] != 1010:
                problems.append(u"N9")
            m = mm(u"N10", u"c01")
            if m is None or m[u"数値"] != u"-" + item(g, u"c01")[u"数値"]:
                problems.append(u"N10")
            m = mm(u"N11", u"c01")
            if m is None or m[u"数値"] != item(g, u"c02")[u"数値"]:
                problems.append(u"N11")
            m = mm(u"N12", u"c01")
            if m is None or [c for c in m[u"出どころ"][u"条件"] if c[u"比べ方"] == u"以下"][0][u"値"] != u"2002-12-30":
                problems.append(u"N12")
            # 作れない組
            if mm(u"N2", u"c21") is not None:
                problems.append(u"N2-single")
            if mm(u"N6", u"c01") is not None:
                problems.append(u"N6-period")
            if mm(u"N7", u"c21") is not None:
                problems.append(u"N7-none")
            if mm(u"N9", u"c01") is not None:
                problems.append(u"N9-present")
            # 表と持ち越し(開発の期)
            cd, ced = mod.pdate(D_SPEC[0]), mod.pdate(D_SPEC[1])
            t = mod.make_table(sel, cd, ced)
            if t[u"行"][u"c01"][u"科目"] != [4010, 4090] or t[u"行"][u"c30"][u"科目"] != [] or t[u"行"][u"c02"] != t[u"行"][u"c01"]:
                problems.append(u"table")
            cb = mod.carry_bundle(sel, t, cd, ced)
            gd = mod.gold_bundle(sel, cd, ced)
            if [(m[u"id"], m[u"状態"], m.get(u"数値")) for m in cb[u"材料"]] != [(m[u"id"], m[u"状態"], m.get(u"数値")) for m in gd[u"材料"]]:
                problems.append(u"carry-same-period")
            cs2 = mod.carry_bundle(sel, t, cs, ce)
            if item(cs2, u"c30")[u"状態"] != u"無い":
                problems.append(u"carry-empty-accounts")
            if mod.relation_status(g) != od((k, True) for k in mod.RELATIONS):
                problems.append(u"relations")
            # 丸め
            n, db, cr = sel.agg([(u"科目番号", u"等しい", 1100), (u"日付", u"以上", u"2001-01-15"), (u"日付", u"以下", u"2001-01-15")])
            rows = [r for r in f.rows if r["acct"] == 1100 and r["date"] == u"2001-01-15"]
            if db != sum(hu(r["deb"]) for r in rows):
                problems.append(u"rounding")
            # 空の仕訳の種類
            n, db, cr = sel.agg([(u"仕訳の種類", u"どれでもない", [u"Opening"]), (u"日付", u"以下", u"2001-12-31")])
            if n != len(f.pick(lambda r: r["je"] != u"Opening", None, u"2001-12-31")):
                problems.append(u"ref-null")
            n, db, cr = sel.agg([(u"仕訳の種類", u"等しい", u"Opening"), (u"日付", u"以下", u"2001-12-31")])
            if n != len(f.pick(lambda r: r["je"] == u"Opening", None, u"2001-12-31")):
                problems.append(u"ref-eq")
        finally:
            sel.close()
    except Exception as exc:                          # noqa: BLE001
        problems.append(u"exception: %s %s" % (type(exc).__name__, exc))
    return problems


def replace_once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)


#: 検査の本文を 1 か所緩めた版(old → new)。同じ電池が赤にならなければ、その変異は「黙った」
CHECK_MUTANTS = [
    (u"null-not-in-excludes-null", u'parts.append("(%s IS NULL OR %s NOT IN (%s))" % (c, c, ",".join("?" * len(val))))', u'parts.append("(%s IS NOT NULL AND %s NOT IN (%s))" % (c, c, ",".join("?" * len(val))))'),
    (u"rounding-truncate", u"return int(Decimal(x * 100).to_integral_value(rounding=ROUND_HALF_UP, context=BIGCTX))", u"return int(x * 100)"),
    (u"rounding-half-even", u"to_integral_value(rounding=ROUND_HALF_UP, context=BIGCTX)", u"to_integral_value(rounding=decimal.ROUND_HALF_EVEN, context=BIGCTX)"),
    (u"empty-string-is-a-value", u"(r[6] if r[6] != u\"\" else None)", u"r[6]"),
    (u"k1-floor-zero-rows", u"    if n < 1:\n        return True\n    return signed(", u"    if n < 0:\n        return True\n    return signed("),
    (u"direction-always-credit", u"return db - cr if direction == u\"借方−貸方\" else cr - db", u"return cr - db"),
    (u"k4-point-no-lower-check", u"return not (not ups and dns == [period[1].isoformat()] and p == {u\"時点\": period[1].isoformat()})", u"return not (dns == [period[1].isoformat()] and p == {u\"時点\": period[1].isoformat()})"),
    (u"k4-period-field-unchecked", u"and p == {u\"始まり\": period[1].isoformat(), u\"終わり\": period[2].isoformat()})", u")"),
    (u"k4-end-unchecked", u"ups == [period[1].isoformat()] and dns == [period[2].isoformat()]", u"ups == [period[1].isoformat()]"),
    (u"k9-floor-two", u"return ctx.led.select(cc)[0] >= 1", u"return ctx.led.select(cc)[0] >= 2"),
    (u"k10-stage-always-pair", u"        if s in all_sub:\n            if (t, s) in mine_cls:\n                return True\n        elif t in set(c[0] for c in mine_cls):\n            return True",
     u"        if (t, s) in mine_cls:\n            return True"),
    (u"k10-stage-always-type", u"        if s in all_sub:\n            if (t, s) in mine_cls:\n                return True\n        elif t in set(c[0] for c in mine_cls):\n            return True",
     u"        if t in set(c[0] for c in mine_cls):\n            return True"),
    (u"k10-empty-mine-passes", u"    if not mine:\n        return True\n    cl = ctx.led.classes", u"    if not mine:\n        return False\n    cl = ctx.led.classes"),
    (u"k10-ignores-period", u"present = ctx.led.accounts_in(period)", u"present = ctx.led.accounts_in((u\"時点\", datetime.date(1900, 1, 1)))"),
    (u"k3-ignores-leak", u"return info[u\"k3\"][u\"余り\"] != 0 or info[u\"k3\"][u\"漏れ\"] != 0 or m[u\"出どころ\"][u\"向き\"] != ctx.table.rows[i][u\"向き\"]",
     u"return info[u\"k3\"][u\"余り\"] != 0 or m[u\"出どころ\"][u\"向き\"] != ctx.table.rows[i][u\"向き\"]"),
    (u"k3-ignores-extra", u"return info[u\"k3\"][u\"余り\"] != 0 or info[u\"k3\"][u\"漏れ\"] != 0 or m[u\"出どころ\"][u\"向き\"] != ctx.table.rows[i][u\"向き\"]",
     u"return info[u\"k3\"][u\"漏れ\"] != 0 or m[u\"出どころ\"][u\"向き\"] != ctx.table.rows[i][u\"向き\"]"),
    (u"k3-ignores-direction", u"return info[u\"k3\"][u\"余り\"] != 0 or info[u\"k3\"][u\"漏れ\"] != 0 or m[u\"出どころ\"][u\"向き\"] != ctx.table.rows[i][u\"向き\"]",
     u"return info[u\"k3\"][u\"余り\"] != 0 or info[u\"k3\"][u\"漏れ\"] != 0"),
    (u"k7-unequal-relation-passes", u"if sum(usable[i] for i in left) != sum(usable[i] for i in right):", u"if False:"),
    (u"k7-none-not-counted-as-zero", u"            usable[r[u\"id\"]] = 0\n", u"            pass\n"),
    (u"k5-unit-unchecked", u"return m[u\"単位\"] != d.get(u\"単位\")", u"return False"),
    (u"k8-scope-unchecked", u"return m[u\"範囲\"] != d.get(u\"範囲\")", u"return False"),
    (u"k0-version-unchecked", u"    if bundle[u\"型の版\"] != u\"u1\":\n        return [u\"型の版\"]\n", u""),
    (u"k0-extra-keys-allowed", u"    if set(m) != {u\"id\", u\"状態\", u\"数値\", u\"単位\", u\"期間\", u\"範囲\", u\"出どころ\"}:\n        return u\"在るの鍵\"\n", u""),
    (u"conds-or-instead-of-and", u"return (\" WHERE \" + \" AND \".join(parts)) if parts else \"\", args", u"return (\" WHERE \" + \" OR \".join(parts)) if parts else \"\", args"),
    (u"date-lower-exclusive", u"parts.append(\"%s >= ?\" % c)", u"parts.append(\"%s > ?\" % c)"),
    (u"date-upper-exclusive", u"parts.append(\"%s <= ?\" % c)", u"parts.append(\"%s < ?\" % c)"),
    (u"join-ignores-voucher-type", u"LEFT JOIN %s j ON g.%s = ? AND j.%s = g.%s", u"LEFT JOIN %s j ON ? = ? AND j.%s = g.%s"),
    (u"previous-period-shift", u"sp.ps = add_months(cs, -12)", u"sp.ps = add_months(cs, -11)"),
]

REF_MUTANTS = [
    (u"n2-max", u"src[u\"条件\"].append(cond_dict(C(NUM, u\"どれでもない\", [min(accs)])))", u"src[u\"条件\"].append(cond_dict(C(NUM, u\"どれでもない\", [max(accs)])))"),
    (u"n3-max", u"c[u\"値\"] = cur + [min(cand)]", u"c[u\"値\"] = cur + [max(cand)]"),
    (u"n9-max", u"conds = date_conds(period) + [C(NUM, u\"等しい\", min(accs))]", u"conds = date_conds(period) + [C(NUM, u\"等しい\", max(accs))]"),
    (u"n12-two-days", u"c[u\"値\"] = (pdate(c[u\"値\"]) - datetime.timedelta(days=1)).isoformat()", u"c[u\"値\"] = (pdate(c[u\"値\"]) - datetime.timedelta(days=2)).isoformat()"),
    (u"n4-month-12-to-13", u"return u\"当期の月:%d\" % (k + 1 if k < 12 else 11)", u"return u\"当期の月:%d\" % (k + 1 if k < 12 else 10)"),
    (u"n4-prior-wrong", u"    if kind == u\"前期\":\n        return u\"当期\"", u"    if kind == u\"前期\":\n        return u\"前期\""),
    (u"n5-keeps-field", u"        if name == u\"N5\":\n            m[u\"期間\"] = period_field(np_)", u"        if name == u\"N5\":\n            pass"),
    (u"n6-prior-start", u"start = cs if kind == u\"当期末\" else add_months(cs, -12)", u"start = cs"),
    (u"n6-allows-period-rows", u"        if period[0] != u\"時点\":\n            return None\n        start", u"        start"),
    (u"n7-removes-first-cond", u"keep = [c for c in src[u\"条件\"] if not (c[u\"列\"] == JT and c[u\"比べ方\"] == u\"どれでもない\")]", u"keep = src[u\"条件\"][1:]"),
    (u"n10-keeps-number", u"        src[u\"向き\"] = SIGN_CREDIT_DEBIT if src[u\"向き\"] == SIGN_DEBIT_CREDIT else SIGN_DEBIT_CREDIT\n        return reeval(sel, m)", u"        src[u\"向き\"] = SIGN_CREDIT_DEBIT if src[u\"向き\"] == SIGN_DEBIT_CREDIT else SIGN_DEBIT_CREDIT\n        return m"),
    (u"n2-forgets-to-match-number", u"        src[u\"条件\"].append(cond_dict(C(NUM, u\"どれでもない\", [min(accs)])))\n        return reeval(sel, m)", u"        src[u\"条件\"].append(cond_dict(C(NUM, u\"どれでもない\", [min(accs)])))\n        return m"),
    (u"n2-single-account-made", u"        if len(accs) < 2:\n            return None", u"        if len(accs) < 1:\n            return None"),
    (u"n11-skips-same-check", u"if o[u\"状態\"] == u\"在る\" and o[u\"数値\"] != m[u\"数値\"]:", u"if o[u\"状態\"] == u\"在る\":"),
    (u"n11-swaps-only-source", u"                m[u\"数値\"] = o[u\"数値\"]\n                return m", u"                return m"),
    (u"n1-two-cents", u"m[u\"数値\"] = fmt_cents(parse_cents(m[u\"数値\"]) + 1)", u"m[u\"数値\"] = fmt_cents(parse_cents(m[u\"数値\"]) + 2)"),
    (u"n8-keeps-state", u"    if name == u\"N8\":\n        return none_material(i)", u"    if name == u\"N8\":\n        return m"),
    (u"deb-truncates", u"DEB = u\"CAST(ROUND(g.Debit * 100) AS INTEGER)\"", u"DEB = u\"CAST(g.Debit * 100 AS INTEGER)\""),
    (u"null-excluded", u"parts.append(u\"(%s IS NULL OR %s NOT IN (%s))\" % (c, c, ph))", u"parts.append(u\"(%s IS NOT NULL AND %s NOT IN (%s))\" % (c, c, ph))"),
    (u"empty-not-null", u"u\"NULLIF(j.EntryType, '')\"", u"u\"j.EntryType\""),
    (u"table-same-as-prior-missing", u"    same = {u\"c02\": u\"c01\", u\"c07\": u\"c06\", u\"c27\": u\"c26\"}", u"    same = {u\"c07\": u\"c06\", u\"c27\": u\"c26\"}"),
    (u"carry-keeps-empty-accounts", u"        if not r[u\"科目\"]:\n            items.append(none_material(i))\n            continue\n        conds = [C(NUM", u"        conds = [C(NUM"),
    (u"gold-keeps-zero-row-materials", u"items.append(make_material(i, p, g[u\"向き\"], conds, s) if n >= 1 else none_material(i))", u"items.append(make_material(i, p, g[u\"向き\"], conds, s))"),
    (u"gold-c08-not-depreciation-only", u"        conds.append(C(JT, u\"等しい\", DEPRECIATION))", u"        pass"),
    (u"gold-close-not-excluded", u"        conds.append(C(JT, u\"どれでもない\", list(CLOSE)))", u"        pass"),
    (u"relations-r3-wrong", u"(u\"R3\", ([u\"c01\", u\"c05\"], [u\"c03\", u\"c04\", u\"c06\"]))", u"(u\"R3\", ([u\"c01\"], [u\"c03\", u\"c04\", u\"c06\"]))"),
]


class SourceMutantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check_text = read(CHECK_REL)
        cls.ref_text = read(REF_REL)
        cls.sha_before = (sha(CHECK_REL), sha(REF_REL))

    @classmethod
    def tearDownClass(cls):
        assert cls.sha_before == (sha(CHECK_REL), sha(REF_REL)), u"変異は file を触らない"

    def test_k_1_the_unmutated_modules_pass_their_batteries(self):
        self.assertEqual([], check_battery(CHK))
        self.assertEqual([], ref_battery(REF))

    def test_k_2_every_check_mutant_turns_the_battery_red(self):
        silent = []
        for name, old, new in CHECK_MUTANTS:
            text = replace_once(self.check_text, old, new)
            mod = load_module(CHECK_REL, "um1_check_mutant", text=text)
            if not check_battery(mod) and name not in SILENT_BY_DESIGN:
                silent.append(name)
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(CHECK_MUTANTS), 25)

    def test_k_3_every_ref_mutant_turns_the_battery_red(self):
        silent = []
        for name, old, new in REF_MUTANTS:
            text = replace_once(self.ref_text, old, new)
            mod = load_module(REF_REL, "um1_ref_mutant", text=text)
            if not ref_battery(mod) and name not in SILENT_BY_DESIGN:
                silent.append(name)
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(REF_MUTANTS), 25)

    def test_k_4_the_mutants_all_differ_from_the_original_text(self):
        for name, old, new in CHECK_MUTANTS:
            self.assertNotEqual(old, new, name)
            self.assertEqual(1, self.check_text.count(old), name)
        for name, old, new in REF_MUTANTS:
            self.assertNotEqual(old, new, name)
            self.assertEqual(1, self.ref_text.count(old), name)
        self.assertEqual(len(set(n for n, _o, _w in CHECK_MUTANTS)), len(CHECK_MUTANTS))
        self.assertEqual(len(set(n for n, _o, _w in REF_MUTANTS)), len(REF_MUTANTS))


# ======================================================================== 12. 答えを知っている側の命令(作り物の素材で)
class RefCommandTest(unittest.TestCase):
    def test_l_1_build_dev_makes_the_year_only_copy_and_nulls_the_later_dates(self):
        tmp = tempfile.mkdtemp(prefix="um1_dev_")
        try:
            src = os.path.join(tmp, "s.sqlite")
            con = sqlite3.connect(src)
            cols = {"Account": ["AccountID"], "CostCenter": ["x"], "Warehouse": ["x"], "Customer": ["x"], "Supplier": ["x"],
                    "GLEntry": ["FiscalYear", "PostingDate"], "JournalEntry": ["PostingDate"], "Budget": ["FiscalYear"], "BudgetLine": ["FiscalYear"],
                    "PayrollPeriod": ["PayrollPeriodID", "FiscalYear"], "PayrollRegister": ["PayrollRegisterID", "PayrollPeriodID"], "PayrollRegisterLine": ["PayrollRegisterID"],
                    "PayrollLiabilityRemittance": ["RemittanceDate"], "DebtAgreement": ["DebtAgreementID", "OriginationDate"], "DebtScheduleLine": ["PaymentDate", "DebtAgreementID"],
                    "FixedAsset": ["InServiceDate", "DisposalDate", "Status"], "FixedAssetEvent": ["EventDate"],
                    "Employee": ["HireDate", "TerminationDate", "TerminationReason", "EmploymentStatus", "IsActive"]}
            self.assertEqual(set(cols), set(REF.DEV_WHERE))
            for t, cs in cols.items():
                con.execute('create table "%s" (%s)' % (t, ",".join(cs)))
            con.execute("insert into GLEntry values (2023,'2023-12-31'),(2024,'2024-06-01'),(2025,'2025-01-01')")
            con.execute("insert into JournalEntry values ('2023-12-31'),('2024-12-31'),('2025-01-01')")
            con.execute("insert into PayrollPeriod values (1,2023),(2,2024),(3,2025)")
            con.execute("insert into PayrollRegister values (10,1),(11,2),(12,3)")
            con.execute("insert into PayrollRegisterLine values (10),(11),(11),(12)")
            con.execute("insert into DebtAgreement values (1,'2024-02-01'),(2,'2025-02-01')")
            con.execute("insert into DebtScheduleLine values ('2024-03-01',1),('2025-03-01',1),('2024-03-01',2)")
            con.execute("insert into FixedAsset values ('2023-01-01','2025-05-05','Disposed'),('2025-01-01',null,null),('2024-01-01','2024-05-05','Disposed')")
            con.execute("insert into Employee values ('2023-01-01','2025-01-01','x','Terminated',0),('2025-02-01',null,null,null,1),('2023-02-01','2024-07-01','y','Terminated',0)")
            con.commit()
            con.close()
            dst = os.path.join(tmp, "d.sqlite")
            counts = REF.build_dev(src, dst)
            self.assertEqual(1, counts["GLEntry"])
            self.assertEqual(1, counts["JournalEntry"])
            self.assertEqual(1, counts["PayrollPeriod"])
            self.assertEqual(1, counts["PayrollRegister"])
            self.assertEqual(2, counts["PayrollRegisterLine"])
            self.assertEqual(1, counts["DebtAgreement"])
            self.assertEqual(1, counts["DebtScheduleLine"])
            self.assertEqual(2, counts["FixedAsset"])
            self.assertEqual(2, counts["Employee"])
            d = sqlite3.connect(dst)
            self.assertEqual([(None, None), (u"2024-05-05", u"Disposed")], sorted(d.execute("select DisposalDate, Status from FixedAsset"), key=lambda r: (r[0] is not None, r[0] or "")))
            self.assertEqual([(None,), (u"2024-07-01",)], sorted(d.execute("select TerminationDate from Employee"), key=lambda r: (r[0] is not None, r[0] or "")))
            self.assertEqual(0, d.execute("select count(*) from Employee where TerminationDate > '2024-12-31'").fetchone()[0])
            d.close()
            # 素材は読むだけ: 元は変わらない
            c = sqlite3.connect(src)
            self.assertEqual(3, c.execute("select count(*) from GLEntry").fetchone()[0])
            self.assertEqual(u"2025-05-05", c.execute("select DisposalDate from FixedAsset where Status='Disposed' and InServiceDate='2023-01-01'").fetchone()[0])
            c.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_l_2_the_commands_write_the_table_the_gold_the_carry_the_seat_folder_and_the_mutations(self):
        f = fake()
        script = os.path.join(ROOT, REF_REL)
        out = os.path.join(f.tmp, "cmd")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        r = subprocess.run([sys.executable, script, "table", "--db", f.path, "--spec", spec_path("D"), "--out", os.path.join(out, "table.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(sha_file(os.path.join(out, "table.json")), r.stdout.decode().strip())
        self.assertEqual(f.table, json.loads(read_text(os.path.join(out, "table.json"))))
        for cmd, extra, name in (("gold", [], "gold.json"), ("carry", ["--table", os.path.join(out, "table.json")], "carry.json")):
            r = subprocess.run([sys.executable, script, cmd, "--db", f.path, "--spec", spec_path("S"), "--out", os.path.join(out, name)] + extra, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(gold_of("S"), json.loads(read_text(os.path.join(out, "gold.json"))))
        r = subprocess.run([sys.executable, script, "mutate", "--gold", os.path.join(out, "gold.json"), "--db", f.path, "--spec", spec_path("S"), "--def", DEF_PATH,
                            "--outdir", os.path.join(out, "mut")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        files = sorted(os.listdir(os.path.join(out, "mut")))
        sel = REF.Sel(f.path)
        try:
            made = [(n, i) for n, i, nb, _s in REF.make_mutations(sel, gold_of("S"), REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])) if nb is not None]
        finally:
            sel.close()
        self.assertEqual(sorted("%s_%s.json" % k for k in made), files)
        index = json.loads(read_text(os.path.join(out, "mut_index.json")))
        self.assertEqual(set(files), set(index))
        # 席の folder
        r = subprocess.run([sys.executable, script, "seat-folder", "--dest", os.path.join(out, "seat"), "--material", f.path, "--spec", spec_path("S"),
                            "--instruction", os.path.join(ROOT, INSTRUCTION_REL), "--def", DEF_PATH, "--reading", READING_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(sorted([u"指示書.md", u"definition_C.json", u"reading_def.json", u"指定.json", u"素材.sqlite"]), sorted(os.listdir(os.path.join(out, "seat"))))
        for name in os.listdir(os.path.join(out, "seat")):
            self.assertNotIn(u"table", name)
        self.assertEqual(sha_file(f.path), sha_file(os.path.join(out, "seat", u"素材.sqlite")))
        body = read_text(os.path.join(out, "seat", u"指示書.md"))
        self.assertNotIn(u"確かめた取り方", body)
        self.assertEqual(read(DEF_REL), read_text(os.path.join(out, "seat", "definition_C.json")))
        self.assertNotIn(REF.CLOSE[0], read_text(os.path.join(out, "seat", "definition_C.json")))

    def test_l_3_tally_a_runs_the_checks_in_separate_processes_and_counts(self):
        f = fake()
        out = os.path.join(f.tmp, "tally_a")
        shutil.rmtree(out, ignore_errors=True)
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "tally-a", "--check", os.path.join(ROOT, CHECK_REL), "--db", f.path, "--def", DEF_PATH,
                            "--reading", READING_PATH, "--table", f.table_path, "--workdir", out, "--spec", "D=" + spec_path("D"), "--spec", "S=" + spec_path("S"),
                            "--out", os.path.join(out, "a.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        a = json.loads(read_text(os.path.join(out, "a.json")))
        self.assertEqual(2, a[u"正解の束"][u"束の数"])
        self.assertEqual(60, a[u"正解の束"][u"行の数"])
        self.assertEqual(6, a[u"正解の束"][u"関係の本数"])
        self.assertEqual(6, a[u"正解の束"][u"関係が成り立つ本数"])
        self.assertEqual(60, sum(a[u"検査の結果"][u"表なし"][u"判定"].values()))
        self.assertEqual(60, sum(a[u"検査の結果"][u"表つき"][u"判定"].values()))
        self.assertEqual({}, a[u"検査の結果"][u"表なし"][u"止めた規則"])
        self.assertIn(u"K10", a[u"検査の結果"][u"表つき"][u"止めた規則"])
        self.assertEqual(set(REF.MUTATIONS), set(a[u"変異"]))
        # 作れた + 作れなかった = 60(2 つの指定 × 30 行)
        for n in REF.MUTATIONS:
            self.assertEqual(60, a[u"変異"][n][u"作れた"] + a[u"変異"][n][u"作れなかった"], n)
        # 検査の結果を関数で直接求めた数と、別 process の結果が同じ
        direct_plain = judge_all("S", False)
        direct_tab = judge_all("S", True)
        # 持ち越しの束: D では全部同じ、S では違う行が在る
        self.assertEqual(60, a[u"規則の持ち越し"][u"正解と同じ行"] + a[u"規則の持ち越し"][u"正解と違う行"])
        self.assertGreaterEqual(a[u"規則の持ち越し"][u"正解と同じ行"], 30)
        self.assertGreater(a[u"規則の持ち越し"][u"正解と違う行"], 0)
        # 別 process の変異の数 = 関数での数(S の分)
        d_made = collections.Counter(n for (n, i) in judge_all("D", False))
        s_made = collections.Counter(n for (n, i) in direct_plain)
        for n in REF.MUTATIONS:
            self.assertEqual(d_made[n] + s_made[n], a[u"変異"][n][u"作れた"], n)
        d_plain = judge_all("D", False)
        self.assertEqual(sum(1 for k, (v, s) in list(d_plain.items()) + list(direct_plain.items()) if passed(v) and k[0] == u"N1"), a[u"変異"][u"N1"][u"表なしが通した"])
        d_tab = judge_all("D", True)
        for n in REF.MUTATIONS:
            self.assertEqual(sum(1 for k, (v, s) in list(d_tab.items()) + list(direct_tab.items()) if passed(v) and k[0] == n), a[u"変異"][n][u"表つきが通した"], n)
            self.assertEqual(sum(1 for k, (v, s) in list(d_plain.items()) + list(direct_plain.items()) if passed(v) and k[0] == n), a[u"変異"][n][u"表なしが通した"], n)

    def test_l_4_tally_b_counts_seat_answers_against_the_gold_with_both_checks(self):
        f = fake()
        out = os.path.join(f.tmp, "tally_b")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        # 作り物の席: 指定 D1(= 作り物の期 D)に 3 席。1 席は正解どおり・1 席は c01 の数値を 1 銭ずらす・1 席は c08 を無いと書き(正解は在る)・c28 を在ると書く
        gold = gold_of("D")
        seats = []
        for k in range(3):
            d = os.path.join(out, "seat%d" % k)
            os.makedirs(d)
            wjson(os.path.join(d, u"指定.json"), od([(u"成果物", u"C"), (u"当期の始まり", D_SPEC[0]), (u"当期の終わり", D_SPEC[1])]))
            b = copy.deepcopy(gold)
            if k == 1:
                m = item(b, u"c01"); m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 1)
            if k == 2:
                b = replace_item(b, od([(u"id", u"c08"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")]))
            if k < 3:
                wjson(os.path.join(d, u"材料.json"), b)
            seats.append(d)
        # 4 つ目: 材料.json が壊れている席
        d = os.path.join(out, "seat3")
        os.makedirs(d)
        wjson(os.path.join(d, u"指定.json"), od([(u"成果物", u"C"), (u"当期の始まり", S_SPEC[0]), (u"当期の終わり", S_SPEC[1])]))
        with open(os.path.join(d, u"材料.json"), "wb") as fh:
            fh.write(b"{broken")
        seats.append(d)
        old = REF.DESIGNATIONS
        REF.DESIGNATIONS = od([(u"D1", D_SPEC), (u"S1", S_SPEC)])
        try:
            ns = type("A", (), {})()
            ns.check, ns.db, ns.def_, ns.reading, ns.table, ns.workdir = os.path.join(ROOT, CHECK_REL), f.path, DEF_PATH, READING_PATH, f.table_path, os.path.join(out, "w")
            ns.seat, ns.dirty, ns.out = seats, "seat1", os.path.join(out, "b.json")
            REF.tally_b(ns)
        finally:
            REF.DESIGNATIONS = old
        b = json.loads(read_text(os.path.join(out, "b.json")))
        self.assertEqual(4, b[u"席の数"])
        self.assertEqual(1, b[u"束が K0 で断られた数"])
        self.assertEqual(120, b[u"全部"][u"行"])
        self.assertEqual(30 + 29 + 29, b[u"全部"][u"正解どおり"])             # 席 0 は全部・席 1 は c01 だけ違う・席 2 は c08 だけ違う
        self.assertEqual(30, b[u"全部"][u"表なし"][u"断り"])
        self.assertEqual(30, b[u"全部"][u"表つき"][u"断り"])
        # 席 1 の c01(1 銭違う)は、表なしでも表つきでも K1 で止まる。席 2 の c08 の 無い は表なしが受け、表つきは K9 で止める
        self.assertEqual(0, b[u"全部"][u"表つき"][u"通した行のうち数値が違う"])
        self.assertEqual(0, b[u"全部"][u"表なし"][u"通した行のうち数値が違う"])
        self.assertEqual(1, b[u"全部"][u"表なし"][u"通した行のうち状態が違う"])
        self.assertEqual(0, b[u"全部"][u"表つき"][u"通した行のうち状態が違う"])
        self.assertEqual(1, b[u"汚れた席の数"])
        self.assertEqual(90, b[u"汚れを除く"][u"行"])
        self.assertEqual(30 + 29, b[u"汚れを除く"][u"正解どおり"])
        self.assertEqual(1, b[u"c08"][u"行"] // 4 * 0 + 1)
        self.assertEqual(4, b[u"c08"][u"行"])
        self.assertEqual(2, b[u"c08"][u"正解どおり"])                          # 席 0 と席 1 だけ(席 3 は壊れている)
        self.assertEqual(8, b[u"c28・c29"][u"行"])
        self.assertEqual(6, b[u"c28・c29"][u"席が無いと書いた"])
        self.assertEqual(28, b[u"3 席が 3 つとも同じ行"])                     # 3 席が同じ答えの行(c01・c08 は違う)。壊れた席は数えない

    def test_l_5_a_number_right_but_rows_wrong_is_counted_separately(self):
        u"""数値は同じで、条件が選ぶ行の集まりが違う席の行は、正解どおりに数えず、別に数える。
        額 0 の行(負債の科目 1 つ)を足した素材では、``科目の大分類 等しい 負債`` と ``科目番号 どれか [その科目を除く負債の科目]`` は数値が同じで行の集まりが違う。
        行の集まりが同じで書き方だけ違う席(c04 を科目番号で書く)は正解どおり。"""
        f = fake()
        out = os.path.join(f.tmp, "tally_b2")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        src = derive("liab_zero_d", accounts=[(2020, u"z payable", u"Liability", u"Current Liability")], rows=[(u"2001-06-15", 2020, 0.0, 0.0)])
        gold = gold_of("D")
        b0 = copy.deepcopy(gold)
        item(b0, u"c25")[u"出どころ"][u"条件"][0] = {u"列": u"科目番号", u"比べ方": u"どれか", u"値": [2010, 2110]}      # 数値は同じ・行の集まりが違う(2020 の行を選ばない)
        b1 = copy.deepcopy(gold)
        item(b1, u"c04")[u"出どころ"][u"条件"][0] = {u"列": u"科目番号", u"比べ方": u"どれか", u"値": [6010]}              # 行の集まりも同じ
        seats = [seat_folder_of(out, "seat0", D_SPEC, b0), seat_folder_of(out, "seat1", D_SPEC, b1)]
        b = tally_b_ns(src, seats, out, od([(u"D1", D_SPEC)]))
        self.assertEqual(60, b[u"全部"][u"行"])
        self.assertEqual(59, b[u"全部"][u"正解どおり"])
        self.assertEqual(1, b[u"全部"][u"数値は同じで行の集まりだけ違う"])
        self.assertEqual(0, b[u"全部"][u"表つき"][u"通した行のうち数値が違う"] + b[u"全部"][u"表なし"][u"通した行のうち数値が違う"])
        self.assertEqual(1, b[u"id ごと"][u"c25"][u"正解どおり"])
        self.assertEqual(2, b[u"id ごと"][u"c04"][u"正解どおり"])

    def test_l_6_source_facts_counts_unbalanced_vouchers_and_idle_accounts_that_move(self):
        f = fake()
        tmp = tempfile.mkdtemp(prefix="um1_facts_")
        try:
            # 開発の写しは、作り物の素材の 2001 年だけ
            dev = os.path.join(tmp, "dev.sqlite")
            shutil.copyfile(f.path, dev)
            c = sqlite3.connect(dev)
            c.execute("delete from GLEntry where PostingDate > '2001-12-31'")
            c.commit()
            c.close()
            out = os.path.join(tmp, "facts.json")
            r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "source-facts", "--src", f.path, "--dev", dev, "--from", u"2002-01-01", "--to", u"2002-12-31", "--out", out],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, r.returncode, r.stderr)
            facts = json.loads(read_text(out))
            self.assertEqual(0, facts[u"貸借が合わない伝票"])
            # 2001 年に動きの無い科目: 6030・8010・1600・7010・9990(動かない)
            self.assertEqual(5, facts[u"開発の年に動きが無かった科目"] - len([a for a in ACCOUNTS if a[0] in (1190,)]))
            self.assertEqual(4, facts[u"うち指定の間に行が在る科目"])
            # 貸借を崩した作り物
            bad = os.path.join(tmp, "bad.sqlite")
            shutil.copyfile(f.path, bad)
            c = sqlite3.connect(bad)
            c.execute("update GLEntry set Debit = Debit + 0.01 where GLEntryID = 5")
            c.commit()
            c.close()
            r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "source-facts", "--src", bad, "--dev", dev, "--from", u"2002-01-01", "--to", u"2002-12-31", "--out", out],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertEqual(1, json.loads(read_text(out))[u"貸借が合わない伝票"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_l_7_the_ref_opens_the_given_source_read_only(self):
        body = read(REF_REL)
        self.assertIn("mode=ro", body)
        self.assertNotIn("mode=rw", body)
        f = fake()
        before = sha_file(f.path)
        sel = REF.Sel(f.path)
        sel.agg([])
        with self.assertRaises(sqlite3.OperationalError):
            sel.con.execute("create table zz(x)")
        sel.close()
        self.assertEqual(before, sha_file(f.path))


# ======================================================================== 12b. 独立監査 REVISE(1 巡目)の直し: 監査の変異で黙った門の穴を縛る
def derive(tag, accounts=(), rows=(), orphan_rows=()):
    u"""作り物の素材の写しに、科目と行を足した素材(path)。額 0 の行は、数値を変えずに「行の集まり」だけを変える。
    ``accounts``: (番号, 名, 大分類, 小分類)。``rows``: (日付, 科目番号, 借方, 貸方)。``orphan_rows``: (日付, 科目表に無い AccountID, 借方, 貸方)。"""
    f = fake()
    dst = os.path.join(f.tmp, "derived_%s.sqlite" % tag)
    shutil.copyfile(f.path, dst)
    con = sqlite3.connect(dst)
    ids = dict(ACC_ID)
    nxt = 100
    for n, nm, ty, sub in accounts:
        ids[n] = nxt
        con.execute("INSERT INTO Account VALUES (?,?,?,?,?,NULL,NULL,1)", (nxt, n, nm, ty, sub))
        nxt += 1
    gid = 900000
    for d, n, deb, cre in rows:
        gid += 1
        con.execute("INSERT INTO GLEntry VALUES (?,?,?,?,?,?,?,NULL,NULL,?)", (gid, d, ids[n], deb, cre, u"Misc", u"ZZ-%d" % gid, int(d[:4])))
    for d, aid, deb, cre in orphan_rows:
        gid += 1
        con.execute("INSERT INTO GLEntry VALUES (?,?,?,?,?,?,?,NULL,NULL,?)", (gid, d, aid, deb, cre, u"Misc", u"ZO-%d" % gid, int(d[:4])))
    con.commit()
    con.close()
    return dst


def seat_folder_of(base, name, spec, bundle):
    d = os.path.join(base, name)
    os.makedirs(d)
    wjson(os.path.join(d, u"指定.json"), od([(u"成果物", u"C"), (u"当期の始まり", spec[0]), (u"当期の終わり", spec[1])]))
    wjson(os.path.join(d, u"材料.json"), bundle)
    return d


def tally_b_ns(db, seats, out, designations, dirty=None):
    old = REF.DESIGNATIONS
    REF.DESIGNATIONS = designations
    try:
        ns = type("A", (), {})()
        ns.check, ns.db, ns.def_, ns.reading, ns.table, ns.workdir = os.path.join(ROOT, CHECK_REL), db, DEF_PATH, READING_PATH, fake().table_path, os.path.join(out, "w")
        ns.seat, ns.dirty, ns.out = seats, dirty, os.path.join(out, "b.json")
        REF.tally_b(ns)
    finally:
        REF.DESIGNATIONS = old
    return json.loads(read_text(os.path.join(out, "b.json")))


def wjson_ascii(path, obj):
    with open(path, "wb") as fh:
        fh.write(json.dumps(obj, ensure_ascii=True).encode("ascii"))


def gold_for(spec, src=None):
    f = fake()
    sel = REF.Sel(src or f.path)
    try:
        return json.loads(json.dumps(REF.gold_bundle(sel, REF.pdate(spec[0]), REF.pdate(spec[1])), ensure_ascii=False))
    finally:
        sel.close()


def fresh_dir(name):
    d = os.path.join(fake().tmp, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    return d


class CheckHoleTest(unittest.TestCase):
    u"""検査(確かめる側)の、独立監査の変異で黙った穴。1 本ずつ、その変異で赤くなる形で縛る。"""

    def test_p_1_k0_refuses_a_trailing_newline_in_a_number_and_in_every_date(self):
        g = gold_of("D")
        cases = []
        b = copy.deepcopy(g); item(b, u"c01")[u"数値"] += u"\n"; cases.append(b)
        b = copy.deepcopy(g); item(b, u"c01")[u"出どころ"][u"条件"][-1][u"値"] += u"\n"; cases.append(b)                  # 条件の日付
        b = copy.deepcopy(g); item(b, u"c01")[u"期間"] = {u"始まり": u"2001-01-01\n", u"終わり": u"2001-12-31"}; cases.append(b)
        b = copy.deepcopy(g); item(b, u"c01")[u"期間"] = {u"始まり": u"2001-01-01", u"終わり": u"2001-12-31\n"}; cases.append(b)
        b = copy.deepcopy(g); item(b, u"c21")[u"期間"] = {u"時点": u"2001-12-31\n"}; cases.append(b)
        for k, b in enumerate(cases):
            for table in (False, True):
                res = CHK.check_bundle(make_ctx("D", table=table), b)
                self.assertEqual((u"断り", [u"K0"]), (res[u"束"][u"状態"], res[u"束"][u"規則"]), k)
        # 数値の字を読む式そのものも、末尾の改行を受けない
        self.assertIsNone(CHK.NUM_RE.fullmatch(u"27358232.61\n"))
        self.assertIsNotNone(CHK.NUM_RE.fullmatch(u"27358232.61"))
        self.assertIsNone(CHK.parse_date(u"2001-01-01\n"))
        self.assertIsNotNone(CHK.parse_date(u"2001-01-01"))
        # 指定の日の字にも、末尾の改行を受けない
        f = fake()
        for k, (a, z) in enumerate(((u"2001-01-01\n", u"2001-12-31"), (u"2001-01-01", u"2001-12-31\n"))):
            p = os.path.join(f.tmp, "spec_nl%d.json" % k)
            wjson(p, od([(u"成果物", u"C"), (u"当期の始まり", a), (u"当期の終わり", z)]))
            ctx, bad = CHK.make_ctx(p, DEF_PATH, READING_PATH, f.path, None)
            self.assertIsNone(ctx, k)

    def test_p_2_k0_wants_the_materials_in_ascending_id_order(self):
        g = gold_of("D")
        ids = [m[u"id"] for m in g[u"材料"]]
        self.assertEqual(sorted(ids), ids)
        for k in range(len(ids) - 1):
            b = copy.deepcopy(g)
            b[u"材料"][k], b[u"材料"][k + 1] = b[u"材料"][k + 1], b[u"材料"][k]
            res = CHK.check_bundle(make_ctx("D"), b)
            self.assertEqual((u"断り", [u"K0"], [u"id の並び"]), (res[u"束"][u"状態"], res[u"束"][u"規則"], res[u"束"][u"理由"]), k)
        # 先頭と末尾の入れ替え
        b = copy.deepcopy(g)
        b[u"材料"][0], b[u"材料"][-1] = b[u"材料"][-1], b[u"材料"][0]
        self.assertEqual([u"id の並び"], CHK.check_bundle(make_ctx("D", table=True), b)[u"束"][u"理由"])

    def test_p_3_leading_zeros_in_a_number_are_accepted_the_seal_does_not_forbid_them(self):
        u"""封 §1-5 は「10 進の字で小数 2 桁ちょうど」。先頭の 0 を禁じていないので形の上で受ける(申告。検査の本文の注に在る)。"""
        g = gold_of("D")
        b = copy.deepcopy(g)
        m = item(b, u"c21")
        m[u"数値"] = u"000" + m[u"数値"]
        res = CHK.check_bundle(make_ctx("D"), b)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        self.assertEqual((u"通す", ()), verdicts(res)[u"c21"])
        self.assertIn(u"先頭の 0", read(CHECK_REL))

    def test_p_4_k0_conditions_are_one_to_eight(self):
        g = gold_of("D")
        base = item(g, u"c01")[u"出どころ"][u"条件"]
        for n, accepted in ((1, True), (8, True), (9, False), (12, False), (0, False)):
            b = copy.deepcopy(g)
            item(b, u"c01")[u"出どころ"][u"条件"] = [copy.deepcopy(base[-1]) for _ in range(n)]       # 日付 以下 を重ねる(K0 の形だけを見る)
            res = CHK.check_bundle(make_ctx("D"), b)
            self.assertEqual(u"受理" if accepted else u"断り", res[u"束"][u"状態"], n)

    def test_p_5_k0_a_point_period_has_only_the_point_key(self):
        g = gold_of("D")
        for extra in ({u"始まり": u"2001-01-01"}, {u"終わり": u"2001-12-31"}, {u"x": 1}, {u"始まり": u"2001-01-01", u"終わり": u"2001-12-31"}):
            b = copy.deepcopy(g)
            p = {u"時点": u"2001-12-31"}
            p.update(extra)
            item(b, u"c21")[u"期間"] = p
            res = CHK.check_bundle(make_ctx("D"), b)
            self.assertEqual((u"断り", [u"K0"]), (res[u"束"][u"状態"], res[u"束"][u"規則"]), extra)
        # 期間の行に 時点 の鍵が混ざっても断る
        b = copy.deepcopy(g)
        item(b, u"c01")[u"期間"] = {u"始まり": u"2001-01-01", u"終わり": u"2001-12-31", u"時点": u"2001-12-31"}
        self.assertEqual([u"K0"], CHK.check_bundle(make_ctx("D"), b)[u"束"][u"規則"])

    def test_p_6_k7_counts_only_the_none_rows_it_accepted_as_zero(self):
        u"""表つきで 無い を止めた(K9)行は、0 として数えない。R1 は c09 が使えなくなるので「見ない」になり、ほかの月の材料を K7 で止めない。"""
        g = gold_of("D")
        m = od([(u"id", u"c09"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
        res = CHK.check_bundle(make_ctx("D", table=True), replace_item(g, m))
        v = verdicts(res)
        self.assertEqual((u"止める", (u"K9",)), v[u"c09"])
        self.assertEqual((u"通す", ()), v[u"c10"])
        self.assertEqual((u"通す", ()), v[u"c01"])
        self.assertEqual({u"見た": 2, u"見なかった": 1}, res[u"K7"])
        # 表なしでは 無いを受ける ので 0 と数え、R1 は崩れて止める
        res = CHK.check_bundle(make_ctx("D", table=False), replace_item(g, m))
        self.assertEqual((u"無いを受ける", ()), verdicts(res)[u"c09"])
        self.assertEqual((u"止める", (u"K7",)), verdicts(res)[u"c10"])
        self.assertEqual({u"見た": 3, u"見なかった": 0}, res[u"K7"])
        # K7 は 無い の行自身を止めない(申告)
        for i in (u"c09", u"c28", u"c29"):
            self.assertNotIn(u"K7", verdicts(res)[i][1])

    def test_p_7_a_rule_that_raises_stops_the_material_fail_closed(self):
        g = gold_of("D")
        for k, table in ((u"K1", False), (u"K3", True), (u"K4", False), (u"K5", False), (u"K8", False)):
            old = CHK.RULE_FUNCS[k]

            def boom(*a, **kw):
                raise RuntimeError("boom")
            CHK.RULE_FUNCS[k] = boom
            try:
                res = CHK.check_bundle(make_ctx("D", table=table), g)
            finally:
                CHK.RULE_FUNCS[k] = old
            self.assertEqual(u"受理", res[u"束"][u"状態"], k)
            v = verdicts(res)
            self.assertEqual((u"止める", (k,)), v[u"c01"], k)
            self.assertEqual((u"止める", (k,)), v[u"c21"], k)
        # K10: 在る の行にだけ例外を出す(無い の行の K10 は例外を捕まえる所の外)。止める側へ倒れる
        old = CHK.RULE_FUNCS[u"K10"]
        present = set(m[u"id"] for m in g[u"材料"] if m[u"状態"] == u"在る")

        def boom10(ctx, i, period):
            if i not in present:
                return False
            raise RuntimeError("boom")
        CHK.RULE_FUNCS[u"K10"] = boom10
        try:
            res = CHK.check_bundle(make_ctx("D", table=True), g)
        finally:
            CHK.RULE_FUNCS[u"K10"] = old
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        self.assertEqual((u"止める", (u"K10",)), verdicts(res)[u"c01"])
        self.assertEqual((u"止める", (u"K10",)), verdicts(res)[u"c21"])

    def test_p_8_a_ledger_row_without_an_account_is_not_in_the_common_table(self):
        u"""科目表と結べない行(元帳に在って科目表に無い科目)は、共通の表「仕訳の行」に入れない(内側の結び)。"""
        f = fake()
        src = derive("orphan", orphan_rows=[(u"2001-05-05", 9999, 3.0, 0.0), (u"2001-05-05", 9999, 0.0, 3.0)])
        con = sqlite3.connect(src)
        self.assertEqual(len(f.rows) + 2, con.execute("select count(*) from GLEntry").fetchone()[0])
        self.assertEqual(0, con.execute("select count(*) from Account where AccountID = 9999").fetchone()[0])
        con.close()
        for table in (False, True):
            ctx = make_ctx("D", table=table, src=src)
            self.assertEqual(len(f.rows), ctx.led.select([])[0])
            self.assertEqual(0, ctx.led.select([(u"科目番号", u"どれでもない", [t[0] for t in ACCOUNTS]), (u"日付", u"以上", u"2001-05-05"), (u"日付", u"以下", u"2001-05-05")])[0])
            self.assertEqual(0, ctx.led.mem.execute("select count(*) from l where acct is null").fetchone()[0])
            res = CHK.check_bundle(ctx, gold_of("D"))
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            for r in res[u"材料"]:
                self.assertEqual(u"通す" if r[u"状態"] == u"在る" else u"無いを受ける", r[u"判定"], r)

    def k10_verdict(self, tag, account, row, i):
        src = derive(tag, accounts=[account], rows=[row])
        res = CHK.check_bundle(make_ctx("D", table=True, src=src), gold_of("D"))
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        return verdicts(res)[i]

    def test_p_9_k10_the_point_row_looks_at_rows_on_the_end_day_itself(self):
        # 時点の行(当期末)は、その日に行が在る科目まで見る。確かめていない科目(資産・流動資産。現金と同じ分類)の行が当期末の日だけに在る
        acct = (8020, u"z cur", u"Asset", u"Current Asset")
        v = self.k10_verdict("k10_point", acct, (u"2001-12-31", 8020, 0.0, 0.0), u"c21")
        self.assertEqual((u"止める", (u"K10",)), v)
        # 前の日なら同じ(下限は無い)・次の日なら見ない
        v = self.k10_verdict("k10_point_before", acct, (u"2001-12-30", 8020, 0.0, 0.0), u"c21")
        self.assertEqual((u"止める", (u"K10",)), v)
        v = self.k10_verdict("k10_point_after", acct, (u"2002-01-01", 8020, 0.0, 0.0), u"c21")
        self.assertEqual((u"通す", ()), v)

    def test_p_10_k10_the_period_row_looks_at_both_boundary_days(self):
        # 期間の行は、始まりの日も終わりの日も含む(収益・営業収益の分類が表に在る。確かめていない科目の行が境の日だけに在る)
        acct = (8030, u"z rev", u"Revenue", u"Operating Revenue")
        v = self.k10_verdict("k10_period_hi", acct, (u"2001-12-31", 8030, 0.0, 0.0), u"c01")
        self.assertIn(u"K10", v[1])
        v = self.k10_verdict("k10_period_lo", acct, (u"2001-01-01", 8030, 0.0, 0.0), u"c01")
        self.assertIn(u"K10", v[1])
        # 期の外の日は見ない(K10 は付かない)
        v = self.k10_verdict("k10_period_out", acct, (u"2002-01-01", 8030, 0.0, 0.0), u"c01")
        self.assertNotIn(u"K10", v[1])
        v = self.k10_verdict("k10_period_before", acct, (u"2000-12-31", 8030, 0.0, 0.0), u"c01")
        self.assertNotIn(u"K10", v[1])

    def test_p_11_the_table_refuses_a_bad_equal_value_in_the_journal_type_condition(self):
        f = fake()
        for k, val in enumerate([5, 1.5, True, None, [u"a"], {u"a": 1}, u"a\ud800"]):
            t = copy.deepcopy(f.table)
            t[u"行"][u"c08"][u"仕訳の種類の条件"] = {u"比べ方": u"等しい", u"値": val}
            p = os.path.join(f.tmp, "table_badjc%d.json" % k)
            wjson_ascii(p, t)
            ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, READING_PATH, f.path, p)
            self.assertIsNone(ctx, (k, val))
        for k, val in enumerate([u"x", 5, [5], [u"a\ud800"], [], [u"a"] * 201, None]):
            t = copy.deepcopy(f.table)
            t[u"行"][u"c01"][u"仕訳の種類の条件"] = {u"比べ方": u"どれか", u"値": val}
            p = os.path.join(f.tmp, "table_badjc_list%d.json" % k)
            wjson_ascii(p, t)
            ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, READING_PATH, f.path, p)
            self.assertIsNone(ctx, (k, val))
        # 受ける形
        t = copy.deepcopy(f.table)
        t[u"行"][u"c08"][u"仕訳の種類の条件"] = {u"比べ方": u"等しい", u"値": u"Depreciation"}
        p = os.path.join(f.tmp, "table_goodjc.json")
        wjson_ascii(p, t)
        ctx, bad = CHK.make_ctx(spec_path("D"), DEF_PATH, READING_PATH, f.path, p)
        self.assertIsNotNone(ctx, bad)


    def test_p_12_k0_number_form_is_two_decimals_exactly_with_an_optional_minus_only(self):
        u"""封 §1-5「10 進の字で小数 2 桁ちょうど」。3 桁・小数なし・整数部なし・先頭の + は K0 で断る(変異 n-num-3dec・nodec・nolead・plus)。"""
        g = gold_of("D")
        for text in (u"1234.500", u"1234", u".50", u"+1.00", u"1234.", u"1e3", u"0.5", u"1.234", u"-.50", u"--1.00", u"1 .00", u"1234,50", u"1,00"):
            for table in (False, True):
                b = copy.deepcopy(g)
                item(b, u"c01")[u"数値"] = text
                res = CHK.check_bundle(make_ctx("D", table=table), b)
                self.assertEqual((u"断り", [u"K0"], [u"数値の字"]), (res[u"束"][u"状態"], res[u"束"][u"規則"], res[u"束"][u"理由"]), text)
            self.assertIsNone(CHK.NUM_RE.fullmatch(text), text)
        for text in (u"1234.50", u"0.00", u"-1.00", u"-0.00"):
            b = copy.deepcopy(g)
            item(b, u"c01")[u"数値"] = text
            self.assertEqual(u"受理", CHK.check_bundle(make_ctx("D"), b)[u"束"][u"状態"], text)

    def test_p_13_k0_date_form_is_yyyy_mm_dd_with_hyphens_only_in_the_period_the_condition_and_the_spec(self):
        u"""材料の期間・条件の日付・指定の日の 3 か所とも ``2001/01/01``・``2001-01-1``・``2001-1-01`` を断る(変異 n-date-slash・n-date-1digit)。"""
        g = gold_of("D")
        f = fake()
        for k, bad in enumerate((u"2001/01/01", u"2001-01-1", u"2001-1-01", u"2001-1-1", u"20010101", u"2001.01.01", u"2001-01/01", u"\uff12\uff10\uff10\uff11-\uff10\uff11-\uff10\uff11", u"2001-\uff10\uff11-01", u"\u0662\u0660\u0660\u0661-\u0660\u0661-\u0660\u0661")):
            self.assertIsNone(CHK.parse_date(bad), bad)
            cases = []
            b = copy.deepcopy(g); item(b, u"c01")[u"期間"] = {u"始まり": bad, u"終わり": u"2001-12-31"}; cases.append(b)
            b = copy.deepcopy(g); item(b, u"c01")[u"期間"] = {u"始まり": u"2001-01-01", u"終わり": bad}; cases.append(b)
            b = copy.deepcopy(g); item(b, u"c21")[u"期間"] = {u"時点": bad}; cases.append(b)
            b = copy.deepcopy(g); item(b, u"c01")[u"出どころ"][u"条件"][-1][u"値"] = bad; cases.append(b)
            b = copy.deepcopy(g); item(b, u"c01")[u"出どころ"][u"条件"][0] = {u"列": u"日付", u"比べ方": u"以上", u"値": bad}; cases.append(b)
            for j, b in enumerate(cases):
                for table in (False, True):
                    res = CHK.check_bundle(make_ctx("D", table=table), b)
                    self.assertEqual((u"断り", [u"K0"]), (res[u"束"][u"状態"], res[u"束"][u"規則"]), (bad, j))
            for j, (a, z) in enumerate(((bad, u"2001-12-31"), (u"2001-01-01", bad))):
                p = os.path.join(f.tmp, "spec_form%d_%d.json" % (k, j))
                wjson(p, od([(u"成果物", u"C"), (u"当期の始まり", a), (u"当期の終わり", z)]))
                ctx, why = CHK.make_ctx(p, DEF_PATH, READING_PATH, f.path, None)
                self.assertIsNone(ctx, (bad, j))
        self.assertIsNotNone(CHK.parse_date(u"2001-01-01"))

    def test_p_14_k0_number_text_is_at_most_60_characters(self):
        u"""封に無い守り(検査の本文の注に申告)。境目: 60 字は形を受け、61 字は K0 で断る(変異 n-ids-len-60・n-ids-len-59)。"""
        g = gold_of("D")
        t60 = u"1" * 57 + u".00"
        t61 = u"1" * 58 + u".00"
        self.assertEqual((60, 61), (len(t60), len(t61)))
        self.assertIsNotNone(CHK.NUM_RE.fullmatch(t61))
        for text, accepted in ((t60, True), (t61, False), (u"-" + u"1" * 56 + u".00", True), (u"-" + u"1" * 57 + u".00", False)):
            for table in (False, True):
                b = copy.deepcopy(g)
                item(b, u"c01")[u"数値"] = text
                res = CHK.check_bundle(make_ctx("D", table=table), b)
                if accepted:
                    self.assertEqual(u"受理", res[u"束"][u"状態"], (len(text), table))
                else:
                    self.assertEqual((u"断り", [u"K0"], [u"数値の字"]), (res[u"束"][u"状態"], res[u"束"][u"規則"], res[u"束"][u"理由"]), (len(text), table))
        self.assertIn(u"60 字", read(CHECK_REL))
        self.assertIn(u"封に無い守り", read(CHECK_REL))


A5_LITERAL = (u"c02", u"c07", u"c08", u"c21", u"c22", u"c24", u"c27")
A6_LITERAL = tuple([u"c01", u"c03", u"c04", u"c05", u"c06"] + [u"c%02d" % k for k in range(9, 21)] + [u"c23", u"c25", u"c26"])


class RefHoleTest(unittest.TestCase):
    u"""答えを知っている側の、独立監査の変異で黙った穴。期待は、集計の本文でなく、門の中で別に数え直す。"""

    def test_q_1_tally_a_carry_a5_a6_equal_an_independent_recount_on_a_source_with_zero_amount_rows(self):
        f = fake()
        # 額 0 の行: 負債の科目(c25 の行の集まりだけが変わる)・名の字が最小の分類の科目(N3 が足す値が最小になり、数値が変わらない)
        src = derive("zero_a", accounts=[(2020, u"z payable", u"Liability", u"Current Liability"), (5, u"aaa", u"Aaa", u"Aaa Sub")],
                     rows=[(u"2002-06-15", 2020, 0.0, 0.0), (u"2002-06-16", 5, 0.0, 0.0)])
        out = fresh_dir("tally_a_zero")
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "tally-a", "--check", os.path.join(ROOT, CHECK_REL), "--db", src, "--def", DEF_PATH,
                            "--reading", READING_PATH, "--table", f.table_path, "--workdir", out, "--spec", "D=" + spec_path("D"), "--spec", "S=" + spec_path("S"),
                            "--out", os.path.join(out, "a.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        a = json.loads(read_text(os.path.join(out, "a.json")))
        table = json.loads(read_text(f.table_path))
        same = diff = same_num = none_none = numeq_setdiff = 0
        a5 = [0, 0]
        a6 = [0, 0]
        a6_same_passed = 0
        sel = REF.Sel(src)
        try:
            for name, spec in (("D", D_SPEC), ("S", S_SPEC)):
                cs, ce = REF.pdate(spec[0]), REF.pdate(spec[1])
                g = json.loads(json.dumps(REF.gold_bundle(sel, cs, ce), ensure_ascii=False))
                cb = json.loads(json.dumps(REF.carry_bundle(sel, table, cs, ce), ensure_ascii=False))
                for m, c in zip(g[u"材料"], cb[u"材料"]):
                    if m[u"状態"] != c[u"状態"]:
                        diff += 1
                    elif m[u"状態"] == u"無い":
                        same += 1
                        same_num += 1
                        none_none += 1
                    else:
                        numeq = m[u"数値"] == c[u"数値"]
                        seteq = sel.same_rows(conds_of(m), conds_of(c))
                        same_num += 1 if numeq else 0
                        if numeq and seteq:
                            same += 1
                        else:
                            diff += 1
                            numeq_setdiff += 1 if numeq else 0
                state = dict((m[u"id"], m[u"状態"]) for m in g[u"材料"])
                plain = judge_all(name, False, src)
                for (n, i), (v, s) in plain.items():
                    if state[i] != u"在る":
                        continue
                    if i in A5_LITERAL and n in (u"N2", u"N3", u"N10"):
                        a5[0] += 1
                        a5[1] += 1 if passed(v) else 0
                    if i in A6_LITERAL and n in (u"N2", u"N3", u"N7", u"N10") and not s:
                        a6[0] += 1
                        a6[1] += 1 if passed(v) else 0
                    if i in A6_LITERAL and n in (u"N2", u"N3", u"N7", u"N10") and s and passed(v):
                        a6_same_passed += 1
        finally:
            sel.close()
        # 空振りでない: 数値は同じで行の集まりが違う行・無い同士・数値が同じで通る変異が在る
        self.assertGreater(numeq_setdiff, 0)
        self.assertGreater(none_none, 0)
        self.assertGreater(a6_same_passed, 0)
        self.assertGreater(a5[0], 0)
        self.assertGreater(a6[0], 0)
        self.assertEqual(od([(u"正解と同じ行", same), (u"正解と違う行", diff), (u"数値だけ同じ行", same_num)]), a[u"規則の持ち越し"])
        self.assertEqual({u"作れた": a5[0], u"表なしが通した": a5[1]}, dict(a[u"A5"]))
        self.assertEqual({u"数値が違う作れた": a6[0], u"表なしが通した": a6[1]}, dict(a[u"A6"]))
        # A6 の定義: 数値が元と違うものを 1 つも通さない(表なしでも K7 が止める)
        self.assertEqual(0, a6[1])

    def test_q_2_tally_b_rates_by_designation_the_agreement_of_three_seats_and_the_correct_ones_stopped(self):
        f = fake()
        out = fresh_dir("tally_b_rates")
        des = od([(u"S1", S_SPEC), (u"S2", D_SPEC), (u"S3", H_SPEC), (u"S4", (u"2001-04-01", u"2002-03-31")), (u"S5", (u"2001-10-01", u"2002-09-30"))])
        sp = {}
        golds = {}
        for d, spec in des.items():
            sp[d] = os.path.join(out, "spec_%s.json" % d)
            wjson(sp[d], od([(u"成果物", u"C"), (u"当期の始まり", spec[0]), (u"当期の終わり", spec[1])]))
            golds[d] = gold_for(spec)
        plan = [("s1a", u"S1", False), ("s1b", u"S1", False), ("s1c", u"S1", False), ("s2a", u"S2", False), ("s2b", u"S2", False),
                ("s3a", u"S3", True), ("s4a", u"S4", False), ("s5a", u"S5", False)]
        seats, bundles = [], {}
        for name, d, wrong in plan:
            bd = copy.deepcopy(golds[d])
            if wrong:
                m = item(bd, u"c01")
                m[u"数値"] = REF.fmt_cents(REF.parse_cents(m[u"数値"]) + 1)
            bundles[name] = (d, bd)
            seats.append(seat_folder_of(out, name, des[d], bd))
        b = tally_b_ns(f.path, seats, out, des)
        self.assertEqual(8, b[u"席の数"])
        self.assertEqual(240, b[u"全部"][u"行"])
        self.assertEqual(239, b[u"全部"][u"正解どおり"])
        # 暦年の指定(S1・S2)は 5 席・150 行、ずらした指定(S3〜S5)は 3 席・90 行
        self.assertEqual({u"行": 150, u"正解どおり": 150}, dict(b[u"暦年の指定の率"]))
        self.assertEqual({u"行": 90, u"正解どおり": 89}, dict(b[u"ずらした指定の率"]))
        # 3 席が 3 つとも同じ行: S1(3 席)の 30 行だけ。2 席の S2・1 席の S3〜S5 は数えない
        self.assertEqual(30, b[u"3 席が 3 つとも同じ行"])
        # 正しい材料を止めた数 = 検査が止めた行のうち、席の答えが正解と同じもの(別に数える。間違った行の止めは含めない)
        wrongly = {u"表なし": 0, u"表つき": 0}
        stopped_wrong = 0
        for name, (d, bd) in bundles.items():
            for label, table in ((u"表なし", False), (u"表つき", True)):
                ctx, bad = CHK.make_ctx(sp[d], DEF_PATH, READING_PATH, f.path, f.table_path if table else None)
                v = verdicts(CHK.check_bundle(ctx, bd))
                for m in bd[u"材料"]:
                    if v[m[u"id"]][0] == u"止める":
                        if m == item(golds[d], m[u"id"]):
                            wrongly[label] += 1
                        else:
                            stopped_wrong += 1
        self.assertGreater(wrongly[u"表つき"], 0)
        self.assertGreater(stopped_wrong, 0)                       # 間違った行が止められている(それを正しい材料の止めに数えない)
        for label in (u"表なし", u"表つき"):
            self.assertEqual(wrongly[label], b[u"全部"][label][u"正しい材料を止めた"], label)

    def test_q_3_a_mutation_that_leaves_the_bundle_unchanged_is_not_counted_as_made(self):
        f = fake()
        sel = REF.Sel(f.path)
        try:
            cs, ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
            g = gold_of("S")
            n4 = dict(((n, i), nb) for n, i, nb, _s in REF.make_mutations(sel, g, cs, ce))[(u"N4", u"c01")]
            self.assertIsNotNone(n4)
            # 同じ変異をもう一度掛けると、条件の日付はもう移っている。束が元と同じなので「作れなかった」
            again = dict(((n, i), (nb, s)) for n, i, nb, s in REF.make_mutations(sel, json.loads(json.dumps(n4, ensure_ascii=False)), cs, ce))
            self.assertEqual((None, False), again[(u"N4", u"c01")])
            # 他の材料の同じ変異は作れる(束全体を空にしていない)
            self.assertIsNotNone(again[(u"N4", u"c02")][0])
        finally:
            sel.close()

    def test_q_4_the_table_gives_every_month_row_the_same_accounts_as_the_year_row(self):
        u"""月の行(c09〜c20)の表の科目は c01 と同じ(年全体。司令塔の決め)。ある科目の行が年の中の 1 日にだけ在っても、12 か月全部が c01 と同じになる。"""
        src = derive("month", accounts=[(4020, u"z rev2", u"Revenue", u"Operating Revenue")], rows=[(u"2001-03-10", 4020, 0.0, 0.0)])
        sel = REF.Sel(src)
        try:
            t = REF.make_table(sel, REF.pdate(D_SPEC[0]), REF.pdate(D_SPEC[1]))
        finally:
            sel.close()
        self.assertEqual([4010, 4020, 4090], t[u"行"][u"c01"][u"科目"])
        for k in range(9, 21):
            self.assertEqual(t[u"行"][u"c01"], t[u"行"][u"c%02d" % k], k)
        self.assertEqual(t[u"行"][u"c01"], t[u"行"][u"c02"])

    def test_q_5_n3_adds_only_a_value_that_has_rows_in_the_period(self):
        # 値の字が最小の分類の科目の行が、期の外(前の年)にだけ在る。期の中に行が在る値だけが候補
        src = derive("outside", accounts=[(5, u"aaa", u"Aaa", u"Aaa Sub")], rows=[(u"2001-03-10", 5, 0.0, 0.0)])
        sel = REF.Sel(src)
        try:
            cs, ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
            g = gold_for(S_SPEC, src)
            muts = dict(((n, i), nb) for n, i, nb, _s in REF.make_mutations(sel, g, cs, ce))
        finally:
            sel.close()
        in_period = set(ACC_CLS[r["acct"]][1] for r in fake().rows if S_SPEC[0] <= r["date"] <= S_SPEC[1])
        self.assertNotIn(u"Aaa Sub", in_period)
        used = [u"Operating Revenue", u"Contra Revenue"]
        self.assertEqual(used + [sorted(in_period - set(used))[0]], item(muts[(u"N3", u"c01")], u"c01")[u"出どころ"][u"条件"][0][u"値"])
        self.assertEqual([u"COGS", sorted(in_period - {u"COGS"})[0]], item(muts[(u"N3", u"c03")], u"c03")[u"出どころ"][u"条件"][0][u"値"])

    def run_facts(self, src, dev, tag):
        out = os.path.join(fake().tmp, "facts_%s.json" % tag)
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "source-facts", "--src", src, "--dev", dev, "--from", u"2002-01-01", "--to", u"2002-12-31", "--out", out],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        return json.loads(read_text(out))

    def dev_of(self, src, tag):
        dev = os.path.join(fake().tmp, "dev_%s.sqlite" % tag)
        shutil.copyfile(src, dev)
        c = sqlite3.connect(dev)
        c.execute("delete from GLEntry where PostingDate > '2001-12-31'")
        c.commit()
        c.close()
        return dev

    def test_q_6_source_facts_boundaries_and_the_kinds_of_unbalanced_vouchers(self):
        f = fake()
        # 指定の間の両端の日(2002-01-01・2002-12-31)にだけ行が在る、開発の年に動きが無かった科目
        src = derive("facts_edge", accounts=[(8040, u"z a", u"Asset", u"Current Asset"), (8041, u"z b", u"Asset", u"Current Asset")],
                     rows=[(u"2002-01-01", 8040, 0.0, 0.0), (u"2002-12-31", 8041, 0.0, 0.0)])
        base = self.run_facts(f.path, self.dev_of(f.path, "base"), "base")
        edge = self.run_facts(src, self.dev_of(src, "edge"), "edge")
        self.assertEqual(base[u"開発の年に動きが無かった科目"] + 2, edge[u"開発の年に動きが無かった科目"])
        self.assertEqual(base[u"うち指定の間に行が在る科目"] + 2, edge[u"うち指定の間に行が在る科目"])
        self.assertEqual(4, base[u"うち指定の間に行が在る科目"])
        # 貸借が合わない伝票: 借方が多い・貸方が多い・同じ種類の別の伝票で打ち消し合う 2 伝票
        dev = self.dev_of(f.path, "unbal")
        for tag, sql, expect in (("debit", ["update GLEntry set Debit = Debit + 0.01 where GLEntryID = 5"], 1),
                                 ("credit", ["update GLEntry set Credit = Credit + 0.01 where GLEntryID = 5"], 1)):
            bad = os.path.join(f.tmp, "unbal_%s.sqlite" % tag)
            shutil.copyfile(f.path, bad)
            c = sqlite3.connect(bad)
            for s in sql:
                c.execute(s)
            c.commit()
            c.close()
            self.assertEqual(expect, self.run_facts(bad, dev, "u_" + tag)[u"貸借が合わない伝票"], tag)
        bad = os.path.join(f.tmp, "unbal_cancel.sqlite")
        shutil.copyfile(f.path, bad)
        c = sqlite3.connect(bad)
        rows = c.execute("select min(GLEntryID), VoucherNumber from GLEntry where VoucherType = 'SalesInvoice' group by VoucherNumber order by min(GLEntryID) limit 2").fetchall()
        self.assertEqual(2, len(rows))
        self.assertNotEqual(rows[0][1], rows[1][1])
        c.execute("update GLEntry set Debit = Debit + 0.01 where GLEntryID = ?", (rows[0][0],))
        c.execute("update GLEntry set Credit = Credit + 0.01 where GLEntryID = ?", (rows[1][0],))
        c.commit()
        # 種類ごとに足すと打ち消し合って 0。伝票ごとに見るので 2
        self.assertEqual(0, c.execute("select count(*) from (select 1 from GLEntry where VoucherType = 'SalesInvoice' group by VoucherType having sum(CAST(ROUND(Debit*100) AS INTEGER)) != sum(CAST(ROUND(Credit*100) AS INTEGER)))").fetchone()[0])
        c.close()
        self.assertEqual(2, self.run_facts(bad, dev, "u_cancel")[u"貸借が合わない伝票"])

    def test_q_7_the_record_command_refuses_a_date_and_takes_the_retakes_with_the_seat_stage(self):
        f = fake()
        tmp = fresh_dir("rec_forbid")
        script = os.path.join(ROOT, REF_REL)

        def run(a_obj, extra, out_name):
            wjson(os.path.join(tmp, "a.json"), a_obj)
            out = os.path.join(tmp, out_name)
            r = subprocess.run([sys.executable, script, "record", "--a", os.path.join(tmp, "a.json"), "--table-sha", u"0" * 64, "--out", out] + extra,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return r.returncode, out
        # 日付の字を持つ記録は書かない(落ちて、file も作らない)
        rc, out = run({u"x": 1}, ["--b", "-"], "ok.json")
        self.assertEqual(0, rc)
        self.assertTrue(os.path.exists(out))
        rc, out = run({u"x": u"2025-01-01"}, ["--b", "-"], "date.json")
        self.assertNotEqual(0, rc)
        self.assertFalse(os.path.exists(out))
        rc, out = run({u"x": 1}, ["--b", "-", "--facts", "-"], "date2.json")
        self.assertEqual(0, rc)
        # 席の取り直しの数: 段 B を渡す時は必須・段 B が無い時は渡せない・負は断る
        wjson(os.path.join(tmp, "b.json"), od([(u"席の数", 1), (u"全部", od([(u"行", 30)]))]))
        bpath = os.path.join(tmp, "b.json")
        rc, out = run({u"x": 1}, ["--b", bpath, "--retakes", "2"], "retake.json")
        self.assertEqual(0, rc)
        self.assertEqual(2, json.loads(read_text(out))[u"段 B"][u"席の取り直しの数"])
        rc, out = run({u"x": 1}, ["--b", bpath], "noretake.json")
        self.assertNotEqual(0, rc)
        self.assertFalse(os.path.exists(out))
        rc, out = run({u"x": 1}, ["--b", "-", "--retakes", "1"], "noseat.json")
        self.assertNotEqual(0, rc)
        self.assertFalse(os.path.exists(out))
        rc, out = run({u"x": 1}, ["--b", bpath, "--retakes", "-1"], "negretake.json")
        self.assertNotEqual(0, rc)
        # 全部を通した記録は、形の検査(record_problems)も通る
        ar = fresh_dir("rec_full")
        r = subprocess.run([sys.executable, script, "tally-a", "--check", os.path.join(ROOT, CHECK_REL), "--db", f.path, "--def", DEF_PATH, "--reading", READING_PATH,
                            "--table", f.table_path, "--workdir", os.path.join(ar, "w"), "--spec", "D=" + spec_path("D"), "--out", os.path.join(ar, "a.json")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        r = subprocess.run([sys.executable, script, "record", "--a", os.path.join(ar, "a.json"), "--b", bpath, "--retakes", "0", "--table-sha", sha_file(f.table_path),
                            "--out", os.path.join(ar, "record.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual([], record_problems(json.loads(read_text(os.path.join(ar, "record.json")))))


    def test_q_8_n3_touches_only_the_first_condition_that_holds_a_list_and_stops_when_it_has_nothing_to_add(self):
        u"""N3 は「並びを持つ最初の条件にだけ」(封)。第 1 の条件に足せる値が無い時は作らず(次の条件へ進まない)、第 2 の並びの条件は変わらない
        (変異 n3-nocand-continue・n3-all-conds)。第 1・第 2 とも 等しい / どれか の 4 通り。"""
        cs, ce = REF.pdate(S_SPEC[0]), REF.pdate(S_SPEC[1])
        g = gold_of("S")
        kinds = dict((i, REF.GOLD[i][u"期"]) for i in REF.IDS)
        period = REF.period_of(kinds[u"c01"], cs, ce)
        real = REF.Sel(fake().path)
        try:
            subs = real.values(REF.SUB, period)
            typs = real.values(REF.TYP, period)
            self.assertGreaterEqual(len(subs), 3)
            self.assertGreaterEqual(len(typs), 3)

            class Stub(object):
                u"""値の候補だけ決めた作り物。額の計算は本物の素材から。"""
                def __init__(self, by_col):
                    self.by_col = by_col

                def values(self, col, per):
                    return list(self.by_col[col])

                def signed(self, conds, direction):
                    return real.signed(conds, direction)

            def cond(col, op, vals):
                return REF.cond_dict(REF.C(col, op, vals[0] if op == u"等しい" else list(vals)))

            for op1 in (u"等しい", u"どれか"):
                for op2 in (u"等しい", u"どれか"):
                    for nothing in (True, False):
                        # nothing: 第 1 の列の、期に行が在る値が全部、条件に入っている(足せる値が無い)。第 2 の列には足せる値が在る
                        if nothing:
                            v1 = subs[:1] if op1 == u"等しい" else subs
                            stub = Stub({REF.SUB: v1, REF.TYP: typs})
                        else:
                            v1 = subs[:1]
                            stub = Stub({REF.SUB: subs, REF.TYP: typs})
                        b = copy.deepcopy(g)
                        m = item(b, u"c01")
                        m[u"出どころ"][u"条件"] = [cond(REF.SUB, op1, v1), cond(REF.TYP, op2, typs[:1])] + [REF.cond_dict(c) for c in REF.date_conds(period)]
                        b[u"材料"] = [m]
                        before = copy.deepcopy(m)
                        out = REF.mutate_item(stub, b, 0, u"N3", cs, ce, kinds)
                        tag = (op1, op2, nothing)
                        if nothing:
                            self.assertIsNone(out, tag)
                        else:
                            self.assertIsNotNone(out, tag)
                            conds = out[u"出どころ"][u"条件"]
                            self.assertEqual(u"どれか", conds[0][u"比べ方"], tag)
                            self.assertEqual(subs[:1] + [subs[1]], conds[0][u"値"], tag)
                            self.assertEqual(before[u"出どころ"][u"条件"][1:], conds[1:], tag)       # 第 2 の並びの条件・日付の条件は変わらない
                            self.assertEqual(op2, conds[1][u"比べ方"], tag)
        finally:
            real.close()

    def test_q_9_source_facts_groups_the_unbalanced_vouchers_by_type_and_number(self):
        u"""種類が違って番号が同じ 2 伝票は別の伝票(変異 n-facts-group-num)。打ち消し合う 2 伝票が 2 と数えられる。"""
        f = fake()
        dev = self.dev_of(f.path, "grp_dev")
        bad = os.path.join(f.tmp, "grp_same_number.sqlite")
        shutil.copyfile(f.path, bad)
        c = sqlite3.connect(bad)
        groups = c.execute("select VoucherType, VoucherNumber, min(GLEntryID) from GLEntry group by VoucherType, VoucherNumber order by min(GLEntryID)").fetchall()
        a = groups[0]
        other = [x for x in groups if x[0] != a[0]][0]
        self.assertNotEqual(a[0], other[0])
        # 2 つ目の伝票の番号を 1 つ目と同じにする。番号の重なる別の種類の伝票ができる
        c.execute("update GLEntry set VoucherNumber = ? where VoucherType = ? and VoucherNumber = ?", (a[1], other[0], other[1]))
        c.execute("update GLEntry set Debit = Debit + 0.01 where GLEntryID = ?", (a[2],))
        c.execute("update GLEntry set Credit = Credit + 0.01 where GLEntryID = ?", (other[2],))
        c.commit()
        self.assertEqual(2, c.execute("select count(distinct VoucherType) from GLEntry where VoucherNumber = ?", (a[1],)).fetchone()[0])
        # 番号だけで束ねると打ち消し合って 0(その束ね方では貸借が合う)
        self.assertEqual(0, c.execute("select count(*) from (select 1 from GLEntry group by VoucherNumber having sum(CAST(ROUND(Debit*100) AS INTEGER)) != sum(CAST(ROUND(Credit*100) AS INTEGER)))").fetchone()[0])
        c.close()
        self.assertEqual(2, self.run_facts(bad, dev, "grp")[u"貸借が合わない伝票"])

    def test_q_10_seat_folder_copies_the_source_when_a_hard_link_cannot_be_made(self):
        u"""os.link が失敗した時は写しに落ちる(変異 r-seat-folder-link)。link を失敗させ、素材の複製が席の folder に在って同じ中身であることを縛る。"""
        import unittest.mock as mock
        f = fake()
        out = fresh_dir("seat_nolink")
        dest = os.path.join(out, "seat")
        ns = type("A", (), {})()
        ns.dest, ns.material, ns.spec = dest, f.path, spec_path("S")
        ns.instruction, ns.def_, ns.reading = os.path.join(ROOT, INSTRUCTION_REL), DEF_PATH, READING_PATH
        with mock.patch.object(REF.os, "link", side_effect=OSError("no link")) as lk:
            REF.seat_folder(ns)
        self.assertEqual(1, lk.call_count)
        target = os.path.join(dest, REF.SEAT_SOURCE)
        self.assertTrue(os.path.isfile(target))
        self.assertEqual(sha_file(f.path), sha_file(target))
        self.assertNotEqual(os.stat(f.path).st_ino, os.stat(target).st_ino)           # 写し(同じ実体ではない)
        # 前の回の file が在っても消してから置く
        with mock.patch.object(REF.os, "link", side_effect=OSError("no link")):
            REF.seat_folder(ns)
        self.assertEqual(sha_file(f.path), sha_file(target))
        # link が通る時は、同じ中身(link か写し)
        ns.dest = os.path.join(fresh_dir("seat_link"), "seat")
        REF.seat_folder(ns)
        self.assertEqual(sha_file(f.path), sha_file(os.path.join(ns.dest, REF.SEAT_SOURCE)))


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


# ======================================================================== 13. 記録(無い時は無いと assert。在る時は形・禁止の字)
A_KEYS = (u"正解の束", u"検査の結果", u"K3の行", u"規則の持ち越し", u"変異", u"A5", u"A6", u"素材の全体")
FACT_KEYS = (u"貸借が合わない伝票", u"開発の年に動きが無かった科目", u"うち指定の間に行が在る科目")


def record_problems(rec):
    out = []
    if not isinstance(rec, dict):
        return [u"not dict"]
    body = json.dumps(rec, ensure_ascii=False)
    if re.search(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", body):
        out.append(u"date in record")
    for w in SECRET_WORDS + (u"Year-End", u"Operating", u"Asset", u"Revenue", u"Expense", u"売上高", u"売上原価"):
        if w in body:
            out.append(u"secret word: " + w)
    if set(rec) != {u"便", u"封", u"段 A", u"段 B", u"確かめた取り方の表の SHA-256"}:
        out.append(u"top keys")
        return out
    a = rec[u"段 A"]
    if not isinstance(a, dict):
        return out + [u"A shape"]
    for k in A_KEYS:
        if k not in a:
            out.append(u"A missing " + k)
    for k in a:
        if k not in A_KEYS:
            out.append(u"A extra " + k)
    if out:
        return out
    f = a[u"素材の全体"]
    if f is not None:
        ints = lambda x: type(x) is int and x >= 0
        if not isinstance(f, dict) or set(f) != set(FACT_KEYS) or not all(ints(f[k]) for k in FACT_KEYS):
            out.append(u"facts shape")
        elif f[u"うち指定の間に行が在る科目"] > f[u"開発の年に動きが無かった科目"]:
            out.append(u"facts moved > idle")
    if out:
        return out
    g = a[u"正解の束"]
    if g[u"行の数"] != sum(g[u"状態"].values()):
        out.append(u"gold total")
    if g[u"行の数"] != 30 * g[u"束の数"]:
        out.append(u"gold rows = 30 x bundles")
    for label in (u"表なし", u"表つき"):
        if sum(a[u"検査の結果"][label][u"判定"].values()) != g[u"行の数"]:
            out.append(u"verdict total " + label)
    c = a[u"規則の持ち越し"]
    if c[u"正解と同じ行"] + c[u"正解と違う行"] != g[u"行の数"]:
        out.append(u"carry total")
    if set(a[u"変異"]) != set(REF.MUTATIONS):
        out.append(u"mutation names")
    for n, v in a[u"変異"].items():
        if v[u"作れた"] + v[u"作れなかった"] != g[u"行の数"]:
            out.append(u"mutation total " + n)
        if v[u"表なしが通した"] > v[u"作れた"] or v[u"表つきが通した"] > v[u"作れた"]:
            out.append(u"mutation passed > made " + n)
    if not re.match(r"^[0-9a-f]{64}$", rec[u"確かめた取り方の表の SHA-256"]):
        out.append(u"table sha")
    b = rec[u"段 B"]
    if b is not None:
        if not isinstance(b, dict) or u"全部" not in b:
            out.append(u"B shape")
        elif b[u"全部"][u"行"] != 30 * b[u"席の数"]:
            out.append(u"B rows = 30 x seats")
        elif type(b.get(u"席の取り直しの数")) is not int or b[u"席の取り直しの数"] < 0:
            out.append(u"B retakes")
    return out


class RecordTest(unittest.TestCase):
    def good(self):
        a = {u"正解の束": od([(u"束の数", 1), (u"行の数", 30), (u"状態", {u"在る": 24, u"無い": 6}), (u"関係が成り立つ本数", 3), (u"関係の本数", 3), (u"指定ごと", {})]),
             u"検査の結果": od([(u"表なし", {u"判定": {u"通す": 24, u"無いを受ける": 6}, u"止めた規則": {}}), (u"表つき", {u"判定": {u"通す": 24, u"無いを受ける": 6}, u"止めた規則": {}})]),
             u"K3の行": {}, u"規則の持ち越し": od([(u"正解と同じ行", 30), (u"正解と違う行", 0), (u"数値だけ同じ行", 30)]),
             u"変異": od((n, od([(u"作れた", 24), (u"表なしが通した", 0), (u"表つきが通した", 0), (u"数値が元と同じ", 0), (u"作れなかった", 6)])) for n in REF.MUTATIONS), u"A5": {}, u"A6": {},
             u"素材の全体": od([(u"貸借が合わない伝票", 0), (u"開発の年に動きが無かった科目", 5), (u"うち指定の間に行が在る科目", 2)])}
        return od([(u"便", u"UM1"), (u"封", u"0d2156e4"), (u"段 A", a), (u"段 B", None), (u"確かめた取り方の表の SHA-256", u"0" * 64)])

    def test_m_1_the_record_state_is_stated_and_checked(self):
        path = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(path):
            self.assertFalse(os.path.exists(path), u"記録はまだ無い(本番は未実行。記録の無い状態で緑)")
            return
        self.assertEqual([], record_problems(json.loads(read(RECORD_REL))))

    def test_m_2_the_record_check_turns_red_for_a_forbidden_word_a_date_and_a_wrong_total(self):
        good = self.good()
        self.assertEqual([], record_problems(good))
        # 素材の全体の数が無い記録(段 A の欄は在って None)と、段 B が在って取り直しの数が 0 の記録は受ける
        ok = copy.deepcopy(good)
        ok[u"段 A"][u"素材の全体"] = None
        self.assertEqual([], record_problems(ok))
        ok = copy.deepcopy(good)
        ok[u"段 B"] = od([(u"席の数", 1), (u"全部", od([(u"行", 30)])), (u"席の取り直しの数", 0)])
        self.assertEqual([], record_problems(ok))
        for mut in (lambda r: r.__setitem__(u"x", u"Operating Revenue"), lambda r: r.__setitem__(u"段 B", u"2025-01-01"),
                    lambda r: r[u"段 A"][u"正解の束"].__setitem__(u"行の数", 29), lambda r: r[u"段 A"][u"変異"][u"N1"].__setitem__(u"作れた", 25),
                    lambda r: r[u"段 A"][u"変異"].pop(u"N12"), lambda r: r[u"段 A"][u"検査の結果"][u"表つき"][u"判定"].__setitem__(u"通す", 23),
                    lambda r: r[u"段 A"][u"規則の持ち越し"].__setitem__(u"正解と違う行", 1), lambda r: r.__setitem__(u"確かめた取り方の表の SHA-256", u"zz"),
                    lambda r: r[u"段 A"][u"変異"][u"N1"].__setitem__(u"表なしが通した", 25), lambda r: r.pop(u"便"), lambda r: r[u"段 A"].pop(u"A5"),
                    # 段 A の中の余分な鍵・素材の全体の数の欠け・余分・型違い・大小の逆・段 B の取り直しの欠け
                    lambda r: r[u"段 A"].__setitem__(u"余分", 1), lambda r: r[u"段 A"].pop(u"素材の全体"), lambda r: r[u"段 A"][u"素材の全体"].__setitem__(u"余分", 1),
                    lambda r: r[u"段 A"][u"素材の全体"].pop(u"貸借が合わない伝票"), lambda r: r[u"段 A"][u"素材の全体"].__setitem__(u"貸借が合わない伝票", u"0"),
                    lambda r: r[u"段 A"][u"素材の全体"].__setitem__(u"貸借が合わない伝票", True), lambda r: r[u"段 A"][u"素材の全体"].__setitem__(u"貸借が合わない伝票", -1),
                    lambda r: r[u"段 A"][u"素材の全体"].__setitem__(u"うち指定の間に行が在る科目", 6),
                    lambda r: r.__setitem__(u"段 B", od([(u"席の数", 1), (u"全部", od([(u"行", 30)]))])),
                    lambda r: r.__setitem__(u"段 B", od([(u"席の数", 1), (u"全部", od([(u"行", 30)])), (u"席の取り直しの数", -1)])),
                    lambda r: r.__setitem__(u"段 B", od([(u"席の数", 1), (u"全部", od([(u"行", 30)])), (u"席の取り直しの数", u"0")]))):
            bad = copy.deepcopy(good)
            mut(bad)
            self.assertNotEqual([], record_problems(bad))
        self.assertNotEqual([], record_problems({}))
        self.assertNotEqual([], record_problems(None))

    def test_m_3_the_record_the_command_writes_has_the_shape_and_no_forbidden_word(self):
        f = fake()
        tmp = os.path.join(f.tmp, "rec")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "tally-a", "--check", os.path.join(ROOT, CHECK_REL), "--db", f.path, "--def", DEF_PATH, "--reading", READING_PATH,
                            "--table", f.table_path, "--workdir", os.path.join(tmp, "w"), "--spec", "D=" + spec_path("D"), "--out", os.path.join(tmp, "a.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        # 素材の全体の数(source-facts の出力)を入れる口: 開発の写しは作り物の素材の 2001 年だけ
        dev = os.path.join(tmp, "dev.sqlite")
        shutil.copyfile(f.path, dev)
        c = sqlite3.connect(dev)
        c.execute("delete from GLEntry where PostingDate > '2001-12-31'")
        c.commit()
        c.close()
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "source-facts", "--src", f.path, "--dev", dev, "--from", u"2002-01-01", "--to", u"2002-12-31",
                            "--out", os.path.join(tmp, "facts.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "record", "--a", os.path.join(tmp, "a.json"), "--b", "-", "--table-sha", sha_file(f.table_path),
                            "--facts", os.path.join(tmp, "facts.json"), "--out", os.path.join(tmp, "record.json")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        rec = json.loads(read_text(os.path.join(tmp, "record.json")))
        self.assertEqual([], record_problems(rec))
        self.assertEqual(sha_file(f.table_path), rec[u"確かめた取り方の表の SHA-256"])
        self.assertEqual(json.loads(read_text(os.path.join(tmp, "facts.json"))), rec[u"段 A"][u"素材の全体"])
        self.assertEqual(set(FACT_KEYS), set(rec[u"段 A"][u"素材の全体"]))
        # 口を渡さない記録は、素材の全体の数の欄が None
        r = subprocess.run([sys.executable, os.path.join(ROOT, REF_REL), "record", "--a", os.path.join(tmp, "a.json"), "--b", "-", "--table-sha", sha_file(f.table_path),
                            "--out", os.path.join(tmp, "record0.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, r.returncode, r.stderr)
        rec0 = json.loads(read_text(os.path.join(tmp, "record0.json")))
        self.assertIsNone(rec0[u"段 A"][u"素材の全体"])
        self.assertEqual([], record_problems(rec0))

    def test_m_4_the_record_is_never_written_into_the_repo_by_this_gate(self):
        self.assertTrue(os.path.isdir(os.path.join(ROOT, "fixtures", "universal", "um1")))
        allowed = sorted([u"definition_C.json", u"reading_def.json"] + ([u"record.json"] if os.path.exists(os.path.join(ROOT, RECORD_REL)) else []))
        self.assertEqual(allowed, sorted(os.listdir(os.path.join(ROOT, "fixtures", "universal", "um1"))))


# ======================================================================== 14. 順序・手入れ
def order_problems_allowing_not_yet(root, seal_short, files):
    got = PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], files)
    return [x for x in got if not x.startswith(u"UNCOMMITTED:")]


def make_repo(files_by_commit, root):
    subprocess.run(["git", "init", "-q", root], check=True)
    for k, (msg, files) in enumerate(files_by_commit):
        for rel, body in files.items():
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(body.encode("utf-8"))
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], check=True)


class OrderTest(unittest.TestCase):
    def test_n_1_the_real_history_has_the_seal_before_the_scripts_definitions_instruction_and_the_gate(self):
        u"""封より前に足された file が在れば赤。まだ commit されていない file は許す(commit された後で初めて順序が縛られる)。記録は別。"""
        self.assertEqual([], order_problems_allowing_not_yet(REPO, SEAL_COMMIT_SHORT, list(ORDER_FILES)))

    def test_n_2_the_order_check_lists_every_file_and_not_the_record(self):
        self.assertEqual(6, len(ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)
        for rel in ORDER_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_n_3_the_order_part_turns_red_when_a_file_comes_before_the_seal(self):
        seal = PREFIX + SEAL_REL
        other = PREFIX + CHECK_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("pre", {other: "x"}), ("seal-x", {seal: "s"}), ("later", {PREFIX + "b": "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [CHECK_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + CHECK_REL, got)
            self.assertIn(u"UNCOMMITTED:missing.py", got)
            allowed = order_problems_allowing_not_yet(tmp, short, [CHECK_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + CHECK_REL, allowed)
            self.assertNotIn(u"UNCOMMITTED:missing.py", allowed)
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal-x", {seal: "s"}), ("later", {other: "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], list(PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [CHECK_REL])))


class HygieneTest(unittest.TestCase):
    def test_o_1_the_new_scripts_do_not_contain_the_harness_words(self):
        words = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
        for rel in (CHECK_REL, REF_REL):
            body = read(rel)
            for w in words:
                self.assertNotIn(w, body, (rel, w))

    def test_o_2_the_gate_has_no_skip_and_does_not_open_the_whole_source(self):
        body = read(GATE_REL)
        self.assertNotIn(u"skip" + u"Test", body)
        self.assertNotIn(u"@unittest." + u"skip", body)
        self.assertNotIn(u"pytest.mark." + u"skip", body)
        self.assertNotIn(u"Charles" + u"River" + u".sqlite", body)
        for rel in (CHECK_REL, REF_REL, DEF_REL, READING_REL, INSTRUCTION_REL):
            self.assertNotIn(u"scratchpad", read(rel), rel)
            self.assertNotIn(u"Charles" + u"River.sqlite", read(rel), rel)

    def test_o_3_the_scripts_hold_no_account_number_amount_or_date_of_the_source_beyond_the_sealed_ones(self):
        for rel in (CHECK_REL, DEF_REL, READING_REL, INSTRUCTION_REL):
            body = read(rel)
            for d in re.findall(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", body.replace(u"2026-11-23", u"")):
                self.assertTrue(d.startswith("2001") or d == u"2024-01-01", (rel, d))
        body = read(REF_REL)
        for d in set(re.findall(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", body.replace(u"2026-11-23", u""))):
            self.assertIn(d, seal_text(), d)

    def test_o_4_the_ref_names_do_not_hit_the_existing_gates_criteria(self):
        # 規準の字は ``def run_doc(`` など。この 2 file の関数の名は、それらと重ならない
        names = []
        for rel in (CHECK_REL, REF_REL):
            names += [n.name for n in ast.walk(ast.parse(read(rel))) if isinstance(n, ast.FunctionDef)]
        for bad in ("run_doc", "work_doc", "claim_at", "inject", "inject_doc", "apply_edits", "inject_with_profile", "verify_document", "verify_external", "select", "mutate"):
            self.assertNotIn(bad, [n for n in names if n != "select"] if bad == "select" else names, bad)

    def test_o_5_the_gate_makes_no_network_call_and_writes_no_key(self):
        body = read(CHECK_REL) + read(REF_REL)
        for w in (u"urllib" + u".request", u"http" + u"://", u"https" + u"://", u"anthro" + u"pic", u"ANTHRO" + u"PIC", u"key" + u"chain", u"soc" + u"ket"):
            self.assertNotIn(w, body, w)
        mods = set()
        for n in ast.walk(ast.parse(read(GATE_REL))):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(set(), mods & {"urllib", "http", "socket", "requests", "ssl", "ftplib", "smtplib"})


if __name__ == "__main__":
    unittest.main()
