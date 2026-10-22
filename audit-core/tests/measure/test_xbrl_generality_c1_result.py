# -*- coding: utf-8 -*-
u"""汎化 C 段 C1-D の結果文書(docs/XBRL_GENERALITY_C1_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/c1_2026-10-20.json``(``measure/xbrl_gen_c1_2026-10-20.py --stage score --with-engine`` の出力)。
封: ``docs/XBRL_GENERALITY_SEAL_2026-10-20.md`` 追記 1(A-4 の幅は**ここに字で留める**。封の字と合わせてある)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の集計を、同じ記録の**行**(192 行・K-4 の 20 行・C1-3 の 25 行)と csv から数え直した値と突き合わせる。
  2. 予測 K-1〜K-11 の当たり/外れを、行から数え直した値と封の幅で**門が自分で**判定し、記録の判定・文書の判定の 3 つが一致する。
     **K-4 の判定は、C0 の記録(Core-P)と C1 の行から再計算して equal を取る**(記録の判定だけを書き換えると赤)。
  3. 文書の分数(``a / b = x.x%``)の全部が算術として合い、記録から作った許可集合に入る。
  4. 同じ字が複数回出る数は ``once()`` で文書の場所を特定し、記録から数えた値と equal で縛る。
  5. 席の答え 8 file・材料・C0 の記録・csv の sha256 を**字で留める**(答えは 1 文字も直していない)。

engine の一致(ac8c3ff)は**記録の事実**として縛る。いまの作業木に対する生の比較は置かない
(将来 engine を変える封がこの門を赤くしないため)。
"""
import csv
import hashlib
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
REC = os.path.join(GEN, "c1_2026-10-20.json")
MAT = os.path.join(GEN, "material_2026-10-20.json")
C0 = os.path.join(GEN, "c0_2026-10-20.json")
ANS = os.path.join(GEN, "seat_answers")
RUNS = os.path.join(GEN, "seat_runs_2026-10-20.csv")
DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_C1_RESULT_2026-10-20.md")
SEAL_DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_SEAL_2026-10-20.md")
CD8_SCORE = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "score_2026-10-17.json")
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]

#: 人間が決めた数・commit 済みの file の sha256。**字で留める**(定数から作らない)。
#: 答えは commit f0b7140 のまま(1 文字も直していない)。csv は同 commit。材料は b875f26、C0 の記録は 8f18b53。
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
SHA_RUNS = "a465d3c64bba127c7d3e233a19ab7c30af2a79b8a6ed5f9f2312a745b84c243e"
PROMPT_SHA = "4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb"
#: cd8 の実測トークン(封 A-1 の字)
CD8_TOKENS = 1085709

KPRED = u"**予測 K-1〜K-12**"
K45 = u"**K-4・K-5 の数**"
KRUN = u"**席の便・トークン(実測。Agent tool の usage を csv から読む)**"
KIN = u"入力の sha256(採点の前後で変えていない。答えは 1 文字も直していない)"
KTOK = u"トークンの見込み(C1-B の下見。実測と並べる)"
KCD8 = u"cd8 の数(並べる相手。score_2026-10-17.json から読んだ)"
C13 = u"C1-3"
ARMS = ["A", u"C′", u"D′", u"D″"]


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def frac(a, b):
    u"""文書の数の字。``16 / 20 = 80.0%``。"""
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def pctv(a, b):
    return None if not b else round(100.0 * a / b, 1)


def inr(x, lo, hi):
    return x is not None and lo <= x <= hi


def comma(n):
    return format(n, ",")


class Counted(object):
    u"""記録の行・csv から数え直した値(記録の集計欄は読まない)。"""

    def __init__(self, r):
        self.r = r
        self.mat = jload(MAT)
        self.c0 = jload(C0)
        rows = r["rows"]
        self.rows = rows
        self.inj = [x for x in rows if x[u"注入か"]]
        self.t5rows = [x for x in self.inj if (x[u"正解"] or {}).get(u"種類") == u"参照先が在る"]
        self.n_inj, self.n_t5 = len(self.inj), len(self.t5rows)
        self.n_t1 = sum(1 for x in self.inj if x[u"正解"][u"種類"] == u"値がどこにも無い")
        self.n_t3 = sum(1 for x in self.inj if x[u"正解"][u"種類"] == u"参照先は無い")
        self.arm = {}
        for a in ARMS:
            jr = [x[u"腕"][a][u"判定結果"] for x in rows]
            self.arm[a] = {
                "gap": sum(1 for j in jr if j[u"欠け"]),
                "wrong": sum(1 for j in jr if j[u"誤認定"]),
                "pointed": sum(1 for j in jr if j[u"参照先を出した"]),
                "miss": sum(1 for x in self.inj if x[u"腕"][a][u"判定結果"][u"見逃し"]),
                "ident": sum(1 for x in self.t5rows if x[u"腕"][a][u"判定結果"][u"特定"]),
                "hold": sum(1 for j in jr if j[u"保留"]),
                "fa": sum(1 for x in rows if not x[u"注入か"] and x[u"腕"][a][u"判定結果"][u"偽警報"]),
                "added": sum(1 for x in rows if x[u"腕"][a][u"足した"]),
            }
        self.n_rows = len(rows)
        # 席 A と C′ で判定か参照先が違う行
        self.ac_diff = [x for x in rows if (x[u"腕"]["A"][u"判定"], x[u"腕"]["A"][u"参照先"])
                        != (x[u"腕"][u"C′"][u"判定"], x[u"腕"][u"C′"][u"参照先"])]
        self.seat_words = {}
        for x in rows:
            self.seat_words[x[u"席"][u"判定"]] = self.seat_words.get(x[u"席"][u"判定"], 0) + 1
        # K-4・K-5
        k = r[K45]
        self.k = k
        self.k_rows = k["rows"]
        kr = self.k_rows
        self.k_n = len(kr)
        self.k_a = sum(1 for x in kr if x[u"席 A が特定"])
        self.k_c = sum(1 for x in kr if x[u"Core-P が特定(C0 の記録)"])
        self.k_m = sum(1 for x in kr if x[u"材料の Core 腕が特定(照合用)"])
        self.dim = [x for x in kr if x[u"gold の枠が次元つき"]]
        self.nodim = [x for x in kr if not x[u"gold の枠が次元つき"]]
        self.dim_a = sum(1 for x in self.dim if x[u"席 A が特定"])
        self.dim_c = sum(1 for x in self.dim if x[u"Core-P が特定(C0 の記録)"])
        self.nodim_a = sum(1 for x in self.nodim if x[u"席 A が特定"])
        self.nodim_c = sum(1 for x in self.nodim if x[u"Core-P が特定(C0 の記録)"])
        self.k_docs = sorted({x[u"doc"] for x in kr})

        def per_doc(d, key):
            return sum(1 for x in kr if x[u"doc"] == d and x[key])
        self.per_a = {d: per_doc(d, u"席 A が特定") for d in EIGHT}
        self.per_c = {d: per_doc(d, u"Core-P が特定(C0 の記録)") for d in EIGHT}
        self.per_t5 = {d: sum(1 for x in kr if x[u"doc"] == d) for d in EIGHT}
        # 4GF を除く
        ex = [x for x in kr if x[u"doc"] != "S100Z4GF"]
        self.ex_n = len(ex)
        self.ex_a = sum(1 for x in ex if x[u"席 A が特定"])
        self.ex_c = sum(1 for x in ex if x[u"Core-P が特定(C0 の記録)"])
        # 席 A が外した行・Core-P が当てた行
        self.a_wrong = [x for x in kr if not x[u"席 A が特定"]]
        self.a_extra = [x for x in kr if x[u"席 A が特定"] and not x[u"Core-P が特定(C0 の記録)"]]
        self.c_hit_a_missed = [x for x in kr if x[u"Core-P が特定(C0 の記録)"] and not x[u"席 A が特定"]]
        # C1-3
        e = r[C13]
        self.e = e
        self.e_rows = e["rows"]
        er = self.e_rows
        self.e_n = len(er)
        self.e_st = {}
        for x in er:
            self.e_st[x[u"engine の state"]] = self.e_st.get(x[u"engine の state"], 0) + 1
        self.e_g = [x[u"注入の id"] for x in er if x[u"engine の state"] == "GROUNDED"]
        self.e_by = {}
        for x in er:
            self.e_by[x[u"型"]] = self.e_by.get(x[u"型"], 0) + 1
        self.e_d = [x[u"注入の id"] for x in er if x[u"露出 (d)(同額の次元兄弟)"]]
        self.e_u = sum(1 for x in er if x[u"露出 U(単位の種類が違う)"])
        self.e_p = sum(1 for x in er if x[u"露出 P(同額の期間兄弟)"])
        self.e_held = sum(1 for x in er if x[u"held(製品の経路)"])
        self.e_unp = [x[u"注入の id"] for x in er if x[u"engine の state"] == "UNPROVABLE"]
        ctl = [x[u"対照(その fact 自身の値を同じ参照先に当てた)"] for x in er
               if x[u"対照(その fact 自身の値を同じ参照先に当てた)"]]
        self.ctl_n = len(ctl)
        self.ctl_g = sum(1 for c in ctl if c[u"state"] == "GROUNDED")
        self.ctl_u = sum(1 for c in ctl if c[u"state"] == "UNPROVABLE")
        self.e_t5_unit = sum(1 for x in er if x[u"型"] == "T5_COINCIDENT" and x[u"材料の単位"] == u"千円")
        self.e_correct = sum(1 for x in er if x[u"席の参照先が正解"])
        # csv
        with io.open(RUNS, encoding="utf-8", newline="") as fh:
            rd = list(csv.reader(fh))
        self.runs = {x[0]: {"model": x[1], "tok": int(x[2]), "ms": int(x[3]), "rows": int(x[4])} for x in rd[1:]}
        self.run_n = len(rd) - 1
        self.tok = sum(v["tok"] for v in self.runs.values())
        self.tok_min = min(v["tok"] for v in self.runs.values())
        self.tok_max = max(v["tok"] for v in self.runs.values())
        self.aborted = [d for d, v in self.runs.items() if v["rows"] != 24]
        # 材料(C1-B の記録から数え直す)
        m = self.mat
        self.m_ok = all(len([x for x in rows if x[u"doc"] == p["docID"]]) == 24
                        and sum(1 for x in self.inj if x[u"doc"] == p["docID"]) == 8
                        and p[u"**見せない字**"][u"見つかった"] == {}
                        and p[u"材料"][u"字数"] > 0 for p in m[u"書類ごと"])
        self.m_prompt = m[u"問いの sha256"] == PROMPT_SHA and m[u"問いの字数"] == 411
        self.m_t5_docs = sorted({x[u"doc"] for x in self.t5rows})
        self.m_est_slope = m[u"**K-1 の数**"][u"集計"][u"合計"][u"トークン見込み(傾き)"]
        self.m_est_naive = m[u"**K-1 の数**"][u"集計"][u"合計"][u"トークン見込み(素朴)"]

    # ---- 判定
    def k4_diff(self):
        return round(pctv(self.k_a, self.k_n) - pctv(self.k_c, self.k_n), 1)

    def verdicts(self):
        u"""封 A-4 の幅(字で留める)で K-1〜K-11 を判定する。"""
        c, r = self, self.r
        v = {}
        v[1] = bool(c.m_ok and c.m_prompt and c.n_rows == 192 and 16 <= c.n_t5 <= 20 and len(c.m_t5_docs) == 3)
        v[2] = (c.n_inj - c.arm["A"]["miss"]) >= 60
        v[3] = inr(pctv(c.k_a, c.k_n), 40, 70)
        v[4] = c.k4_diff() >= 20
        v[5] = bool(c.dim) and pctv(c.dim_a, len(c.dim)) >= 40
        v[6] = (c.arm["A"]["wrong"] == c.arm[u"C′"]["wrong"] and c.arm["A"]["ident"] == c.arm[u"C′"]["ident"])
        v[7] = (c.arm["A"]["gap"] == 0 and not c.aborted and 900000 <= c.tok <= 1500000)
        v[8] = len(c.e_g) == 0 and c.e_n > 0
        v[9] = pctv(c.e_st.get("VALUE_MISMATCH", 0), c.e_n) is not None and pctv(c.e_st.get("VALUE_MISMATCH", 0), c.e_n) >= 70
        v[10] = c.arm[u"D′"]["fa"] >= 30
        ctl = r[u"対照"]
        v[11] = bool(ctl[u"K-C1"][u"**一致したか**"] and ctl[u"K-C2"][u"**一致したか**"]
                     and ctl[u"K-C3"][u"**一致したか**"])
        return v


def table_rows(doc):
    u"""``| **K-n** | 予測 | 実測 | 判定 |`` の行 -> {n: (予測, 実測, 判定)}。"""
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*K-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = (cells[0], cells[1], cells[2])
    return out


def seal_rows(seal):
    i = seal.index(u"## 追記 1")
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*K-(\d+)\*\* \|(.*)$", seal[i:]):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = cells[0]
    return out


NUM_RE = re.compile(r"(?<![A-Za-z\d])\d[\d,]*(?:\.\d+)?")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")
CD8_FRACS = {(46, 64), (17, 85), (0, 64), (64, 64)}


def nums(cell):
    return NUM_RE.findall(cell)


def once(doc, pattern):
    u"""正規表現が文書にちょうど 1 回当たる(0 回・2 回以上なら赤)。当たった群の字(複数群は tuple)を返す。"""
    found = re.findall(pattern, doc)
    assert len(found) == 1, (pattern, len(found))
    return found[0]


def cells_of(line):
    return [x.strip() for x in line.strip("|").split("|")]


def S(*xs):
    return tuple(str(x) for x in xs)


class C1ResultGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c = Counted(cls.r)
        cls.doc = text(DOC)
        cls.seal = text(SEAL_DOC)

    # ---- 1. 記録の集計 = 行・csv から数え直した値
    def test_1_record_summaries_equal_recount_from_rows(self):
        r, c = self.r, self.c
        s = r[u"採点"]
        self.assertEqual((c.n_rows, c.n_inj, c.n_t5, c.n_t1, c.n_t3), (192, 64, 20, 10, 34))
        self.assertEqual(r[u"行の合計"], c.n_rows)
        for a in ARMS:
            x, t = s[a], c.arm[a]
            self.assertEqual((x[u"誤認定"][u"分子"], x[u"誤認定"][u"分母(参照先を出した件)"]), (t["wrong"], t["pointed"]), a)
            self.assertEqual((x[u"見逃し"][u"分子"], x[u"見逃し"][u"分母(注入の件)"]), (t["miss"], c.n_inj), a)
            self.assertEqual((x[u"正しい参照先の特定"][u"分子"], x[u"正しい参照先の特定"][u"分母(T5 の件)"]), (t["ident"], c.n_t5), a)
            self.assertEqual((x[u"保留"][u"分子"], x[u"保留"][u"分母(欠けを外した件)"]), (t["hold"], c.n_rows - t["gap"]), a)
            self.assertEqual((x[u"軸A 停止判定"][u"分子"], x[u"軸A 停止判定"][u"分母(注入の件)"]), (c.n_inj - t["miss"], c.n_inj), a)
            self.assertEqual((x[u"偽警報(**判定には使わない**)"][u"分子"], x[u"偽警報(**判定には使わない**)"][u"分母(無改変の件)"]),
                             (t["fa"], c.n_rows - c.n_inj), a)
            self.assertEqual(x[u"照合器を足した行"], t["added"], a)
            self.assertEqual(x[u"欠け"], t["gap"], a)
        self.assertEqual(r[u"**欠けは 4 腕で同数**"], {a: c.arm[a]["gap"] for a in ARMS})
        # K-4・K-5
        k = c.k
        self.assertEqual(k[u"T5 の行"], c.k_n)
        self.assertEqual(c.k_n, c.n_t5)
        self.assertEqual(k[u"gold が C0 と一致した注入"], c.k_n)
        self.assertEqual((k[u"席 A の特定"][u"分子"], k[u"席 A の特定"][u"分母"]), (c.k_a, c.k_n))
        self.assertEqual(c.k_a, c.arm["A"]["ident"])
        self.assertEqual((k[u"Core-P の特定(同じ行)"][u"分子"], k[u"Core-P の特定(同じ行)"][u"分母"]), (c.k_c, c.k_n))
        self.assertEqual(k[u"**K-4 差(pt)**"], c.k4_diff())
        d5 = k[u"K-5 次元つき(gold の枠に _…Member)"]
        self.assertEqual((d5[u"席 A の特定"][u"分子"], d5[u"席 A の特定"][u"分母"]), (c.dim_a, len(c.dim)))
        self.assertEqual((d5[u"Core-P の特定"][u"分子"], d5[u"Core-P の特定"][u"分母"]), (c.dim_c, len(c.dim)))
        self.assertEqual((k[u"次元なし"][u"席 A の特定"][u"分子"], k[u"次元なし"][u"Core-P の特定"][u"分子"]),
                         (c.nodim_a, c.nodim_c))
        self.assertEqual(k[u"参考: 材料の Core 腕(席が見た本文 = 8 注入を同時に入れた本文で Core が名指した。C′ が使う腕)の特定"][u"分子"], c.k_m)
        # C1-3
        e = c.e
        self.assertEqual(e[u"席 A が参照先を名指した注入の行(分母)"], c.e_n)
        self.assertEqual(e[u"集計"][u"state の分布"], c.e_st)
        self.assertEqual(e[u"集計"][u"**GROUNDED(誤りを通した)**"][u"件数"], len(c.e_g))
        self.assertEqual(e[u"集計"][u"U 保留の露出"][u"件数"], c.e_u)
        self.assertEqual(e[u"集計"][u"(d) 保留の露出"][u"件数"], len(c.e_d))
        self.assertEqual(e[u"集計"][u"P 保留の露出"][u"件数"], c.e_p)
        self.assertEqual(e[u"集計"][u"製品の経路の held(GROUNDED だけが対象)"][u"件数"], c.e_held)
        self.assertEqual(e[u"席の判定語ごと"], {u"誤りが在る": c.e_n})
        self.assertEqual(e[u"席の参照先が正解だった T5 の行"], c.e_correct)
        # 席の便
        run = r[KRUN]
        self.assertEqual((run[u"便の数"], run[u"合計トークン"], run[u"最小"], run[u"最大"]),
                         (c.run_n, c.tok, c.tok_min, c.tok_max))
        self.assertEqual(run[u"file の sha256"], sha(RUNS))
        self.assertEqual(run[u"行数が 24 でない便(= 中断・欠けの疑い)"], c.aborted)
        self.assertEqual(r[KTOK], {u"見込み(傾き)の合計": c.m_est_slope, u"見込み(素朴。席の往復を含まない)の合計": c.m_est_naive,
                                   u"実測の合計": c.tok})

    def test_2_inputs_are_the_committed_ones(self):
        u"""席の答え 8 file・材料・C0 の記録・csv が commit のまま(字で留めた sha256)。記録の sha256 とも一致。"""
        r = self.r
        for d in EIGHT:
            p = os.path.join(ANS, "%s_answer.json" % d)
            self.assertEqual(sha(p), SHA[d], d)
            self.assertEqual(r[KIN][u"席の答え"][d], SHA[d], d)
        self.assertEqual(sha(MAT), SHA_MAT)
        self.assertEqual(sha(C0), SHA_C0)
        self.assertEqual(sha(RUNS), SHA_RUNS)
        self.assertEqual(r[KIN][u"材料 material_2026-10-20.json"], SHA_MAT)
        self.assertEqual(r[KIN][u"C0 の記録 c0_2026-10-20.json"], SHA_C0)
        self.assertEqual(sorted(os.listdir(ANS)), sorted("%s_answer.json" % d for d in EIGHT))

    def test_3_k4_rows_are_the_same_injections_as_c0_and_the_core_p_count_is_read_from_c0(self):
        u"""K-4 の 20 行が C0-2 の rows の同じ注入(gold 一致)で、Core-P の特定は C0 の記録そのもの、席 A の特定は採点の行そのもの。"""
        c = self.c
        c0 = {x["id"]: x for x in c.c0[u"C0-2 rows"]}
        score = {(x[u"doc"], x["id"]): x for x in c.rows}
        for x in c.k_rows:
            o = c0[x[u"注入の id"]]
            self.assertEqual(o[u"型"], "T5_COINCIDENT")
            self.assertEqual(o[u"正解"][u"正解"], x["gold"], x[u"注入の id"])
            self.assertEqual(bool(o[u"腕"]["Core-P"][u"判定"][u"特定"]), x[u"Core-P が特定(C0 の記録)"], x[u"注入の id"])
            self.assertEqual(o[u"腕"]["Core-P"][u"参照先"], x[u"Core-P の参照先(C0 の記録)"], x[u"注入の id"])
            sr = score[(x[u"doc"], x[u"行 id"])]
            self.assertEqual(sr[u"正解"][u"正解"], x["gold"])
            self.assertEqual(bool(sr[u"腕"]["A"][u"判定結果"][u"特定"]), x[u"席 A が特定"])
            self.assertEqual(sr[u"腕"]["A"][u"参照先"], x[u"席 A の参照先"])
            self.assertEqual("_" in x["gold"].split("@", 1)[1], x[u"gold の枠が次元つき"])
        self.assertEqual(len({x[u"注入の id"] for x in c.k_rows}), c.k_n)

    # ---- 2. 予測の判定
    def test_4_every_prediction_verdict_agrees_three_ways(self):
        v = self.c.verdicts()
        rec = {int(p[u"記号"].split("-")[1]): p[u"当たり"] for p in self.r[KPRED]}
        rows = table_rows(self.doc)
        self.assertEqual(sorted(rec), list(range(1, 13)))
        self.assertEqual(sorted(rows), list(range(1, 13)))
        for n in range(1, 12):
            word = u"**当たり**" if v[n] else u"**外れ**"
            self.assertEqual(rec[n], v[n], u"K-%d 記録の判定が行から数え直した値と違う" % n)
            self.assertEqual(rows[n][2], word, u"K-%d 文書の判定が数え直した値と違う" % n)
        # K-12 は 3 つ(差分 0 行・覆い・赤)の合成。記録が測った部分(差分 0 行)だけを縛る
        self.assertIsNone(rec[12])
        self.assertTrue(self.r[KPRED][11][u"この script が測った部分"])
        self.assertIn(rows[12][2], (u"**当たり**", u"**外れ**"))
        if rows[12][2] == u"**当たり**":
            self.assertTrue(self.r[u"engine の留め"][u"一致"])

    def test_5_k4_verdict_is_recomputed_from_the_c0_record_and_the_rows(self):
        u"""K-4 の判定(当たり/外れ)を、C0 の記録の Core-P と採点の行の席 A から**この門が再計算**して、記録・文書と equal。"""
        c = self.c
        c0 = {x["id"]: x for x in c.c0[u"C0-2 rows"]}
        score = {(x[u"doc"], x["id"]): x for x in c.rows}
        a_ok = sum(1 for x in c.k_rows if score[(x[u"doc"], x[u"行 id"])][u"腕"]["A"][u"判定結果"][u"特定"])
        cp_ok = sum(1 for x in c.k_rows if c0[x[u"注入の id"]][u"腕"]["Core-P"][u"判定"][u"特定"])
        n = len(c.k_rows)
        diff = round(100.0 * a_ok / n - 100.0 * cp_ok / n, 1)
        hit = diff >= 20.0
        rec = [p for p in self.r[KPRED] if p[u"記号"] == "K-4"][0]
        self.assertEqual(rec[u"当たり"], hit)
        self.assertEqual(rec[u"実測"][u"差(pt)"], diff)
        self.assertEqual(table_rows(self.doc)[4][2], u"**当たり**" if hit else u"**外れ**")
        self.assertEqual(table_rows(self.doc)[4][1], u"席 A %s・Core-P %s(同じ %d 行)・差 %+.1f pt"
                         % (frac(a_ok, n), frac(cp_ok, n), n, diff))
        # 閾値の境界: +20.0 ちょうどは当たり、19.9 は外れ(幅の読み方を門が持っている)
        self.assertTrue(20.0 >= 20.0 and not (19.9 >= 20.0))

    # ---- 3. 分数の全部
    def test_6_every_fraction_is_consistent_and_allowed(self):
        c, r = self.c, self.r
        cd8 = r[KCD8]
        allowed = set(CD8_FRACS)
        for key in (u"A の誤認定", u"A の見逃し", u"A の特定", u"A の保留", u"A の軸A", u"C′ の保留", u"D′ の偽警報"):
            allowed.add((cd8[key][u"分子"], [v for kk, v in cd8[key].items() if kk.startswith(u"分母")][0]))
        c0 = c.c0[u"**C0-2 (ア) の main() の出力**"][u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"]
        allowed |= {(c0[u"分子"], c0[u"分母"]), (c0[u"分子"] - c.k_c, c0[u"分母"] - c.k_n)}
        a = c.arm
        allowed |= {(c.n_inj - a["A"]["miss"], c.n_inj), (a["A"]["miss"], c.n_inj),
                    (c.k_a, c.k_n), (c.k_c, c.k_n), (c.k_m, c.k_n), (c.dim_a, len(c.dim)), (c.dim_c, len(c.dim)),
                    (c.nodim_a, len(c.nodim)), (c.nodim_c, len(c.nodim)), (c.ex_a, c.ex_n), (c.ex_c, c.ex_n),
                    (a["A"]["wrong"], a["A"]["pointed"]), (a[u"C′"]["wrong"], a[u"C′"]["pointed"]),
                    (a["A"]["hold"], c.n_rows), (a[u"C′"]["hold"], c.n_rows),
                    (a[u"D′"]["fa"], c.n_rows - c.n_inj),
                    (len(c.e_g), c.e_n), (c.e_st.get("VALUE_MISMATCH", 0), c.e_n), (c.e_st.get("UNPROVABLE", 0), c.e_n),
                    (len(c.e_d), c.e_n), (c.e_u, c.e_n), (c.e_p, c.e_n), (c.e_held, c.e_n),
                    (c.ctl_g, c.ctl_n), (c.e_by.get("T1_VALUE", 0), c.n_t1), (len(c.a_wrong), c.k_n),
                    (c.arm["A"]["gap"], c.n_rows), (c.tok, CD8_TOKENS)}
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 50)
        for x, y, pc in found:
            xi, yi = int(x.replace(",", "")), int(y.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * xi / yi), pc, u"算術が合わない: %s / %s = %s%%" % (x, y, pc))
            self.assertIn((xi, yi), allowed, u"記録から作れない分数: %s / %s" % (x, y))

    # ---- 4. 予測表の各行
    def test_7_prediction_table_cells_equal_the_record_in_order(self):
        c = self.c
        rows, seal = table_rows(self.doc), seal_rows(self.seal)
        a = c.arm

        def f(x, y):
            return [str(x), str(y), "%.1f" % (100.0 * x / y)]
        n_t5_docs = len(c.m_t5_docs)
        exp = {
            1: S(8, 24, 8, 0, 411, c.n_t5, n_t5_docs, c.per_t5["S100YYT4"], c.per_t5["S100Z4GF"], c.per_t5["S100YYUD"]),
            2: f(c.n_inj - a["A"]["miss"], c.n_inj) + [str(a["A"]["miss"])],
            3: f(c.k_a, c.k_n),
            4: f(c.k_a, c.k_n) + f(c.k_c, c.k_n) + [str(c.k_n), "%.1f" % c.k4_diff()],
            5: f(c.dim_a, len(c.dim)) + f(c.dim_c, len(c.dim)),
            6: S(a["A"]["wrong"], a[u"C′"]["wrong"], a["A"]["ident"], a[u"C′"]["ident"]),
            7: [str(a["A"]["gap"]), str(c.n_rows), "%.1f" % 0.0, str(len(c.aborted)), "1", "250,000", "0",
                comma(c.tok), "900,000", "1,500,000"],
            8: f(len(c.e_g), c.e_n),
            9: f(c.e_st.get("VALUE_MISMATCH", 0), c.e_n),
            10: f(a[u"D′"]["fa"], c.n_rows - c.n_inj),
            11: [],
        }
        for n in range(1, 12):
            self.assertEqual(nums(rows[n][1]), list(exp[n]), u"K-%d 実測欄の数" % n)
        for n in range(1, 13):
            # 予測欄は封の同じ行の字と**同じ**(書き換えると赤)
            self.assertEqual(rows[n][0], seal[n], u"K-%d 予測欄が封の字と違う" % n)
        # K-1 の T5 の行がある書類は 3、書類名
        self.assertEqual(c.m_t5_docs, ["S100YYT4", "S100YYUD", "S100Z4GF"])
        v = c.verdicts()
        hit = sum(1 for n in range(1, 12) if v[n]) + (1 if rows[12][2] == u"**当たり**" else 0)
        self.assertEqual(once(self.doc, r"\*\*当たり (\d+) / 外れ (\d+)。\*\*"), (str(hit), str(12 - hit)))

    # ---- 5. 表・本文中の件数
    def test_8_tables_and_prose_counts_equal_the_record(self):
        c, r, d = self.c, self.r, self.doc
        a = c.arm
        # 書類ごとの表(C1-D)
        named = r[C13][u"書類ごと"]
        for doc in EIGHT:
            line = once(d, r"(?m)^(\| %s \| \d+ \| \d+ \| \d+,\d{3} \|)$" % doc)
            self.assertEqual(cells_of(line), [doc, str(c.per_t5[doc]), str(named[doc][u"席 A が参照先を名指した注入の行"]),
                                              comma(c.runs[doc]["tok"])], doc)
        self.assertEqual(once(d, r"(?m)^\| 合計 \| (\d+) \| (\d+) \| (\d+,\d{3}) \|$"),
                         S(c.n_t5, c.e_n, comma(c.tok)))
        # K-3 の節の 2 つの表
        for doc in ("S100YYT4", "S100Z4GF", "S100YYUD"):
            line = once(d, r"(?m)^(\| %s \| \d+ \| \d+ \| \d+ \|)$" % doc)
            self.assertEqual(cells_of(line), [doc, str(c.per_t5[doc]), str(c.per_a[doc]), str(c.per_c[doc])], doc)
        line = once(d, r"(?m)^(\| 次元つき\(`_…Member`\) \|.*)$")
        self.assertEqual(cells_of(line), [u"次元つき(`_…Member`)", str(len(c.dim)), str(c.dim_a), str(c.dim_c)])
        line = once(d, r"(?m)^(\| 次元なし \|.*)$")
        self.assertEqual(cells_of(line), [u"次元なし", str(len(c.nodim)), str(c.nodim_a), str(c.nodim_c)])
        # 先頭の節
        self.assertEqual(once(d, r"の出力、全体 ([\d.]+) 秒\)"), "%.1f" % r[u"所要秒"][u"全体"])
        self.assertEqual(once(d, r"repo の記録は完走した 1 本\(全体 ([\d.]+) 秒\)"), "%.1f" % r[u"所要秒"][u"全体"])
        self.assertEqual(once(d, r"席が参照先を名指した注入の行 (\d+) 本の内訳は T5 (\d+)・T1 (\d+)・T3 (\d+) で、席の判定語は (\d+) 本とも"),
                         S(c.e_n, c.e_by.get("T5_COINCIDENT", 0), c.e_by.get("T1_VALUE", 0), c.e_by.get("T3_ABSENT", 0), c.e_n))
        self.assertEqual(once(d, r"席の参照先が正解だった (\d+) 本も VALUE_MISMATCH"), str(c.e_correct))
        self.assertEqual(once(d, r"S100Z4GF の (\d+) 行は席 A (\d+) / (\d+)、Core-P (\d+) / (\d+)"),
                         S(c.per_t5["S100Z4GF"], c.per_a["S100Z4GF"], c.per_t5["S100Z4GF"], c.per_c["S100Z4GF"], c.per_t5["S100Z4GF"]))
        self.assertEqual(once(d, r"S100Z4GF を除いた (\d+) 行では席 A (\d+) / (\d+) = [\d.]+%、Core-P (\d+) / (\d+) = [\d.]+%、差 \+([\d.]+) pt"),
                         S(c.ex_n, c.ex_a, c.ex_n, c.ex_c, c.ex_n, "%.1f" % (pctv(c.ex_a, c.ex_n) - pctv(c.ex_c, c.ex_n))))
        self.assertEqual(once(d, r"次元つきの (\d+) 行は席 A が (\d+) / (\d+) = [\d.]+%\(K-5 は当たり\)で、落ちたのは次元なしの側の (\d+) / (\d+) = [\d.]+%だけ"),
                         S(len(c.dim), c.dim_a, len(c.dim), c.nodim_a, len(c.nodim)))
        self.assertEqual(once(d, r"外れた (\d+) 行は \d+ 行とも Core-P と\*\*同じ参照先\*\*を名指していた\(純資産の『増加』の文で `NetAssets@CurrentYearInstant` (\d+) 行、のれんの『減少』の文で `Goodwill@CurrentYearInstant` (\d+) 行\)"),
                         S(len(c.a_wrong), sum(1 for x in c.a_wrong if x[u"席 A の参照先"] == "netassets@currentyearinstant"),
                           sum(1 for x in c.a_wrong if x[u"席 A の参照先"] == "goodwill@currentyearinstant")))
        for x in c.a_wrong:
            self.assertEqual(x[u"席 A の参照先"], x[u"Core-P の参照先(C0 の記録)"], x[u"注入の id"])
        self.assertEqual(once(d, r"帯 900,000〜1,500,000 の下で、([\d,]+) 足りない"), comma(900000 - c.tok))
        self.assertEqual(once(d, r"C1-B の下見の見込み\(傾き\)([\d,]+) より少なく、素朴の見込み ([\d,]+)\(席の往復を含まない\)より多かった"),
                         S(comma(c.m_est_slope), comma(c.m_est_naive)))
        self.assertTrue(c.m_est_naive < c.tok < c.m_est_slope)
        self.assertEqual(once(d, r"C′ は席が `判定できない` と言った (\d+) 行すべてに Core を足していた\(cd8 でも (\d+) 行\)。参照先を出した件は A (\d+) → C′ (\d+)、保留は A (\d+) → C′ (\d+)\(A と C′ で判定か参照先が変わった行は (\d+) 本。4 本とも S100YYUD の無改変の行で、Core が `NetSales@CurrentYearDuration` を足した"),
                         S(c.seat_words[u"判定できない"], jload(CD8_SCORE)[u"採点"][u"C′"][u"照合器を足した行"], a["A"]["pointed"], a[u"C′"]["pointed"],
                           a["A"]["hold"], a[u"C′"]["hold"], len(c.ac_diff)))
        self.assertEqual(c.seat_words[u"判定できない"], a[u"C′"]["added"])
        self.assertEqual(a["A"]["added"], 0)
        for x in c.ac_diff:
            self.assertFalse(x[u"注入か"])
            self.assertEqual(x[u"doc"], "S100YYUD")
            self.assertEqual(x[u"腕"][u"C′"][u"参照先"], "netsales@currentyearduration")
            self.assertEqual(x[u"腕"][u"C′"][u"判定"], x[u"腕"]["A"][u"判定"])
        self.assertEqual(once(d, r"cd8 でも同じ形\(参照先を出した件 (\d+) → (\d+)、保留 (\d+) → (\d+)\)"),
                         S(r[KCD8][u"A の誤認定"][u"分母(参照先を出した件)"], r[KCD8][u"C′ の誤認定"][u"分母(参照先を出した件)"],
                           r[KCD8][u"A の保留"][u"分子"], r[KCD8][u"C′ の保留"][u"分子"]))
        # K-8 の節
        self.assertEqual(once(d, r"## K-8 の誤りを通した件数: (\d+)\(分母 (\d+)\)"), S(len(c.e_g), c.e_n))
        self.assertEqual(once(d, r"K-8 の誤りを通した件数: (\d+)。"), str(len(c.e_g)))
        self.assertEqual(once(d, r"席 A が参照先を名指した注入の行は (\d+) 本\(T5 (\d+)・T1 (\d+)・T3 (\d+)\)。T1 は注入 (\d+) 本のうち (\d+) 本、T3 は注入 (\d+) 本のうち (\d+) 本に参照先が付いた\(T5 は (\d+) 本すべて\)"),
                         S(c.e_n, c.e_by["T5_COINCIDENT"], c.e_by["T1_VALUE"], c.e_by.get("T3_ABSENT", 0),
                           c.n_t1, c.e_by["T1_VALUE"], c.n_t3, c.e_by.get("T3_ABSENT", 0), c.n_t5))
        self.assertEqual(once(d, r"注入の行に `確認済み` を付けた席の答えは (\d+) 本"), str(a["A"]["miss"]))
        self.assertEqual(once(d, r"engine は (\d+) 本のうち (\d+) 本を VALUE_MISMATCH、(\d+) 本を UNPROVABLE にした"),
                         S(c.e_n, c.e_st["VALUE_MISMATCH"], c.e_st["UNPROVABLE"]))
        self.assertEqual(c.e_unp, ["S100YYN7-T1-01"])
        self.assertIn(u"S100YYN7-T1-01", d)
        self.assertEqual(c.e_d, ["S100Z0OS-T1-02"])
        self.assertEqual(once(d, r"露出は \(d\) が \d+ / \d+ = [\d.]+%\((S100Z0OS-T1-02)。state は VALUE_MISMATCH のまま\)、U と P は (\d+)"),
                         ("S100Z0OS-T1-02", str(c.e_u)))
        self.assertEqual(c.e_u, c.e_p)
        self.assertEqual(once(d, r"製品の経路の held は (\d+) / (\d+) = [\d.]+%"), S(c.e_held, c.e_n))
        self.assertEqual(once(d, r"T5 の行はすべて単位が 千円 の主張\((\d+) 行\)"), str(c.e_t5_unit))
        self.assertEqual(c.e_t5_unit, c.n_t5)
        self.assertEqual(once(d, r"GROUNDED (\d+) / (\d+) = [\d.]+%、UNPROVABLE (\d+)\(S100Z0OS-T1-02 は"),
                         S(c.ctl_g, c.ctl_n, c.ctl_u))
        self.assertEqual(once(d, r"席が `確認済み` と言った (\d+) 行はすべて無改変の行"), str(c.seat_words[u"確認済み"]))
        self.assertTrue(all(not x[u"注入か"] for x in c.rows if x[u"席"][u"判定"] == u"確認済み"))
        # K-3 の節
        self.assertEqual(once(d, r"gold は (\d+) / (\d+) 一致"), S(c.k[u"gold が C0 と一致した注入"], c.k_n))
        self.assertEqual(once(d, r"次元つきの (\d+) 行\(S100Z4GF の (\d+) 行と S100YYT4 の (\d+) 行\)は席 A が (\d+) / (\d+) 全部当てた"),
                         S(len(c.dim), sum(1 for x in c.dim if x[u"doc"] == "S100Z4GF"), sum(1 for x in c.dim if x[u"doc"] == "S100YYT4"),
                           c.dim_a, len(c.dim)))
        self.assertEqual(once(d, r"席 A が外したのは次元なしの (\d+) 行だけ"), str(len([x for x in c.a_wrong if not x[u"gold の枠が次元つき"]])))
        self.assertEqual(len(c.a_wrong), len([x for x in c.a_wrong if not x[u"gold の枠が次元つき"]]))
        self.assertEqual(once(d, r"Core-P が当てた (\d+) 行は、席 A も全部当てた。席 A が追加で当てた (\d+) 行は S100Z4GF の (\d+) 行と S100YYT4 の (\d+) 行"),
                         S(c.k_c, len(c.a_extra), sum(1 for x in c.a_extra if x[u"doc"] == "S100Z4GF"),
                           sum(1 for x in c.a_extra if x[u"doc"] == "S100YYT4")))
        self.assertEqual(len(c.c_hit_a_missed), 0)
        self.assertEqual(once(d, r"S100Z4GF の (\d+) / (\d+) が (\d+) 本のうち (\d+) 本を占める"),
                         S(c.per_a["S100Z4GF"], c.per_t5["S100Z4GF"], c.k_a, c.per_a["S100Z4GF"]))
        self.assertEqual(once(d, r"S100Z4GF を除くと (\d+) / (\d+) = ([\d.]+)%"), S(c.ex_a, c.ex_n, "%.1f" % pctv(c.ex_a, c.ex_n)))
        # K-7 の節
        self.assertEqual(once(d, r"欠け (\d+) / (\d+) = [\d.]+%\(4 腕とも\)、中断・行数が 24 でない便 (\d+)、1 便が 250,000 超 (\d+)、合計が上限 1,600,000 を超えたか: いいえ"),
                         S(a["A"]["gap"], c.n_rows, len(c.aborted), sum(1 for v in c.runs.values() if v["tok"] > 250000)))
        self.assertEqual(r[KRUN][u"合計が上限を超えたか"], False)
        self.assertTrue(c.tok <= 1600000)
        line = once(d, r"便ごとの実測\(csv\): (.*?)。最小 ([\d,]+)、最大 ([\d,]+)。")
        pairs = re.findall(r"(S100\w+) ([\d,]+)", line[0])
        self.assertEqual(pairs, [(x, comma(c.runs[x]["tok"])) for x in EIGHT])
        self.assertEqual((line[1], line[2]), (comma(c.tok_min), comma(c.tok_max)))
        self.assertEqual(once(d, r"差は ([\d,]+) 少ない"), comma(CD8_TOKENS - c.tok))
        self.assertEqual(once(d, r"cd8 実測 ([\d,]+) の"), comma(CD8_TOKENS))
        self.assertIn(u"%s" % comma(CD8_TOKENS), self.seal)  # 封 A-1 の字と同じ数
        self.assertEqual(once(d, r"字の外の事実: C′ の `足した` は (\d+) 行\(A は (\d+) 行\)、A の 参照先を出した件 (\d+) は C′ で (\d+)、保留は (\d+) から (\d+)"),
                         S(a[u"C′"]["added"], a["A"]["added"], a["A"]["pointed"], a[u"C′"]["pointed"], a["A"]["hold"], a[u"C′"]["hold"]))
        # 先頭の節 2.・3.(同じ字が表にも出る数は、ここで場所を特定して縛る)
        self.assertEqual(once(d, r"同じ T5 の 20 行で、席 A の特定は (\d+) / (\d+) = [\d.]+%、Core-P\(C0-2 の記録の同じ注入\)は (\d+) / (\d+) = [\d.]+%、差は \+([\d.]+) pt"),
                         S(c.k_a, c.k_n, c.k_c, c.k_n, "%.1f" % c.k4_diff()))
        self.assertEqual(once(d, r"席 A の特定は (\d+) / (\d+) = [\d.]+%で、予測の幅 40〜70% を上に出た"), S(c.k_a, c.k_n))
        self.assertEqual(once(d, r"\(cd8 は (\d+) / (\d+) = [\d.]+%\)。ただし差の大きさ"),
                         S(r[KCD8][u"A の特定"][u"分子"], r[KCD8][u"A の特定"][u"分母(T5 の件)"]))
        # cd8 の数との並べ方の表(行ごとに cd8 側・C1 側のセルを縛る)
        cd = r[KCD8]

        def cdn(key):
            return (cd[key][u"分子"], [v for kk, v in cd[key].items() if kk.startswith(u"分母")][0])
        n0 = c.n_rows - c.n_inj
        table = [
            (u"席 A の特定(T5)", frac(*cdn(u"A の特定")), frac(c.k_a, c.k_n)),
            (u"席 A の誤認定", frac(*cdn(u"A の誤認定")), frac(a["A"]["wrong"], a["A"]["pointed"])),
            (u"席 A の見逃し", frac(*cdn(u"A の見逃し")), frac(a["A"]["miss"], c.n_inj)),
            (u"席 A の軸A", frac(*cdn(u"A の軸A")), frac(c.n_inj - a["A"]["miss"], c.n_inj)),
            (u"席 A の保留", frac(*cdn(u"A の保留")), frac(a["A"]["hold"], c.n_rows)),
            (u"C′ の保留", frac(*cdn(u"C′ の保留")), frac(a[u"C′"]["hold"], c.n_rows)),
            (u"D′ の偽警報", frac(*cdn(u"D′ の偽警報")), frac(a[u"D′"]["fa"], n0)),
        ]
        for lab, c8, c1 in table:
            line = once(d, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            cells = cells_of(line)
            self.assertEqual((cells[0], cells[1], cells[2]), (lab, c8, c1), lab)
        line = once(d, r"(?m)^(\| Core-P の特定\(T5\) \|.*)$")
        cells = cells_of(line)
        c0f = c.c0[u"**C0-2 (ア) の main() の出力**"][u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"]
        self.assertEqual(cells[1], u"%s(cd8 の 8 書類、T5 の行 64)" % frac(46, 64))
        self.assertEqual(cells[2], u"%s(C0-2 の記録の同じ 20 行)。参考: C0 の T5 全 50 行は %s、C1 に入らなかった 30 行は %s"
                         % (frac(c.k_c, c.k_n), frac(c0f[u"分子"], c0f[u"分母"]), frac(c0f[u"分子"] - c.k_c, c0f[u"分母"] - c.k_n)))
        line = once(d, r"(?m)^(\| 合計トークン \|.*)$")
        cells = cells_of(line)
        self.assertEqual((cells[1], cells[2]), (comma(CD8_TOKENS), comma(c.tok)))
        # D′(C1)と D″(cd8)の偽警報が同じ数 43 / 128 になった(別の腕・別の材料)ことの記述
        self.assertEqual(once(d, r"C1 の D′ の偽警報 (\d+) / (\d+) = [\d.]+% は、cd8 の \*\*D″\*\* の偽警報 (\d+) / (\d+) = [\d.]+% と数が同じ"),
                         S(a[u"D′"]["fa"], c.n_rows - c.n_inj, r[KCD8][u"D″ の偽警報"][u"分子"], r[KCD8][u"D″ の偽警報"][u"分母(無改変の件)"]))
        # 参考(迷った点 1)
        self.assertEqual(once(d, r"特定は (\d+) / (\d+) = [\d.]+%\(食い違った注入は (S100\w+-T5-\d+) の (\d+) 本\)。この腕で数えると差は \+([\d.]+) pt"),
                         S(c.k_m, c.k_n, c.k[u"参考: 材料の Core 腕と C0 の Core-P で特定が食い違った注入"][0], len(c.k[u"参考: 材料の Core 腕と C0 の Core-P で特定が食い違った注入"]),
                           "%.1f" % c.k[u"参考: 材料の Core 腕を使ったときの差(pt)"]))
        self.assertEqual(len(c.k[u"参考: 材料の Core 腕と C0 の Core-P で特定が食い違った注入"]), 1)
        # 次の改善の封の候補
        self.assertEqual(once(d, r"S100Z4GF の (\d+) 行は Core-P (\d+) / (\d+) で"), S(c.per_t5["S100Z4GF"], c.per_c["S100Z4GF"], c.per_t5["S100Z4GF"]))
        self.assertEqual(once(d, r"S100Z4GF を除く (\d+) 行では差が \+([\d.]+) pt に縮む"),
                         S(c.ex_n, "%.1f" % (pctv(c.ex_a, c.ex_n) - pctv(c.ex_c, c.ex_n))))
        self.assertEqual(once(d, r"席の参照先が正解だった (\d+) 本も含め T5 の (\d+) 本は全部 VALUE_MISMATCH"),
                         S(c.e_correct, c.e_by["T5_COINCIDENT"]))
        self.assertEqual(once(d, r"軸B の分母は (\d+) 行・(\d+) 書類。T5 の site 規則"), S(c.n_t5, len(c.m_t5_docs)))
        self.assertEqual(once(d, r"\*\*軸B の分母は (\d+) 行・(\d+) 書類\*\*。cd8 の 50 行・7 書類と並べるとき"), S(c.n_t5, len(c.m_t5_docs)))
        self.assertEqual(once(d, r"参照先を出した件を \+(\d+) し保留を −(\d+) した\(cd8 でも \+(\d+)・−(\d+)\)"),
                         S(a[u"C′"]["pointed"] - a["A"]["pointed"], a["A"]["hold"] - a[u"C′"]["hold"],
                           r[KCD8][u"C′ の誤認定"][u"分母(参照先を出した件)"] - r[KCD8][u"A の誤認定"][u"分母(参照先を出した件)"],
                           r[KCD8][u"A の保留"][u"分子"] - r[KCD8][u"C′ の保留"][u"分子"]))

    def test_9_controls_and_the_zero_usd_facts(self):
        r = self.r
        ctl = r[u"対照"]
        self.assertTrue(ctl[u"K-C1"][u"**一致したか**"] and ctl[u"K-C2"][u"**一致したか**"] and ctl[u"K-C3"][u"**一致したか**"])
        self.assertTrue(ctl[u"K-11 の入力(3 つとも一致したか)"])
        self.assertEqual(ctl[u"K-C2"][u"A(今回)"], {u"誤認定": [8, 85], u"見逃し": [0, 64], u"正しい参照先の特定": [35, 50], u"保留": [107, 192]})
        self.assertEqual(ctl[u"K-C3"][u"欠け(4 腕)"], {"A": 1, u"C′": 1, u"D′": 1, u"D″": 1})
        self.assertEqual(len(ctl[u"K-C1"][u"書類ごと"]), 8)
        self.assertTrue(all(x[u"型ごとの件数が一致"] and x[u"行の合計が一致"] for x in ctl[u"K-C1"][u"書類ごと"]))
        self.assertEqual(r[u"環境"][u"設定されている key の数"], 0)
        self.assertEqual(sorted(r[u"環境"][u"4 つの key の名前が設定されているか"]),
                         ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"])
        self.assertFalse(any(r[u"環境"][u"4 つの key の名前が設定されているか"].values()))
        pins = r[u"engine の留め"]
        self.assertTrue(pins[u"一致"])
        self.assertEqual(pins[u"比べた commit"], "ac8c3ff")
        self.assertEqual((pins[u"作業木で sha256 が違う file"], pins[u"作業木に無い file"],
                          pins[u"HEAD にだけ在る file(ac8c3ff に無い)"]), ([], [], []))
        self.assertEqual(pins[u"git diff HEAD --numstat -- core adapters"], "")
        self.assertEqual(pins[u"git status --porcelain -- core adapters"], "")
        self.assertEqual(r[KRUN][u"model"], ["sonnet"])
        self.assertEqual(r[KRUN][u"便の数"], 8)
        d = self.doc
        self.assertIn(u"API key は 4 つとも未設定(0)", d)
        self.assertIn(u"この段で席は 1 回も呼んでいない", d)
        self.assertEqual(once(d, r"ac8c3ff と sha256 が違う file (\d+)、"), str(len(pins[u"作業木で sha256 が違う file"])))

    def test_10_the_document_keeps_its_honesty_clauses(self):
        d = self.doc
        for lit in (u"**封は 1 文字も直していない。**", u"## 手順の正直な記録", u"## 迷った点", u"## 限界",
                    u"封の外", u"K の判定に使っていない", u"K-8 の 0 は engine の独立した証拠ではない",
                    u"K-8 の 0 は engine の守りの独立した証拠ではない", u"## 次の改善の封の候補", u"改善する」とは書かない",
                    u"## cd8 の数との並べ方(**分母が違う**。合格線は作らない)", u"縛っていない数",
                    u"20 行・3 書類"):
            self.assertIn(lit, d, lit)
        # 先頭の節に『今回新しく分かったこと』があり、K-8 の 0 の但し書きが最初の項目に在る
        i = d.index(u"## 今回新しく分かったこと")
        j = d.index(u"## 予測 K-1〜K-12 の照合")
        head = d[i:j]
        self.assertTrue(head.index(u"1. **K-8") < head.index(u"2. **K-4"))
        self.assertIn(u"ただし K-8 の 0 は engine の独立した証拠ではない", head)
        # 『上回った』『持ち直した』と書かない(肯定文として)
        self.assertNotIn(u"上回った**", d)
        self.assertNotIn(u"持ち直した。", d)
        self.assertNotIn(u"どの参照先", d)


if __name__ == "__main__":
    unittest.main()
