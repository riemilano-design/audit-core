# -*- coding: utf-8 -*-
u"""名指しの直し(P21)段 1 の結果文書(docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/naming_fix/p21_2026-10-20.json``(``measure/xbrl_naming_fix_2026-10-20.py`` の出力)。
封: ``docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md``(§3 の幅は**ここに字で留める**。封の字と合わせてある)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の集計(採点・K-4・C0-3・無改変 40 書類の集計)を、同じ記録の**行**
     (gen_c の P21 の 128 行・c0_p20 の記録の P20 の 128 行・cd8 の P21 の 142 行・cd8 の P20 の記録の 142 行・
     C1 の記録の 20 行・動いた主張の 1 件ずつ)から**この門が数え直した値**と突き合わせる(記録の集計欄を信じない)。
  2. 予測 N-1〜N-7・N-9 の当たり/外れを、行から数え直した値と封の幅で**門が自分で**判定し、
     記録の判定・文書の判定の 3 つが一致する。
  3. 動いた主張(無改変 40 書類)の型(F1′・F2′・F3b)を、P20/P21 の pointer の字から**門が別に分類し直して**equal。
  4. 文書の分数(``a / b = x.x%``)の全部が算術として合い、記録から作った許可集合に入る。
  5. 入力(c0_p20・C0・C1・cd8 の記録・draw)の sha256 を**字で留める**(読むだけで、1 文字も直していない)。

engine の sha は**記録の事実**として字で留める(測った時点の recipes.py・vocabulary.py)。いまの作業木に対する生の比較は置かない
(将来 engine を変える封がこの門を赤くしないため。過去の門の留めは各門の遷移の字が受け持つ)。
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
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(ROOT, "fixtures", "xbrl", "naming_fix", "p21_2026-10-20.json")
C0P20 = os.path.join(GEN, "c0_p20_2026-10-20.json")
C1 = os.path.join(GEN, "c1_2026-10-20.json")
CD8P20 = os.path.join(CD8, "a_core_vs_grep_P20_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "XBRL_NAMING_FIX_RESULT_2026-10-20.md")
SEAL_DOC = os.path.join(ROOT, "docs", "XBRL_NAMING_FIX_SEAL_2026-10-20.md")

#: commit 済みの入力の sha256。**字で留める**(定数から作らない)。
SHA = {
    u"c0_p20_2026-10-20.json": "d4091508077c0830dbd9f393bcd4b9719702686828d43a058df6ceae2448e051",
    u"c0_2026-10-20.json": "30fe3e2bb4a74bdd746d5bd95973e78a757ab06fbc23ffd114ddb509dc7953ad",
    u"c1_2026-10-20.json": "4f6141aaeffa87ded81247902d498a6591270bc7036390ea22d8d9bc8683f0d4",
    u"draw_2026-10-20.json": "025945ccb39bac8e63d801d871ec55e77442746344ce02af327c6219843a7a8c",
    u"cd8 a_core_vs_grep_P20_2026-10-17.json": "2be67f2a0df6a363530d2ee4f41ce0942104306d24ee9c681c11164bff7198fa",
    u"cd8 draw_2026-10-17.json": "773c58e3f44879f817fb7a3fc1e8f71c5309f6ba7352191e07d8a0008aa16919",
}
#: 測った時点の engine(記録の事実)。16 桁。
ENGINE_AT_MEASURE = {u"adapters/xbrl/recipes.py": "2f692bca1eac3cd3", u"adapters/xbrl/vocabulary.py": "6c6db4c75e571a6c"}

#: 無改変の 40 書類。5 群(字で留める)。
DEV_14 = ["S100YMFV", "S100Z1WR", "S100Z35K", "S100Z37J", "S100Z3BW", "S100Z3CO", "S100Z3HP", "S100Z3JY",
          "S100Z3V1", "S100Z433", "S100Z4B6", "S100Z4DE", "S100Z4PA", "S100Z4Q1"]
UNUSED_2 = ["S100Z39P", "S100Z4N9"]
GROUP_SIZES = {u"gen_c 8": 8, u"(ア)/final8 8": 8, u"cd8 の引いた 8": 8, u"開発 14": 14, u"未使用 2": 2}

NEWLY = ["S100Z4GF-T5-02", "S100Z4GF-T5-07", "S100Z4GF-T5-12", "S100Z4GF-T5-16", "S100Z4GF-T5-23"]
PRED = u"**予測 N-1〜N-12**"
K4 = u"**K-4 の再計算**"
C03 = u"**C0-3 engine を Core-P(P21)の参照先に当てた**"
UNT = u"無改変の 40 書類"
RGC = u"gen_c (ア) rows(P21)"
RCD = u"cd8 (ア) rows(P21)"


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
    u"""文書の数の字。``26 / 50 = 52.0%``。"""
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def inr(x, lo, hi):
    return x is not None and lo <= x <= hi


NUM_RE = re.compile(r"(?<![A-Za-z\d])\d[\d,]*(?:\.\d+)?")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")


def once(doc, pattern):
    u"""正規表現が文書にちょうど 1 回当たる(0 回・2 回以上なら赤)。当たった群の字(複数群は tuple)を返す。"""
    found = re.findall(pattern, doc)
    assert len(found) == 1, (pattern, len(found))
    return found[0]


def S(*xs):
    return tuple(str(x) for x in xs)


def table_rows(doc):
    u"""``| **N-n** | 予測 | 実測 | 判定 |`` の行 -> {n: (予測, 実測, 判定)}。"""
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*N-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = (cells[0], cells[1], cells[2])
    return out


def seal_rows(seal):
    i = seal.index(u"## §3")
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*N-(\d+)\*\* \|(.*)$", seal[i:]):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = cells[0]
    return out


def cp(r):
    return r[u"腕"]["Core-P"]


class Counted(object):
    u"""(ア) の rows から数え直した値(記録の集計欄は読まない)。特定 = 参照先の字が gold と同じ。"""

    def __init__(self, rows):
        self.rows = rows
        self.t5 = [r for r in rows if r[u"型"] == "T5_COINCIDENT"]
        self.t1 = [r for r in rows if r[u"型"] == "T1_VALUE"]
        self.t3 = [r for r in rows if r[u"型"] == "T3_ABSENT"]
        self.ok = {r["id"]: (cp(r)[u"参照先"] is not None and cp(r)[u"参照先"] == r[u"正解"][u"正解"]) for r in self.t5}
        self.n_ident = sum(1 for r in self.t5 if self.ok[r["id"]])
        self.wrong_t5 = [r for r in self.t5 if cp(r)[u"参照先"] is not None and not self.ok[r["id"]]]
        self.t1_pass = [r for r in self.t1 if cp(r)[u"言うこと"] == u"確認済み"]
        self.t3_named = [r for r in self.t3 if cp(r)[u"参照先"] is not None]
        self.pointed = [r for r in rows if cp(r)[u"参照先"] is not None]
        self.ids_ok = sorted(i for i, v in self.ok.items() if v)


def kind_of(m):
    u"""動いた主張の型を、P20/P21 の state と pointer の字から**門が書いた分類**(スクリプトとは別)。"""
    a, b = m[u"P20"], m[u"P21"]
    if a[u"state"] == "VALUE_MISMATCH" and b[u"state"] == "POINTER_NOT_FOUND":
        return u"F2′(名指さず止めた)"
    if len(b[u"pointers"]) == 3 and b[u"pointers"][2] == "formula:a-b" and len(a[u"pointers"]) == 1:
        return u"F3b(残高の対)"
    if len(b[u"pointers"]) == 1 and "@Prior1Year" in b[u"pointers"][0] and a[u"pointers"] != b[u"pointers"]:
        return u"F1′(前期の fact)"
    return u"その他"


class NamingFixResultGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c0p = jload(C0P20)
        cls.c1 = jload(C1)
        cls.cd = jload(CD8P20)
        cls.doc = text(DOC)
        cls.seal = text(SEAL_DOC)
        cls.g21 = Counted(cls.r[RGC])
        cls.g20 = Counted(cls.c0p[u"C0-2 rows(P20)"])
        cls.d21 = Counted(cls.r[RCD])
        cls.d20 = Counted(cls.cd["rows"])
        by21 = {x["id"]: x for x in cls.r[RGC]}
        cls.k = []
        for x in cls.c1[u"**K-4・K-5 の数**"]["rows"]:
            o = by21[x[u"注入の id"]]
            cls.k.append({"id": x[u"注入の id"], "doc": x["doc"], "gold": x["gold"], "a": bool(x[u"席 A が特定"]),
                          "p20": cls.g20.ok[x[u"注入の id"]], "p21": cls.g21.ok[x[u"注入の id"]],
                          "dim": "_" in x["gold"].split("@", 1)[1], "gold21": o[u"正解"][u"正解"],
                          "ptr_a": x[u"席 A の参照先"], "ptr21": cp(o)[u"参照先"]})
        cls.moved = cls.r[UNT][u"動いた行(1 件ずつ)"]

    # ---- 派生
    def verdicts(self):
        u"""封 §3 の幅(字で留める)で N-1〜N-7・N-9 を判定する。"""
        a, b, c, d = self.g21, self.g20, self.d21, self.d20
        k = self.k
        v = {}
        v[1] = (a.n_ident == 26 and len(a.t5) == 50 and b.n_ident == 21 and len(a.wrong_t5) == 3 and len(b.wrong_t5) == 19
                and sorted(set(a.ids_ok) - set(b.ids_ok)) == NEWLY and sorted(set(b.ids_ok) - set(a.ids_ok)) == [])
        v[2] = c.n_ident == 46 and len(c.t5) == 64 and d.n_ident == 46 and len(d.wrong_t5) == 12 and len(c.wrong_t5) == 6
        v[3] = (len(a.t1_pass) == 0 and len(a.t1) == 38 and len(c.t1_pass) == 0 and len(c.t1) == 38
                and len(a.t3_named) == 7 and len(a.t3) == 40 and len(c.t3_named) == 6 and len(c.t3) == 40)
        n_moved = len(self.moved)
        g_moved = sum(1 for m in self.moved if m[u"P20"][u"state"] == "GROUNDED" or m[u"P21"][u"state"] == "GROUNDED")
        only = all(m[u"P20"][u"state"] in ("VALUE_MISMATCH", "POINTER_NOT_FOUND") and m[u"P21"][u"state"] in ("VALUE_MISMATCH", "POINTER_NOT_FOUND")
                   for m in self.moved)
        v[4] = g_moved == 0 and only and inr(n_moved, 120, 220)
        # N-5: gen_c 8 書類の state の合計は P20 で 443/194/165/111。VM -> PNF に動く行 0〜10。GROUNDED は動かない
        gen = set(self.r[UNT][u"群"][u"gen_c 8"])
        gm = [m for m in self.moved if m[u"doc"] in gen]
        vm_pnf = sum(1 for m in gm if m[u"P20"][u"state"] == "VALUE_MISMATCH" and m[u"P21"][u"state"] == "POINTER_NOT_FOUND")
        st20 = {}
        st21 = {}
        for p in self.r[u"C0-1 書類ごと(P21)"]:
            for s_, n_ in p[u"states"].items():
                st21[s_] = st21.get(s_, 0) + n_
        for s_, n_ in self.r[u"C0-1(製品の経路)gen_c 8 書類の state の合計"][u"P20"].items():
            st20[s_] = n_
        delta = {s_: st21.get(s_, 0) - st20.get(s_, 0) for s_ in set(st20) | set(st21)}
        v[5] = (st20 == {"GROUNDED": 443, "POINTER_NOT_FOUND": 111, "UNVERIFIABLE": 165, "VALUE_MISMATCH": 194}
                and delta.get("GROUNDED", 0) == 0 and inr(vm_pnf, 0, 10) and sum(abs(x) for x in delta.values()) <= 20)
        ka = sum(1 for x in k if x["a"])
        k21 = sum(1 for x in k if x["p21"])
        k20 = sum(1 for x in k if x["p20"])
        diff = round(pctv(ka, len(k)) - pctv(k21, len(k)), 1)
        v[6] = inr(k21, 9, 12) and len(k) == 20 and k20 == 7 and ka == 16 and inr(diff, 20, 35)
        c3 = self.r[C03][u"rows"]
        v[7] = sum(1 for x in c3 if x[u"engine の state"] == "GROUNDED") == 0 and len(c3) > 0
        f = self.r[u"engine の差分"][u"git diff HEAD --numstat -- core adapters"]
        e = self.r[u"engine の差分"]
        v[9] = (sorted(f) == ["adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py"]
                and f["adapters/xbrl/recipes.py"][1] == 0 and f["adapters/xbrl/recipes.py"][0] <= 40
                and e[u"recipes.py の差分は挿入 1 か所だけ(HEAD の行は 1 つも変えていない)"] is True
                and e[u"挿入先の関数"] == "def _direct_value_claim" and e[u"core/ の差分の file"] == []
                and e[u"instance.py・extract.py の差分"] == [])
        return v

    # ---- 1. 記録の集計 = 行から数え直した値
    def test_1_record_summaries_equal_recount_from_rows(self):
        r = self.r
        for lab, c, key in ((u"gen_c P21", self.g21, u"gen_c (ア) P21 の採点"), (u"gen_c P20", self.g20, u"gen_c (ア) P20 の採点"),
                            (u"cd8 P21", self.d21, u"cd8 (ア) P21 の採点"), (u"cd8 P20", self.d20, u"cd8 (ア) P20(記録)の採点")):
            x = r[key]
            self.assertEqual((x[u"T5 の件数"], x[u"注入の合計"]), (len(c.t5), len(c.rows)), lab)
            self.assertEqual((x[u"T5 の特定(Core-P)"][u"分子"], x[u"T5 の特定(Core-P)"][u"分母"]), (c.n_ident, len(c.t5)), lab)
            self.assertEqual(x[u"T5 の誤認定(Core-P。別の参照先を名指した行)"], len(c.wrong_t5), lab)
            self.assertEqual(x[u"T5 の誤認定の id"], [z["id"] for z in c.wrong_t5], lab)
            self.assertEqual(x[u"T5 の特定の id"], [z["id"] for z in c.t5 if c.ok[z["id"]]], lab)
            self.assertEqual((x[u"T1 の通し(Core-P。確認済みと言った)"][u"分子"], x[u"T1 の通し(Core-P。確認済みと言った)"][u"分母"]),
                             (len(c.t1_pass), len(c.t1)), lab)
            self.assertEqual((x[u"T3 の名指し(Core-P)"][u"分子"], x[u"T3 の名指し(Core-P)"][u"分母"]), (len(c.t3_named), len(c.t3)), lab)
            self.assertEqual((x[u"誤認定率(分母 = 参照先を出した全型の件。参考)"][u"分子"], x[u"誤認定率(分母 = 参照先を出した全型の件。参考)"][u"分母"]),
                             (len(c.wrong_t5) + len(c.t1_pass) + len(c.t3_named), len(c.pointed)), lab)
        # (ア) の main() の出力の採点と数え直しが一致
        for key, c in ((u"gen_c (ア) の main() の出力(P21)", self.g21), (u"cd8 (ア) の main() の出力(P21)", self.d21)):
            tal = r[key][u"採点"]["Core-P"]
            self.assertEqual((tal[u"特定率(分母 = T5 の件数)"][u"分子"], tal[u"特定率(分母 = T5 の件数)"][u"分母"]), (c.n_ident, len(c.t5)), key)
            self.assertEqual(tal[u"T1 の通し(値がどこにも無いのに確認済み)"][u"分子"], len(c.t1_pass), key)
            self.assertEqual(tal[u"T3 の名指し(参照先が無いのに名指した)"][u"分子"], len(c.t3_named), key)
        self.assertTrue(r[u"数え直しの照合"][u"全部一致"])
        # C0-3 の集計を行から
        c3 = r[C03]
        rows = c3[u"rows"]
        st = {}
        for x in rows:
            st[x[u"engine の state"]] = st.get(x[u"engine の state"], 0) + 1
        self.assertEqual(c3[u"集計"][u"state の分布"], st)
        self.assertEqual(len(rows), c3[u"集計"][u"engine を通せた行(分母)"])
        self.assertEqual(sorted(x["id"] for x in rows), sorted(x["id"] for x in self.g21.pointed))
        self.assertEqual(c3[u"集計"][u"**GROUNDED(誤りを通した)**"][u"件数"], sum(1 for x in rows if x[u"engine の state"] == "GROUNDED"))

    def test_2_inputs_are_the_committed_ones_and_unchanged(self):
        ins = self.r[u"入力の sha256(前後で変えていない)"]
        self.assertTrue(ins[u"一致"])
        self.assertEqual(ins[u"前"], ins[u"後"])
        self.assertEqual(ins[u"前"], SHA)
        self.assertEqual(sha(C0P20), SHA[u"c0_p20_2026-10-20.json"])
        self.assertEqual(sha(C1), SHA[u"c1_2026-10-20.json"])
        self.assertEqual(sha(CD8P20), SHA[u"cd8 a_core_vs_grep_P20_2026-10-17.json"])

    def test_3_same_injections_as_p20(self):
        a, b = self.r[RGC], self.c0p[u"C0-2 rows(P20)"]
        self.assertEqual([x["id"] for x in a], [x["id"] for x in b])
        self.assertEqual([x[u"正解"] for x in a], [x[u"正解"] for x in b])
        self.assertEqual([x[u"改変後の値"] for x in a], [x[u"改変後の値"] for x in b])
        self.assertEqual(len(a), 128)
        c, d = self.r[RCD], self.cd["rows"]
        self.assertEqual([x["id"] for x in c], [x["id"] for x in d])
        self.assertEqual([x[u"正解"] for x in c], [x[u"正解"] for x in d])
        self.assertEqual(len(c), 142)
        # 違った行の一覧(記録)は、門が行から比べた id と同じ
        self.assertEqual([x[u"id"] for x in self.r[u"gen_c P20 と P21 で rows が違った注入(1 件ずつ)"]],
                         [x["id"] for x, y in zip(b, a) if x != y])
        self.assertEqual([x[u"id"] for x in self.r[u"cd8 P20 と P21 で rows が違った注入(1 件ずつ)"]],
                         [x["id"] for x, y in zip(d, c) if x != y])

    def test_4_every_prediction_verdict_agrees_three_ways(self):
        v = self.verdicts()
        rec = {int(p[u"記号"].split("-")[1]): p[u"当たり"] for p in self.r[PRED]}
        rows = table_rows(self.doc)
        self.assertEqual(sorted(rec), list(range(1, 13)))
        self.assertEqual(sorted(rows), list(range(1, 13)))
        for n in (1, 2, 3, 4, 5, 6, 7, 9):
            word = u"**当たり**" if v[n] else u"**外れ**"
            self.assertEqual(rec[n], v[n], u"N-%d 記録の判定が行から数え直した値と違う" % n)
            self.assertEqual(rows[n][2], word, u"N-%d 文書の判定が数え直した値と違う" % n)
        # N-8・N-10・N-11・N-12 は pytest などの別の測り。記録は None、文書が当たり/外れを書く
        for n in (8, 10):
            self.assertIsNone(rec[n], n)
            self.assertIn(rows[n][2], (u"**当たり**", u"**外れ**"), n)
        # N-11 は engine の commit のあとでないと測れない(axis3 の test_9 は commit 前は緑)。N-12 は段 2 の予測
        self.assertIsNone(rec[11])
        self.assertEqual(rows[11][2], u"**判定しない(commit 後)**")
        self.assertIsNone(rec[12])
        self.assertEqual(rows[12][2], u"**判定しない(段 2)**")
        n8 = [p for p in self.r[PRED] if p[u"記号"] == "N-8"][0]
        self.assertTrue(n8[u"この script が測った部分"])
        self.assertEqual(n8[u"この script が測った部分"], self.r[u"**対照 M-C1**"][u"当たり"] and self.r[u"**対照 M-C3**"][u"当たり"])
        for n in range(1, 13):
            self.assertEqual(rows[n][0], seal_rows(self.seal)[n], u"N-%d 予測欄が封の字と違う" % n)

    def test_5_n4_moved_rows_are_recounted_one_by_one(self):
        u"""N-4: 動いた主張 1 件ずつから、合計・GROUNDED・state の組・型・書類ごとの数を門が数え直す。"""
        u40, moved = self.r[UNT], self.moved
        ids = u40[u"id の一覧"]
        self.assertEqual(len(ids), 40)
        self.assertEqual(len(set(ids)), 40)
        grp = u40[u"群"]
        self.assertEqual({k: len(v) for k, v in grp.items()}, GROUP_SIZES)
        self.assertEqual(grp[u"開発 14"], DEV_14)
        self.assertEqual(grp[u"未使用 2"], UNUSED_2)
        self.assertEqual(grp[u"gen_c 8"], [x for x in self.r[u"材料"][u"gen_c 8 書類"]])
        self.assertEqual(grp[u"(ア)/final8 8"], self.cd[u"書類"])
        self.assertEqual(sum(grp.values(), []), ids)
        self.assertEqual(u40[u"キャッシュに無い書類"], [])
        tot = u40[u"集計"]
        self.assertEqual(tot[u"動いた"], len(moved))
        self.assertEqual(tot.get(u"GROUNDED の行で動いた", 0), sum(1 for m in moved if "GROUNDED" in (m[u"P20"][u"state"], m[u"P21"][u"state"])))
        self.assertTrue(all(m[u"GROUNDED が関わる"] is False for m in moved))
        # 動いた主張はほんとうに違う(5 つ組)
        for m in moved:
            a, b = m[u"P20"], m[u"P21"]
            key = lambda z: (z[u"state"], tuple(z[u"pointers"]), z[u"reason"], z[u"recomputed"], z[u"form"])
            self.assertNotEqual(key(a), key(b), (m[u"doc"], m[u"id"]))
            self.assertIn(m[u"doc"], ids)
        self.assertEqual(len({(m[u"doc"], m[u"id"]) for m in moved}), len(moved))
        pairs = {}
        for m in moved:
            k_ = u"%s -> %s" % (m[u"P20"][u"state"], m[u"P21"][u"state"])
            pairs[k_] = pairs.get(k_, 0) + 1
        self.assertEqual({k_: v_ for k_, v_ in tot.items() if " -> " in k_}, pairs)
        kinds = {}
        for m in moved:
            kk = kind_of(m)
            self.assertEqual(m[u"型(機械的な読み)"], kk, (m[u"doc"], m[u"id"]))
            kinds[kk] = kinds.get(kk, 0) + 1
        self.assertEqual({k_[2:]: v_ for k_, v_ in tot.items() if k_.startswith(u"型 ")}, kinds)
        self.assertNotIn(u"その他", kinds)
        # 書類ごと
        per = u40[u"書類ごと"]
        self.assertEqual([p[u"doc"] for p in per], ids)
        for p in per:
            self.assertEqual(p[u"動いた"], sum(1 for m in moved if m[u"doc"] == p[u"doc"]), p[u"doc"])
            self.assertEqual(p[u"GROUNDED(P20)"], p[u"GROUNDED(P21)"], p[u"doc"])
        self.assertEqual(sum(p[u"claims"] for p in per), tot[u"claims"])
        self.assertEqual(sum(p[u"動いた"] for p in per), len(moved))

    def test_6_k4_is_recomputed_from_the_three_records(self):
        k, r = self.k, self.r[K4]
        n = len(k)
        self.assertEqual(n, 20)
        for x in k:
            self.assertEqual(x["gold"], x["gold21"], x["id"])
            self.assertEqual(x["a"], x["ptr_a"] == x["gold"], x["id"])
            self.assertEqual(x["p21"], x["ptr21"] == x["gold"], x["id"])
        ka, k20, k21 = (sum(1 for x in k if x[f]) for f in ("a", "p20", "p21"))
        self.assertEqual((ka, k20), (16, 7))
        self.assertEqual((r[u"席 A の特定(C1 の記録。不変)"][u"分子"], r[u"Core-P(P20)の特定"][u"分子"], r[u"Core-P(P21)の特定"][u"分子"]), (ka, k20, k21))
        self.assertEqual((r[u"差 席 A − Core-P(P21)(pt)"], r[u"差 席 A − Core-P(P20)(pt)"]),
                         (round(100.0 * ka / n - 100.0 * k21 / n, 1), round(100.0 * ka / n - 100.0 * k20 / n, 1)))
        self.assertEqual(r[u"P21 で特定が増えた行"], [x["id"] for x in k if x["p21"] and not x["p20"]])
        self.assertEqual(r[u"P21 で特定が減った行"], [x["id"] for x in k if x["p20"] and not x["p21"]])
        # 席 A の答えは C1 の記録のまま
        self.assertEqual(sum(1 for x in self.c1[u"**K-4・K-5 の数**"]["rows"] if x[u"席 A が特定"]), 16)
        # 境界: N-6 の幅 9〜12・差 +20〜+35 の両端は当たり側(幅の読み方を門が持っている)
        self.assertTrue(inr(9, 9, 12) and inr(12, 9, 12) and not inr(8, 9, 12) and not inr(13, 9, 12))
        self.assertTrue(inr(35.0, 20, 35) and not inr(35.1, 20, 35) and inr(20.0, 20, 35) and not inr(19.9, 20, 35))

    def test_7_every_fraction_is_consistent_and_allowed(self):
        a, b, c, d, k = self.g21, self.g20, self.d21, self.d20, self.k
        allowed = {(46, 64)}
        for z in (a, b, c, d):
            allowed |= {(z.n_ident, len(z.t5)), (len(z.wrong_t5), len(z.t5)),
                        (len(z.wrong_t5) + len(z.t1_pass) + len(z.t3_named), len(z.pointed)),
                        (len(z.t1_pass), len(z.t1)), (len(z.t3_named), len(z.t3)),
                        (len(z.wrong_t5), len(z.pointed))}
        for sel in (lambda x: True, lambda x: x["dim"], lambda x: not x["dim"], lambda x: x["doc"] == "S100Z4GF", lambda x: x["doc"] != "S100Z4GF"):
            rs = [x for x in k if sel(x)]
            for f in ("a", "p20", "p21"):
                allowed.add((sum(1 for x in rs if x[f]), len(rs)))
        for z in (a, b):
            gf = [x for x in z.t5 if x["doc"] == "S100Z4GF"]
            allowed.add((sum(1 for x in gf if z.ok[x["id"]]), len(gf)))
            ex = [x for x in z.t5 if x["doc"] != "S100Z4GF"]
            allowed.add((sum(1 for x in ex if z.ok[x["id"]]), len(ex)))
        rows = self.r[C03][u"rows"]
        allowed |= {(sum(1 for x in rows if x[u"engine の state"] == s_), len(rows)) for s_ in ("GROUNDED", "VALUE_MISMATCH")}
        tot = self.r[UNT][u"集計"]
        allowed.add((len(self.moved), tot[u"claims"]))
        for p in self.r[UNT][u"書類ごと"]:
            allowed.add((p[u"動いた"], p[u"claims"]))
        c3_20 = self.c0p[u"**C0-3 engine を Core-P(P20)の参照先に当てた**"][u"rows"]
        allowed |= {(sum(1 for x in c3_20 if x[u"engine の state"] == "GROUNDED"), len(c3_20)),
                    (sum(1 for x in c3_20 if x[u"露出 (d)(同額の次元兄弟)"]), len(c3_20)),
                    (sum(1 for x in rows if x[u"露出 (d)(同額の次元兄弟)"]), len(rows))}
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 20)
        for x, y, pc in found:
            xi, yi = int(x.replace(",", "")), int(y.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * xi / yi), pc, u"算術が合わない: %s / %s = %s%%" % (x, y, pc))
            self.assertIn((xi, yi), allowed, u"記録から作れない分数: %s / %s" % (x, y))

    def expected_cells(self):
        u"""N-1〜N-7・N-9 の実測欄の字を、記録の行から門が組み立てる(文書の字と完全一致を見る)。"""
        a, b, c, d, k = self.g21, self.g20, self.d21, self.d20, self.k
        moved, tot = self.moved, self.r[UNT][u"集計"]
        pairs = {}
        for m in moved:
            kk = (m[u"P20"][u"state"], m[u"P21"][u"state"])
            pairs[kk] = pairs.get(kk, 0) + 1
        kinds = {}
        for m in moved:
            kinds[kind_of(m)] = kinds.get(kind_of(m), 0) + 1
        ka, k20, k21 = (sum(1 for x in k if x[f]) for f in ("a", "p20", "p21"))
        c3 = self.r[C03][u"rows"]
        e = self.r[u"engine の差分"][u"git diff HEAD --numstat -- core adapters"]
        st = self.r[u"C0-1(製品の経路)gen_c 8 書類の state の合計"]
        gen = set(self.r[UNT][u"群"][u"gen_c 8"])
        vm_pnf = sum(1 for m in moved if m[u"doc"] in gen and m[u"P20"][u"state"] == "VALUE_MISMATCH" and m[u"P21"][u"state"] == "POINTER_NOT_FOUND")
        s20, s21 = st[u"P20"], st[u"P21"]
        return {
            1: u"P21 の特定 %s(P20 は %s)・誤認定 %d 件(P20 は %d 件)・増えた特定は %s"
               % (frac(a.n_ident, 50), frac(b.n_ident, 50), len(a.wrong_t5), len(b.wrong_t5), u"・".join(sorted(set(a.ids_ok) - set(b.ids_ok)))),
            2: u"cd8 の T5 64 件で P21 の特定 %s(P20 の記録は %s)・誤認定 %d 件(P20 の記録は %d 件)"
               % (frac(c.n_ident, 64), frac(d.n_ident, 64), len(c.wrong_t5), len(d.wrong_t5)),
            3: u"T1 の通し gen_c %s・cd8 %s、T3 の名指し gen_c %s・cd8 %s(P20 の記録と同じ)"
               % (frac(len(a.t1_pass), 38), frac(len(c.t1_pass), 38), frac(len(a.t3_named), 40), frac(len(c.t3_named), 40)),
            4: u"無改変 40 書類・主張 %s 本のうち、動いた %d 本(うち GROUNDED の行 %d 本)。VM → VM %d・VM → PNF %d・PNF → VM %d。型は F1′ %d・F2′ %d・F3b %d"
               % (format(tot[u"claims"], ","), len(moved), sum(1 for m in moved if "GROUNDED" in (m[u"P20"][u"state"], m[u"P21"][u"state"])),
                  pairs.get(("VALUE_MISMATCH", "VALUE_MISMATCH"), 0), pairs.get(("VALUE_MISMATCH", "POINTER_NOT_FOUND"), 0),
                  pairs.get(("POINTER_NOT_FOUND", "VALUE_MISMATCH"), 0),
                  kinds.get(u"F1′(前期の fact)", 0), kinds.get(u"F2′(名指さず止めた)", 0), kinds.get(u"F3b(残高の対)", 0)),
            5: u"P20 の合計 GROUNDED %d・VM %d・UNVERIFIABLE %d・PNF %d、P21 は GROUNDED %d・VM %d・UNVERIFIABLE %d・PNF %d。gen_c 8 書類で VM → PNF に動いた行 %d"
               % (s20["GROUNDED"], s20["VALUE_MISMATCH"], s20["UNVERIFIABLE"], s20["POINTER_NOT_FOUND"],
                  s21["GROUNDED"], s21["VALUE_MISMATCH"], s21["UNVERIFIABLE"], s21["POINTER_NOT_FOUND"], vm_pnf),
            6: u"席 A %s・Core-P(P21)%s(P20 は %s)・差 %+.1f pt" % (frac(ka, 20), frac(k21, 20), frac(k20, 20), round(pctv(ka, 20) - pctv(k21, 20), 1)),
            7: u"GROUNDED %s(Core-P が名指した注入の行 %d 本を engine に通した)"
               % (frac(sum(1 for x in c3 if x[u"engine の state"] == "GROUNDED"), len(c3)), len(c3)),
            9: u"recipes.py は %d 行追加・%d 行削除(`_direct_value_claim` の最後の枝の中の 1 か所)、vocabulary.py は %d 行追加・%d 行削除、core/ は 0 行、instance.py・extract.py は 0 行"
               % (e["adapters/xbrl/recipes.py"][0], e["adapters/xbrl/recipes.py"][1], e["adapters/xbrl/vocabulary.py"][0], e["adapters/xbrl/vocabulary.py"][1]),
        }

    def test_8_prediction_table_cells_equal_the_record_in_order(self):
        rows = table_rows(self.doc)
        exp = self.expected_cells()
        for n, want in exp.items():
            self.assertEqual(rows[n][1], want, u"N-%d 実測欄の字" % n)
        a, b, c, d = self.g21, self.g20, self.d21, self.d20
        # N-3 の『P20 の記録と同じ』は P20 の数と P21 の数が equal のとき
        self.assertEqual((len(a.t1_pass), len(a.t3_named), len(c.t1_pass), len(c.t3_named)),
                         (len(b.t1_pass), len(b.t3_named), len(d.t1_pass), len(d.t3_named)))
        # N-12: 参考の数(段 2 の予測。判定しない)。記録の 5 行と equal
        ref = self.r[UNT][u"参考(判定に使わない): 未使用 2 書類を test_p16_matches_the_holdout_dumps と同じ照合に当てた"]
        self.assertEqual((ref["S100Z4N9"]["P21"][u"違った行"], ref["S100Z39P"]["P21"][u"違った行"], ref["S100Z4N9"]["P20"][u"違った行"], ref["S100Z39P"]["P20"][u"違った行"]),
                         (4, 1, 0, 0))
        self.assertEqual(sorted(x[u"行の鍵"].split(":")[1] for x in ref["S100Z4N9"]["P21"][u"明細"]), ["H-067", "H-120", "H-122", "H-124"])
        self.assertEqual([x[u"行の鍵"].split(":")[1] for x in ref["S100Z39P"]["P21"][u"明細"]], ["H-075"])
        for x in ref["S100Z4N9"]["P21"][u"明細"] + ref["S100Z39P"]["P21"][u"明細"]:
            self.assertEqual((x[u"dump(P16)"][u"state"], x["P21"][u"state"]), ("VALUE_MISMATCH", "VALUE_MISMATCH"), x[u"行の鍵"])
            self.assertNotEqual(x[u"dump(P16)"][u"pointers"], x["P21"][u"pointers"], x[u"行の鍵"])
        # 判定の集計
        v = self.verdicts()
        hit = sum(1 for n in (1, 2, 3, 4, 5, 6, 7, 9) if v[n]) + sum(1 for n in (8, 10) if rows[n][2] == u"**当たり**")
        miss = sum(1 for n in (1, 2, 3, 4, 5, 6, 7, 9) if not v[n]) + sum(1 for n in (8, 10) if rows[n][2] == u"**外れ**")
        undecided = sum(1 for n in range(1, 13) if rows[n][2].startswith(u"**判定しない("))
        self.assertEqual(once(self.doc, r"\*\*当たり (\d+) / 外れ (\d+) / 判定しない (\d+)。\*\*"), S(hit, miss, undecided))
        self.assertEqual(hit + miss + undecided, 12)

    def test_8b_p20_p21_table_and_group_table_are_recounted(self):
        a, b, c, d, k = self.g21, self.g20, self.d21, self.d20, self.k
        c3_21 = self.r[C03][u"rows"]
        c3_20 = self.c0p[u"**C0-3 engine を Core-P(P20)の参照先に当てた**"][u"rows"]
        st = self.r[u"C0-1(製品の経路)gen_c 8 書類の state の合計"]

        def gf(z):
            x = [y for y in z.t5 if y["doc"] == "S100Z4GF"]
            return sum(1 for y in x if z.ok[y["id"]]), len(x)

        def wr(z):
            return len(z.wrong_t5) + len(z.t1_pass) + len(z.t3_named)
        want = [
            (u"gen_c の T5 50 件の Core-P の特定", frac(b.n_ident, 50), frac(a.n_ident, 50)),
            (u"gen_c の T5 の誤認定(別の参照先を名指した件)", u"%d 件" % len(b.wrong_t5), u"%d 件" % len(a.wrong_t5)),
            (u"S100Z4GF の T5 24 件の特定", frac(*gf(b)), frac(*gf(a))),
            (u"gen_c の誤認定率(分母 = 参照先を出した全型の件)", frac(wr(b), len(b.pointed)), frac(wr(a), len(a.pointed))),
            (u"gen_c の T1 の通し", frac(len(b.t1_pass), 38), frac(len(a.t1_pass), 38)),
            (u"gen_c の T3 の名指し", frac(len(b.t3_named), 40), frac(len(a.t3_named), 40)),
            (u"cd8 の T5 64 件の Core-P の特定", frac(d.n_ident, 64), frac(c.n_ident, 64)),
            (u"cd8 の T5 の誤認定(別の参照先を名指した件)", u"%d 件" % len(d.wrong_t5), u"%d 件" % len(c.wrong_t5)),
            (u"cd8 の誤認定率(分母 = 参照先を出した全型の件)", frac(wr(d), len(d.pointed)), frac(wr(c), len(c.pointed))),
            (u"cd8 の T1 の通し", frac(len(d.t1_pass), 38), frac(len(c.t1_pass), 38)),
            (u"cd8 の T3 の名指し", frac(len(d.t3_named), 40), frac(len(c.t3_named), 40)),
            (u"K-4 の 20 行の Core-P の特定", frac(sum(1 for x in k if x["p20"]), 20), frac(sum(1 for x in k if x["p21"]), 20)),
            (u"C0-3 で engine が GROUNDED にした件数", frac(sum(1 for x in c3_20 if x[u"engine の state"] == "GROUNDED"), len(c3_20)),
             frac(sum(1 for x in c3_21 if x[u"engine の state"] == "GROUNDED"), len(c3_21))),
            (u"C0-3 の (d) 保留の露出", frac(sum(1 for x in c3_20 if x[u"露出 (d)(同額の次元兄弟)"]), len(c3_20)),
             frac(sum(1 for x in c3_21 if x[u"露出 (d)(同額の次元兄弟)"]), len(c3_21))),
            (u"C0-1(gen_c 8 書類)の GROUNDED の合計", str(st[u"P20"]["GROUNDED"]), str(st[u"P21"]["GROUNDED"])),
            (u"C0-1(gen_c 8 書類)の VALUE_MISMATCH の合計", str(st[u"P20"]["VALUE_MISMATCH"]), str(st[u"P21"]["VALUE_MISMATCH"])),
            (u"C0-1(gen_c 8 書類)の POINTER_NOT_FOUND の合計", str(st[u"P20"]["POINTER_NOT_FOUND"]), str(st[u"P21"]["POINTER_NOT_FOUND"])),
            (u"C0-1(gen_c 8 書類)の UNVERIFIABLE の合計", str(st[u"P20"]["UNVERIFIABLE"]), str(st[u"P21"]["UNVERIFIABLE"])),
        ]
        sec_ = self.doc[self.doc.index(u"## P20 の数と P21 の数を並べる"):self.doc.index(u"## 変わった注入 1 件ずつ")]
        lines = re.findall(r"(?m)^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", sec_)
        lines = [x for x in lines if x[0] != u"" and not x[0].startswith("---")]      # 見出し行(空の左上)と区切り行を除く
        self.assertEqual([tuple(x) for x in lines], want)
        # 群の表
        u40 = self.r[UNT]
        per = {p[u"doc"]: p for p in u40[u"書類ごと"]}
        sec2 = self.doc[self.doc.index(u"## 無改変の 40 書類"):self.doc.index(u"## 対照")]
        g = re.findall(r"(?m)^\| (gen_c 8|\(ア\)/final8 8|cd8 の引いた 8|開発 14|未使用 2) \| (\d+) \| ([\d,]+) \| (\d+) \|$", sec2)
        wantg = [(n, str(len(l)), format(sum(per[x][u"claims"] for x in l), ","), str(sum(per[x][u"動いた"] for x in l))) for n, l in u40[u"群"].items()]
        self.assertEqual(g, wantg)
        self.assertEqual(once(sec2, r"(?m)^\| 合計 \| (\d+) \| ([\d,]+) \| (\d+) \|$"),
                         S(40, format(u40[u"集計"][u"claims"], ","), len(self.moved)))
        self.assertEqual(sum(int(x[3]) for x in g), len(self.moved))

    def test_9_changed_rows_tables_are_recounted(self):
        u"""P20 -> P21 で変わった注入の一覧(記録)を、門が P20/P21 の行の字から作り直して equal。文書は各 id を載せる。"""
        for key, old, new in ((u"gen_c P20 と P21 で rows が違った注入(1 件ずつ)", self.c0p[u"C0-2 rows(P20)"], self.r[RGC]),
                              (u"cd8 P20 と P21 で rows が違った注入(1 件ずつ)", self.cd["rows"], self.r[RCD])):
            want = []
            for x, y in zip(old, new):
                if x != y:
                    want.append((x["id"], cp(x)[u"参照先"], cp(y)[u"参照先"], x[u"正解"][u"正解"]))
            got = [(z[u"id"], z[u"P20"][u"参照先"], z[u"P21"][u"参照先"], z["gold"]) for z in self.r[key]]
            self.assertEqual(got, want, key)
            for iid, p20, p21, gold in want:
                self.assertIn(iid, self.doc, iid)
        # gen_c: 特定が増えたのは 5 件だけ・誤認定が消えたのは 12 件(T5)
        gen_changed = {z[u"id"]: z for z in self.r[u"gen_c P20 と P21 で rows が違った注入(1 件ずつ)"]}
        became_ok = sorted(i for i, z in gen_changed.items() if z[u"P21"][u"特定"] and not z[u"P20"][u"特定"])
        self.assertEqual(became_ok, NEWLY)
        stopped = sorted(i for i, z in gen_changed.items() if z[u"P20"][u"誤認定"] and z[u"P21"][u"参照先"] is None)
        self.assertEqual(len(stopped), 11)
        self.assertEqual(once(self.doc, r"誤った名指しを止めた T5 は gen_c (\d+) 件・cd8 (\d+) 件"),
                         S(len(stopped), sum(1 for z in self.r[u"cd8 P20 と P21 で rows が違った注入(1 件ずつ)"]
                                             if z[u"P20"][u"誤認定"] and z[u"P21"][u"参照先"] is None)))

    def test_10_controls_engine_and_the_zero_usd_facts(self):
        r = self.r
        mc1, mc3 = r[u"**対照 M-C1**"], r[u"**対照 M-C3**"]
        self.assertTrue(mc1[u"当たり"])
        self.assertEqual(mc1[u"(ア) main() の出力(rows 以外)で違った欄"], [])
        for key, val in mc1.items():
            if key != u"(ア) main() の出力(rows 以外)で違った欄":
                self.assertIs(val, True, key)
        self.assertTrue(mc3[u"当たり"])
        self.assertIs(mc3[u"rows が c0_p20 の記録と一致"], False)
        self.assertTrue(mc3[u"違った注入の id が P21 の run で動いた id と同じ"])
        self.assertEqual(mc3[u"違った注入の件数"], len(r[u"gen_c P20 と P21 で rows が違った注入(1 件ずつ)"]))
        self.assertEqual(r[u"補助: cd8 の (ア) を P20 で回すと記録に全欄一致"][u"違った欄"], [])
        self.assertEqual(r["profile"], "P21(対照 P20)")
        self.assertEqual(r[u"環境"][u"設定されている key の数"], 0)
        self.assertEqual(sorted(r[u"環境"][u"4 つの key の名前が設定されているか"]),
                         ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"])
        self.assertFalse(any(r[u"環境"][u"4 つの key の名前が設定されているか"].values()))
        sh = r[u"engine の sha"][u"主な file の sha256"]
        for rel, want in ENGINE_AT_MEASURE.items():
            self.assertEqual(sh[rel][:16], want, rel)
        # instance.py・extract.py は P20 のままの sha(記録の事実。engine の外側 3 本)
        self.assertEqual(r[u"engine の差分"][u"git diff HEAD --numstat -- core adapters"]["adapters/xbrl/vocabulary.py"], [8, 1])
        d = self.doc
        self.assertIn(u"API key は 4 つとも未設定(0)", d)
        self.assertIn(u"席(LLM API)は 1 回も呼んでいない", d)
        self.assertEqual(once(d, r"recipes\.py は (\d+) 行追加・(\d+) 行削除"), S(*r[u"engine の差分"][u"git diff HEAD --numstat -- core adapters"]["adapters/xbrl/recipes.py"]))

    def test_11_the_document_keeps_its_honesty_clauses(self):
        d = self.doc
        for lit in (u"**封は 1 文字も直していない。**", u"## 手順の正直な記録", u"## 迷った点", u"## 限界",
                    u"## 今回新しく分かったこと", u"**外れは外れのまま書く。**", u"段 2 はこの文書では決めない",
                    u"既定の profile は P20 のまま", u"人間が決めた止めを壊した", u"API key は 4 つとも未設定(0)",
                    u"席(LLM API)は 1 回も呼んでいない"):
            self.assertIn(lit, d, lit)
        for bad in (u"改善した。", u"良くなった", u"持ち直した。", u"汎化した"):
            self.assertNotIn(bad, d, bad)


if __name__ == "__main__":
    unittest.main()
