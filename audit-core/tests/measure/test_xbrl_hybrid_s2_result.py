# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)段 2 の結果文書(docs/XBRL_HYBRID_S2_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json``(``measure/xbrl_hybrid_s2_2026-10-20.py --stage score`` の出力)。
封: ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md`` §2(段 2)。予測の幅は**封の字から読む**(この門に写さない)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 入力(材料・席の答え 8 本・便の記録 csv・段 1 の記録・draw・封)の sha256 を**字で留める**。
  2. 記録の行 192 本を、入力と突き合わせる(席の判定と参照先は答えの file から、注入の型と行は材料の明細から、
     Core 自身の state は材料の ``席の前に出せる分`` から)。
  3. 「席の見逃し 0 件」(T6・T7・T2 金額系)は**答えの file と材料の明細から直接**数え直す(0 を自分の欠陥と疑う)。
  4. 合成 H の規則・3 群を行から再適用し、記録の欄と一致させる。記録の集計を行から数え直す。
  5. 予測 P-1〜P-7 を、行・封の幅・csv・材料の記録から**門が自分で**判定し、記録・文書の判定と一致させる。
  6. 文書の表の行(§2〜§6)は行から作った字と完全一致。分数 ``a / b = x.x%`` は算術として合い、許可集合に入る。
  7. script を**もう一度走らせて**(0 USD・通信しない)記録の行・集計・予測を再現できる。
"""
import ast
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
REC = os.path.join(GEN, "hybrid_s2_2026-10-20.json")
MAT = os.path.join(GEN, "hybrid_s2_material_2026-10-20.json")
ANS = os.path.join(GEN, "hybrid_s2_answers")
RUNS = os.path.join(GEN, "hybrid_s2_runs_2026-10-20.csv")
S1 = os.path.join(GEN, "hybrid_trust_2026-10-20.json")
DRAW = os.path.join(GEN, "draw_2026-10-20.json")
DOC = os.path.join(ROOT, "docs", "XBRL_HYBRID_S2_RESULT_2026-10-20.md")
SEAL = os.path.join(ROOT, "docs", "XBRL_HYBRID_TRUST_SEAL_2026-10-20.md")
SCRIPT = os.path.join(ROOT, "measure", "xbrl_hybrid_s2_2026-10-20.py")

#: commit 済みの file の sha256。**字で留める**(定数から作らない)。
SHA_ANS = {
    "S100YYN7_answer.json": "fc73d1e23cce627a3e7b7954e2317e59300bf820fe192d7cb420b3c6987a205b",
    "S100YYT4_answer.json": "56a3d88ab362bd1f13ebeafea34a1bb9ec086aa918c2a4115630b8f19bdf146f",
    "S100YYT8_answer.json": "88b6de83bfc5b232b7874268b04a3e389c963dc64f1b2bd70c2005873c9056ab",
    "S100YYUD_answer.json": "e81dc8cf31c287872287d376ef113ba912516bdc45e9d3b1bd65fb8189e0c263",
    "S100Z0OS_answer.json": "0f801c7b3292d59a2a09b8470446d393cd4acf8fcac5b18a6d93fda1f171abbf",
    "S100Z42X_answer.json": "c5bf198c4f022714ea79ab6d7bfec424c3922b9778a91cb16b3b1601e99e2413",
    "S100Z4GF_answer.json": "ae565afa6907c3bd6b333f6a05bd6ec83a9b8b9fd194b56a337f064cc3adf09c",
    "S100Z4J8_answer.json": "369cf4f0d1e4bec4f5f56321146405d887aab6be4b94138b9276fe3c100b577c"}
SHA_MAT = "c3068024ff8c2812fabbf54e36f50b1cedeccb7955e9455603d1a17018418149"
SHA_RUNS = "0af87402548002d695272b7b6bd10b829e968a902a5d9e23373878db8eab8b54"
SHA_S1 = "1fb7cfdb114c6e82b73875c32270d0ad4f77ca0156204a0a63adfdf6628ff177"
SHA_DRAW = "025945ccb39bac8e63d801d871ec55e77442746344ce02af327c6219843a7a8c"
SHA_SEAL = "4ca1b7b7ad47a152e6efc30a9758001ebdbf1a3e44e1ee06bdf322a80bb69ba8"
ENGINE_BUNDLE = "5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee"

DOCS = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]
WORDS = (u"確認済み", u"誤りが在る", u"判定できない")
ORDER = (u"GROUNDED", u"VALUE_MISMATCH", u"UNPROVABLE", u"UNVERIFIABLE", u"POINTER_NOT_FOUND", u"対応なし", u"参照先なし")
NUM_RE = re.compile(r"(?<![A-Za-z\d§])\d[\d,]*(?:\.\d+)?")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")
TKEYS = (u"T6_PRIOR", u"T7_ROUND", u"T2_UNIT", u"T2_UNIT 金額系", u"T2_UNIT ％系", u"T2_UNIT 件→回")
FAMILY = {"money": u"金額系", "ratio": u"％系", "count_item": u"件→回"}


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def F(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def fr(a, b):
    return [str(a), str(b), "%.1f" % (100.0 * a / b)]


def nums(cell):
    return NUM_RE.findall(cell)


def brk(counter):
    return u"・".join(u"%s %d" % (k, counter[k]) for k in ORDER if counter.get(k))


def cnt(rows, f):
    c = {}
    for r in rows:
        c[r[f]] = c.get(r[f], 0) + 1
    return c


def seal_pred(seal, h):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % h):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")][1]
    raise AssertionError(h)


def pairs(s):
    return [(int(a.replace(",", "")), int(b.replace(",", ""))) for a, b in re.findall(r"(\d[\d,]*)〜(\d[\d,]*)", s)]


def cells(doc, h):
    for l in doc.splitlines():
        if l.startswith(u"| **%s** |" % h):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(h)


def h_of(seat, ok):
    if seat == u"誤りが在る":
        return u"誤り(席)"
    if seat == u"確認済み":
        return u"二重確認" if ok else u"警告"
    if seat == u"判定できない":
        return u"Core のみ確認" if ok else u"保留"
    raise AssertionError(seat)


def load_script():
    sp = importlib.util.spec_from_file_location("hybrid_s2_score_for_gate", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    with contextlib.redirect_stdout(io.StringIO()):
        sp.loader.exec_module(m)
    return m


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rows = cls.rec[u"行"]
        cls.doc = text(DOC)
        cls.seal = text(SEAL)
        cls.mat = jload(MAT)
        cls.agg = cls.rec[u"集計"]
        cls.preds = {p[u"記号"]: p for p in cls.rec[u"**予測 P-1〜P-7**"]}
        cls.inj = [r for r in cls.rows if r[u"注入か"]]
        cls.unc = [r for r in cls.rows if not r[u"注入か"]]
        cls.g1 = [r for r in cls.rows if r[u"席の判定"] == u"確認済み"]

    def groups(self, field):
        return {u"G1": self.g1, u"G2": [r for r in self.g1 if r[field] == u"GROUNDED"],
                u"G3": [r for r in self.g1 if r[field] != u"GROUNDED"]}

    @property
    def GA(self):
        return self.groups(u"α 型の state")

    @property
    def GS(self):
        return self.groups(u"Core 自身(既定)の state")

    def tm(self, key):
        f = {u"T6_PRIOR": lambda r: r[u"注入の型"] == u"T6_PRIOR", u"T7_ROUND": lambda r: r[u"注入の型"] == u"T7_ROUND",
             u"T2_UNIT": lambda r: r[u"注入の型"] == u"T2_UNIT",
             u"T2_UNIT 金額系": lambda r: r[u"T2 の系"] == u"金額系", u"T2_UNIT ％系": lambda r: r[u"T2 の系"] == u"％系",
             u"T2_UNIT 件→回": lambda r: r[u"T2 の系"] == u"件→回"}[key]
        return [r for r in self.inj if f(r)]

    def prec(self, m):
        return F(sum(1 for r in m if not r[u"注入か"]), len(m))

    def csv_runs(self):
        with io.open(RUNS, encoding="utf-8", newline="") as fh:
            rd = list(csv.reader(fh))
        return rd[0], rd[1:]


class InputsTest(Base):
    def test_1_inputs_pinned_literally(self):
        inp = self.rec[u"入力の sha256(読むだけ。1 文字も直していない)"]
        self.assertEqual(inp[u"席の答え(hybrid_s2_answers)"], SHA_ANS)
        self.assertEqual(sorted(os.listdir(ANS)), sorted(SHA_ANS))
        for fn, h in SHA_ANS.items():
            self.assertEqual(sha(os.path.join(ANS, fn)), h, fn)
        for key, p, h in ((u"材料 hybrid_s2_material_2026-10-20.json", MAT, SHA_MAT),
                          (u"便の記録 hybrid_s2_runs_2026-10-20.csv", RUNS, SHA_RUNS),
                          (u"段 1 の記録 hybrid_trust_2026-10-20.json", S1, SHA_S1),
                          (u"draw", DRAW, SHA_DRAW), (u"封", SEAL, SHA_SEAL)):
            self.assertEqual(inp[key], h, key)
            self.assertEqual(sha(p), h, key)

    def test_2_environment_and_engine_pins_are_recorded_facts(self):
        env = self.rec[u"環境"]
        self.assertEqual(env[u"設定されている key の数"], 0)
        self.assertTrue(all(v is False for v in env[u"4 つの key の名前が設定されているか"].values()))
        pins = self.rec[u"engine の留め"]
        self.assertEqual(pins[u"作業木で HEAD と sha256 が違う file"], [])
        self.assertEqual(pins[u"git diff HEAD --numstat -- core adapters"], "")
        self.assertEqual(pins[u"git status --porcelain -- core adapters"], "")
        self.assertEqual(pins[u"vocabulary.DEFAULT_PROFILE"], "P21")
        self.assertTrue(pins[u"一致"])
        self.assertEqual(pins[u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)"], ENGINE_BUNDLE)
        self.assertEqual(pins[u"core/ と adapters/ の追跡 file 数"], 36)
        # 段 1 の記録と同じ束(engine は段 1 から 1 行も変わっていない)
        s1pins = jload(S1)[u"engine の留め"]
        self.assertEqual(pins[u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)"],
                         s1pins[u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)"])

    def test_3_material_is_the_p21_material_with_192_rows(self):
        self.assertEqual(self.mat["profile"], "P21")
        self.assertEqual([p["docID"] for p in self.mat[u"書類ごと"]], DOCS)
        self.assertEqual(self.mat[u"**P-7**"][u"**P-7 の判定**"], u"緑")


class RowsTest(Base):
    def test_4_rows_match_the_inputs(self):
        self.assertEqual(len(self.rows), 192)
        self.assertEqual(len(self.inj), 64)
        det = {p["docID"]: p for p in self.mat[u"書類ごと(段 2)"]}
        seen = set()
        for p in self.mat[u"書類ごと"]:
            d = p["docID"]
            ans = {str(x["id"]).strip(): x for x in jload(os.path.join(ANS, "%s_answer.json" % d))}
            self.assertEqual(sorted(ans), sorted(p[u"席の前に出せる分"]), d)
            mdet = {x[u"行 id"]: x for x in det[d][u"注入"][u"明細"]}
            mine = {r["id"]: r for r in self.rows if r["doc"] == d}
            self.assertEqual(sorted(mine), sorted(p[u"席の前に出せる分"]), d)
            for rid, pre in p[u"席の前に出せる分"].items():
                r = mine[rid]
                seen.add((d, rid))
                self.assertEqual(r[u"注入か"], bool(pre[u"注入か"]), (d, rid))
                self.assertEqual(r[u"注入か"], rid in mdet, (d, rid))
                self.assertEqual(r[u"正解"], pre[u"正解"], (d, rid))
                self.assertEqual(r[u"席の判定"], ans[rid][u"判定"], (d, rid))
                self.assertIn(r[u"席の判定"], WORDS)
                a = ans[rid][u"参照先"]
                self.assertEqual(r[u"席の参照先"], None if a in (None, "", u"なし", u"無し") else a.strip().lower(), (d, rid))
                self.assertEqual(r[u"α 型の state"] == u"参照先なし", r[u"席の参照先"] is None, (d, rid))
                c = pre["Core"]
                self.assertEqual(r[u"Core 自身(既定)の state"], c.get("state") or u"対応なし", (d, rid))
                self.assertEqual(r[u"Core 自身(既定)の参照先"], c["参照先"], (d, rid))
                if rid in mdet:
                    x = mdet[rid]
                    self.assertEqual(r[u"注入の型"], x[u"型"], (d, rid))
                    self.assertEqual((r[u"元の字"], r[u"後の字"]), (x[u"元の字"], x[u"後の字"]), (d, rid))
                    self.assertEqual(r[u"T2 の系"], FAMILY[x["detail"]["unit_family"]] if x[u"型"] == "T2_UNIT" else None, (d, rid))
                else:
                    self.assertIsNone(r[u"注入の型"], (d, rid))
        self.assertEqual(len(seen), 192)

    def test_5_zero_counts_recounted_straight_from_answers_and_material(self):
        u"""『T6・T7・T2 金額系の見逃し 0 件』を、記録の行を使わず答えの file と材料の明細から数え直す(0 を疑う)。"""
        missed = {}
        n_inj = {}
        for p in self.mat[u"書類ごと(段 2)"]:
            ans = {str(x["id"]).strip(): x for x in jload(os.path.join(ANS, "%s_answer.json" % p["docID"]))}
            for x in p[u"注入"][u"明細"]:
                k = x[u"型"] if x[u"型"] != "T2_UNIT" else u"T2_UNIT %s" % FAMILY[x["detail"]["unit_family"]]
                n_inj[k] = n_inj.get(k, 0) + 1
                if ans[x[u"行 id"]][u"判定"] == u"確認済み":
                    missed[k] = missed.get(k, 0) + 1
        self.assertEqual(n_inj, {"T6_PRIOR": 10, "T7_ROUND": 10, u"T2_UNIT 金額系": 25, u"T2_UNIT ％系": 18, u"T2_UNIT 件→回": 1})
        self.assertEqual(missed, {u"T2_UNIT ％系": 8})
        self.assertEqual(sum(missed.values()), len(self.g1) - sum(1 for r in self.unc if r[u"席の判定"] == u"確認済み"))
        for k in (u"T6_PRIOR", u"T7_ROUND", u"T2_UNIT 金額系", u"T2_UNIT 件→回"):
            self.assertEqual(sum(1 for r in self.tm(k) if r[u"席の判定"] == u"確認済み"), 0, k)

    def test_6_rule_h_and_groups_reapplied_from_rows(self):
        for r in self.rows:
            use_alpha = r[u"α 型の state"] != u"参照先なし"
            st = r[u"α 型の state"] if use_alpha else r[u"Core 自身(既定)の state"]
            self.assertEqual(r[u"H の Core の出どころ"], u"α 型" if use_alpha else u"Core 自身")
            self.assertEqual(r[u"H の Core の state"], st)
            self.assertEqual(r[u"H の出力"], h_of(r[u"席の判定"], st == u"GROUNDED"), (r["doc"], r["id"]))
            g1 = r[u"席の判定"] == u"確認済み"
            self.assertEqual(r[u"G1(席が確認済み)"], g1)
            self.assertEqual(r[u"群(α 型)"], (u"G2" if r[u"α 型の state"] == u"GROUNDED" else u"G3") if g1 else None)
            self.assertEqual(r[u"群(Core 自身)"], (u"G2" if r[u"Core 自身(既定)の state"] == u"GROUNDED" else u"G3") if g1 else None)
        # G1 の行は全部 α 型が効く。注入 64 行のうち α 型は 54
        self.assertEqual(sum(1 for r in self.g1 if r[u"α 型の state"] == u"参照先なし"), 0)
        self.assertEqual(sum(1 for r in self.inj if r[u"α 型の state"] != u"参照先なし"), 54)
        self.assertEqual(sum(1 for r in self.rows if r[u"α 型の state"] != u"参照先なし"), 128)

    def test_7_aggregates_recounted_from_rows(self):
        a = self.agg
        c = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
        self.assertEqual(a[u"席の字"], {
            u"行": 192, u"注入": 64, u"無改変": 128,
            u"席が確認済みにした注入(見逃し)": c(self.inj, u"確認済み"), u"席が誤りが在るにした注入(検出)": c(self.inj, u"誤りが在る"),
            u"席が判定できないにした注入": c(self.inj, u"判定できない"),
            u"席が確認済みにした無改変": c(self.unc, u"確認済み"), u"席が判定できないにした無改変": c(self.unc, u"判定できない"),
            u"席の偽警報(無改変で誤りが在る)": c(self.unc, u"誤りが在る")})
        for key, G, f in ((u"3 群(α 型)", self.GA, u"α 型の state"), (u"3 群(Core 自身)", self.GS, u"Core 自身(既定)の state")):
            for g in (u"G1", u"G2", u"G3"):
                m = G[g]
                ok = sum(1 for r in m if not r[u"注入か"])
                self.assertEqual(a[key][g], {
                    u"行": len(m), u"注入": len(m) - ok, u"無改変": ok,
                    u"精度(注入でない行 / 群)": {u"分子": ok, u"分母": len(m), u"率": round(100.0 * ok / len(m), 1)}}, (key, g))
            self.assertEqual(a[key][u"G3 の state の内訳"], dict(sorted(cnt(G[u"G3"], f).items())), key)
        h = {}
        for kind, m in ((u"無改変", self.unc), (u"注入", self.inj), (u"全部", self.rows)):
            h[kind] = dict(sorted(cnt(m, u"H の出力").items()))
        self.assertEqual(a[u"H の出力"], h)
        conf = lambda m: sum(1 for r in m if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        self.assertEqual((a[u"H の確認(二重確認 + Core のみ確認)"][u"分子"], a[u"H の確認(二重確認 + Core のみ確認)"][u"分母"]), (conf(self.rows), 192))
        self.assertEqual((a[u"誤りを通した(注入の行が二重確認か Core のみ確認)"][u"分子"], a[u"誤りを通した(注入の行が二重確認か Core のみ確認)"][u"分母"]), (conf(self.inj), 64))
        for k in TKEYS:
            m = self.tm(k)
            t = a[u"型別"][k]
            al = [r for r in m if r[u"α 型の state"] != u"参照先なし"]
            self.assertEqual(t[u"注入"], len(m), k)
            self.assertEqual(t[u"席の判定"], {w: sum(1 for r in m if r[u"席の判定"] == w) for w in WORDS}, k)
            self.assertEqual(t[u"α 型の state(注入の行の全部)"], dict(sorted(cnt(m, u"α 型の state").items())), k)
            self.assertEqual(t[u"Core が通した(α 型 GROUNDED。注入の行の全部)"][u"分子"], sum(1 for r in m if r[u"α 型の state"] == u"GROUNDED"), k)
            self.assertEqual(t[u"Core 自身が GROUNDED"][u"分子"], sum(1 for r in m if r[u"Core 自身(既定)の state"] == u"GROUNDED"), k)
            self.assertEqual(t[u"席の見逃しのうち G3(α 型)"], sum(1 for r in m if r[u"G1(席が確認済み)"] and r[u"群(α 型)"] == u"G3"), k)
            self.assertEqual(t[u"保留規則の発火(hold_rules。α 型を当てた注入)"],
                             {x: sum(1 for r in al if x in r[u"α 型の hold_rules"]) for x in ("d", "P", "U")}, k)
            self.assertEqual(t[u"誤りを通した(二重確認か Core のみ確認)"][u"分子"], conf(m), k)
        self.assertEqual(sum(a[u"型別"][k][u"注入"] for k in (u"T6_PRIOR", u"T7_ROUND", u"T2_UNIT")), 64)
        self.assertEqual(self.rec[u"分母と封の割当"][u"実数"], {"T6_PRIOR": 10, "T7_ROUND": 10, "T2_UNIT": 44})

    def test_8_hold_rules_fire_zero_because_nothing_reached_grounded(self):
        u"""発火 0 を疑う: 規則は GROUNDED の応答にだけ掛かる(holds.apply_holds)。注入の行で α 型が GROUNDED の行が 0 だから 0。
        対照: 無改変の行には露出が在り、α 型が GROUNDED にした行は 40 あるが、規則が発火した行の数は記録の行から数える。"""
        self.assertEqual(sum(1 for r in self.inj if r[u"α 型の state"] == u"GROUNDED"), 0)
        self.assertEqual(sum(1 for r in self.inj if r[u"α 型の hold_rules"]), 0)
        self.assertEqual(sum(1 for r in self.inj if r[u"α 型の held"]), 0)
        src = text(os.path.join(ROOT, "adapters", "xbrl", "holds.py"))
        self.assertIn(u'if out.get("state") != GROUNDED or f is None:', src)
        # 規則は『発火したら必ず held』と揃っている(行から)
        for r in self.rows:
            if r[u"α 型の hold_rules"]:
                self.assertTrue(r[u"α 型の held"], (r["doc"], r["id"]))
        # T2 の UNPROVABLE 16 件の理由の字(保留規則でない)
        t2u = [r for r in self.tm(u"T2_UNIT") if r[u"α 型の state"] == u"UNPROVABLE"]
        self.assertEqual(len(t2u), 16)
        self.assertEqual(sorted(r[u"α 型の reason"] for r in t2u),
                         sorted([u"規則 単一の値(金額) は金額の単位を要る(渡されたのは '円')"] * 6
                                + [u"規則 単一の値(金額) は金額の単位を要る(渡されたのは 'ポイント')"] * 10))

    def test_9_core_self_passes_t6_prior_value_with_prior_pointers(self):
        sg = [r for r in self.inj if r[u"Core 自身(既定)の state"] == u"GROUNDED"]
        self.assertEqual(len(sg), 6)
        self.assertEqual({r[u"注入の型"] for r in sg}, {"T6_PRIOR"})
        for r in sg:
            self.assertIn("@prior1year", r[u"Core 自身(既定)の参照先"])
            self.assertEqual(r[u"席の判定"], u"誤りが在る")
            self.assertEqual(r[u"H の出力"], u"誤り(席)")
            self.assertEqual(r[u"α 型の state"], u"VALUE_MISMATCH")


class PredictionTest(Base):
    def judge(self):
        seal = self.seal
        p1, p2, p3 = pairs(seal_pred(seal, "P-1")), pairs(seal_pred(seal, "P-2")), pairs(seal_pred(seal, "P-3"))
        pts = [int(x) for x in re.findall(r"\*\*(\d+) pt\*\*", seal_pred(seal, "P-3"))]
        p5 = pairs(seal_pred(seal, "P-5"))
        cap = int(re.search(r"1 便 ([\d,]+)", seal_pred(seal, "P-5")).group(1).replace(",", ""))
        p6 = pairs(seal_pred(seal, "P-6"))
        r = {}
        n_missed = sum(1 for x in self.inj if x[u"席の判定"] == u"確認済み")
        r[u"P-1"] = p1[0][0] <= n_missed <= p1[0][1]
        thr = [x for x in self.inj if x[u"α 型の state"] == u"GROUNDED"]
        r[u"P-2"] = (p2[0][0] <= len(thr) <= p2[0][1]
                     and not any(x[u"注入の型"] in (u"T6_PRIOR", u"T2_UNIT") for x in thr))
        GA = self.GA
        a = lambda g: Fraction(100 * sum(1 for x in GA[g] if not x[u"注入か"]), len(GA[g])) if GA[g] else None
        a1, a2, a3 = a(u"G1"), a(u"G2"), a(u"G3")
        r[u"P-3"] = None if None in (a1, a2, a3) else bool(
            p3[0][0] <= a1 <= p3[0][1] and a2 >= a1 + pts[0] and a3 <= a1 - pts[1])
        inj_g1 = sum(1 for x in GA[u"G1"] if x[u"注入か"])
        inj_g3 = sum(1 for x in GA[u"G3"] if x[u"注入か"])
        r[u"P-4"] = None if not inj_g1 else bool(3 * inj_g3 >= 2 * inj_g1)
        hdr, body = self.csv_runs()
        toks = [int(b[2]) for b in body]
        files_ok = all(
            len(jload(os.path.join(ANS, "%s_answer.json" % d))) == 24 and
            sorted(str(x["id"]) for x in jload(os.path.join(ANS, "%s_answer.json" % d))) == sorted(x["id"] for x in self.rows if x["doc"] == d)
            for d in DOCS)
        r[u"P-5"] = bool(len(body) == 8 and all(int(b[4]) == 24 for b in body) and {b[1] for b in body} == {"sonnet"}
                         and p5[0][0] <= sum(toks) <= p5[0][1] and max(toks) <= cap and files_ok)
        g1u = sum(1 for x in self.unc if x[u"席の判定"] == u"確認済み")
        fa = sum(1 for x in self.unc if x[u"席の判定"] == u"誤りが在る")
        g3u = sum(1 for x in GA[u"G3"] if not x[u"注入か"])
        r[u"P-6"] = bool(p6[0][0] <= g1u <= p6[0][1] and p6[1][0] <= fa <= p6[1][1]
                         and p6[2][0] <= Fraction(100 * g3u, g1u) <= p6[2][1])
        m7 = self.mat[u"**P-7**"]
        r[u"P-7"] = bool(m7[u"**P-7 の判定**"] == u"緑" and m7[u"見せない字 0(8 書類とも。封の字の 9 語)"]
                         and m7[u"字数が C1 の ±30% の中(8 書類とも)"])
        return r

    def test_10_seal_wording_is_what_the_script_holds(self):
        tree = ast.parse(text(SCRIPT))
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                try:
                    consts[node.targets[0].id] = ast.literal_eval(node.value)
                except Exception:
                    pass
        s = self.seal
        p1, p2, p3 = pairs(seal_pred(s, "P-1")), pairs(seal_pred(s, "P-2")), pairs(seal_pred(s, "P-3"))
        pts = [int(x) for x in re.findall(r"\*\*(\d+) pt\*\*", seal_pred(s, "P-3"))]
        p5, p6 = pairs(seal_pred(s, "P-5")), pairs(seal_pred(s, "P-6"))
        self.assertEqual(consts["P1_RANGE"], p1[0])
        self.assertEqual(consts["P1_T7"], p1[1])
        self.assertEqual(consts["P1_T2"], p1[2])
        self.assertEqual(consts["P2_RANGE"], p2[0])
        self.assertEqual(consts["P3_G1"], p3[0])
        self.assertEqual((consts["P3_G2_PT"], consts["P3_G3_PT"]), tuple(pts))
        self.assertEqual((consts["P4_NUM"], consts["P4_DEN"]), (2, 3))
        self.assertIn(u"**その 2/3**", seal_pred(s, "P-4"))
        self.assertEqual(consts["P5_TOTAL"], p5[0])
        self.assertEqual(consts["P5_RUN_CAP"], int(re.search(r"1 便 ([\d,]+)", seal_pred(s, "P-5")).group(1).replace(",", "")))
        self.assertEqual(consts["P6_G1_UNMOD"], p6[0])
        self.assertEqual(consts["P6_FALSE"], p6[1])
        self.assertEqual(consts["P6_G3_SHARE"], p6[2])

    def test_11_judgments_recomputed_equal_record_and_doc(self):
        j = self.judge()
        self.assertEqual(sorted(j), [u"P-%d" % i for i in range(1, 8)])
        for h, v in j.items():
            self.assertEqual(self.preds[h][u"当たり"], v, h)
            jd = cells(self.doc, h)[3]
            word = {True: u"**当たり**", False: u"**外れ**", None: u"**判定しない**"}[v]
            self.assertTrue(jd.startswith(word), (h, jd))
        n_missed = sum(1 for x in self.inj if x[u"席の判定"] == u"確認済み")
        self.assertEqual(cells(self.doc, "P-1")[3], u"**当たり**(全体 %d / 64)" % n_missed)
        hit = sum(1 for v in j.values() if v is True)
        miss = sum(1 for v in j.values() if v is False)
        self.assertIn(u"**予測 当たり %d / 外れ %d**(P-3・P-6)。**P-1 は全体は当たり、型別の序列と T7 は外れ**" % (hit, miss), self.doc)
        self.assertIn(u"**当たり %d / 外れ %d**(P-3・P-6)。P-1 は全体 %d / 64 で当たり、型別の序列と T7 は外れ" % (hit, miss, n_missed), self.doc)
        self.assertEqual({h for h, v in j.items() if v is False}, {u"P-3", u"P-6"})
        # P-1 の型別(率に直して判定。司令塔の決定 2026-10-20): 序列は逆向き = 外れ、T7 は封の幅の外 = 外れ、T2 は中
        p1 = pairs(seal_pred(self.seal, "P-1"))
        t = lambda k: Fraction(sum(1 for r in self.tm(k) if r[u"席の判定"] == u"確認済み"), len(self.tm(k)))
        r6, r7, r2 = t(u"T6_PRIOR"), t(u"T7_ROUND"), t(u"T2_UNIT")
        self.assertIn(u"T7_ROUND が最多", seal_pred(self.seal, "P-1"))
        self.assertIn(u"T2_UNIT が最少", seal_pred(self.seal, "P-1"))
        order_ok = r7 >= r6 and r7 >= r2 and r2 <= r6 and r2 <= r7     # 封の序列: T7 最多・T2 最少
        t7_ok = Fraction(p1[1][0], 24) <= r7 <= Fraction(p1[1][1], 24)
        t2_ok = Fraction(p1[2][0], 16) <= r2 <= Fraction(p1[2][1], 16)
        self.assertEqual((order_ok, t7_ok, t2_ok), (False, False, True))
        self.assertIn(u"実測は T2 が最多(%.1f%%)、T7 は T6 と並んで最少(%.1f%%)で逆向きなので外れ" % (100 * r2, 100 * r7), self.doc)
        self.assertEqual(r7, r6)
        self.assertGreater(r2, r7)
        # P-1 の行の内側の一文を縛る(序列と T7 の『外れ』、T2 の『中』)
        row = cells(self.doc, "P-1")[2]
        self.assertIn(u"で逆向きなので外れ。T7 は率 %.1f%% が封の 3〜12 / 24(%.1f〜%.1f%%)の外で外れ。T2 は率 %.1f%% が封の 0〜4 / 16(%.1f〜%.1f%%)の中。" % (
            100 * r7, 100.0 * p1[1][0] / 24, 100.0 * p1[1][1] / 24, 100 * r2, 100.0 * p1[2][0] / 16, 100.0 * p1[2][1] / 16), row)
        # 記録の json は直していない(直す前の字が残る)。文書の『判定しない』は §9-1 の注記の 1 行だけ
        self.assertEqual(self.preds[u"P-1"][u"型別の部分"], u"判定しない")
        ls = [l for l in self.doc.splitlines() if u"判定しない" in l]
        self.assertEqual(len(ls), 1)
        self.assertTrue(ls[0].startswith(u"1. **P-1 の判定**(2026-10-20 に直した)"))
        self.assertIn(u"**判定しない → 実数の分母で判定(序列と T7 は外れ)に直した(2026-10-20、監査の指摘)。**", ls[0])
        self.assertIn(u"P-1 の型別の分母は実数で採点する", ls[0])

    def test_12_prediction_table_wording_and_numbers(self):
        for h in sorted(self.preds):
            self.assertEqual(cells(self.doc, h)[1], seal_pred(self.seal, h), h)
        GA, GS = self.GA, self.GS
        S = self.seal
        p1, p2, p3 = pairs(seal_pred(S, "P-1")), pairs(seal_pred(S, "P-2")), pairs(seal_pred(S, "P-3"))
        pts = [int(x) for x in re.findall(r"\*\*(\d+) pt\*\*", seal_pred(S, "P-3"))]
        p5, p6 = pairs(seal_pred(S, "P-5")), pairs(seal_pred(S, "P-6"))
        miss = lambda k: sum(1 for r in self.tm(k) if r[u"席の判定"] == u"確認済み")
        n_missed = sum(1 for r in self.inj if r[u"席の判定"] == u"確認済み")
        thr = lambda k: sum(1 for r in self.tm(k) if r[u"α 型の state"] == u"GROUNDED")
        sg = [r for r in self.inj if r[u"Core 自身(既定)の state"] == u"GROUNDED"]
        a = lambda g: Fraction(100 * sum(1 for x in GA[g] if not x[u"注入か"]), len(GA[g]))
        ok = lambda g: sum(1 for x in GA[g] if not x[u"注入か"])
        d21, d31 = round(float(a(u"G2") - a(u"G1")), 1), round(float(a(u"G1") - a(u"G3")), 1)
        inj_g1 = sum(1 for x in GA[u"G1"] if x[u"注入か"])
        inj_g3 = sum(1 for x in GA[u"G3"] if x[u"注入か"])
        hdr, body = self.csv_runs()
        toks = [int(b[2]) for b in body]
        g1u = sum(1 for x in self.unc if x[u"席の判定"] == u"確認済み")
        fa = sum(1 for x in self.unc if x[u"席の判定"] == u"誤りが在る")
        g3u = sum(1 for x in GA[u"G3"] if not x[u"注入か"])
        comma = lambda n: format(n, ",")
        exp = {
            u"P-1": (fr(n_missed, 64) + [str(p1[0][0]), str(p1[0][1])] + fr(miss(u"T6_PRIOR"), 10) + fr(miss(u"T7_ROUND"), 10)
                     + fr(miss(u"T2_UNIT"), 44) + fr(miss(u"T2_UNIT 金額系"), 25) + fr(miss(u"T2_UNIT ％系"), 18) + fr(miss(u"T2_UNIT 件→回"), 1)
                     + ["%.1f" % (100.0 * miss(u"T2_UNIT") / 44), "%.1f" % (100.0 * miss(u"T7_ROUND") / 10), "%.1f" % (100.0 * miss(u"T7_ROUND") / 10)]
                     + [str(p1[1][0]), str(p1[1][1]), "24", "%.1f" % (100.0 * p1[1][0] / 24), "%.1f" % (100.0 * p1[1][1] / 24),
                        "%.1f" % (100.0 * miss(u"T2_UNIT") / 44), str(p1[2][0]), str(p1[2][1]), "16",
                        "%.1f" % (100.0 * p1[2][0] / 16), "%.1f" % (100.0 * p1[2][1] / 16),
                        str(p1[0][0] - 1), str(p1[0][1] + 1), "3", str(n_missed)]),
            u"P-2": (fr(thr(u"T6_PRIOR") + thr(u"T7_ROUND") + thr(u"T2_UNIT"), 64) + [str(p2[0][0]), str(p2[0][1])]
                     + [str(thr(u"T6_PRIOR")), str(thr(u"T7_ROUND")), str(thr(u"T2_UNIT")), "0"]
                     + fr(len(sg), 64) + fr(sum(1 for r in sg if r[u"注入の型"] == u"T6_PRIOR"), 10)),
            u"P-3": (fr(ok(u"G1"), len(GA[u"G1"])) + fr(ok(u"G2"), len(GA[u"G2"])) + fr(ok(u"G3"), len(GA[u"G3"]))
                     + ["%.1f" % d21, str(pts[0]), "%.1f" % d31, str(pts[1]), str(p3[0][0]), str(p3[0][1])]),
            u"P-4": ([str(inj_g1)] + fr(inj_g3, inj_g1) + ["2", "3", str(inj_g3),
                      str(sum(1 for r in self.g1 if r[u"注入か"] and r[u"α 型の state"] == u"参照先なし"))]),
            u"P-5": (["8", "24", "8", comma(sum(toks)), comma(p5[0][0]), comma(p5[0][1]), "1", comma(max(toks)), "250,000"]),
            u"P-6": ([str(g1u), str(p6[0][0]), str(p6[0][1])] + fr(g1u, 128) + [str(fa)] + fr(fa, 128)
                     + [str(p6[1][0]), str(p6[1][1]), str(g3u)] + fr(g3u, g1u) + [str(p6[2][0]), str(p6[2][1])]),
            u"P-7": ["7", "9", "0", "30", "8"]}
        for h, e in exp.items():
            self.assertEqual(nums(cells(self.doc, h)[2]), e, h)
        # 記録の 実測 の欄とも合う
        self.assertEqual(self.preds[u"P-5"][u"実測"][u"合計トークン"], sum(toks))
        self.assertEqual(self.preds[u"P-5"][u"実測"][u"1 便の最大"], max(toks))
        self.assertEqual(self.preds[u"P-3"][u"実測"][u"G2 - G1(pt)"], d21)
        self.assertEqual(self.preds[u"P-3"][u"実測"][u"G3 - G1(pt)"], -d31)
        self.assertEqual(self.preds[u"P-4"][u"実測"][u"席が支持した注入"], inj_g1)

    def test_13_csv_parsed_independently(self):
        hdr, body = self.csv_runs()
        self.assertEqual(len(body), 8)
        self.assertEqual(sorted(b[0] for b in body), sorted(DOCS))
        self.assertEqual(sum(int(b[2]) for b in body), 892938)
        self.assertEqual(max(int(b[2]) for b in body), 150985)
        run = self.rec[u"便の記録"]
        self.assertEqual((run[u"合計トークン"], run[u"最大"], run[u"最小"], run[u"便の数"]), (892938, 150985, 96425, 8))
        self.assertEqual(run[u"1 便が上限を超えた便"], [])
        self.assertEqual(run[u"行数が 24 でない便"], [])


class DocTest(Base):
    def lines(self):
        return set(self.doc.splitlines())

    def expect_lines(self):
        L = []
        rows, inj, unc, g1 = self.rows, self.inj, self.unc, self.g1
        for k, q in ((u"T6_PRIOR", 24), (u"T7_ROUND", 24), (u"T2_UNIT", 16)):
            n = len(self.tm(k))
            L.append(u"| %s | %d | %d | %+d |" % (k, q, n, n - q))
        c = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
        L.append(u"| %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            len(rows), len(inj), len(unc), c(inj, u"確認済み"), c(inj, u"誤りが在る"), c(inj, u"判定できない"),
            c(unc, u"確認済み"), c(unc, u"判定できない"), c(unc, u"誤りが在る")))
        names = {u"G1": u"G1(席が確認済み)", u"G2": u"G2(Core も GROUNDED)", u"G3": u"G3(Core が GROUNDED にしない)"}
        for G, lab, f in ((self.GA, u"α 型", u"α 型の state"), (self.GS, u"Core 自身", u"Core 自身(既定)の state")):
            for k in (u"G1", u"G2", u"G3"):
                m = G[k]
                L.append(u"| %s | %d | %d | %s |" % (names[k], len(m), sum(1 for r in m if r[u"注入か"]), self.prec(m)))
            g3 = G[u"G3"]
            L.append(u"| %s | %s | %s | %s |" % (lab, brk(cnt(g3, f)), brk(cnt([r for r in g3 if r[u"注入か"]], f)),
                                                brk(cnt([r for r in g3 if not r[u"注入か"]], f))))
        L.append(u"- 席が確認済みにした %d 行のうち参照先なしの行は %d(α 型は G1 の全行に効いた)。α 型を当てた行は 192 行中 %d、うち注入の行は %d。" % (
            len(g1), sum(1 for r in g1 if r[u"α 型の state"] == u"参照先なし"),
            sum(1 for r in rows if r[u"α 型の state"] != u"参照先なし"), sum(1 for r in inj if r[u"α 型の state"] != u"参照先なし")))
        for k in TKEYS:
            m = self.tm(k)
            al = [r for r in m if r[u"α 型の state"] != u"参照先なし"]
            mg = [r for r in m if r[u"G1(席が確認済み)"]]
            L.append(u"| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (
                k, len(m), c(m, u"確認済み"), c(m, u"誤りが在る"), c(m, u"判定できない"), len(al),
                sum(1 for r in m if r[u"α 型の state"] == u"VALUE_MISMATCH"), sum(1 for r in m if r[u"α 型の state"] == u"UNPROVABLE"),
                sum(1 for r in m if r[u"α 型の state"] == u"参照先なし"), sum(1 for r in m if r[u"α 型の state"] == u"GROUNDED"),
                sum(1 for r in m if r[u"Core 自身(既定)の state"] == u"GROUNDED"), sum(1 for r in mg if r[u"群(α 型)"] == u"G3")))
            fire = lambda x: sum(1 for r in al if x in r[u"α 型の hold_rules"])
            L.append(u"| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
                k, len(al), fire(u"d"), fire(u"P"), fire(u"U"), sum(1 for r in al if r[u"α 型の held"]),
                sum(1 for r in al if r[u"α 型の露出 (d)"]), sum(1 for r in al if r[u"α 型の露出 P"]), sum(1 for r in al if r[u"α 型の露出 U"])))
        for r in inj:
            if r[u"G1(席が確認済み)"]:
                L.append(u"| %s %s | %s %s | %s → %s | %s | %s | %s |" % (
                    r["doc"], r["id"], r[u"注入の型"], r[u"T2 の系"], r[u"元の字"], r[u"後の字"],
                    r[u"α 型の state"], r[u"Core 自身(既定)の state"], r[u"H の出力"]))
        for kind, m in ((u"無改変", unc), (u"注入", inj), (u"全部", rows)):
            k = lambda w: sum(1 for r in m if r[u"H の出力"] == w)
            L.append(u"| %s | %d | %d | %d | %d | %d | %d |" % (kind, len(m), k(u"二重確認"), k(u"Core のみ確認"), k(u"警告"), k(u"保留"), k(u"誤り(席)")))
        pas = lambda m: sum(1 for r in m if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        L.append(u"- **誤りを通した行**(注入の行が二重確認か Core のみ確認): %s。型別: T6_PRIOR %s・T7_ROUND %s・T2_UNIT %s。" % (
            F(pas(inj), 64), F(pas(self.tm(u"T6_PRIOR")), 10), F(pas(self.tm(u"T7_ROUND")), 10), F(pas(self.tm(u"T2_UNIT")), 44)))
        L.append(u"- 見逃し 8 件は H で『警告』(席は確認済み・Core は G3)になり、誤りとは言わないが確認済みの印は付かない。"
                 u"H の確認(二重確認 + Core のみ確認)は %s で、席が確認済みにした %d 行より少ない。" % (F(pas(rows), 192), len(g1)))
        L.append(u"- Core のみ確認は 0 件: 席が判定できないとした %d 行(注入 %d・無改変 %d)のうち Core が GROUNDED にした行は %d。" % (
            c(rows, u"判定できない"), c(inj, u"判定できない"), c(unc, u"判定できない"),
            sum(1 for r in rows if r[u"席の判定"] == u"判定できない" and r[u"H の Core の state"] == u"GROUNDED")))
        return L

    def test_14_doc_lines_equal_lines_built_from_rows(self):
        have = self.lines()
        for l in self.expect_lines():
            self.assertIn(l, have, l)

    def test_15_summary_lines(self):
        GA = self.GA
        d21 = round(float(Fraction(100 * sum(1 for x in GA[u"G2"] if not x[u"注入か"]), len(GA[u"G2"]))
                          - Fraction(100 * sum(1 for x in GA[u"G1"] if not x[u"注入か"]), len(GA[u"G1"]))), 1)
        d31 = round(float(Fraction(100 * sum(1 for x in GA[u"G1"] if not x[u"注入か"]), len(GA[u"G1"]))
                          - Fraction(100 * sum(1 for x in GA[u"G3"] if not x[u"注入か"]), len(GA[u"G3"]))), 1)
        self.assertIn(u"G1 %s・G2 %s・G3 %s。G2 は G1 より %.1f pt 高く、G3 は G1 より %.1f pt 低い。**G2 に注入は %d 件**" % (
            self.prec(GA[u"G1"]), self.prec(GA[u"G2"]), self.prec(GA[u"G3"]), d21, d31, sum(1 for x in GA[u"G2"] if x[u"注入か"])), self.doc)
        g3u = [x for x in GA[u"G3"] if not x[u"注入か"]]
        g1u = sum(1 for x in self.unc if x[u"席の判定"] == u"確認済み")
        self.assertIn(u"G3 の無改変 %d 行は G1 の無改変 %d 行の %s" % (len(g3u), g1u, F(len(g3u), g1u)), self.doc)
        self.assertIn(u"席が確認済みにした無改変 %d 行のうち α 型が GROUNDED にしたのは %d 行にとどまった" % (
            g1u, sum(1 for r in self.unc if r[u"席の判定"] == u"確認済み" and r[u"α 型の state"] == u"GROUNDED")), self.doc)
        self.assertIn(u"G3 は %d 行で、うち注入は %d(全部 T2 の％系)、無改変は %d(%s)" % (
            len(GA[u"G3"]), sum(1 for x in GA[u"G3"] if x[u"注入か"]), len(g3u), brk(cnt(g3u, u"α 型の state"))), self.doc)
        self.assertEqual({x[u"T2 の系"] for x in GA[u"G3"] if x[u"注入か"]}, {u"％系"})
        self.assertIn(u"所要 %s 秒(全体)" % self.rec[u"所要秒"][u"全体"], self.doc)
        self.assertIn(u"束ねた sha256 `%s`" % ENGINE_BUNDLE, self.doc)
        self.assertIn(u"core/ と adapters/ の追跡 36 file", self.doc)
        self.assertIn(u"- **Core 自身の T6_PRIOR**: 前期の値に置き換えた 10 件のうち 6 件を Core 自身は GROUNDED にした", self.doc)
        self.assertIn(u"- **発火は T6・T7・T2 とも 0 件。**", self.doc)
        self.assertIn(u"Core 自身だけで確認していたら T6 を通す(値の実在は見るが期間は縛らない)。", self.doc)
        a = lambda g: Fraction(100 * sum(1 for x in GA[g] if not x[u"注入か"]), len(GA[g]))
        self.assertTrue(a(u"G2") > a(u"G1") > a(u"G3"))
        self.assertEqual(sum(1 for x in GA[u"G2"] if x[u"注入か"]), 0)
        self.assertIn(u"封 §0 の並び G2 > G1 > G3 は α 型で %.1f > %.1f > %.1f と数の上では成り立つ。ただし G2 の 100.0%% は注入が 1 件も G2 に来なかった結果で『誤りを通さなかった実績』ではなく、"
                      u"P-3 は G3 が %.1f pt 届かず外れた。**『Core の一致は信頼の印』とは断じない。**" % (
                          a(u"G2"), a(u"G1"), a(u"G3"), round(10 - float(a(u"G1") - a(u"G3")), 1)), self.doc)
        self.assertIn(u"### 3-5. 並び G2 > G1 > G3 の読み", self.doc)

    def test_16_every_fraction_is_arithmetic_and_in_the_allowed_set(self):
        allowed = set()
        for G in (self.GA, self.GS):
            for k in (u"G1", u"G2", u"G3"):
                allowed.add((sum(1 for r in G[k] if not r[u"注入か"]), len(G[k])))
        n_missed = sum(1 for r in self.inj if r[u"席の判定"] == u"確認済み")
        allowed.add((n_missed, 64))
        for k in TKEYS:
            m = self.tm(k)
            allowed.add((sum(1 for r in m if r[u"席の判定"] == u"確認済み"), len(m)))
            allowed.add((sum(1 for r in m if r[u"H の出力"] in (u"二重確認", u"Core のみ確認")), len(m)))
        allowed.add((sum(1 for r in self.inj if r[u"α 型の state"] == u"GROUNDED"), 64))
        allowed.add((sum(1 for r in self.inj if r[u"Core 自身(既定)の state"] == u"GROUNDED"), 64))
        allowed.add((sum(1 for r in self.inj if r[u"Core 自身(既定)の state"] == u"GROUNDED" and r[u"注入の型"] == u"T6_PRIOR"), 10))
        allowed.add((sum(1 for r in self.inj if r[u"H の出力"] in (u"二重確認", u"Core のみ確認")), 64))
        allowed.add((sum(1 for r in self.rows if r[u"H の出力"] in (u"二重確認", u"Core のみ確認")), 192))
        g1u = sum(1 for r in self.unc if r[u"席の判定"] == u"確認済み")
        fa = sum(1 for r in self.unc if r[u"席の判定"] == u"誤りが在る")
        allowed.add((g1u, 128))
        allowed.add((fa, 128))
        allowed.add((sum(1 for r in self.GA[u"G3"] if not r[u"注入か"]), g1u))
        allowed.add((sum(1 for r in self.GA[u"G3"] if r[u"注入か"]), sum(1 for r in self.GA[u"G1"] if r[u"注入か"])))
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 30)
        for a, b, p in found:
            a_, b_ = int(a.replace(",", "")), int(b.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * a_ / b_), p, (a, b, p))
            self.assertIn((a_, b_), allowed, (a, b, p))

    def test_17_limits_and_wording_exist(self):
        for s in (u"## 8. 限界", u"## 9. 迷った点", u"## 10. 再現",
                  u"**この採点では席を呼んでいない・通信していない・engine(`core/`・`adapters/`)0 行。**",
                  u"型別の分母は実数(T6 10・T7 10・T2 44)で、封の 24 / 24 / 16 と違う",
                  u"**T2 の注入 44 件のうち％系 18 件(％ ↔ ポイント)は、数が正しいまま単位の語だけが違う。『注入か』の物差しの限界**",
                  u"材料の記録の『絞る前の T7 31』は再現できない数なので使っていない",
                  u"引用(材料の独立監査の指摘。この採点では再測定していない)",
                  u"**縛っていないもの**: 本文の文章、§8 の引用(材料の独立監査の指摘)。",
                  u"- **見逃し 8 件は 2 書類に集中している**(S100Z0OS 4・S100YYN7 4。他の 6 書類は 0)。S100Z0OS は無改変を 1 件も確認済みにしていない。",
                  u"**原文が『ポイント』の無改変行は本標本に 0 件**(記録の `材料の単位` で数えた)",
                  u"この規則が正しい『ポイント』の行も止めるかは**未測定**",
                  u"- **8 件は性質が揃っていない。** 3 件(S100Z0OS R024 法人税等の負担率・S100YYN7 R022・R023 自己資本比率)は水準の率に『ポイント』を付けた表記の誤りそのもの",
                  u"『Core が誤りを見抜いた』ではなく『語彙の規則が結果として当たった』と読む余地がある"):
            self.assertIn(s, self.doc, s)
        # §8 の数を記録から数える: 見逃しの書類別・無改変の『ポイント』・G3 の理由の字
        miss = [r for r in self.inj if r[u"席の判定"] == u"確認済み"]
        bydoc = {}
        for r in miss:
            bydoc[r["doc"]] = bydoc.get(r["doc"], 0) + 1
        self.assertEqual(bydoc, {"S100Z0OS": 4, "S100YYN7": 4})
        self.assertEqual(sum(1 for r in self.unc if r["doc"] == "S100Z0OS" and r[u"席の判定"] == u"確認済み"), 0)
        self.assertEqual(sum(1 for r in self.unc if r[u"材料の単位"] == u"ポイント"), 0)
        self.assertGreater(sum(1 for r in self.unc if r[u"材料の単位"] in (u"％", u"%")), 0)     # 0 を疑う: 単位の欄は読めている
        self.assertGreater(sum(1 for r in self.inj if r[u"材料の単位"] == u"ポイント"), 0)
        self.assertEqual({r[u"α 型の reason"] for r in miss}, {u"規則 単一の値(金額) は金額の単位を要る(渡されたのは 'ポイント')"})
        ids = {(r["doc"], r["id"]) for r in miss}
        self.assertEqual(ids, {("S100Z0OS", "R011"), ("S100Z0OS", "R012"), ("S100Z0OS", "R013"), ("S100Z0OS", "R024"),
                               ("S100YYN7", "R010"), ("S100YYN7", "R019"), ("S100YYN7", "R022"), ("S100YYN7", "R023")})
        lim = self.rec["limits"]
        self.assertTrue(any(u"％系 18(％↔ポイント)は数が正しいままで" in x for x in lim))
        self.assertTrue(any(u"絞る前の T7 31" in x for x in lim))
        self.assertEqual(self.agg[u"席の字"][u"席が確認済みにした注入(見逃し)"], 8)


class ReproduceTest(Base):
    def test_18_script_reproduces_rows_aggregates_and_predictions(self):
        S = load_script()
        if not all(os.path.exists(S.C1.ED.cache_path(d)) for d in DOCS):
            self.skipTest(u"EDINET のキャッシュ ~/.cache/audit-core/edinet/<docID>.zip が無い(組み直せない)")
        tmp = tempfile.mkdtemp(prefix="hybrid_s2_score_gate_")
        out = os.path.join(tmp, "again.json")
        old = os.environ.get("TMPDIR")
        os.environ["TMPDIR"] = tmp
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                S.main(["--stage", "score", "--out", out])
        finally:
            if old is None:
                del os.environ["TMPDIR"]
            else:
                os.environ["TMPDIR"] = old
        self.addCleanup(shutil.rmtree, tmp, True)
        again = jload(out)
        for k in (u"行", u"集計", u"**予測 P-1〜P-7**", u"席が確認済みにした注入の行(見逃し)", u"便の記録", u"席の答えの形",
                  u"入力の sha256(読むだけ。1 文字も直していない)", u"分母と封の割当"):
            self.assertEqual(again[k], self.rec[k], k)
        # 既に在る出力は上書きしない
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(io.StringIO()):
                S.main(["--stage", "score", "--out", out])


if __name__ == "__main__":
    unittest.main()
