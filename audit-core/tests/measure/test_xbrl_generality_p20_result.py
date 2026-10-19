# -*- coding: utf-8 -*-
u"""汎化 C 追記 2 段 P-B の結果文書(docs/XBRL_GENERALITY_P20_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/c0_p20_2026-10-20.json``(``measure/xbrl_gen_c_p20_2026-10-20.py`` の出力)。
封: ``docs/XBRL_GENERALITY_SEAL_2026-10-20.md`` 追記 2(B-3 の幅は**ここに字で留める**。封の字と合わせてある)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の集計(数え直しの欄・(ア) の採点・K-4)を、同じ記録の**行**(P20 の 128 行・C0 の記録の P16 の 128 行・C1 の記録の 20 行)から
     この門が数え直した値と突き合わせる(記録の集計欄を信じない)。
  2. 予測 R-1〜R-10 の当たり/外れを、行から数え直した値と封の幅で**門が自分で**判定し、記録の判定・文書の判定の 3 つが一致する。
     **R-4・R-6 は C0 の記録・C1 の記録・P20 の行から再計算して equal**(記録の判定だけを書き換えると赤)。
  3. 文書の分数(``a / b = x.x%``)の全部が算術として合い、記録から作った許可集合に入る。
  4. 同じ字が複数回出る数は ``once()`` で文書の場所を特定し、記録から数えた値と equal で縛る。
  5. 29 件の表の分類を、gold と参照先の字から**門が別に分類し直して**行ごとに equal。
  6. C0・C1 の記録・席の答え・材料の sha256 を**字で留める**(読むだけで、1 文字も直していない)。

engine の一致(ac8c3ff)は**記録の事実**として縛る。いまの作業木に対する生の比較は置かない
(将来 engine を変える封がこの門を赤くしないため)。
"""
import hashlib
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
REC = os.path.join(GEN, "c0_p20_2026-10-20.json")
C0 = os.path.join(GEN, "c0_2026-10-20.json")
C1 = os.path.join(GEN, "c1_2026-10-20.json")
MAT = os.path.join(GEN, "material_2026-10-20.json")
ANS = os.path.join(GEN, "seat_answers")
DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_P20_RESULT_2026-10-20.md")
SEAL_DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_SEAL_2026-10-20.md")
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]
CONSOLIDATED = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100YYUD"]

#: commit 済みの file の sha256。**字で留める**(定数から作らない)。C0 の記録は 8f18b53、C1 の記録は 4e7f490、答えは f0b7140。
SHA = {
    "S100YYN7": "784a40dbcb7e037b719aed0a7c9f500fd8078f90af22692ed5293d9bab1fdc98",
    "S100YYT4": "02aa3cc939ed7fbe85fcd7975ba260c8b551c6a1f4680f4247c593d1bf43ae8a",
    "S100YYT8": "6a6453aad09154dfdd71e84e6f6710280bc30d6c5e2b7540d02a38c7ce3bf4fc",
    "S100YYUD": "04bca508a8dbbca062daff1e3c7f0e7ab9aae6362753252a5b3ccdacb50e8a8a",
    "S100Z0OS": "82d846ff004a0303fde95d1c745bf89f5387b98c60ce16f6f965792ad0610a23",
    "S100Z42X": "a515ace495c1a790dde7b5f8fd12449ee103d02033c318dd0723b0d0a9966831",
    "S100Z4GF": "252fbe466dffb6de48ea1d4517605f5ce060063c53517deb24884dcdc4cc0262",
    "S100Z4J8": "16dc09e69c5a4b99021981758573a5c86ba0c129d735bf384a69f3b1fa932c67",
}
SHA_MAT = "2a33dd21f252de15651168a015147c5206bf92ec676a6f8142a4ecd14f067d37"
SHA_C0 = "30fe3e2bb4a74bdd746d5bd95973e78a757ab06fbc23ffd114ddb509dc7953ad"
SHA_C1 = "4f6141aaeffa87ded81247902d498a6591270bc7036390ea22d8d9bc8683f0d4"

R_C0 = u"C0-2 rows"
R_P20 = u"C0-2 rows(P20)"
K4 = u"**K-4 の再計算**"
PRED = u"**予測 R-1〜R-11**"
CNT = u"**数え直し(P16 は C0 の記録の rows、P20 は今回の rows。同じ関数を当てた)**"
C03 = u"**C0-3 engine を Core-P(P20)の参照先に当てた**"
NONSPEC = u"**P20 で特定しなかった T5 の行(1 件ずつ読む)**"
DECOY = u"**補助(封の外。R-8 の 0 が独立した証拠でないことの確認。判定に使わない)T5 の偶然一致する側を engine に渡した(P20)**"


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def pctv(a, b):
    return None if not b else round(100.0 * a / b, 1)


def frac(a, b):
    u"""文書の数の字。``21 / 50 = 42.0%``。"""
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def inr(x, lo, hi):
    return x is not None and lo <= x <= hi


NUM_RE = re.compile(r"(?<![A-Za-z\d])\d[\d,]*(?:\.\d+)?")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")


def nums(cell):
    return NUM_RE.findall(cell)


def once(doc, pattern):
    u"""正規表現が文書にちょうど 1 回当たる(0 回・2 回以上なら赤)。当たった群の字(複数群は tuple)を返す。"""
    found = re.findall(pattern, doc)
    assert len(found) == 1, (pattern, len(found))
    return found[0]


def S(*xs):
    return tuple(str(x) for x in xs)


def cells_of(line):
    return [x.strip() for x in line.strip("|").split("|")]


def table_rows(doc):
    u"""``| **R-n** | 予測 | 実測 | 判定 |`` の行 -> {n: (予測, 実測, 判定)}。"""
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*R-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = (cells[0], cells[1], cells[2])
    return out


def seal_rows(seal):
    i = seal.index(u"## 追記 2")
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*R-(\d+)\*\* \|(.*)$", seal[i:]):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = cells[0]
    return out


def classify(gold, ptr):
    u"""gold と参照先の字から、科目 -> 期間 -> 枠の順に比べる(スクリプトとは別に、門が書いた分類)。"""
    if ptr is None:
        return u"参照先を出さない"
    gn, gc = gold.split("@", 1)
    pn, pc = ptr.split("@", 1)
    gper, gsep, grest = gc.partition("_")
    pper, psep, prest = pc.partition("_")
    if gn != pn:
        return u"科目が違う"
    if gper != pper:
        return u"期間だけ違う" if grest == prest else u"期間と枠が違う"
    return u"特定" if grest == prest else u"枠(次元)だけ違う"


class Counted(object):
    u"""記録の行から数え直した値(記録の集計欄は読まない)。P16 は C0 の記録の rows、P20 は今回の rows。"""

    def __init__(self, rows):
        self.rows = rows
        self.t5 = [r for r in rows if r[u"型"] == "T5_COINCIDENT"]
        self.t1 = [r for r in rows if r[u"型"] == "T1_VALUE"]
        self.t3 = [r for r in rows if r[u"型"] == "T3_ABSENT"]
        # 特定 = 参照先が gold と同じ(判定の欄を読まず、字から)
        self.ok = {r["id"]: (r[u"腕"]["Core-P"][u"参照先"] is not None and r[u"腕"]["Core-P"][u"参照先"] == r[u"正解"][u"正解"])
                   for r in self.t5}
        self.pointed = [r for r in rows if r[u"腕"]["Core-P"][u"参照先"] is not None]
        self.t5_pointed_wrong = [r for r in self.t5 if r[u"腕"]["Core-P"][u"参照先"] is not None and not self.ok[r["id"]]]
        self.t3_named = [r for r in self.t3 if r[u"腕"]["Core-P"][u"参照先"] is not None]
        self.t1_pass = [r for r in self.t1 if r[u"腕"]["Core-P"][u"言うこと"] == u"確認済み"]
        # (ア) の誤認定: T5 は特定でない参照先、T1 は確認済みと言った件、T3 は名指した件
        self.wrong = len(self.t5_pointed_wrong) + len(self.t1_pass) + len(self.t3_named)
        self.dim = [r for r in self.t5 if "_" in r[u"正解"][u"正解"].split("@", 1)[1]]
        self.nodim = [r for r in self.t5 if r not in self.dim]
        self.gf = [r for r in self.t5 if r["doc"] == "S100Z4GF"]
        self.j8_t3 = [r for r in self.t3 if r["doc"] == "S100Z4J8"]
        self.j8_t1 = [r for r in self.t1 if r["doc"] == "S100Z4J8"]
        self.n_ident = sum(1 for r in self.t5 if self.ok[r["id"]])

    def n_ok(self, rs):
        return sum(1 for r in rs if self.ok[r["id"]])

    def gf_split(self):
        u"""S100Z4GF の T5: (特定, 誤認定, 参照先を出さない)。"""
        a = self.n_ok(self.gf)
        b = sum(1 for r in self.gf if r[u"腕"]["Core-P"][u"参照先"] is not None and not self.ok[r["id"]])
        c = sum(1 for r in self.gf if r[u"腕"]["Core-P"][u"参照先"] is None)
        return a, b, c


class P20ResultGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c0 = jload(C0)
        cls.c1 = jload(C1)
        cls.doc = text(DOC)
        cls.seal = text(SEAL_DOC)
        cls.p20 = Counted(cls.r[R_P20])
        cls.p16 = Counted(cls.c0[R_C0])
        cls.mat = jload(MAT)
        # K-4: C1 の記録の席 A の答え + P20 の行の Core-P(id で対応)
        by20 = {x["id"]: x for x in cls.r[R_P20]}
        cls.k = []
        for x in cls.c1[u"**K-4・K-5 の数**"]["rows"]:
            o = by20[x[u"注入の id"]]
            cls.k.append({"id": x[u"注入の id"], "doc": x["doc"], "gold": x["gold"], "a": bool(x[u"席 A が特定"]),
                          "p16": bool(x[u"Core-P が特定(C0 の記録)"]),
                          "p20": cls.p20.ok[x[u"注入の id"]], "dim": "_" in x["gold"].split("@", 1)[1],
                          "gold_p20": o[u"正解"][u"正解"], "ptr_a": x[u"席 A の参照先"],
                          "ptr_p20": o[u"腕"]["Core-P"][u"参照先"]})

    # ---- 派生
    def kn(self, f=None):
        return [x for x in self.k if f is None or f(x)]

    def verdicts(self):
        u"""封 追記 2 B-3 の幅(字で留める)で R-1〜R-10 を判定する。"""
        p, q, k = self.p20, self.p16, self.k
        v = {}
        ids20 = [x["id"] for x in self.r[R_P20]]
        ids16 = [x["id"] for x in self.c0[R_C0]]
        v[1] = (ids20 == ids16 and len(ids20) == 128 and (len(p.t5), len(p.t1), len(p.t3)) == (50, 38, 40)
                and [x[u"正解"] for x in self.r[R_P20]] == [x[u"正解"] for x in self.c0[R_C0]])
        v[2] = inr(p.n_ok(p.gf), 14, 22) and len(p.gf) == 24
        v[3] = inr(p.n_ok(p.dim), 14, 24) and len(p.dim) == 30
        v[4] = inr(p.n_ident, 27, 37) and len(p.t5) == 50
        wr = pctv(p.wrong, len(p.pointed))
        t3r = pctv(len(p.t3_named), len(p.t3))
        v[5] = inr(wr, 15, 40) and len(p.t1_pass) == 0 and len(p.t1) == 38 and t3r is not None and t3r <= 25
        kc = sum(1 for x in k if x["p20"])
        ka = sum(1 for x in k if x["a"])
        diff = round(pctv(ka, len(k)) - pctv(kc, len(k)), 1)
        v[6] = inr(kc, 11, 16) and len(k) == 20 and ka == 16 and 0 <= diff <= 25
        dim = [x for x in k if x["dim"]]
        v[7] = inr(sum(1 for x in dim if x["p20"]), 6, 10) and len(dim) == 10
        c3 = self.r[C03][u"rows"]
        grounded = sum(1 for x in c3 if x[u"engine の state"] == "GROUNDED")
        v[8] = grounded == 0 and len(c3) > 0
        v[9] = (inr(len([x for x in p.j8_t3 if x[u"腕"]["Core-P"][u"参照先"] is not None]), 0, 3) and len(p.j8_t3) == 5
                and len([x for x in p.j8_t1 if x[u"腕"]["Core-P"][u"言うこと"] == u"確認済み"]) == 0 and len(p.j8_t1) == 5)
        r = self.r
        v[10] = bool(r[u"**対照 R-C1**"][u"当たり"] and r[u"**対照 R-C2**"][u"当たり"] and r[u"**対照 R-C3**"][u"当たり"])
        return v

    # ---- 1. 記録の集計 = 行から数え直した値
    def test_1_record_summaries_equal_recount_from_rows(self):
        r, p, q = self.r, self.p20, self.p16
        cnt = r[CNT]
        for name, c in ((u"P20", p), (u"P16", q)):
            x = cnt[name]
            self.assertEqual((x[u"T5 の件数"], x[u"注入の合計"], x[u"T1"], x[u"T3"]), (len(c.t5), len(c.rows), len(c.t1), len(c.t3)), name)
            for key, (a, b) in (
                    (u"T5 の特定(Core-P)", (c.n_ident, len(c.t5))),
                    (u"Core-P の誤認定率(分母 = 参照先を出した件)", (c.wrong, len(c.pointed))),
                    (u"T1 の通し(Core-P。確認済みと言った)", (len(c.t1_pass), len(c.t1))),
                    (u"T3 の名指し(Core-P)", (len(c.t3_named), len(c.t3))),
                    (u"S100Z4GF の T5", (c.n_ok(c.gf), len(c.gf))),
                    (u"次元つき gold の T5", (c.n_ok(c.dim), len(c.dim))),
                    (u"次元なし gold の T5", (c.n_ok(c.nodim), len(c.nodim))),
                    (u"次元つき gold のうち S100Z4GF 以外", (c.n_ok([z for z in c.dim if z["doc"] != "S100Z4GF"]),
                                                    len([z for z in c.dim if z["doc"] != "S100Z4GF"]))),
                    (u"S100Z4J8 の T3 の名指し", (len([z for z in c.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None]), len(c.j8_t3))),
                    (u"S100Z4J8 の T1 の通し", (len([z for z in c.j8_t1 if z[u"腕"]["Core-P"][u"言うこと"] == u"確認済み"]), len(c.j8_t1)))):
                self.assertEqual((x[key][u"分子"], x[key][u"分母"]), (a, b), (name, key))
            self.assertEqual(x[u"D′ の特定"][u"分子"], sum(1 for z in c.t5 if z[u"腕"][u"D′"][u"参照先"] == z[u"正解"][u"正解"]))
        # (ア) の採点(main() の出力)と数え直しが一致
        tal = r[u"**C0-2 (ア) の main() の出力(P20)**"][u"採点"]["Core-P"]
        self.assertEqual((tal[u"特定率(分母 = T5 の件数)"][u"分子"], tal[u"特定率(分母 = T5 の件数)"][u"分母"]), (p.n_ident, 50))
        self.assertEqual((tal[u"誤認定率(分母 = 参照先を出した件)"][u"分子"], tal[u"誤認定率(分母 = 参照先を出した件)"][u"分母"]),
                         (p.wrong, len(p.pointed)))
        self.assertEqual(tal[u"T1 の通し(値がどこにも無いのに確認済み)"][u"分子"], len(p.t1_pass))
        self.assertEqual(tal[u"T3 の名指し(参照先が無いのに名指した)"][u"分子"], len(p.t3_named))
        self.assertTrue(r[u"Recorder をかぶせた再走が main() の出力と一致(P20)"])
        self.assertTrue(r[u"(ア) の採点と数え直しの照合"][u"全部一致"])
        # C0-3 の集計を行から
        c3 = r[C03]
        rows = c3[u"rows"]
        st = {}
        for x in rows:
            st[x[u"engine の state"]] = st.get(x[u"engine の state"], 0) + 1
        self.assertEqual(c3[u"集計"][u"state の分布"], st)
        self.assertEqual(len(rows), c3[u"集計"][u"engine を通せた行(分母)"])
        self.assertEqual(len(rows), len(p.pointed))
        self.assertEqual(sorted(x["id"] for x in rows), sorted(x["id"] for x in p.pointed))
        self.assertEqual(c3[u"集計"][u"(d) 保留の露出"][u"件数"], sum(1 for x in rows if x[u"露出 (d)(同額の次元兄弟)"]))
        self.assertEqual(c3[u"集計"][u"U 保留の露出"][u"件数"], sum(1 for x in rows if x[u"露出 U(単位の種類が違う)"]))
        self.assertEqual(c3[u"集計"][u"製品の経路の held(GROUNDED だけが対象)"][u"件数"], sum(1 for x in rows if x[u"held(製品の経路)"]))
        by = {}
        for x in rows:
            by[x[u"型"]] = by.get(x[u"型"], 0) + 1
        self.assertEqual(by, {"T5_COINCIDENT": 40, "T1_VALUE": 8, "T3_ABSENT": 7})
        self.assertEqual(sum(1 for x in rows if x[u"型"] == "T5_COINCIDENT" and x[u"材料の単位"] == u"千円"), 40)
        d = r[DECOY]
        self.assertEqual(d[u"集計"][u"state の分布"], {"VALUE_MISMATCH": 50})
        self.assertEqual((d[u"集計"][u"GROUNDED"], d[u"集計"][u"単位込み(円換算)で値が一致する行"]), (0, 0))
        self.assertEqual(len([x for x in d[u"rows"] if x[u"state"] == "VALUE_MISMATCH"]), 50)

    def test_2_inputs_are_the_committed_ones_and_unchanged(self):
        u"""C0 の記録・C1 の記録・材料・席の答えが commit のまま(字で留めた sha256)。記録の前後の sha256 とも一致。"""
        r = self.r
        for d in EIGHT:
            self.assertEqual(sha(os.path.join(ANS, "%s_answer.json" % d)), SHA[d], d)
        self.assertEqual(sha(C0), SHA_C0)
        self.assertEqual(sha(C1), SHA_C1)
        self.assertEqual(sha(MAT), SHA_MAT)
        ins = r[u"入力の sha256(前後で変えていない)"]
        self.assertTrue(ins[u"一致"])
        self.assertEqual(ins[u"前"], ins[u"後"])
        self.assertEqual(ins[u"前"][u"c0_2026-10-20.json"], SHA_C0)
        self.assertEqual(ins[u"前"][u"c1_2026-10-20.json"], SHA_C1)
        self.assertEqual(ins[u"前"][u"material_2026-10-20.json"], SHA_MAT)

    def test_3_r1_same_injections_as_p16(self):
        u"""R-1: 注入の id の並び・gold・改変後の値・件数が C0 の記録(P16)と同じ(門が行から比べる)。"""
        a, b = self.r[R_P20], self.c0[R_C0]
        self.assertEqual([x["id"] for x in a], [x["id"] for x in b])
        self.assertEqual([x[u"型"] for x in a], [x[u"型"] for x in b])
        self.assertEqual([x[u"改変後の値"] for x in a], [x[u"改変後の値"] for x in b])
        self.assertEqual([x[u"正解"] for x in a], [x[u"正解"] for x in b])
        self.assertEqual(len(a), 128)
        r1 = self.r[u"**R-1**"]
        self.assertTrue(r1[u"当たり"])
        self.assertEqual(r1[u"型別 P20"], {"T5_COINCIDENT": 50, "T1_VALUE": 38, "T3_ABSENT": 40})

    def test_4_every_prediction_verdict_agrees_three_ways(self):
        v = self.verdicts()
        rec = {int(p[u"記号"].split("-")[1]): p[u"当たり"] for p in self.r[PRED]}
        rows = table_rows(self.doc)
        self.assertEqual(sorted(rec), list(range(1, 12)))
        self.assertEqual(sorted(rows), list(range(1, 12)))
        for n in range(1, 11):
            word = u"**当たり**" if v[n] else u"**外れ**"
            self.assertEqual(rec[n], v[n], u"R-%d 記録の判定が行から数え直した値と違う" % n)
            self.assertEqual(rows[n][2], word, u"R-%d 文書の判定が数え直した値と違う" % n)
        # R-11 は 3 つ(差分 0 行・覆い・赤)の合成。記録が測った部分(差分 0 行)だけを縛る
        self.assertIsNone(rec[11])
        self.assertTrue(self.r[PRED][10][u"この script が測った部分"])
        self.assertIn(rows[11][2], (u"**当たり**", u"**外れ**"))
        if rows[11][2] == u"**当たり**":
            self.assertTrue(self.r[u"engine の留め"][u"一致"])

    def test_5_k4_and_r6_r7_are_recomputed_from_the_three_records(self):
        u"""R-6・R-7 の判定を、C1 の記録(席 A)・P20 の行(Core-P)・C0 の記録(P16)から**この門が再計算**して、記録・文書と equal。"""
        k, r = self.k, self.r[K4]
        n = len(k)
        self.assertEqual(n, 20)
        self.assertEqual(len({x["id"] for x in k}), n)
        for x in k:
            self.assertEqual(x["gold"], x["gold_p20"], x["id"])          # gold が C1 と P20 で一致
            self.assertEqual(x["a"], x["ptr_a"] == x["gold"], x["id"])    # 席 A の特定は参照先と gold の一致
            self.assertEqual(x["p20"], x["ptr_p20"] == x["gold"], x["id"])
        ka = sum(1 for x in k if x["a"])
        kc20 = sum(1 for x in k if x["p20"])
        kc16 = sum(1 for x in k if x["p16"])
        # P16 の特定は C0 の記録の行から(C1 の記録に写された値と一致)
        c0by = {x["id"]: x for x in self.c0[R_C0]}
        for x in k:
            o = c0by[x["id"]]
            self.assertEqual(x["p16"], o[u"腕"]["Core-P"][u"参照先"] == o[u"正解"][u"正解"], x["id"])
        self.assertEqual((ka, kc16, kc20), (16, 5, 7))
        self.assertEqual((r[u"席 A の特定(C1 の記録。不変)"][u"分子"], r[u"Core-P(P20)の特定"][u"分子"], r[u"Core-P(P16)の特定(C0 の記録)"][u"分子"]),
                         (ka, kc20, kc16))
        diff20 = round(100.0 * ka / n - 100.0 * kc20 / n, 1)
        diff16 = round(100.0 * ka / n - 100.0 * kc16 / n, 1)
        self.assertEqual((r[u"差 席 A − Core-P(P20)(pt)"], r[u"差 席 A − Core-P(P16)(pt)"], r[u"C1 の記録の K-4 の差(照合用)"]),
                         (diff20, diff16, diff16))
        hit6 = 11 <= kc20 <= 16 and 0.0 <= diff20 <= 25.0
        rec6 = [p for p in self.r[PRED] if p[u"記号"] == "R-6"][0]
        self.assertEqual(rec6[u"当たり"], hit6)
        self.assertEqual(rec6[u"実測"][u"差(pt)"], diff20)
        self.assertEqual(table_rows(self.doc)[6][2], u"**当たり**" if hit6 else u"**外れ**")
        self.assertEqual(table_rows(self.doc)[6][1], u"席 A %s・Core-P(P20)%s・差 %+.1f pt" % (frac(ka, n), frac(kc20, n), diff20))
        dim = [x for x in k if x["dim"]]
        d20 = sum(1 for x in dim if x["p20"])
        hit7 = 6 <= d20 <= 10 and len(dim) == 10
        self.assertEqual([p for p in self.r[PRED] if p[u"記号"] == "R-7"][0][u"当たり"], hit7)
        self.assertEqual(table_rows(self.doc)[7][2], u"**当たり**" if hit7 else u"**外れ**")
        # 境界: R-6 の差 +25.0 ちょうどは当たり側、25.1 は外れ側(幅の読み方を門が持っている)
        self.assertTrue(0.0 <= 25.0 <= 25.0 and not (0.0 <= 25.1 <= 25.0))
        # 席 A の答えは C1 の記録のまま(門は C1 の rows の特定を数えただけ)
        self.assertEqual(sum(1 for x in self.c1[u"**K-4・K-5 の数**"]["rows"] if x[u"席 A が特定"]), 16)

    # ---- 3. 分数の全部
    def test_6_every_fraction_is_consistent_and_allowed(self):
        p, q, k = self.p20, self.p16, self.k
        allowed = {(46, 64)}                                           # cd8 の Core-P の特定(封の字)
        for c in (p, q):
            allowed |= {(c.n_ident, len(c.t5)), (c.wrong, len(c.pointed)), (len(c.t1_pass), len(c.t1)),
                        (len(c.t3_named), len(c.t3)), (c.n_ok(c.gf), len(c.gf)), (c.n_ok(c.dim), len(c.dim)),
                        (c.n_ok(c.nodim), len(c.nodim)),
                        (c.n_ok([z for z in c.dim if z["doc"] != "S100Z4GF"]), len([z for z in c.dim if z["doc"] != "S100Z4GF"])),
                        (c.n_ok([z for z in c.t5 if z["doc"] != "S100Z4GF"]), len([z for z in c.t5 if z["doc"] != "S100Z4GF"])),
                        (len([z for z in c.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None]), len(c.j8_t3)),
                        (len([z for z in c.j8_t1 if z[u"腕"]["Core-P"][u"言うこと"] == u"確認済み"]), len(c.j8_t1))}
        for key, sel in ((u"all", lambda x: True), (u"dim", lambda x: x["dim"]), (u"nodim", lambda x: not x["dim"]),
                         (u"gf", lambda x: x["doc"] == "S100Z4GF"), (u"ex", lambda x: x["doc"] != "S100Z4GF")):
            rs = [x for x in k if sel(x)]
            for f in ("a", "p16", "p20"):
                allowed.add((sum(1 for x in rs if x[f]), len(rs)))
        rows = self.r[C03][u"rows"]
        allowed |= {(sum(1 for x in rows if x[u"engine の state"] == "GROUNDED"), len(rows)),
                    (sum(1 for x in rows if x[u"engine の state"] == "VALUE_MISMATCH"), len(rows)),
                    (sum(1 for x in rows if x[u"露出 (d)(同額の次元兄弟)"]), len(rows)),
                    (sum(1 for x in rows if x[u"held(製品の経路)"]), len(rows))}
        c03_16 = self.c0[u"**C0-3 engine を Core-P の参照先に当てた**"][u"rows"]
        allowed |= {(sum(1 for x in c03_16 if x[u"engine の state"] == "GROUNDED"), len(c03_16)),
                    (sum(1 for x in c03_16 if x[u"露出 (d)(同額の次元兄弟)"]), len(c03_16))}
        d = self.r[DECOY][u"rows"]
        allowed.add((len([x for x in d if x[u"state"] == "VALUE_MISMATCH"]), len(d)))
        r2 = self.r[u"**対照 R-C2**"]
        allowed |= {(r2[u"6 書類の rows の件数"], r2[u"6 書類の rows の件数"]),
                    (r2[u"連結の無い 2 書類で P20 と P16 の rows が違った注入"], r2[u"連結の無い 2 書類の注入の件数"])}
        gfs, gfs16 = p.gf_split(), q.gf_split()
        allowed |= {(gfs16[1], 24), (gfs16[2], 24), (gfs[1], 24), (gfs[2], 24)}
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 60)
        for x, y, pc in found:
            xi, yi = int(x.replace(",", "")), int(y.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * xi / yi), pc, u"算術が合わない: %s / %s = %s%%" % (x, y, pc))
            self.assertIn((xi, yi), allowed, u"記録から作れない分数: %s / %s" % (x, y))

    # ---- 4. 予測表の各行
    def test_7_prediction_table_cells_equal_the_record_in_order(self):
        p, q, k = self.p20, self.p16, self.k
        rows, seal = table_rows(self.doc), seal_rows(self.seal)

        def f(x, y):
            return [str(x), str(y), "%.1f" % (100.0 * x / y)]
        c3 = self.r[C03][u"rows"]
        j8n = len([z for z in p.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None])
        dimx = [z for z in p.dim if z["doc"] != "S100Z4GF"]
        ka = sum(1 for x in k if x["a"])
        kc20 = sum(1 for x in k if x["p20"])
        dim = [x for x in k if x["dim"]]
        exp = {
            1: S(len(p.rows), len(p.t5), len(p.t1), len(p.t3)),
            2: f(p.n_ok(p.gf), 24) + f(q.n_ok(q.gf), 24),
            3: f(p.n_ok(p.dim), 30) + f(q.n_ok(q.dim), 30) + [str(len(dimx))] + f(p.n_ok(dimx), len(dimx)),
            4: f(p.n_ident, 50) + f(q.n_ident, 50),
            5: f(p.wrong, len(p.pointed)) + f(len(p.t1_pass), 38) + f(len(p.t3_named), 40),
            6: f(ka, 20) + f(kc20, 20) + ["%.1f" % round(100.0 * ka / 20 - 100.0 * kc20 / 20, 1)],
            7: f(sum(1 for x in dim if x["p20"]), 10) + f(sum(1 for x in dim if x["p16"]), 10),
            8: f(sum(1 for x in c3 if x[u"engine の state"] == "GROUNDED"), len(c3)),
            9: [str(len([z for z in p.rows if z["doc"] == "S100Z4J8" and z[u"型"] == "T5_COINCIDENT"])), str(j8n), "5",
                "%.1f" % (100.0 * j8n / 5), "0", "5", "0.0"],
            10: [],
        }
        for n in range(1, 11):
            self.assertEqual(nums(rows[n][1]), list(exp[n]), u"R-%d 実測欄の数" % n)
        for n in range(1, 12):
            # 予測欄は封の同じ行の字と**同じ**(書き換えると赤)
            self.assertEqual(rows[n][0], seal[n], u"R-%d 予測欄が封の字と違う" % n)
        v = self.verdicts()
        hit = sum(1 for n in range(1, 11) if v[n]) + (1 if rows[11][2] == u"**当たり**" else 0)
        self.assertEqual(once(self.doc, r"\*\*当たり (\d+) / 外れ (\d+)。\*\*"), (str(hit), str(11 - hit)))

    # ---- 5. 29 件の表
    def test_8_the_29_row_table_is_reclassified_by_the_gate(self):
        d, p = self.doc, self.p20
        want = {x["id"]: x for x in p.t5 if not p.ok[x["id"]]}
        self.assertEqual(len(want), 29)
        lines = re.findall(r"(?m)^\| (S100\w+-T5-\d+) \| ([^|]+?) \| `([^`]+)` \| (`[^`]+`|\(なし\)) \| (`[^`]+`|\(なし\)) \|$", d)
        self.assertEqual(len(lines), 29)
        self.assertEqual(sorted(x[0] for x in lines), sorted(want))
        cls = {}
        by16 = {x["id"]: x for x in self.c0[R_C0]}
        for iid, kind, gold, p20, p16 in lines:
            row = want[iid]
            self.assertEqual(gold, row[u"正解"][u"正解"], iid)
            ptr = row[u"腕"]["Core-P"][u"参照先"]
            self.assertEqual(p20, "`%s`" % ptr if ptr else u"(なし)", iid)
            q = by16[iid][u"腕"]["Core-P"][u"参照先"]
            self.assertEqual(p16, "`%s`" % q if q else u"(なし)", iid)
            self.assertEqual(kind, classify(gold, ptr), iid)
            cls[iid] = kind
        # 記録の 29 件(スクリプトが書いた)とも一致
        self.assertEqual(sorted(x["id"] for x in self.r[NONSPEC]), sorted(want))
        by = {}
        for iid, kind in cls.items():
            doc = iid.split("-")[0]
            by[(kind, doc)] = by.get((kind, doc), 0) + 1

        def n(kind, doc=None):
            return sum(v for (kk, dd), v in by.items() if kk == kind and (doc is None or dd == doc))
        self.assertEqual(once(d, r"科目が違う (\d+) 件\(S100YYT4 (\d+)・S100YYUD (\d+)・S100Z4GF (\d+)\)、期間だけ違う (\d+) 件\(すべて S100Z4GF\)、"
                                 r"枠\(次元\)だけ違う (\d+) 件\(S100Z4GF\)、期間と枠が違う (\d+) 件\(S100Z4GF\)、"
                                 r"参照先を出さない (\d+) 件\(S100YYT4 (\d+)・S100Z4GF (\d+)\)。特定 (\d+) 件は S100YYT4 (\d+)・S100Z4GF (\d+)・S100YYUD (\d+)"),
                         S(n(u"科目が違う"), n(u"科目が違う", "S100YYT4"), n(u"科目が違う", "S100YYUD"), n(u"科目が違う", "S100Z4GF"),
                           n(u"期間だけ違う"), n(u"枠(次元)だけ違う"), n(u"期間と枠が違う"),
                           n(u"参照先を出さない"), n(u"参照先を出さない", "S100YYT4"), n(u"参照先を出さない", "S100Z4GF"),
                           p.n_ident,
                           sum(1 for z in p.t5 if z["doc"] == "S100YYT4" and p.ok[z["id"]]),
                           sum(1 for z in p.t5 if z["doc"] == "S100Z4GF" and p.ok[z["id"]]),
                           sum(1 for z in p.t5 if z["doc"] == "S100YYUD" and p.ok[z["id"]])))
        self.assertEqual(n(u"期間だけ違う", "S100Z4GF"), n(u"期間だけ違う"))
        self.assertEqual(n(u"枠(次元)だけ違う", "S100Z4GF"), n(u"枠(次元)だけ違う"))
        self.assertEqual(n(u"期間と枠が違う", "S100Z4GF"), n(u"期間と枠が違う"))
        # S100Z4GF の誤認定 12 件の内訳(科目 3・期間 5・枠 2+2)と、P16/P20 の 24 件の内訳
        gfs, gfs16 = p.gf_split(), self.p16.gf_split()
        self.assertEqual(once(d, r"科目が違う (\d+) 件、期間だけ違う (\d+) 件\(文は"), S(n(u"科目が違う", "S100Z4GF"), n(u"期間だけ違う")))
        self.assertEqual(once(d, r"枠\(次元\)だけ違う (\d+) 件と期間と枠が両方違う (\d+) 件\(セグメント利益の文"),
                         S(n(u"枠(次元)だけ違う"), n(u"期間と枠が違う")))
        self.assertEqual(once(d, r"P16 は参照先を出さない (\d+) 件・誤認定 (\d+) 件・特定 (\d+) 件、P20 は特定 (\d+) 件・誤認定 (\d+) 件・参照先を出さない (\d+) 件"),
                         S(gfs16[2], gfs16[1], gfs16[0], gfs[0], gfs[1], gfs[2]))
        self.assertEqual(gfs[1], n(u"科目が違う", "S100Z4GF") + n(u"期間だけ違う") + n(u"枠(次元)だけ違う") + n(u"期間と枠が違う"))
        # 候補 1 の『合わせて 7 / 24 件』= 期間だけ + 期間と枠
        self.assertEqual(once(d, r"期間と枠が両方違う 2 件\(合わせて (\d+) / (\d+) 件\)"), S(n(u"期間だけ違う") + n(u"期間と枠が違う"), len(p.gf)))
        # 4 件の枠の参照先は同じ 1 つ
        frame4 = [z for z in p.gf if z["id"] in ("S100Z4GF-T5-01", "S100Z4GF-T5-10", "S100Z4GF-T5-13", "S100Z4GF-T5-17")]
        self.assertEqual({z[u"腕"]["Core-P"][u"参照先"] for z in frame4}, {"operatingincome@currentyearduration_nonconsolidatedmember"})
        self.assertEqual(len(frame4), n(u"枠(次元)だけ違う") + n(u"期間と枠が違う"))
        # 期間だけ違う 5 件: gold は前期、Core-P の名指しは当期(門が字で確かめる)
        for iid, kind, gold, p20, p16 in lines:
            if kind == u"期間だけ違う":
                self.assertIn("@prior1yearduration", gold, iid)
                self.assertIn("@currentyearduration", p20, iid)

    # ---- 6. 表・本文中の件数
    def test_9_tables_and_prose_counts_equal_the_record(self):
        p, q, k, d, r = self.p20, self.p16, self.k, self.doc, self.r
        self.assertEqual(once(d, r"の出力、全体 ([\d.]+) 秒\)"), "%.1f" % r[u"所要秒"][u"全体"])
        self.assertEqual(once(d, r"実測 script は 1 回だけ走らせ、repo の記録 `c0_p20_2026-10-20.json` はその完走した 1 本\(全体 ([\d.]+) 秒\)"),
                         "%.1f" % r[u"所要秒"][u"全体"])
        # 先頭 1.
        self.assertEqual(once(d, r"T5 50 件の Core-P の特定は P20 で (\d+) / (\d+) = [\d.]+%\(P16 は (\d+) / (\d+) = [\d.]+%、cd8 は (\d+) / (\d+) = [\d.]+%\)"),
                         S(p.n_ident, 50, q.n_ident, 50, 46, 64))
        self.assertEqual(once(d, r"増えた (\d+) 件は全部 S100Z4GF\((\d+) / (\d+) = [\d.]+% から (\d+) / (\d+) = [\d.]+%\)で、それ以外の (\d+) 件は P16 でも P20 でも (\d+) / (\d+) = [\d.]+% で同じ"),
                         S(p.n_ident - q.n_ident, q.n_ok(q.gf), 24, p.n_ok(p.gf), 24, 26, p.n_ok([z for z in p.t5 if z["doc"] != "S100Z4GF"]), 26))
        self.assertEqual(p.n_ident - q.n_ident, p.n_ok(p.gf) - q.n_ok(q.gf))
        exs = [z for z in p.t5 if z["doc"] != "S100Z4GF"]
        self.assertEqual(len(exs), 26)
        self.assertEqual(p.n_ok(exs), q.n_ok([z for z in q.t5 if z["doc"] != "S100Z4GF"]))
        # R-C2 を行から
        pr = {z["id"]: z for z in r[R_P20]}
        r16 = {z["id"]: z for z in self.c0[R_C0]}
        six = [i for i in pr if pr[i]["doc"] in CONSOLIDATED]
        two = [i for i in pr if pr[i]["doc"] not in CONSOLIDATED]
        self.assertTrue(all(pr[i] == r16[i] for i in six))
        chg = [i for i in two if pr[i] != r16[i]]
        self.assertEqual(once(d, r"連結のある 6 書類の注入 (\d+) 件は P16 と P20 で全行一致\(R-C2\)で、連結の無い 2 書類の注入 (\d+) 件のうち (\d+) / (\d+) = [\d.]+% が変わった"),
                         S(len(six), len(two), len(chg), len(two)))
        self.assertEqual(once(d, r"S100Z4GF が (\d+) 件・S100Z4J8 が (\d+) 件\)"),
                         S(len([i for i in chg if pr[i]["doc"] == "S100Z4GF"]), len([i for i in chg if pr[i]["doc"] == "S100Z4J8"])))
        self.assertEqual(once(d, r"(\d+) / (\d+) = 100.0%\)。補助で C0-3 の行も一致"), S(len(six), len(six)))
        # 先頭 3.
        self.assertEqual(once(d, r"Core-P の誤認定率は (\d+) / (\d+) = [\d.]+%\(P16 は (\d+) / (\d+) = [\d.]+%\)で R-5 の幅\(15〜40%\)を上に出た"),
                         S(p.wrong, len(p.pointed), q.wrong, len(q.pointed)))
        self.assertEqual(once(d, r"T1 の通しは (\d+) / (\d+) = [\d.]+%、T3 の名指しは (\d+) / (\d+) = [\d.]+%\(P16 は (\d+) / (\d+) = [\d.]+%\)。増えた T3 の名指し (\d+) 件は"),
                         S(len(p.t1_pass), len(p.t1), len(p.t3_named), len(p.t3), len(q.t3_named), len(q.t3), len(p.t3_named) - len(q.t3_named)))
        new3 = sorted(z["id"] for z in p.t3_named if z not in q.t3_named)
        self.assertEqual(new3, ["S100Z4GF-T3-01", "S100Z4J8-T3-04"])
        # 先頭 4.
        ka = sum(1 for x in k if x["a"])
        kc16, kc20 = sum(1 for x in k if x["p16"]), sum(1 for x in k if x["p20"])
        self.assertEqual(once(d, r"席 A は (\d+) / (\d+) = [\d.]+%\(C1 の答えのまま\)、Core-P は P16 の (\d+) / (\d+) = [\d.]+% から P20 の (\d+) / (\d+) = [\d.]+% になり、差は \+([\d.]+) pt から \+([\d.]+) pt"),
                         S(ka, 20, kc16, 20, kc20, 20, "%.1f" % (100.0 * ka / 20 - 100.0 * kc16 / 20), "%.1f" % (100.0 * ka / 20 - 100.0 * kc20 / 20)))
        dim = [x for x in k if x["dim"]]
        self.assertEqual(once(d, r"次元つきの 10 行は席 A (\d+) / (\d+) = [\d.]+%、Core-P は P16 の (\d+) / (\d+) = [\d.]+% から P20 の (\d+) / (\d+) = [\d.]+%"),
                         S(sum(1 for x in dim if x["a"]), 10, sum(1 for x in dim if x["p16"]), 10, sum(1 for x in dim if x["p20"]), 10))
        ex = [x for x in k if x["doc"] != "S100Z4GF"]
        self.assertEqual(once(d, r"S100Z4GF を除く (\d+) 行は P16 も P20 も Core-P (\d+) / (\d+) = [\d.]+%・席 A (\d+) / (\d+) = [\d.]+%\(差 \+([\d.]+) pt\)で動いていない"),
                         S(len(ex), sum(1 for x in ex if x["p20"]), len(ex), sum(1 for x in ex if x["a"]), len(ex),
                           "%.1f" % (pctv(sum(1 for x in ex if x["a"]), len(ex)) - pctv(sum(1 for x in ex if x["p20"]), len(ex)))))
        self.assertEqual(sum(1 for x in ex if x["p20"]), sum(1 for x in ex if x["p16"]))
        # 先頭 5. / R-8
        c3 = r[C03][u"rows"]
        by = {}
        for x in c3:
            by[x[u"型"]] = by.get(x[u"型"], 0) + 1
        self.assertEqual(once(d, r"Core-P が名指した注入の行 (\d+) 本\(T5 (\d+)・T1 (\d+)・T3 (\d+)\)は、Core 自身がすべて VALUE_MISMATCH"),
                         S(len(c3), by["T5_COINCIDENT"], by["T1_VALUE"], by["T3_ABSENT"]))
        self.assertTrue(all(x[u"Core の state"] == "VALUE_MISMATCH" for x in c3))
        self.assertEqual(once(d, r"engine も同じ (\d+) 本を VALUE_MISMATCH にした\((\d+) / (\d+) = 100.0%\)"),
                         S(len(c3), sum(1 for x in c3 if x[u"engine の state"] == "VALUE_MISMATCH"), len(c3)))
        self.assertEqual(once(d, r"直接渡した補助確認\(封の外\)も (\d+) / (\d+) = 100.0% が VALUE_MISMATCH で、単位込みで値が一致する行は (\d+)"),
                         S(50, 50, 0))
        self.assertEqual(once(d, r"\(d\) の露出は (\d+) / (\d+) = [\d.]+%\((S100YYT8-T3-04・S100Z42X-T3-02・S100YYT4-T1-04)。state は VALUE_MISMATCH のまま\)、U と P の露出は (\d+)。製品の経路の held は (\d+) / (\d+) = [\d.]+%"),
                         S(sum(1 for x in c3 if x[u"露出 (d)(同額の次元兄弟)"]), len(c3), "S100YYT8-T3-04・S100Z42X-T3-02・S100YYT4-T1-04", 0, 0, len(c3)))
        self.assertEqual(sorted(x["id"] for x in c3 if x[u"露出 (d)(同額の次元兄弟)"]), ["S100YYT4-T1-04", "S100YYT8-T3-04", "S100Z42X-T3-02"])
        self.assertEqual((sum(1 for x in c3 if x[u"露出 U(単位の種類が違う)"]), sum(1 for x in c3 if x[u"露出 P(同額の期間兄弟)"])), (0, 0))
        self.assertEqual(sum(1 for x in c3 if x[u"held(製品の経路)"]), 0)
        # R-5 の節
        c16 = self.c0[u"**C0-3 engine を Core-P の参照先に当てた**"][u"rows"]
        by16 = {}
        for x in c16:
            by16[x[u"型"]] = by16.get(x[u"型"], 0) + 1
        self.assertEqual(once(d, r"分母は Core-P が参照先を出した件 (\d+)\(T5 (\d+)・T1 (\d+)・T3 (\d+)\)で、P16 の (\d+)\(T5 (\d+)・T1 (\d+)・T3 (\d+)\)から (\d+) 増えた"),
                         S(len(p.pointed), by["T5_COINCIDENT"], by["T1_VALUE"], by["T3_ABSENT"], len(q.pointed),
                           by16["T5_COINCIDENT"], by16["T1_VALUE"], by16["T3_ABSENT"], len(p.pointed) - len(q.pointed)))
        self.assertEqual(once(d, r"誤認定 (\d+) 件の内訳は T5 の誤認定 (\d+) 件と T3 の名指し (\d+) 件"),
                         S(p.wrong, len(p.t5_pointed_wrong), len(p.t3_named)))
        self.assertEqual(once(d, r"T1 の (\d+) 件は参照先を名指したが『確認済み』と言った件は (\d+)"), S(by["T1_VALUE"], len(p.t1_pass)))
        self.assertEqual(once(d, r"S100Z4GF の T5 で名指しが (\d+) 件から (\d+) 件に増え、そのうち (\d+) 件が違った"),
                         S(len(q.gf) - q.gf_split()[2], len(p.gf) - p.gf_split()[2], p.gf_split()[1]))
        # K-4 の節の表
        rows = {
            u"同じ T5 の 20 行": (lambda x: True),
            u"次元つき 10 行": (lambda x: x["dim"]),
            u"次元なし 10 行": (lambda x: not x["dim"]),
            u"S100Z4GF の 8 行": (lambda x: x["doc"] == "S100Z4GF"),
            u"S100Z4GF を除く 12 行": (lambda x: x["doc"] != "S100Z4GF"),
        }
        for lab, sel in rows.items():
            rs = [x for x in k if sel(x)]
            line = once(d, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            self.assertEqual(cells_of(line), [lab, frac(sum(1 for x in rs if x["a"]), len(rs)), frac(sum(1 for x in rs if x["p16"]), len(rs)),
                                              frac(sum(1 for x in rs if x["p20"]), len(rs))], lab)
        self.assertEqual(len([x for x in k if x["doc"] == "S100Z4GF"]), 8)
        self.assertEqual(once(d, r"席 A が当てて Core-P\(P20\)が当てなかった行は (\d+)\(S100YYT4 が (\d+)、S100Z4GF が (\d+)\)"),
                         S(len([x for x in k if x["a"] and not x["p20"]]), len([x for x in k if x["a"] and not x["p20"] and x["doc"] == "S100YYT4"]),
                           len([x for x in k if x["a"] and not x["p20"] and x["doc"] == "S100Z4GF"])))
        self.assertEqual(len([x for x in k if x["p20"] and not x["a"]]), 0)
        self.assertEqual(once(d, r"Core-P\(P20\)が当てて席 A が外した行は (\d+)。席 A が外した (\d+) 行"), S(0, len([x for x in k if not x["a"]])))
        for x in k:
            if not x["a"]:
                self.assertEqual(x["ptr_a"], x["ptr_p20"], x["id"])
        # P16 対 P20 の表
        t5_ex = lambda c: [z for z in c.t5 if z["doc"] != "S100Z4GF"]
        dimx = lambda c: [z for z in c.dim if z["doc"] != "S100Z4GF"]
        tbl = [
            (u"T5 50 件の Core-P の特定", frac(q.n_ident, 50), frac(p.n_ident, 50)),
            (u"S100Z4GF の T5 24 件の特定", frac(q.n_ok(q.gf), 24), frac(p.n_ok(p.gf), 24)),
            (u"次元つき gold 30 件の特定", frac(q.n_ok(q.dim), 30), frac(p.n_ok(p.dim), 30)),
            (u"うち S100Z4GF 以外の 6 件", frac(q.n_ok(dimx(q)), 6), frac(p.n_ok(dimx(p)), 6)),
            (u"次元なし gold 20 件の特定", frac(q.n_ok(q.nodim), 20), frac(p.n_ok(p.nodim), 20)),
            (u"Core-P の誤認定率", frac(q.wrong, len(q.pointed)), frac(p.wrong, len(p.pointed))),
            (u"T1 の通し", frac(len(q.t1_pass), 38), frac(len(p.t1_pass), 38)),
            (u"T3 の名指し", frac(len(q.t3_named), 40), frac(len(p.t3_named), 40)),
            (u"S100Z4J8 の T3 の名指し", frac(len([z for z in q.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None]), 5),
             frac(len([z for z in p.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None]), 5)),
            (u"K-4 の 20 行の Core-P の特定", frac(kc16, 20), frac(kc20, 20)),
            (u"次元つき 10 行の Core-P の特定", frac(sum(1 for x in dim if x["p16"]), 10), frac(sum(1 for x in dim if x["p20"]), 10)),
            (u"C0-3 で engine が GROUNDED にした件数", frac(sum(1 for x in c16 if x[u"engine の state"] == "GROUNDED"), len(c16)),
             frac(sum(1 for x in c3 if x[u"engine の state"] == "GROUNDED"), len(c3))),
            (u"C0-3 の (d) 保留の露出", frac(sum(1 for x in c16 if x[u"露出 (d)(同額の次元兄弟)"]), len(c16)),
             frac(sum(1 for x in c3 if x[u"露出 (d)(同額の次元兄弟)"]), len(c3))),
        ]
        for lab, c16s, c20s in tbl:
            line = once(d, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            cl = cells_of(line)
            self.assertEqual((cl[0], cl[1], cl[2]), (lab, c16s, c20s), lab)
        line = once(d, r"(?m)^(\| \(参考\)cd8 の Core-P の特定 \|.*)$")
        self.assertEqual(cells_of(line)[1], frac(46, 64))
        line = once(d, r"(?m)^(\| 席 A − Core-P の差 \|.*)$")
        self.assertEqual(cells_of(line)[1:3], [u"%+.1f pt" % round(100.0 * ka / 20 - 100.0 * kc16 / 20, 1), u"%+.1f pt" % round(100.0 * ka / 20 - 100.0 * kc20 / 20, 1)])
        # C0-1 の claims 数(P16 は C0 の記録・P20 は今回の記録)
        st16 = {x[u"doc"]: x for x in self.c0[u"C0-1(P16。C-2 と (ア) の基準)"][u"書類ごと"]}
        st20 = {x[u"doc"]: x for x in r[u"C0-1(P20 を明示して回した)"][u"書類ごと"]}
        for dd in ("S100Z4GF", "S100Z4J8"):
            line = once(d, r"(?m)^(\| C0-1 の GROUNDED\(%s\) \|.*)$" % dd)
            cl = cells_of(line)
            self.assertEqual(cl[1], u"%d / %d(claims)" % (st16[dd][u"states"].get("GROUNDED", 0), st16[dd][u"claims"]), dd)
            self.assertEqual(cl[2], u"%d / %d(claims)" % (st20[dd][u"states"].get("GROUNDED", 0), st20[dd][u"claims"]), dd)
        # R-9 の節
        self.assertEqual(once(d, r"R-9\*\*: S100Z4J8 は T5 の注入が (\d+)。T3 の名指し (\d+) / (\d+) = [\d.]+% は (S100Z4J8-T3-04)"),
                         S(0, len([z for z in p.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None]), 5, "S100Z4J8-T3-04"))
        self.assertEqual([z["id"] for z in p.j8_t3 if z[u"腕"]["Core-P"][u"参照先"] is not None], ["S100Z4J8-T3-04"])
        # 対照
        rc3 = r[u"**対照 R-C3**"]
        self.assertEqual(once(d, r"cd8 の \(ア\) を P20 で回し\((\d+) 件\)"), str(rc3[u"注入の合計"]))
        self.assertEqual(once(d, r"一意に対になった主張 (\d+) 本\(延べ\)で判定が動いた (\d+)"),
                         S(r[u"補助: C-2(P20。無改変の主張の state が動いたか。封の外)"][u"一意に対になった主張(延べ)"],
                           r[u"補助: C-2(P20。無改変の主張の state が動いたか。封の外)"][u"判定が動いた(延べ)"]))

    def test_10_controls_and_the_zero_usd_facts(self):
        r = self.r
        rc1, rc2, rc3 = r[u"**対照 R-C1**"], r[u"**対照 R-C2**"], r[u"**対照 R-C3**"]
        self.assertTrue(rc1[u"当たり"])
        self.assertEqual(rc1[u"(ア) main() の出力(rows 以外)で違った欄"], [])
        for key, val in rc1.items():
            if key != u"(ア) main() の出力(rows 以外)で違った欄":
                self.assertIs(val, True, key)
        self.assertTrue(rc2[u"当たり"] and rc2[u"6 書類の rows(P20)が P16(C0 の記録)と全行一致"])
        self.assertEqual(rc2[u"連結のある 6 書類"], CONSOLIDATED)
        self.assertTrue(rc3[u"当たり"])
        self.assertEqual((rc3[u"違った欄"], rc3[u"採点が一致"], rc3[u"rows が一致"], rc3[u"profile"]), ([], True, True, "P20"))
        self.assertEqual(r["profile"], "P20")
        self.assertEqual(r[u"環境"][u"設定されている key の数"], 0)
        self.assertEqual(sorted(r[u"環境"][u"4 つの key の名前が設定されているか"]),
                         ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"])
        self.assertFalse(any(r[u"環境"][u"4 つの key の名前が設定されているか"].values()))
        pins = r[u"engine の留め"]
        self.assertTrue(pins[u"一致"])
        self.assertEqual(pins[u"比べた commit"], "ac8c3ff")
        self.assertEqual((pins[u"作業木で sha256 が違う file"], pins[u"作業木に無い file"], pins[u"HEAD にだけ在る file(ac8c3ff に無い)"]), ([], [], []))
        self.assertEqual(pins[u"git diff HEAD --numstat -- core adapters"], "")
        self.assertEqual(pins[u"git status --porcelain -- core adapters"], "")
        # C0-1(P20 を明示)は既定(C0 の記録)と全書類で同じ
        self.assertTrue(all(x[u"claims が既定(C0 の記録)と同じ"] and x[u"states が既定(C0 の記録)と同じ"]
                            for x in r[u"C0-1(P20 を明示して回した)"][u"既定(C0 の記録)と同じか"]))
        d = self.doc
        self.assertIn(u"API key は 4 つとも未設定(0)", d)
        self.assertIn(u"席(LLM API)は 1 回も呼んでいない", d)
        self.assertEqual(once(d, r"ac8c3ff と sha256 が違う file (\d+)、"), str(len(pins[u"作業木で sha256 が違う file"])))

    def test_11_the_document_keeps_its_honesty_clauses(self):
        d = self.doc
        for lit in (u"**封は 1 文字も直していない。**", u"## 手順の正直な記録", u"## 迷った点", u"## 限界",
                    u"**R-8 の 0 は engine の独立した証拠ではない**", u"ただし R-8 の 0 は engine の独立した証拠ではない",
                    u"## 次の改善の封の候補", u"「改善する」とは書かない", u"## 今回新しく分かったこと",
                    u"縛っていない数", u"**外れは外れのまま書く。**", u"scratchpad に向けた予行は走らせていない",
                    u"書類の側か規則の側かは分けていない"):
            self.assertIn(lit, d, lit)
        i = d.index(u"## 今回新しく分かったこと")
        j = d.index(u"## 予測 R-1〜R-11 の照合")
        head = d[i:j]
        self.assertTrue(head.index(u"1. **R-4") < head.index(u"5. **R-8"))
        self.assertIn(u"ただし R-8 の 0 は engine の独立した証拠ではない", head)
        # 『良くなった』『改善した』『持ち直した』と書かない(肯定文として)
        for bad in (u"持ち直した。", u"改善した。", u"良くなった", u"上回った**"):
            self.assertNotIn(bad, d, bad)


if __name__ == "__main__":
    unittest.main()
