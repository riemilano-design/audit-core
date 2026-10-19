# -*- coding: utf-8 -*-
u"""汎化 C 段 C0 の結果文書(docs/XBRL_GENERALITY_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/c0_2026-10-20.json``(``measure/xbrl_gen_c_2026-10-20.py`` の出力)。
封: ``docs/XBRL_GENERALITY_SEAL_2026-10-20.md``(§4 の幅は**ここに字で留める**。封の字と合わせてある)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の中の集計を、同じ記録の**行**から数え直した値と突き合わせる(記録の数だけを書き換えると赤)。
  2. 予測 G-1〜G-13 の当たり/外れを、行から数え直した値と封の幅で**門が自分で**判定し、
     記録の判定・文書の判定の 3 つが一致する(文書の判定だけを書き換えると赤)。
  3. 文書に出てくる数の字(``a / b = x.x%``)を記録から作って、文書に在ることを確かめる(文書の数だけを書き換えると赤)。
  4. G-8(誤りを通した件数)の判定と C1 の条件の判定が、行から数え直した値と文書で一致する。

engine の一致(ac8c3ff)は**記録の事実**として縛る。いまの作業木に対する生の比較は置かない
(将来 engine を変える封がこの門を赤くしないため)。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "c0_2026-10-20.json")
DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_RESULT_2026-10-20.md")
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]

K01 = u"**C0-1 製品の経路(既定の profile)**"
K01P = u"C0-1(P16。C-2 と (ア) の基準)"
K02 = u"**C0-2 (ア) の main() の出力**"
K03 = u"**C0-3 engine を Core-P の参照先に当てた**"
K12 = u"**G-12 率の主張(C0-1 の既定 profile)**"
KC1, KC2, KC3 = u"**対照 C-1**", u"**対照 C-2**", u"**対照 C-3**"
KPRED = u"**予測 G-1〜G-14**"
KCOND = u"**C1 の条件(封 §0)**"
KDECOY = u"**補助(封の外。数を見た後に足した。G の判定に使わない)T5 の偶然一致する側を engine に渡した**"
KT5READ = u"補助: T5 50 件の読み(gold の枠が次元つきか × Core-P の結果。書類別も)"
KP16 = u"補助: P16 で数えた G-2・G-3・G-11(既定 profile と違う書類があるため)"
KSHAPE = u"補助: 率の単位(%/％)の claims の形(C0-1 既定 profile。form × 参照先の本数 × state)"


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def frac(a, b):
    u"""文書の数の字。``13 / 50 = 26.0%``。"""
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def inr(x, lo, hi):
    return x is not None and lo <= x <= hi


def pctv(a, b):
    return None if not b else round(100.0 * a / b, 1)


class Counted(object):
    u"""記録の行から数え直した値(記録の集計欄は読まない)。"""

    def __init__(self, r):
        self.r = r
        rows = r[u"C0-2 rows"]
        self.rows = rows
        self.n_inj = len(rows)
        t5 = [x for x in rows if x[u"型"] == "T5_COINCIDENT"]
        t1 = [x for x in rows if x[u"型"] == "T1_VALUE"]
        t3 = [x for x in rows if x[u"型"] == "T3_ABSENT"]
        self.t5, self.t1, self.t3 = len(t5), len(t1), len(t3)
        self.t5_docs = len({x["doc"] for x in t5})

        def arm(a):
            pointed = [x for x in rows if x[u"腕"][a][u"判定"][u"参照先を出した"]]
            return {
                "ident": sum(1 for x in t5 if x[u"腕"][a][u"判定"][u"特定"]),
                "pointed": len(pointed),
                "wrong": sum(1 for x in pointed if x[u"腕"][a][u"判定"][u"誤認定"]),
                "t1_pass": sum(1 for x in t1 if x[u"腕"][a][u"言うこと"] == u"確認済み"),
                "t3_named": sum(1 for x in t3 if x[u"腕"][a][u"判定"][u"参照先を出した"]),
            }
        self.cp, self.dp = arm("Core-P"), arm(u"D′")
        # C0-3
        c3 = [x for x in r[K03][u"rows"] if x.get(u"engine の state") is not None]
        self._c3 = c3
        self.c3n = len(c3)
        self.c3_states = {}
        for x in c3:
            self.c3_states[x[u"engine の state"]] = self.c3_states.get(x[u"engine の state"], 0) + 1
        self.c3_g = [x[u"id"] for x in c3 if x[u"engine の state"] == "GROUNDED"]
        self.c3_u = sum(1 for x in c3 if x[u"露出 U(単位の種類が違う)"])
        self.c3_d = sum(1 for x in c3 if x[u"露出 (d)(同額の次元兄弟)"])
        self.c3_held = sum(1 for x in c3 if x[u"held(製品の経路)"])
        # C0-1
        per = r[K01][u"書類ごと"]
        self.claims = sum(p[u"claims"] for p in per)
        self.states = {}
        for p in per:
            for k, v in p[u"states"].items():
                self.states[k] = self.states.get(k, 0) + v
        self.per = per
        per16 = r[K01P][u"書類ごと"]
        self.claims16 = sum(p[u"claims"] for p in per16)
        self.states16 = {}
        for p in per16:
            for k, v in p[u"states"].items():
                self.states16[k] = self.states16.get(k, 0) + v
        # G-12
        g12 = r[K12][u"rows"]
        self.g12_rows = len(g12)
        fired = [x for x in g12 if x[u"engine(PP あり)"][u"derived_pointers"]]
        self.g12_fired = len(fired)
        self.g12_g = sum(1 for x in fired if x[u"engine(PP あり)"][u"state"] == "GROUNDED")
        # 補助
        dec = [x for x in r[KDECOY][u"rows"] if x.get(u"state") is not None]
        self.dec_n = len(dec)
        self.dec_vm = sum(1 for x in dec if x[u"state"] == "VALUE_MISMATCH")
        self.dec_g = sum(1 for x in dec if x[u"state"] == "GROUNDED")
        self.dec_unit_match = sum(1 for x in dec if x[u"単位込みで値が一致(許容 = 単位の 1)"])
        # C-2 / C-3
        self.c2_moved = sum(x[u"判定が動いた"] for x in r[KC2][u"rows"])
        self.c2_paired = sum(x[u"一意に対になった主張"] for x in r[KC2][u"rows"])
        nonpp = [x for x in r[K03][u"rows"] if x.get(u"engine の state") is not None and not x[u"PP の行"]]
        self.c3_nonpp_diff = sum(1 for x in nonpp if x[u"engine(PP あり)"] != x[u"engine(PP なし)"])
        pp = [x for x in g12]
        self.c3_pp_diff = sum(1 for x in pp if x[u"engine(PP あり)"] != x[u"engine(PP なし)"])
        # G-1
        fetched_ok = all(p[u"bytes"] > 0 and p[u"zip が開く"] and p[u"facts"] >= 300
                         and p[u"sha256 が取得の記録と一致"] for p in per)
        self.g1 = fetched_ok and [p[u"doc"] for p in per] == EIGHT

    def c3_by_type(self, t):
        return sum(1 for x in self._c3 if x[u"型"] == t)

    def verdicts(self):
        u"""封 §4 の幅(字で留める)で G-1〜G-13 を判定する。"""
        c, r = self, self.r
        v = {}
        v[1] = c.g1
        v[2] = all(60 <= p[u"claims"] <= 250 for p in c.per) and 600 <= c.claims <= 1600
        g, vm = c.states.get("GROUNDED", 0), c.states.get("VALUE_MISMATCH", 0)
        v[3] = inr(pctv(g, c.claims), 35, 60) and inr(pctv(vm, c.claims), 10, 30)
        v[4] = 100 <= c.n_inj <= 180 and c.t5_docs >= 6
        v[5] = inr(pctv(c.cp["ident"], c.t5), 55, 80)
        t3r = pctv(c.cp["t3_named"], c.t3)
        v[6] = (inr(pctv(c.cp["wrong"], c.cp["pointed"]), 15, 35) and c.cp["t1_pass"] == 0
                and t3r is not None and t3r <= 25)
        dw = pctv(c.dp["wrong"], c.dp["pointed"])
        v[7] = c.dp["ident"] == 0 and dw is not None and dw >= 90
        v[8] = len(c.c3_g) == 0 and c.c3n > 0
        v[9] = (pctv(c.c3_states.get("VALUE_MISMATCH", 0), c.c3n) is not None
                and pctv(c.c3_states.get("VALUE_MISMATCH", 0), c.c3n) >= 60
                and pctv(c.c3_states.get("UNPROVABLE", 0), c.c3n) <= 40)
        v[10] = inr(pctv(c.c3_u, c.c3n), 5, 35) and inr(pctv(c.c3_d, c.c3n), 0, 10)
        v[11] = inr(pctv(g + vm, c.claims), 25, 65)
        v[12] = c.g12_fired >= 10 and c.g12_g * 2 >= c.g12_fired
        c1 = r[KC1][u"全欄一致"]
        c2 = c.c2_moved == 0 and c.c2_paired > 0
        c3 = (r[KC3][u"engine の留め"][u"一致"] and c.c3_nonpp_diff == 0 and c.c3_pp_diff > 0)
        v[13] = bool(c1 and c2 and c3)
        return v

    def c1_condition(self):
        c = self
        g5_miss = not self.verdicts()[5]
        g8_miss = len(c.c3_g) != 0
        proven = pctv(c.states.get("GROUNDED", 0) + c.states.get("VALUE_MISMATCH", 0), c.claims)
        u = pctv(c.c3_u, c.c3n)
        return bool(g5_miss or g8_miss or (40.1 - proven >= 15) or (20.0 - u >= 15))


def doc_verdicts(doc):
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*G-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        # 行は ``| **G-n** | 予測 | 実測 | 判定 |``。group(2) は `` 予測 | 実測 | 判定 |`` の後ろ
        out[int(m.group(1))] = cells[2]
    return out


class ResultGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c = Counted(cls.r)
        cls.doc = text(DOC)

    # ---- 1. 記録の集計 = 行から数え直した値
    def test_1_record_summaries_equal_recount_from_rows(self):
        r, c = self.r, self.c
        s = r[K02][u"採点"]
        cp, dp = s["Core-P"], s[u"D′"]
        self.assertEqual((cp[u"特定率(分母 = T5 の件数)"][u"分子"], cp[u"特定率(分母 = T5 の件数)"][u"分母"]),
                         (c.cp["ident"], c.t5))
        self.assertEqual((cp[u"誤認定率(分母 = 参照先を出した件)"][u"分子"], cp[u"誤認定率(分母 = 参照先を出した件)"][u"分母"]),
                         (c.cp["wrong"], c.cp["pointed"]))
        self.assertEqual(cp[u"T1 の通し(値がどこにも無いのに確認済み)"][u"分子"], c.cp["t1_pass"])
        self.assertEqual((cp[u"T3 の名指し(参照先が無いのに名指した)"][u"分子"],
                          cp[u"T3 の名指し(参照先が無いのに名指した)"][u"分母"]), (c.cp["t3_named"], c.t3))
        self.assertEqual((dp[u"特定率(分母 = T5 の件数)"][u"分子"], dp[u"誤認定率(分母 = 参照先を出した件)"][u"分子"],
                          dp[u"誤認定率(分母 = 参照先を出した件)"][u"分母"]),
                         (c.dp["ident"], c.dp["wrong"], c.dp["pointed"]))
        self.assertEqual(r[K02][u"注入の合計"], c.n_inj)
        t = r[K03][u"集計"]
        self.assertEqual(t[u"**GROUNDED(誤りを通した)**"][u"件数"], len(c.c3_g))
        self.assertEqual(t[u"**GROUNDED(誤りを通した)**"][u"ids"], c.c3_g)
        self.assertEqual(t[u"engine を通せた行(分母)"], c.c3n)
        self.assertEqual(t[u"state の分布"], c.c3_states)
        self.assertEqual(t[u"U 保留の露出"][u"件数"], c.c3_u)
        self.assertEqual(t[u"(d) 保留の露出"][u"件数"], c.c3_d)
        self.assertEqual(t[u"製品の経路の held(GROUNDED だけが対象)"][u"件数"], c.c3_held)
        self.assertEqual(r[K01][u"claims の合計"], c.claims)
        self.assertEqual(r[K01][u"state の合計"], c.states)
        self.assertEqual((r[K12][u"行数"], r[K12][u"PP が発火"], r[K12][u"うち GROUNDED"]),
                         (c.g12_rows, c.g12_fired, c.g12_g))
        self.assertEqual(c.n_inj, 128)  # 字で留める: 実測の件数。変わるなら記録が測り直されている

    def test_2_every_prediction_verdict_agrees_three_ways(self):
        v = self.c.verdicts()
        rec = {int(p[u"記号"].split("-")[1]): p[u"当たり"] for p in self.r[KPRED]}
        dv = doc_verdicts(self.doc)
        self.assertEqual(sorted(rec), list(range(1, 15)))
        self.assertEqual(sorted(dv), list(range(1, 15)))
        for n in range(1, 14):
            word = u"**当たり**" if v[n] else u"**外れ**"
            self.assertEqual(rec[n], v[n], u"G-%d 記録の判定が行から数え直した値と違う" % n)
            self.assertEqual(dv[n], word, u"G-%d 文書の判定が数え直した値と違う" % n)
        # G-14 は 3 つ(差分 0 行・過去の門・覆い)の合成。記録が測った部分(差分 0 行)だけを縛る
        self.assertIsNone(rec[14])
        self.assertTrue(self.r[KPRED][13][u"この script が測った部分"])
        self.assertIn(dv[14], (u"**当たり**", u"**外れ**"))
        if dv[14] == u"**当たり**":
            self.assertTrue(self.r[u"engine の留め"][u"一致"])

    def test_3_numbers_in_the_document_come_from_the_record(self):
        c, d = self.c, self.doc
        g, vm = c.states.get("GROUNDED", 0), c.states.get("VALUE_MISMATCH", 0)
        need = [
            frac(g, c.claims), frac(vm, c.claims), frac(g + vm, c.claims),
            frac(c.cp["ident"], c.t5), frac(c.cp["wrong"], c.cp["pointed"]),
            frac(c.cp["t1_pass"], c.t1), frac(c.cp["t3_named"], c.t3),
            frac(c.dp["ident"], c.t5), frac(c.dp["wrong"], c.dp["pointed"]),
            frac(len(c.c3_g), c.c3n), frac(c.c3_states.get("VALUE_MISMATCH", 0), c.c3n),
            frac(c.c3_u, c.c3n), frac(c.c3_d, c.c3n), frac(c.c3_held, c.c3n),
            frac(c.states16.get("GROUNDED", 0), c.claims16),
            frac(c.states16.get("VALUE_MISMATCH", 0), c.claims16),
            frac(c.states16.get("GROUNDED", 0) + c.states16.get("VALUE_MISMATCH", 0), c.claims16),
            frac(c.dec_vm, c.dec_n),
        ]
        for s in need:
            self.assertIn(s, d, s)
        for p in c.per:
            self.assertIn(u"| %s | %d | %d | %d |" % (p[u"doc"], p[u"bytes"], p[u"facts"], p[u"claims"]), d, p[u"doc"])
        for lit in (u"合計 %d" % c.claims, u"注入の合計 %d" % c.n_inj, u"T5 が 1 件以上の書類 %d" % c.t5_docs,
                    u"PP が発火 %d" % c.g12_fired, u"率の主張で参照先 1 本の行 %d" % c.g12_rows,
                    u"単位込み(円換算)で値が一致する行 %d" % c.dec_unit_match,
                    u"判定が動いた(延べ) %d" % c.c2_moved, u"一意に対になった主張(延べ) %d" % c.c2_paired,
                    u"ac8c3ff と sha256 が違う file %d" % len(self.r[KC3][u"engine の留め"][u"作業木で sha256 が違う file"]),
                    self.r[KC3][u"engine の留め"][u"verify_external.py の sha256"][u"作業木"]):
            self.assertIn(lit, d, lit)

    def test_4_g8_and_c1_condition_are_stated_the_way_the_rows_say(self):
        c, d = self.c, self.doc
        n = len(c.c3_g)
        self.assertIn(u"G-8 の誤りを通した件数: %d" % n, d)
        if n > 0:
            self.assertIn(u"## G-8 の 1 件ずつ", d)
            for i in c.c3_g:
                self.assertIn(i, d)
        else:
            self.assertNotIn(u"## G-8 の 1 件ずつ", d)
        # G-8 の 0 が独立した証拠でない読み: Core 自身が全部 VALUE_MISMATCH で止めていた
        core_vm = sum(1 for x in self.r[K03][u"rows"] if x.get(u"Core の state") == "VALUE_MISMATCH"
                      and x.get(u"engine の state") is not None)
        self.assertEqual(core_vm, c.c3n)
        self.assertIn(u"Core 自身の state は %d 本とも VALUE_MISMATCH" % core_vm, d)
        cond = c.c1_condition()
        self.assertEqual(self.r[KCOND][u"**C1 をやる条件に当たったか**"], cond)
        self.assertIn(u"C1 をやる条件に当たったか: %s" % (u"はい" if cond else u"いいえ"), d)

    def test_5_controls_and_the_zero_usd_facts(self):
        r = self.r
        self.assertTrue(r[KC1][u"全欄一致"] and r[KC1][u"違った欄"] == [])
        self.assertEqual(r[KC1][u"注入の合計"], 142)
        self.assertTrue(r[KC3][u"engine の留め"][u"一致"])
        self.assertEqual(r[KC3][u"engine の留め"][u"比べた commit"], "ac8c3ff")
        self.assertEqual(r[u"環境"][u"設定されている key の数"], 0)
        self.assertEqual(sorted(r[u"環境"][u"4 つの key の名前が設定されているか"]),
                         ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"])
        self.assertFalse(any(r[u"環境"][u"4 つの key の名前が設定されているか"].values()))
        self.assertTrue(r[u"Recorder をかぶせた再走が main() の出力と一致"])
        d = self.doc
        self.assertIn(u"API key は 4 つとも未設定(0)", d)
        self.assertIn(u"席(LLM API)は 1 回も呼んでいない", d)

    def test_6_the_document_keeps_its_honesty_clauses(self):
        d = self.doc
        for lit in (u"**封は 1 文字も直していない。**", u"## 手順の正直な記録", u"## 迷った点",
                    u"## 限界", u"封の外", u"G の判定に使っていない",
                    u"G-8 の 0 は engine の守りが効いた証拠ではない"):
            self.assertIn(lit, d, lit)


SEAL_DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_SEAL_2026-10-20.md")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")
NUM_RE = re.compile(r"(?<![A-Za-z\d])\d[\d,]*(?:\.\d+)?")
CD8_FRACS = {(46, 64), (18, 76), (0, 38), (6, 40), (17, 85), (77, 192), (60, 119), (24, 119)}
PNF_T = u"参照先を出さない(POINTER_NOT_FOUND/no_element)"


def nums(cell):
    return NUM_RE.findall(cell)


def table_rows(doc):
    u"""``| **G-n** | 予測 | 実測 | 判定 |`` の行 -> {n: (予測, 実測, 判定)}。"""
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*G-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = (cells[0], cells[1], cells[2])
    return out


def once(doc, pattern):
    u"""正規表現が文書にちょうど 1 回当たる(0 回・2 回以上なら赤)。当たった群の字(複数群は tuple)を返す。"""
    found = re.findall(pattern, doc)
    assert len(found) == 1, (pattern, len(found))
    return found[0]


def every(doc, pattern, n):
    found = re.findall(pattern, doc)
    assert len(found) == n, (pattern, len(found), n)
    return found


def cells_of(line):
    return [x.strip() for x in line.strip("|").split("|")]


class ResultGateEveryNumber(unittest.TestCase):
    u"""``assertIn`` は同じ字が 4 回出る文書では 1 か所の書き換えを見逃す(独立監査 2026-10-20 の REVISE)。
    ここでは**文書の場所ごとに**正規表現で特定し、記録から数えた値と equal で縛る。"""

    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c = Counted(cls.r)
        cls.doc = text(DOC)
        cls.seal = text(SEAL_DOC)

    # ---- (1) 文書の分数の全部
    def test_7_every_fraction_is_consistent_and_allowed(self):
        c, r = self.c, self.r
        g, vm = c.states["GROUNDED"], c.states["VALUE_MISMATCH"]
        g16, vm16 = c.states16["GROUNDED"], c.states16["VALUE_MISMATCH"]
        t5d = r[KT5READ]
        nodim = sum(t5d[u"全体|gold の枠が次元つき=False"].values())
        allowed = set(CD8_FRACS)
        allowed |= {(g, c.claims), (vm, c.claims), (g + vm, c.claims),
                    (c.states["POINTER_NOT_FOUND"], c.claims), (c.states["UNVERIFIABLE"], c.claims),
                    (g16, c.claims16), (vm16, c.claims16), (g16 + vm16, c.claims16),
                    (c.cp["ident"], c.t5), (c.cp["wrong"], c.cp["pointed"]), (c.cp["t1_pass"], c.t1),
                    (c.cp["t3_named"], c.t3), (c.dp["ident"], c.t5), (c.dp["wrong"], c.dp["pointed"]),
                    (len(c.c3_g), c.c3n), (c.c3_states.get("VALUE_MISMATCH", 0), c.c3n),
                    (c.c3_states.get("UNPROVABLE", 0), c.c3n), (c.c3_u, c.c3n), (c.c3_d, c.c3n),
                    (c.c3_held, c.c3n), (c.dec_vm, c.dec_n),
                    (t5d[u"全体|gold の枠が次元つき=False"].get(u"特定", 0), nodim)}
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 60)
        for a, b, pc in found:
            ai, bi = int(a.replace(",", "")), int(b.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * ai / bi), pc, u"算術が合わない: %s / %s = %s%%" % (a, b, pc))
            self.assertIn((ai, bi), allowed, u"記録から作れない分数: %s / %s" % (a, b))

    # ---- (2) 予測表の各行(実測欄は順序つきで、予測欄は封の同じ行と)
    def test_8_prediction_table_cells_equal_the_record_in_order(self):
        c = self.c
        rows, seal_rows = table_rows(self.doc), table_rows(self.seal)
        per = c.per
        g, vm = c.states["GROUNDED"], c.states["VALUE_MISMATCH"]

        def f(a, b):
            return [str(a), str(b), "%.1f" % (100.0 * a / b)]
        exp = {
            1: ["8", "8", format(min(p[u"bytes"] for p in per), ","), format(max(p[u"bytes"] for p in per), ","),
                str(min(p[u"facts"] for p in per)), str(max(p[u"facts"] for p in per))],
            2: [str(min(p[u"claims"] for p in per)), str(max(p[u"claims"] for p in per)), str(c.claims)],
            3: f(g, c.claims) + f(vm, c.claims),
            4: [str(c.n_inj), str(c.t5), str(c.t1), str(c.t3), "1", str(c.t5_docs)],
            5: f(c.cp["ident"], c.t5),
            6: f(c.cp["wrong"], c.cp["pointed"]) + f(c.cp["t1_pass"], c.t1) + f(c.cp["t3_named"], c.t3),
            7: f(c.dp["ident"], c.t5) + f(c.dp["wrong"], c.dp["pointed"]),
            8: f(len(c.c3_g), c.c3n),
            9: f(c.c3_states.get("VALUE_MISMATCH", 0), c.c3n) + f(c.c3_states.get("UNPROVABLE", 0), c.c3n),
            10: f(c.c3_u, c.c3n) + f(c.c3_d, c.c3n) + f(c.c3_held, c.c3n),
            11: f(g + vm, c.claims),
            12: ["1", str(c.g12_rows), str(c.g12_fired), str(c.g12_g)],
            13: ["1", "2", str(c.c2_moved), "3", str(c.c3_nonpp_diff)],
        }
        for n in range(1, 14):
            self.assertEqual(nums(rows[n][1]), exp[n], u"G-%d 実測欄の数" % n)
        for n in range(1, 15):
            sn = iter(nums(re.sub(r"C0-\d", "", seal_rows[n][0].replace("*", ""))))
            dn = nums(rows[n][0])
            self.assertTrue(dn and all(any(x == y for y in sn) for x in dn),
                            u"G-%d 予測欄の数 %s が封の同じ行の数の部分列でない" % (n, dn))
        v = c.verdicts()
        dv = doc_verdicts(self.doc)
        hit = sum(1 for n in range(1, 14) if v[n]) + (1 if dv[14] == u"**当たり**" else 0)
        self.assertEqual(once(self.doc, r"\*\*当たり (\d+) / 外れ (\d+)。\*\*"), (str(hit), str(14 - hit)))

    # ---- (3) 表・見出し・本文中の件数
    def test_9_tables_headings_and_prose_counts_equal_the_record(self):
        c, r, d = self.c, self.r, self.doc
        S = lambda *xs: tuple(str(x) for x in xs)
        for p in c.per:
            line = once(d, r"(?m)^(\| %s \| \d{5,} \|.*)$" % p[u"doc"])
            st = p[u"states"]
            self.assertEqual(cells_of(line),
                             [p[u"doc"], str(p[u"bytes"]), str(p[u"facts"]), str(p[u"claims"]),
                              str(st.get("GROUNDED", 0)), str(st.get("VALUE_MISMATCH", 0)),
                              str(st.get("UNVERIFIABLE", 0)), str(st.get("POINTER_NOT_FOUND", 0))], p[u"doc"])
        self.assertEqual(once(d, r"(?m)^\| 合計 (\d+) \| \| \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$"),
                         S(c.claims, c.claims, c.states["GROUNDED"], c.states["VALUE_MISMATCH"],
                           c.states["UNVERIFIABLE"], c.states["POINTER_NOT_FOUND"]))
        t5d = r[KT5READ]
        for lab, key in ((u"次元なし", u"全体|gold の枠が次元つき=False"),
                         (u"次元つき(`_…Member`)", u"全体|gold の枠が次元つき=True")):
            t = t5d[key]
            line = once(d, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            self.assertEqual(cells_of(line),
                             [lab, str(sum(t.values())), str(t.get(u"特定", 0)), str(t.get(u"誤認定", 0)),
                              str(t.get(PNF_T, 0)), str(t.get(u"対応が付かない", 0))], lab)
        tf, tt = t5d[u"全体|gold の枠が次元つき=False"], t5d[u"全体|gold の枠が次元つき=True"]
        nodim, dim = sum(tf.values()), sum(tt.values())
        z4t = t5d[u"S100Z4GF|gold の枠が次元つき=True"]
        z4 = sum(z4t.values())
        p16 = {p[u"doc"]: p for p in r[K01P][u"書類ごと"]}
        p20 = {p[u"doc"]: p for p in c.per}

        def gg(dd, x):
            return dd[x][u"states"].get("GROUNDED", 0)

        def pn(dd, x):
            return dd[x][u"states"].get("POINTER_NOT_FOUND", 0)
        # 見出し・先頭の節
        self.assertEqual(once(d, r"## G-8 の誤りを通した件数: (\d+)\(分母 (\d+)\)"), S(len(c.c3_g), c.c3n))
        self.assertEqual(once(d, r"### G-5・G-6\(外れ\): Core-P の特定 (\d+) / (\d+) = [\d.]+%・誤認定 (\d+) / (\d+)"),
                         S(c.cp["ident"], c.t5, c.cp["wrong"], c.cp["pointed"]))
        self.assertEqual(once(d, r"Core-P が名指した注入の行 (\d+) 本は、engine に渡す前から"), str(c.c3n))
        self.assertEqual(once(d, r"engine も同じ (\d+) 本を VALUE_MISMATCH"), str(c.c3n))
        self.assertEqual(once(d, r"製品の経路の held は (\d+)\)"), str(c.c3_held))
        self.assertEqual(once(d, r"単位込み\(円換算\)で値が一致する行は (\d+)。"), str(c.dec_unit_match))
        self.assertEqual(once(d, r"読んだ事実: T5 (\d+) 件のうち gold の参照先の枠が次元つき\(`_…Member`\)の (\d+) 件は特定 0 件"
                                 r"\(参照先を出さない (\d+)・誤認定 (\d+)・対応が付かない (\d+)\)、次元なしの (\d+) 件は特定 (\d+) 件"),
                         S(c.t5, dim, tt.get(PNF_T, 0), tt.get(u"誤認定", 0), tt.get(u"対応が付かない", 0),
                           nodim, tf.get(u"特定", 0)))
        self.assertEqual(once(d, r"次元つきの (\d+) 件のうち (\d+) 件は S100Z4GF の gold で、その (\d+) 件の gold の枠は"),
                         S(dim, z4, z4))
        self.assertEqual(once(d, r"GROUNDED は P16 で S100Z4GF (\d+)・S100Z4J8 (\d+)、既定の P20 では (\d+)・(\d+)\)"),
                         S(gg(p16, "S100Z4GF"), gg(p16, "S100Z4J8"), gg(p20, "S100Z4GF"), gg(p20, "S100Z4J8")))
        shape = r[KSHAPE]
        n_ratio = sum(shape.values())
        d2 = shape[u"derived_value|参照先 2 本|GROUNDED"] + shape[u"derived_value|参照先 2 本|VALUE_MISMATCH"]
        d3 = shape[u"derived_value|参照先 3 本|GROUNDED"] + shape[u"derived_value|参照先 3 本|VALUE_MISMATCH"]
        d0 = shape[u"derived_value|参照先 0 本|POINTER_NOT_FOUND"] + shape[u"derived_value|参照先 0 本|UNVERIFIABLE"]
        x0 = shape[u"direct_value|参照先 0 本|POINTER_NOT_FOUND"] + shape[u"direct_value|参照先 0 本|UNVERIFIABLE"]
        x1 = shape[u"direct_value|参照先 1 本|GROUNDED"]
        self.assertEqual(once(d, r"率の単位の claims (\d+) 件のうち、Core が参照先 1 本を名指したのは (\d+) 件"),
                         S(n_ratio, c.g12_rows))
        self.assertEqual(once(d, r"derived_value・参照先 2 本 (\d+) 件、3 本 (\d+) 件\)。engine の PP は"), S(d2, d3))
        self.assertEqual(once(d, r"発火が (\d+) 行に留まった"), str(c.g12_fired))
        self.assertEqual(once(d, r"外れた T5 (\d+) 件のうち (\d+) 件は P16"), S(c.t5, z4))
        self.assertEqual(once(d, r"率の単位\(`%`/`％`\)の claims は (\d+) 件。形\(記録 `補助: 率の単位の claims の形`\)は "
                                 r"derived_value・参照先 2 本 (\d+) 件、参照先 3 本 (\d+) 件、参照先 0 本 (\d+) 件、"
                                 r"direct_value・参照先 0 本 (\d+) 件、direct_value・参照先 1 本 (\d+) 件"),
                         S(n_ratio, d2, d3, d0, x0, x1))
        # G-8 の節
        self.assertEqual(once(d, r"注入の行は (\d+) 本\(T5 (\d+)・T1 (\d+)・T3 (\d+)\)。Core 自身の state は (\d+) 本とも"),
                         S(c.c3n, c.c3_by_type("T5_COINCIDENT"), c.c3_by_type("T1_VALUE"),
                           c.c3_by_type("T3_ABSENT"), c.c3n))
        dec = r[KDECOY][u"集計"]
        self.assertEqual(once(d, r"T5 (\d+) 行すべてについて"), str(dec[u"T5 の行"]))
        self.assertEqual(once(d, r"結果は GROUNDED (\d+)・VALUE_MISMATCH \d+ / \d+ = [\d.]+%・保留 (\d+)。単位込み\(円換算\)で値が一致する行 (\d+)。"),
                         S(c.dec_g, dec[u"保留(held)"], c.dec_unit_match))
        self.assertEqual(once(d, r"この (\d+) 件の注入では測れていない\(cd8"), str(c.n_inj))
        self.assertEqual(once(d, r"上と同じ (\d+) 行"), str(c.c3n))
        # G-4 の節
        cnt = r[K02][u"注入の件数"]

        def t1s(ds):
            return u"・".join(str(cnt[x]["T1_VALUE"][u"作れる site"]) for x in ds)
        self.assertEqual(once(d, r"T5 は S100YYT4 (\d+)・S100Z4GF (\d+)・S100YYUD (\d+)、残り 5 書類は 0。T1 の作れる site も 5 書類は ([\d・]+) と少なく、他の 3 書類は ([\d・]+)。"),
                         tuple([str(cnt[x]["T5_COINCIDENT"][u"作れる site"]) for x in ("S100YYT4", "S100Z4GF", "S100YYUD")]
                               + [t1s(("S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100Z4J8")),
                                  t1s(("S100YYT4", "S100Z4GF", "S100YYUD"))]))
        self.assertEqual(once(d, r"注入の合計 (\d+) は幅"), str(c.n_inj))
        self.assertEqual(once(d, r"### G-4\(外れ\): T5 が作れた書類は (\d+) / 8"), str(c.t5_docs))
        # G-5・G-6 の節
        self.assertEqual(once(d, r"S100Z4GF の (\d+) 件中 (\d+) 件が参照先を出さず、gold の枠は (\d+) 件とも"),
                         S(z4, z4t.get(PNF_T, 0), z4))
        self.assertEqual(once(d, r"参照先を出さなかった (\d+) 件の Core の claim"), str(tt.get(PNF_T, 0)))
        self.assertEqual(once(d, r"次元つきの (\d+) 件で Core-P は特定 0 件"), str(dim))
        self.assertEqual(once(d, r"GROUNDED は S100Z4GF が P20 (\d+)・P16 (\d+)、S100Z4J8 が P20 (\d+)・P16 (\d+)。POINTER_NOT_FOUND は P16 で (\d+) と (\d+)"),
                         S(gg(p20, "S100Z4GF"), gg(p16, "S100Z4GF"), gg(p20, "S100Z4J8"), gg(p16, "S100Z4J8"),
                           pn(p16, "S100Z4GF"), pn(p16, "S100Z4J8")))
        self.assertEqual(once(d, r"誤認定 (\d+) 件の読み: Core-P は"), str(tf.get(u"誤認定", 0)))
        self.assertEqual(once(d, r"G-6 の誤認定 (\d+) 件 = T5 の誤認定 (\d+) \+ T3 の名指し (\d+)。"),
                         S(c.cp["wrong"], c.cp["wrong"] - c.cp["t3_named"], c.cp["t3_named"]))
        self.assertEqual(once(d, r"T1 は (\d+) 本が参照先を名指して"), str(c.c3_by_type("T1_VALUE")))
        # G-10・G-11・G-12 の節
        self.assertEqual(once(d, r"Core-P の参照先 (\d+) 本は、単位の種類が主張と全部一致した"), str(c.c3n))
        self.assertEqual(once(d, r"幅\(25〜65%\)を上に出た。分母は Core の切り出し全部\((\d+) claims\)"), str(c.claims))
        self.assertEqual(once(d, r"### G-12\(外れ\): PP が発火した行 (\d+)"), str(c.g12_fired))
        row0 = r[K12][u"rows"][0]
        self.assertEqual(once(d, r"VALUE_MISMATCH\(recomputed (-?[\d.]+)\)にした"), "%.2f" % row0[u"engine(PP あり)"][u"recomputed"])
        self.assertIsNone(row0[u"符号"])
        self.assertEqual(r[K12][u"rows"][1][u"engine(PP あり)"][u"reason"], "not_current_year")
        self.assertEqual(once(d, r"fact は (\d+)〜(\d+)。"),
                         S(min(p[u"facts"] for p in c.per), max(p[u"facts"] for p in c.per)))
        lo, hi = min(c.per, key=lambda p: p[u"claims"]), max(c.per, key=lambda p: p[u"claims"])
        self.assertEqual(once(d, r"claims は (S\w+) が最小\((\d+)\)、(S\w+) が最大\((\d+)\)"),
                         S(lo[u"doc"], lo[u"claims"], hi[u"doc"], hi[u"claims"]))
        # 対照
        self.assertEqual(once(d, r"違った欄 (\d+)・全欄一致\(注入 (\d+) 件。"), S(len(r[KC1][u"違った欄"]), r[KC1][u"注入の合計"]))
        self.assertEqual(once(d, r"注入 (\d+) 件のそれぞれで、改変前の P16"), str(c.n_inj))
        self.assertEqual(once(d, r"一意に対になった主張\(延べ\) (\d+) のうち 判定が動いた\(延べ\) (\d+)。"), S(c.c2_paired, c.c2_moved))
        self.assertEqual(once(d, r"注入ごとに最大 (\d+)\(内訳は読んでいない\)"), str(r[KC2][u"集計"][u"対にならなかった(原文側)の最大"]))
        pins = r[KC3][u"engine の留め"]
        self.assertEqual(once(d, r"追跡 file (\d+) 本を ac8c3ff と作業木で sha256 比較し、ac8c3ff と sha256 が違う file (\d+)・作業木に無い file (\d+)・HEAD にだけ在る file (\d+)"),
                         S(pins[u"ac8c3ff の core/ と adapters/ の file 数"], len(pins[u"作業木で sha256 が違う file"]),
                           len(pins[u"作業木に無い file"]), len(pins[u"HEAD にだけ在る file(ac8c3ff に無い)"])))
        every(d, r"ac8c3ff と sha256 が違う file 0", 2)
        self.assertEqual(once(d, r"PP の行 (\d+) 本中 (\d+) 本が変わり、PP でない行 (\d+) 本のうち変わった行は (\d+)"),
                         S(r[KC3][u"PP の行(行数)"], r[KC3][u"PP の行で period_pair=False と違った行"],
                           r[KC3][u"PP でない行(行数)"], c.c3_nonpp_diff))
        # C1 の節
        proven = 100.0 * (c.states["GROUNDED"] + c.states["VALUE_MISMATCH"]) / c.claims
        self.assertEqual(once(d, r"落ちていない\(([\d.]+) pt 上がった\)"), "%.1f" % (proven - 40.1))
        self.assertEqual(once(d, r"で ([\d.]+) pt 落ちた\(15 pt 以上\)"), "%.1f" % (20.0 - 100.0 * c.c3_u / c.c3n))
        # 所要秒
        tm = r[u"所要秒"]
        self.assertEqual(once(d, r"全体 ([\d.]+) 秒\)"), "%.1f" % tm[u"全体"])
        self.assertEqual(once(d, r"所要: C0-1 ([\d.]+) 秒・C0-2 `main\(\)` ([\d.]+) 秒・Recorder 再走 \+ C0-3 \+ C-2 ([\d.]+) 秒・C-1 ([\d.]+) 秒・全体 ([\d.]+) 秒。"),
                         tuple("%.1f" % tm[k] for k in (u"C0-1(既定 + P16)秒", u"C0-2 (ア) の main() 秒",
                                                       u"C0-2 再走(Recorder)+ C0-3 + C-2 秒", u"C-1 cd8 再現秒", u"全体")))
        self.assertEqual(once(d, r"held で判定すると U・\(d\) とも (\d+) / (\d+) = ([\d.]+)%"),
                         S(c.c3_held, c.c3n, "0.0"))

    def test_10_overclaim_wording_is_gone(self):
        d = self.doc
        self.assertNotIn(u"どの参照先", d)
        self.assertIn(u"偶然一致する側に向けても一致しない", d)
        self.assertIn(u"縛っていない数", d)
        self.assertNotIn(u"それ以外の数は `tests/measure/test_xbrl_generality_result.py` が記録と突き合わせる", d)


if __name__ == "__main__":
    unittest.main()
