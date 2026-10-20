# -*- coding: utf-8 -*-
u"""汎化 C 追記 3 段 α-B の結果文書(docs/XBRL_GENERALITY_ALPHA_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/alpha_2026-10-20.json``(``measure/xbrl_gen_c_alpha_2026-10-20.py`` の出力)。
封: ``docs/XBRL_GENERALITY_SEAL_2026-10-20.md`` 追記 3(C-3 の幅は**ここに字で留める**。封の字と合わせてある)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の集計(α-1・α-3・α-4・対照)を、同じ記録の**行**(席が参照先を出した 102 行)と C1 の記録の 192 行から
     この門が数え直した値と突き合わせる(記録の集計欄を信じない)。A+α の 4 つの数は、この門が**採点器とは別に**
     C1 の記録の行から数え直す。
  2. 予測 S-1〜S-8 の当たり/外れを、行から数え直した値と封の幅で**門が自分で**判定し、記録の判定・文書の判定の 3 つが一致する。
     **S-1・S-3・S-4・S-6 は記録の行から再計算して equal**(記録の判定だけを書き換えると赤)。
  3. 文書の分数(``a / b = x.x%``)の全部が算術として合い、記録から作った許可集合に入る。
  4. 同じ字が複数回出る数は ``once()`` で文書の場所を特定し、記録から数えた値と equal で縛る。
  5. α-2 の表の行・数を記録の読みの材料と突き合わせる。**読み(席の側か Core の側か)はこの門が字で持つラベル**で、
     ラベルが正しいことは門では確かめられない(記録の外)。縛るのは、行の id が記録の VALUE_MISMATCH の行と一致すること・
     表の数が記録と一致すること・ラベルの数え方(S-3)だけ。
  6. 入力(席の答え・材料・C0・P20・C1・cd8 の答えと材料)の sha256 を**字で留める**(読むだけで、1 文字も直していない)。

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
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(GEN, "alpha_2026-10-20.json")
C0 = os.path.join(GEN, "c0_2026-10-20.json")
C0P20 = os.path.join(GEN, "c0_p20_2026-10-20.json")
C1 = os.path.join(GEN, "c1_2026-10-20.json")
MAT = os.path.join(GEN, "material_2026-10-20.json")
ANS = os.path.join(GEN, "seat_answers")
CD8_ANS = os.path.join(CD8, "seat_answers")
CD8_MAT = os.path.join(CD8, "material_2026-10-17.json")
CD8_SCORE = os.path.join(CD8, "score_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_ALPHA_RESULT_2026-10-20.md")
SEAL_DOC = os.path.join(ROOT, "docs", "XBRL_GENERALITY_SEAL_2026-10-20.md")
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]

#: commit 済みの file の sha256。**字で留める**(定数から作らない)。席の答えは f0b7140、C0 は 8f18b53、C1 は 4e7f490。
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
SHA_CD8_ANS = {
    "S100YWGX_answer.json": "52aeac8183593533b7d9dd470bebd18195f11421b672603aab4279c4973dcd16",
    "S100YXF5_answer.json": "864f7e507b7de1be1d1200b44a3244d76fab9787d0605157082fec6ee09aed53",
    "S100YXMA_answer.json": "775bf942c2620360fcc0d6ac26b20637892eb617fc281f6a3f349748844784a4",
    "S100YYRG_answer.json": "9bc7db15998b4939bf9542bf4e695135d4e2e618558a5ebf68d8995559d78a66",
    "S100YYRV_answer.json": "f643a928c800cfa74aeff034f5f001d980ef746a55d0d17adf8536db5edf5587",
    "S100YZ7E_answer.json": "1e06e97bf694cd8afff4f3d1f6a6381915dd4ee45563734f1c5f7bfe3baf0105",
    "S100YZCT_answer.json": "97e06eee0f1a70dea605a147d984a1e2a1c4d7dc16d7b0379bff116cf0952a86",
    "S100YZEV_answer.json": "eba2f890515176b691c810d477c4cc27792a77a4526525d7440736a35fcc6f80",
}
SHA_MAT = "2a33dd21f252de15651168a015147c5206bf92ec676a6f8142a4ecd14f067d37"
SHA_C0 = "30fe3e2bb4a74bdd746d5bd95973e78a757ab06fbc23ffd114ddb509dc7953ad"
SHA_C0P20 = "d4091508077c0830dbd9f393bcd4b9719702686828d43a058df6ceae2448e051"
SHA_C1 = "4f6141aaeffa87ded81247902d498a6591270bc7036390ea22d8d9bc8683f0d4"
SHA_CD8_MAT = "d0538c551627e13dc14df513c401009ac58b722163aaa6523a3256dd099a06b4"

ROWS = u"α-1 の行(席が参照先を出した 102 行。α-2 の読みの材料つき)"
PRED = u"**予測 S-1〜S-9**"
READ = u"読みの材料(α-2)"
PERIOD_DIFF = u"同じ枠で期間だけ違う fact との差が主張の値に合う(差の差が 1 単位以内)"

#: α-2 の読み(**この門が字で持つラベル。人の読みで、記録の外・門で縛れない**)。
#: 縛るのは、キーが記録の VALUE_MISMATCH の 9 行と一致することと、ラベルの数え方(S-3)だけ。
READING = {
    ("S100YYN7", "R006"): u"Core の側",
    ("S100YYT4", "R002"): u"席の側",
    ("S100YYT4", "R004"): u"席の側",
    ("S100Z4J8", "R002"): u"席の側",
    ("S100Z4J8", "R006"): u"席の側",
    ("S100Z4J8", "R009"): u"席の側",
    ("S100Z4J8", "R012"): u"席の側",
    ("S100Z4J8", "R015"): u"席の側",
    ("S100Z4J8", "R017"): u"席の側",
}


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
    u"""文書の数の字。``46 / 77 = 59.7%``。"""
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
    return [x.strip() for x in line.strip().strip("|").split("|")]


def sections(doc):
    u"""``## 見出し`` ごとの本文。"""
    out, name, buf = {}, None, []
    for ln in doc.split("\n"):
        if ln.startswith("## "):
            if name is not None:
                out[name] = "\n".join(buf)
            name, buf = ln[3:].strip(), []
        elif name is not None:
            buf.append(ln)
    if name is not None:
        out[name] = "\n".join(buf)
    return out


def sec(secs, prefix):
    hit = [k for k in secs if k.startswith(prefix)]
    assert len(hit) == 1, (prefix, hit)
    return secs[hit[0]]


def pred_rows(doc):
    u"""``| **S-n** | 予測 | 実測 | 判定 |`` の行 -> {n: (予測, 実測, 判定)}。"""
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*S-(\d+)\*\* \|(.*)$", doc):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = (cells[0], cells[1], cells[2])
    return out


def seal_rows(seal):
    i = seal.index(u"## 追記 3")
    out = {}
    for m in re.finditer(r"(?m)^\| \*\*S-(\d+)\*\* \|(.*)$", seal[i:]):
        cells = [x.strip() for x in m.group(2).split("|")]
        out[int(m.group(1))] = cells[0]
    return out


def money_fmt(x):
    return u"{:,}".format(int(round(x)))


class Metrics(object):
    u"""C1 の記録の 192 行から、腕の 4 つの数 + 偽警報を**採点器とは別に**数える。

    ``lowered`` は (doc, id) の集合: その行は ``判定できない``・参照先 None の腕にする。
    """

    def __init__(self, c1rows, lowered):
        self.n = len(c1rows)
        pointed = wrong = miss = ident = held = fa = stop = inj = t5 = 0
        for r in c1rows:
            seat = r[u"席"]
            word, ptr = seat[u"判定"], seat[u"参照先"]
            if (r["doc"], r["id"]) in lowered:
                word, ptr = u"判定できない", None
            gold, injected = r[u"正解"], r[u"注入か"]
            if injected:
                inj += 1
                if word == u"確認済み":
                    miss += 1
                if word != u"確認済み":
                    stop += 1
            elif word == u"誤りが在る":
                fa += 1
            if ptr is None:
                held += 1
            else:
                pointed += 1
                if gold is not None:
                    k = gold[u"種類"]
                    if k == u"参照先が在る":
                        if ptr != gold[u"正解"]:
                            wrong += 1
                    elif k == u"参照先は無い":
                        wrong += 1
                    elif word == u"確認済み":
                        wrong += 1
            if gold is not None and gold[u"種類"] == u"参照先が在る":
                t5 += 1
                if ptr is not None and ptr == gold[u"正解"]:
                    ident += 1
        self.pointed, self.wrong, self.miss, self.ident, self.held = pointed, wrong, miss, ident, held
        self.fa, self.stop, self.inj, self.t5 = fa, stop, inj, t5
        self.plain = self.n - inj


class AlphaResultGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = jload(REC)
        cls.c1 = jload(C1)
        cls.doc = text(DOC)
        cls.seal = text(SEAL_DOC)
        cls.secs = sections(cls.doc)
        cls.items = cls.r[ROWS]
        cls.plain = [x for x in cls.items if not x[u"注入か"]]
        cls.p77 = [x for x in cls.plain if x[u"席の判定"] == u"確認済み"]
        cls.inj25 = [x for x in cls.items if x[u"注入か"]]
        cls.state_of = {(x["doc"], x["id"]): x[u"engine の state"] for x in cls.items}
        cls.c1rows = cls.c1["rows"]
        cls.vm = [x for x in cls.p77 if x[u"engine の state"] == "VALUE_MISMATCH"]
        cls.lowered = {(x["doc"], x["id"]) for x in cls.vm}
        cls.mA = Metrics(cls.c1rows, set())
        cls.mAa = Metrics(cls.c1rows, cls.lowered)
        cls.hold90 = [r for r in cls.c1rows if r[u"席"][u"判定"] == u"判定できない"]

    # ---- 派生
    def states(self, rows):
        out = {}
        for x in rows:
            out[x[u"engine の state"]] = out.get(x[u"engine の state"], 0) + 1
        return out

    def ctl(self):
        rows = [x for x in self.p77 if x[u"対照(その fact 自身の値)"] is not None]
        g = [x for x in rows if x[u"対照(その fact 自身の値)"][u"state"] == "GROUNDED"]
        return rows, g

    def s3_labels(self):
        return [READING[(x["doc"], x["id"])] for x in self.vm]

    def verdicts(self):
        u"""封 追記 3 C-3 の幅(字で留める)で S-1〜S-8 を判定する。"""
        v = {}
        st = self.states(self.p77)
        g, vm = st.get("GROUNDED", 0), st.get("VALUE_MISMATCH", 0)
        hold = st.get("UNPROVABLE", 0) + st.get("POINTER_NOT_FOUND", 0)
        v[1] = inr(g, 50, 70) and len(self.p77) == 77
        v[2] = inr(vm, 3, 15) and inr(hold, 0, 12)
        labels = self.s3_labels()
        v[3] = sum(1 for z in labels if z == u"席の側") * 2 >= len(labels) and len(labels) > 0
        a, b = self.mA, self.mAa
        v[4] = (b.wrong == 4 and b.miss == 0 and b.ident == 16 and b.t5 == 20 and b.held == a.held + len(self.vm)
                and a.held == 90)
        v[5] = b.fa == 0 and b.plain == 128
        ids90 = {(r["doc"], r["id"]) for r in self.hold90}
        pp20 = {tuple(z) for z in self.r[u"α-4"][u"Core-P(P20)が参照先を出す行の ids"]}
        v[6] = inr(len(pp20), 10, 40) and len(ids90) == 90 and pp20 <= ids90
        core_inj = self.r[u"α-4"][u"注入の行の明細"]
        v[7] = sum(1 for z in core_inj if z[u"engine の state"] == "GROUNDED") == 0
        rows, g_ctl = self.ctl()
        pp_diff = [x for x in self.items if x[u"engine(PP あり)"] != x[u"engine(PP なし)"]]
        v[8] = (len(g_ctl) == len(self.p77) == 77) and self.r[u"cd8(S-C2)"][u"完走"] and self.r[u"cd8(S-C2)"][u"欠け"] == 0 \
            and all(x[u"PP の行"] for x in pp_diff)
        return v

    # ---- 1. 記録の集計 = 行から数え直した値
    def test_1_record_summaries_equal_recount_from_rows(self):
        r = self.r
        a1 = r[u"α-1"]
        st = self.states(self.p77)
        self.assertEqual(len(self.p77), 77)
        self.assertEqual(len(self.inj25), 25)
        self.assertEqual(len(self.items), 102)
        self.assertEqual(a1[u"state の分布"], dict(sorted(st.items())))
        self.assertEqual(a1[u"分母(席 A が 確認済み + 参照先の無改変の行)"], 77)
        self.assertTrue(a1[u"封の 77 と書類ごとの数が一致"])
        by_doc = {d: sum(1 for x in self.p77 if x["doc"] == d) for d in EIGHT}
        self.assertEqual(by_doc, {"S100Z0OS": 3, "S100YYN7": 14, "S100YYT8": 1, "S100Z42X": 14, "S100YYT4": 15,
                                  "S100Z4GF": 9, "S100Z4J8": 15, "S100YYUD": 6})
        self.assertEqual(a1[u"書類ごと"], by_doc)
        for key, n in ((u"GROUNDED", st.get("GROUNDED", 0)), (u"VALUE_MISMATCH", st.get("VALUE_MISMATCH", 0))):
            self.assertEqual((a1[key][u"分子"], a1[key][u"分母"]), (n, 77), key)
        hold = st.get("UNPROVABLE", 0) + st.get("POINTER_NOT_FOUND", 0)
        self.assertEqual((a1[u"保留(UNPROVABLE + POINTER_NOT_FOUND)"][u"分子"], a1[u"保留(UNPROVABLE + POINTER_NOT_FOUND)"][u"分母"]), (hold, 77))
        self.assertEqual(a1[u"state が 4 つの外"], {})
        self.assertEqual(sum(st.values()), 77)
        for d in EIGHT:
            sub = self.states([x for x in self.p77 if x["doc"] == d])
            self.assertEqual(a1[u"書類ごとの state"][d], dict(sorted(sub.items())), d)
        ratio = [x for x in self.p77 if x[u"PP の行"]]
        unitless = [x for x in self.p77 if x[u"材料の単位"] is None]
        money = [x for x in self.p77 if not x[u"PP の行"] and x[u"材料の単位"] is not None]
        self.assertEqual((len(ratio), len(money), len(unitless)), (32, 42, 3))
        self.assertEqual(a1[u"行の種類ごとの件数"], {u"率の行": 32, u"金額の行": 42, u"単位が無い行": 3})
        self.assertEqual(a1[u"行の種類ごとの state"][u"率の行(単位 %)"], dict(sorted(self.states(ratio).items())))
        self.assertEqual(a1[u"行の種類ごとの state"][u"金額の行"], dict(sorted(self.states(money).items())))
        self.assertEqual(a1[u"行の種類ごとの state"][u"単位が無い行"], dict(sorted(self.states(unitless).items())))
        reasons = {}
        for x in self.p77:
            if x[u"engine の state"] == "UNPROVABLE":
                reasons[x[u"engine の reason"]] = reasons.get(x[u"engine の reason"], 0) + 1
        self.assertEqual(a1[u"UNPROVABLE の理由の分布"], reasons)
        self.assertEqual(sum(v for k, v in reasons.items() if k.startswith("ambiguous_dimension")), 18)
        self.assertEqual(a1[u"held(製品の経路)"], sum(1 for x in self.p77 if x[u"held(製品の経路)"]))
        self.assertEqual(a1[u"held(製品の経路)"], 18)
        self.assertTrue(all(x[u"hold_rules(製品の経路)"] == ["d"] for x in self.p77 if x[u"held(製品の経路)"]))
        self.assertEqual(a1[u"参照先が解けなかった行"], [])
        # 注入 25 行
        ai = r[u"α-1(注入 25 行)"]
        self.assertEqual(ai[u"席の判定語"], {u"誤りが在る": 25})
        self.assertEqual(ai[u"規則が掛かる行(席が 確認済み)"], 0)
        self.assertEqual(ai[u"state の分布(この script で当て直した)"], dict(sorted(self.states(self.inj25).items())))
        self.assertEqual(ai[u"state の分布(この script で当て直した)"], {"UNPROVABLE": 1, "VALUE_MISMATCH": 24})
        self.assertEqual(ai[u"C1-3 の rows と state・reason・recomputed・held が違う行"], [])
        c13 = {(x["doc"], x["id"]): x for x in self.c1[u"C1-3"]["rows"]}
        for x in self.inj25:
            o = c13[(x["doc"], x["id"])]
            self.assertEqual((o[u"engine の state"], o[u"engine の reason"], o[u"engine の recomputed"], o[u"held(製品の経路)"]),
                             (x[u"engine の state"], x[u"engine の reason"], x[u"engine の recomputed"], x[u"held(製品の経路)"]), x["id"])
        # 材料の行は C1 の記録の席 A と一致(77 + 25 は席が参照先を出した 102 行)
        named = {(x["doc"], x["id"]) for x in self.items}
        c1named = {(q["doc"], q["id"]) for q in self.c1rows if q[u"席"][u"参照先"] is not None}
        self.assertEqual(named, c1named)
        for q in self.c1rows:
            if q[u"席"][u"参照先"] is not None:
                x = [z for z in self.items if (z["doc"], z["id"]) == (q["doc"], q["id"])][0]
                self.assertEqual((x[u"席の判定"], x[u"注入か"]), (q[u"席"][u"判定"], q[u"注入か"]))
        # α-3: A と A+α を、この門が C1 の記録の行から数え直す(採点器を使わない)
        a3 = r[u"α-3"]
        for name, m in ((u"A(席そのまま。採点器の出力)", self.mA), (u"A+α", self.mAa)):
            x = a3[name]
            self.assertEqual((x[u"誤認定"][u"分子"], x[u"誤認定"][u"分母(参照先を出した件)"]), (m.wrong, m.pointed), name)
            self.assertEqual((x[u"見逃し"][u"分子"], x[u"見逃し"][u"分母(注入の件)"]), (m.miss, m.inj), name)
            self.assertEqual((x[u"正しい参照先の特定"][u"分子"], x[u"正しい参照先の特定"][u"分母(T5 の件)"]), (m.ident, m.t5), name)
            self.assertEqual((x[u"保留"][u"分子"], x[u"保留"][u"分母(欠けを外した件)"]), (m.held, m.n), name)
            self.assertEqual((x[u"偽警報"][u"分子"], x[u"偽警報"][u"分母(無改変の件)"]), (m.fa, m.plain), name)
            self.assertEqual((x[u"軸A 停止判定"][u"分子"], x[u"軸A 停止判定"][u"分母(注入の件)"]), (m.stop, m.inj), name)
            self.assertEqual(x[u"欠け"], 0)
        self.assertEqual(a3[u"規則が掛かる行(席が 確認済み + 参照先)"], 77)
        self.assertEqual(a3[u"下げた行(VALUE_MISMATCH → 判定できない・参照先を外す)"], len(self.vm))
        self.assertEqual({(z["doc"], z["id"]) for z in a3[u"下げた行の ids"]}, self.lowered)
        self.assertEqual(a3[u"下げた行のうち注入の行"], 0)
        self.assertEqual(a3[u"保留の増分"], self.mAa.held - self.mA.held)
        self.assertEqual(a3[u"誤認定の分母(参照先を出した件)の増分"], self.mAa.pointed - self.mA.pointed)
        self.assertTrue(a3[u"A の再現(c1 の記録の 採点/A と全欄一致)"])
        # A は C1 の記録の採点/A と一致(門が数え直した値)
        ca = self.c1[u"採点"]["A"]
        self.assertEqual((ca[u"誤認定"][u"分子"], ca[u"誤認定"][u"分母(参照先を出した件)"], ca[u"保留"][u"分子"]),
                         (self.mA.wrong, self.mA.pointed, self.mA.held))
        # α-4
        a4 = r[u"α-4"]
        ids90 = [(q["doc"], q["id"], bool(q[u"注入か"])) for q in self.hold90]
        self.assertEqual([tuple(z) for z in a4[u"席が 判定できない の行の ids"]], ids90)
        self.assertEqual(len(ids90), 90)
        self.assertEqual((sum(1 for z in ids90 if not z[2]), sum(1 for z in ids90 if z[2])), (51, 39))
        pp20 = [tuple(z) for z in a4[u"Core-P(P20)が参照先を出す行の ids"]]
        pp16 = [tuple(z) for z in a4[u"Core-P(P16。材料の記録)が参照先を出す行の ids"]]
        idset = {(z[0], z[1]) for z in ids90}
        self.assertTrue(set(pp20) <= idset and set(pp16) <= idset)
        inj_ids = {(z[0], z[1]) for z in ids90 if z[2]}
        self.assertEqual((a4[u"Core-P(P20)が参照先を出す行"][u"分子"], a4[u"Core-P(P20)が参照先を出す行"][u"分母"]), (len(pp20), 90))
        self.assertEqual((a4[u"うち無改変"][u"分子"], a4[u"うち無改変"][u"分母"]), (len([z for z in pp20 if z not in inj_ids]), 51))
        self.assertEqual((a4[u"うち注入"][u"分子"], a4[u"うち注入"][u"分母"]), (len([z for z in pp20 if z in inj_ids]), 39))
        self.assertEqual((a4[u"Core-P(P16。材料の記録 material_2026-10-20.json)が参照先を出す行"][u"分子"]), len(pp16))
        # P16 の数は材料の記録(committed)の席の前に出せる分から門が数える
        mat = jload(MAT)
        p16 = [(p["docID"], rid) for p in mat[u"書類ごと"] for rid, pre in p[u"席の前に出せる分"].items()
               if (p["docID"], rid) in idset and pre["Core"][u"参照先"] is not None]
        self.assertEqual(sorted(p16), sorted(pp16))
        self.assertEqual(len(p16), 4)
        self.assertEqual(a4[u"材料の不変(P20 の材料 対 P16 の材料: task の sha256・注入 id・行 id・注入か・正解)"][u"違った所の件数"], 0)
        self.assertTrue(a4[u"材料の再現(P16 で作り直した材料 対 記録の材料)"][u"席の前に出せる分の Core が全行一致"])
        self.assertEqual(a4[u"材料の再現(P16 で作り直した材料 対 記録の材料)"][u"不変の検査で違った所"], [])
        eg = a4[u"Core-P(P20)の参照先を engine に当てた行"]
        self.assertEqual(eg[u"合計"], len(pp20))
        self.assertEqual(eg[u"注入"][u"行"], len(a4[u"注入の行の明細"]))
        self.assertEqual(eg[u"注入"][u"行"], len([z for z in pp20 if z in inj_ids]))
        self.assertEqual(eg[u"注入"][u"GROUNDED(誤りを通した)"][u"件数"],
                         sum(1 for z in a4[u"注入の行の明細"] if z[u"engine の state"] == "GROUNDED"))
        self.assertEqual(eg[u"無改変"][u"state の分布"], {"VALUE_MISMATCH": 6})
        # 対照
        rows, g_ctl = self.ctl()
        c1c = r[u"対照"][u"S-C1"]
        self.assertEqual((c1c[u"対照を当てた行"], c1c[u"GROUNDED"], c1c[u"分母(封の字)"]), (len(rows), len(g_ctl), 77))
        self.assertEqual(c1c[u"当てられなかった行"], 77 - len(rows))
        self.assertEqual(c1c[u"当てられなかった理由の分布"],
                         {u"率の行(ratio_change に「fact 自身の値」は定義できない)": 32, u"金額の単位でない(単位 None)": 3})
        notg = [x for x in rows if x[u"対照(その fact 自身の値)"][u"state"] != "GROUNDED"]
        self.assertEqual(len(c1c[u"当てた行で GROUNDED でなかった行"]), len(notg))
        self.assertTrue(all(x[u"対照(その fact 自身の値)"][u"reason"].startswith("ambiguous_dimension") for x in notg))
        aux = [x for x in self.p77 if x[u"補助(率の行に recomputed を返した。封の外)"] is not None]
        aux_g = [x for x in aux if x[u"補助(率の行に recomputed を返した。封の外)"][u"state"] == "GROUNDED"]
        ax = c1c[u"補助(封の外): 率の行に engine 自身の recomputed を返した"]
        self.assertEqual((ax[u"当てた行"], ax[u"GROUNDED"]), (len(aux), len(aux_g)))
        c3 = r[u"対照"][u"S-C3"]
        pp_diff = [(x["doc"], x["id"]) for x in self.items if x[u"engine(PP あり)"] != x[u"engine(PP なし)"]]
        self.assertEqual([tuple(z) for z in c3[u"PP あり/なしで変わった行(席が参照先を出した 102 行のうち)"]], pp_diff)
        self.assertEqual(c3[u"うち率でない行"], [])
        self.assertTrue(all(x[u"PP の行"] for x in self.items if (x["doc"], x["id"]) in set(pp_diff)))
        off = {}
        for x in self.p77:
            off[x[u"engine(PP なし)"]["state"]] = off.get(x[u"engine(PP なし)"]["state"], 0) + 1
        self.assertEqual(c3[u"無改変 77 行の state(PP なし)"], dict(sorted(off.items())))
        self.assertEqual(c3[u"無改変 77 行の state(PP あり)"], dict(sorted(st.items())))

    def test_2_cd8_block_is_consistent_and_matches_the_committed_cd8_score(self):
        b = self.r[u"cd8(S-C2)"]
        s8 = jload(CD8_SCORE)[u"採点"]["A"]
        A, Aa = b["A"], b[u"A+α"]
        self.assertEqual(b[u"行の合計"], 192)
        self.assertEqual(b[u"欠け"], 0)
        self.assertTrue(b[u"完走"])
        self.assertTrue(b[u"A の再現(K-C2 の 4 つの数: 誤認定 8 / 85・見逃し 0 / 64・特定 35 / 50・保留 107 / 192)"])
        # A は cd8 の commit 済みの採点(score_2026-10-17.json)と一致
        self.assertEqual((A[u"誤認定"][u"分子"], A[u"誤認定"][u"分母(参照先を出した件)"]),
                         (s8[u"誤認定"][u"分子"], s8[u"誤認定"][u"分母(参照先を出した件)"]))
        self.assertEqual((A[u"見逃し"][u"分子"], A[u"見逃し"][u"分母(注入の件)"]), (s8[u"見逃し"][u"分子"], s8[u"見逃し"][u"分母(注入の件)"]))
        self.assertEqual((A[u"正しい参照先の特定"][u"分子"], A[u"正しい参照先の特定"][u"分母(T5 の件)"]),
                         (s8[u"正しい参照先の特定"][u"分子"], s8[u"正しい参照先の特定"][u"分母(T5 の件)"]))
        self.assertEqual((A[u"保留"][u"分子"], A[u"保留"][u"分母(欠けを外した件)"]), (s8[u"保留"][u"分子"], s8[u"保留"][u"分母(欠けを外した件)"]))
        self.assertEqual((A[u"偽警報"][u"分子"], A[u"偽警報"][u"分母(無改変の件)"]),
                         (s8[u"偽警報(**判定には使わない**)"][u"分子"], s8[u"偽警報(**判定には使わない**)"][u"分母(無改変の件)"]))
        # A+α は A から下げた行の分だけ動く
        n_low = b[u"下げた行"]
        self.assertEqual(n_low, len(b[u"下げた行の ids"]))
        self.assertEqual(n_low, b[u"α-1: 確認済み + 参照先の無改変の行"][u"state の分布"].get("VALUE_MISMATCH", 0))
        self.assertEqual(Aa[u"誤認定"][u"分子"], A[u"誤認定"][u"分子"])
        self.assertEqual(Aa[u"誤認定"][u"分母(参照先を出した件)"], A[u"誤認定"][u"分母(参照先を出した件)"] - n_low)
        self.assertEqual(Aa[u"保留"][u"分子"], A[u"保留"][u"分子"] + n_low)
        for k in (u"見逃し", u"正しい参照先の特定", u"偽警報"):
            self.assertEqual(Aa[k][u"分子"], A[k][u"分子"], k)
        st = b[u"α-1: 確認済み + 参照先の無改変の行"]
        self.assertEqual(sum(st[u"state の分布"].values()), st[u"行"])
        self.assertEqual(b[u"規則が掛かる行"], st[u"行"] + b[u"α-1: 確認済み + 参照先の注入の行(= 見逃し)"][u"行"])
        self.assertEqual(b[u"α-1: 確認済み + 参照先の注入の行(= 見逃し)"][u"行"], A[u"見逃し"][u"分子"])
        self.assertEqual(sum(b[u"全 state(席が参照先を出した行の全部)"].values()), b[u"席が参照先を出した行(判定語は問わない)"])

    def test_3_inputs_are_the_committed_ones_and_unchanged(self):
        u"""席の答え・材料・C0・P20・C1・cd8 の答えと材料が commit のまま(字で留めた sha256)。記録の sha256 とも一致。"""
        r = self.r
        for d in EIGHT:
            self.assertEqual(sha(os.path.join(ANS, "%s_answer.json" % d)), SHA[d], d)
        for fn, h in SHA_CD8_ANS.items():
            self.assertEqual(sha(os.path.join(CD8_ANS, fn)), h, fn)
        self.assertEqual(sha(C0), SHA_C0)
        self.assertEqual(sha(C0P20), SHA_C0P20)
        self.assertEqual(sha(C1), SHA_C1)
        self.assertEqual(sha(MAT), SHA_MAT)
        self.assertEqual(sha(CD8_MAT), SHA_CD8_MAT)
        ins = r[u"入力の sha256(読むだけ。1 文字も直していない)"]
        self.assertEqual(ins[u"席の答え(f0b7140)"], SHA)
        self.assertEqual(ins[u"cd8 の答え"], SHA_CD8_ANS)
        self.assertEqual(ins[u"材料 material_2026-10-20.json"], SHA_MAT)
        self.assertEqual(ins[u"C0 の記録 c0_2026-10-20.json"], SHA_C0)
        self.assertEqual(ins[u"P20 の記録 c0_p20_2026-10-20.json"], SHA_C0P20)
        self.assertEqual(ins[u"C1 の記録 c1_2026-10-20.json"], SHA_C1)
        self.assertEqual(ins[u"cd8 の材料 material_2026-10-17.json"], SHA_CD8_MAT)

    def test_4_every_prediction_verdict_agrees_three_ways(self):
        v = self.verdicts()
        rec = {int(p[u"記号"].split("-")[1]): p[u"当たり"] for p in self.r[PRED]}
        rows = pred_rows(self.doc)
        self.assertEqual(sorted(rec), list(range(1, 10)))
        self.assertEqual(sorted(rows), list(range(1, 10)))
        for n in range(1, 9):
            word = u"**当たり**" if v[n] else u"**外れ**"
            if n == 3:
                # S-3 は記録に判定を入れない(読みは記録の外)。文書の判定とこの門のラベル数えが一致
                self.assertIsNone(rec[3])
            else:
                self.assertEqual(rec[n], v[n], u"S-%d 記録の判定が行から数え直した値と違う" % n)
            self.assertEqual(rows[n][2], word, u"S-%d 文書の判定が数え直した値と違う" % n)
        # S-9 は 3 つ(差分 0 行・覆い・赤)の合成。記録が測った部分(差分 0 行)だけを縛る
        self.assertIsNone(rec[9])
        self.assertIn(rows[9][2], (u"**当たり**", u"**外れ**"))
        if rows[9][2] == u"**当たり**":
            self.assertTrue(self.r[u"engine の留め"][u"一致"])
        # 期待する判定(実測。数を見た後の記録)を字で留める: 外れ 4・当たり 4(+ S-9)
        self.assertEqual([v[n] for n in range(1, 9)], [False, False, True, True, True, False, True, False])

    def test_5_s1_s3_s4_s6_are_recomputed_from_the_rows(self):
        u"""S-1・S-3・S-4・S-6 の判定を、記録の行・C1 の記録の行・READING のラベルから**この門が再計算**して、記録・文書と equal。"""
        r, rows = self.r, pred_rows(self.doc)
        st = self.states(self.p77)
        g = st.get("GROUNDED", 0)
        rec = {p[u"記号"]: p for p in r[PRED]}
        self.assertEqual(rec["S-1"][u"実測"], {u"GROUNDED": g, u"分母": 77, u"率": pctv(g, 77)})
        self.assertEqual(rec["S-1"][u"当たり"], inr(g, 50, 70))
        self.assertFalse(inr(g, 50, 70))
        self.assertEqual(rows[1][1], u"GROUNDED %s" % frac(g, 77))
        # 境界: 50 と 70 は当たり側、49 と 71 は外れ側
        self.assertTrue(inr(50, 50, 70) and inr(70, 50, 70) and not inr(49, 50, 70) and not inr(71, 50, 70))
        # S-3: 記録の VALUE_MISMATCH の行の id = READING のキー。ラベルの数え方
        self.assertEqual(sorted(READING), sorted((x["doc"], x["id"]) for x in self.vm))
        self.assertEqual(len(self.vm), 9)
        labels = self.s3_labels()
        n_seat, n_core = labels.count(u"席の側"), labels.count(u"Core の側")
        self.assertEqual((n_seat, n_core), (8, 1))
        self.assertEqual(rows[3][1], u"VALUE_MISMATCH %d 行のうち席の側 %d・Core の側 %d(読みは記録の外)" % (len(self.vm), n_seat, n_core))
        self.assertEqual(rows[3][2], u"**当たり**" if n_seat * 2 >= len(labels) else u"**外れ**")
        # 半分ちょうど(9 行のうち 4.5)は無い。境界の読み方: 半分以上 = 2 倍して以上
        self.assertTrue(4 * 2 >= 8 and not 3 * 2 >= 8)
        self.assertEqual(rec["S-3"][u"実測"][u"VALUE_MISMATCH の行"], len(self.vm))
        # S-4
        a, b = self.mA, self.mAa
        s4 = rec["S-4"][u"実測"]
        self.assertEqual((s4[u"誤認定"], s4[u"見逃し"], s4[u"特定"], s4[u"保留"], s4[u"期待した保留"]),
                         (b.wrong, b.miss, b.ident, b.held, a.held + len(self.vm)))
        self.assertEqual(rec["S-4"][u"当たり"], True)
        self.assertEqual(rows[4][1], u"誤認定 %s・見逃し %s・特定 %s・保留 %s(A の %d + VM の %d)"
                         % (frac(b.wrong, b.pointed), frac(b.miss, b.inj), frac(b.ident, b.t5), frac(b.held, b.n), a.held, len(self.vm)))
        # A+α の誤認定は『分子は同じ・分母が下げた行の分だけ減る』(率は動く)
        self.assertEqual((a.wrong, b.wrong, a.pointed - b.pointed), (4, 4, 9))
        # S-6
        a4 = r[u"α-4"]
        pp20 = {tuple(z) for z in a4[u"Core-P(P20)が参照先を出す行の ids"]}
        ids90 = {(q["doc"], q["id"]) for q in self.hold90}
        self.assertEqual(len(pp20), 6)
        self.assertEqual(rec["S-6"][u"実測"][u"Core-P(P20)が参照先を出す行"], len(pp20))
        self.assertEqual(rec["S-6"][u"当たり"], inr(len(pp20), 10, 40))
        self.assertFalse(inr(len(pp20), 10, 40))
        self.assertTrue(inr(10, 10, 40) and inr(40, 10, 40) and not inr(9, 10, 40) and not inr(41, 10, 40))
        self.assertEqual(rec["S-6"][u"実測"][u"補助(封の外): 言うことが『一意でない』(参照先 2 本以上)の行"], 4)
        self.assertTrue(pp20 <= ids90)

    # ---- 3. 分数の全部
    def test_6_every_fraction_is_consistent_and_allowed(self):
        r = self.r
        a, b = self.mA, self.mAa
        st = self.states(self.p77)
        ratio = [x for x in self.p77 if x[u"PP の行"]]
        money = [x for x in self.p77 if not x[u"PP の行"] and x[u"材料の単位"] is not None]
        a4 = r[u"α-4"]
        pp20 = {tuple(z) for z in a4[u"Core-P(P20)が参照先を出す行の ids"]}
        pp16 = {tuple(z) for z in a4[u"Core-P(P16。材料の記録)が参照先を出す行の ids"]}
        inj_ids = {(q["doc"], q["id"]) for q in self.hold90 if q[u"注入か"]}
        allowed = {(st.get("GROUNDED", 0), 77), (st.get("VALUE_MISMATCH", 0), 77),
                   (st.get("UNPROVABLE", 0) + st.get("POINTER_NOT_FOUND", 0), 77),
                   (self.states(ratio).get("GROUNDED", 0), len(ratio)),
                   (self.states(money).get("GROUNDED", 0), len(money))}
        for m in (a, b):
            allowed |= {(m.wrong, m.pointed), (m.miss, m.inj), (m.ident, m.t5), (m.held, m.n), (m.fa, m.plain), (m.stop, m.inj)}
        allowed |= {(len(pp20), 90), (len([z for z in pp20 if z not in inj_ids]), 51), (len([z for z in pp20 if z in inj_ids]), 39),
                    (len(pp16), 90)}
        rows, g_ctl = self.ctl()
        allowed.add((len(g_ctl), len(rows)))
        aux = [x for x in self.p77 if x[u"補助(率の行に recomputed を返した。封の外)"] is not None]
        allowed.add((sum(1 for x in aux if x[u"補助(率の行に recomputed を返した。封の外)"][u"state"] == "GROUNDED"), len(aux)))
        c = r[u"cd8(S-C2)"]
        for k, f in ((u"誤認定", u"分母(参照先を出した件)"), (u"見逃し", u"分母(注入の件)"), (u"正しい参照先の特定", u"分母(T5 の件)"),
                     (u"保留", u"分母(欠けを外した件)"), (u"偽警報", u"分母(無改変の件)")):
            for arm in ("A", u"A+α"):
                allowed.add((c[arm][k][u"分子"], c[arm][k][f]))
        s = c[u"α-1: 確認済み + 参照先の無改変の行"]
        for state in ("GROUNDED", "VALUE_MISMATCH", "UNPROVABLE"):
            allowed.add((s[u"state の分布"].get(state, 0), s[u"行"]))
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 40)
        for x, y, pc in found:
            xi, yi = int(x.replace(",", "")), int(y.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * xi / yi), pc, u"算術が合わない: %s / %s = %s%%" % (x, y, pc))
            self.assertIn((xi, yi), allowed, u"記録から作れない分数: %s / %s" % (x, y))

    # ---- 4. 予測表の各行
    def test_7_prediction_table_cells_equal_the_record_in_order(self):
        rows, seal = pred_rows(self.doc), seal_rows(self.seal)
        a, b = self.mA, self.mAa
        st = self.states(self.p77)
        hold = st.get("UNPROVABLE", 0) + st.get("POINTER_NOT_FOUND", 0)
        a4 = self.r[u"α-4"]
        pp20 = {tuple(z) for z in a4[u"Core-P(P20)が参照先を出す行の ids"]}
        pp16 = {tuple(z) for z in a4[u"Core-P(P16。材料の記録)が参照先を出す行の ids"]}
        inj_ids = {(q["doc"], q["id"]) for q in self.hold90 if q[u"注入か"]}
        rws, g_ctl = self.ctl()
        n_inj_pp = len([z for z in pp20 if z in inj_ids])
        n_pl_pp = len([z for z in pp20 if z not in inj_ids])

        def f(x, y):
            return [str(x), str(y), "%.1f" % (100.0 * x / y)]
        exp = {
            1: f(st.get("GROUNDED", 0), 77),
            2: f(st.get("VALUE_MISMATCH", 0), 77) + f(hold, 77)[:1] + ["77", "%.1f" % (100.0 * hold / 77)]
               + [str(st.get("UNPROVABLE", 0)), str(st.get("POINTER_NOT_FOUND", 0))],
            3: [str(len(self.vm)), str(self.s3_labels().count(u"席の側")), str(self.s3_labels().count(u"Core の側"))],
            4: f(b.wrong, b.pointed) + f(b.miss, b.inj) + f(b.ident, b.t5) + f(b.held, b.n) + [str(a.held), str(len(self.vm))],
            5: f(b.fa, b.plain),
            6: f(len(pp20), 90) + f(n_pl_pp, 51) + f(n_inj_pp, 39) + f(len(pp16), 90),
            7: [],
            8: [str(len(g_ctl)), str(len(rws)), "%.1f" % (100.0 * len(g_ctl) / len(rws)), str(len(rws)), "77", str(77 - len(rws)), "0", "0"],
        }
        # S-7 の 38・1 は Core-P の言うこと(記録 S-7 の実測)から
        s7 = [p for p in self.r[PRED] if p[u"記号"] == "S-7"][0][u"実測"]
        said = s7[u"注入の行の Core-P の言うこと"]
        self.assertEqual(said, {u"対応が付かない": 38, u"参照先を出さない(POINTER_NOT_FOUND)": 1})
        exp[7] = [str(s7[u"GROUNDED"]), str(s7[u"engine を当てた注入の行"]), "39", "39",
                  str(said[u"対応が付かない"]), str(said[u"参照先を出さない(POINTER_NOT_FOUND)"])]
        self.assertTrue(s7[u"空振り(engine を当てた注入の行が 0)"])
        for n in range(1, 9):
            self.assertEqual(nums(rows[n][1]), list(exp[n]), u"S-%d 実測欄の数" % n)
        # S-6 の括弧の中の無改変・注入・P16 は f() の分子・分母・率。S-6 は上で全部並べた
        for n in range(1, 10):
            # 予測欄は封の同じ行の字と**同じ**(書き換えると赤)
            self.assertEqual(rows[n][0], seal[n], u"S-%d 予測欄が封の字と違う" % n)
        v = self.verdicts()
        hit = sum(1 for n in range(1, 9) if v[n]) + (1 if rows[9][2] == u"**当たり**" else 0)
        self.assertEqual(once(self.doc, r"\*\*当たり (\d+) / 外れ (\d+)。\*\*"), (str(hit), str(9 - hit)))

    # ---- 5. α-2 の表
    def test_8_alpha2_table_rows_equal_the_record(self):
        sc = sec(self.secs, u"α-2")
        lines = re.findall(r"(?m)^\| (S100\w+-R\d+) \| ([^|]+?) \| `([^`]+)` \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", sc)
        self.assertEqual(len(lines), 9)
        want = {"%s-%s" % (x["doc"], x["id"]): x for x in self.vm}
        self.assertEqual(sorted(z[0] for z in lines), sorted(want))
        self.assertEqual(sorted(want), sorted("%s-%s" % k for k in READING))
        for rid, claim, ptr, pv, partner, diff, label in lines:
            x = want[rid]
            rd = x[READ]
            self.assertEqual(label, READING[(x["doc"], x["id"])], rid)
            raw = x[u"参照先(原文)"]
            if u"…" in ptr:
                head, tail = ptr.split(u"…")
                self.assertTrue(raw.startswith(head) and raw.endswith(tail), rid)
            else:
                self.assertEqual(ptr, raw, rid)
            self.assertEqual(money_fmt(rd[u"参照先の fact"]["value"]), pv, rid)
            if x[u"PP の行"]:
                self.assertEqual(claim, u"%s%% 増" % x[u"数の字面"], rid)
                dv = rd[u"PP が派生させた参照先の fact"]
                self.assertEqual(len(dv), 1, rid)
                self.assertTrue(partner.startswith(money_fmt(dv[0]["value"])), rid)
                self.assertEqual(diff, u"PP の再計算 %s" % x[u"engine の recomputed"], rid)
                self.assertTrue(float(x[u"engine の recomputed"]) != float(x[u"材料の値"]))
            else:
                self.assertEqual(claim, u"%s%s" % (u"{:,}".format(int(x[u"材料の値"])), x[u"材料の単位"]), rid)
                pd = rd[PERIOD_DIFF]
                self.assertTrue(len(pd) >= 1, rid)
                self.assertEqual(len({(z[u"その fact の値"], z[u"2 つの fact の差の絶対値"]) for z in pd}), 1, rid)
                self.assertEqual(money_fmt(pd[0][u"その fact の値"]), partner, rid)
                self.assertEqual(money_fmt(pd[0][u"2 つの fact の差の絶対値"]), diff, rid)
                scale = {u"千円": 1000, u"百万円": 1000000}[x[u"材料の単位"]]
                # 『差が主張に合う』= 差と主張(基準単位)の差が 1 単位以内
                self.assertTrue(abs(pd[0][u"2 つの fact の差の絶対値"] - pd[0][u"主張の値(基準単位)"]) <= scale, rid)
                self.assertTrue(abs(rd[u"参照先の fact"]["value"] - x[u"材料の値"] * scale) > scale, rid)
        # 読みの文: 席の側 8・Core の側 1 の数
        self.assertEqual(once(self.doc, r"VALUE_MISMATCH の (\d+) 行のうち (\d+) 行は『席の参照先が、文の数の持ち主ではない』、(\d+) 行は『Core の検算の側\(丸め\)』"),
                         S(len(self.vm), self.s3_labels().count(u"席の側"), self.s3_labels().count(u"Core の側")))
        self.assertIn(u"**読みは記録の外・門で縛れない**", self.doc)
        self.assertIn(u"各行の読みが正しいことは門では確かめられない", sc)

    # ---- 6. 表・本文中の件数
    def test_9_tables_and_prose_counts_equal_the_record(self):
        d, r = self.doc, self.r
        st = self.states(self.p77)
        a, b = self.mA, self.mAa
        hold = st.get("UNPROVABLE", 0) + st.get("POINTER_NOT_FOUND", 0)
        self.assertEqual(once(d, r"の出力、全体 ([\d.]+) 秒\)"), "%.1f" % r[u"所要秒"][u"全体"])
        self.assertEqual(once(d, r"本番、全体 ([\d.]+) 秒\)"), "%.1f" % r[u"所要秒"][u"全体"])
        # 先頭 1.
        self.assertEqual(once(d, r"裏づけたのは (\d+) / (\d+) = [\d.]+%\(予測は"), S(st.get("GROUNDED", 0), 77))
        self.assertEqual(once(d, r"食い違い\(VALUE_MISMATCH\)は (\d+) / (\d+) = [\d.]+%、保留\(UNPROVABLE\)は (\d+) / (\d+) = [\d.]+%、POINTER_NOT_FOUND は (\d+)"),
                         S(st.get("VALUE_MISMATCH", 0), 77, st.get("UNPROVABLE", 0), 77, st.get("POINTER_NOT_FOUND", 0)))
        reasons = self.r[u"α-1"][u"UNPROVABLE の理由の分布"]
        n_d = sum(v for k, v in reasons.items() if k.startswith("ambiguous_dimension"))
        n_unit = sum(v for k, v in reasons.items() if k.startswith(u"規則 単一の値(金額)"))
        n_prior = sum(v for k, v in reasons.items() if k.startswith("prior_sibling"))
        self.assertEqual(n_d + n_unit + n_prior, st.get("UNPROVABLE", 0))
        self.assertEqual(once(d, r"保留 (\d+) のうち (\d+) は保留規則 \(d\)\([^)]*\)、(\d+) は単位が無い主張\([^)]*\)、(\d+) は率の主張で前期の兄弟が無い"),
                         S(hold, n_d, n_unit, n_prior))
        # 先頭 3.
        self.assertEqual(once(d, r"A\+α の誤認定は (\d+) / (\d+) = [\d.]+%\(A は (\d+) / (\d+) = [\d.]+%。分母が (\d+) 減っただけで分子は同じ\)"),
                         S(b.wrong, b.pointed, a.wrong, a.pointed, a.pointed - b.pointed))
        self.assertEqual(once(d, r"見逃し (\d+) / (\d+) = [\d.]+%、特定 (\d+) / (\d+) = [\d.]+%、保留 (\d+) / (\d+) = [\d.]+%\(A は (\d+) / (\d+) = [\d.]+%。\+(\d+)\)、偽警報 (\d+) / (\d+)"),
                         S(b.miss, b.inj, b.ident, b.t5, b.held, b.n, a.held, a.n, b.held - a.held, b.fa, b.plain))
        self.assertEqual(once(d, r"注入の行に 1 件も無い\(見逃し (\d+) / (\d+)\)"), S(a.miss, a.inj))
        # 先頭 4.
        a4 = r[u"α-4"]
        pp20 = {tuple(z) for z in a4[u"Core-P(P20)が参照先を出す行の ids"]}
        pp16 = {tuple(z) for z in a4[u"Core-P(P16。材料の記録)が参照先を出す行の ids"]}
        inj_ids = {(q["doc"], q["id"]) for q in self.hold90 if q[u"注入か"]}
        self.assertEqual(once(d, r"参照先を出した行は (\d+) / (\d+) = [\d.]+%\(幅 10〜40\)"), S(len(pp20), 90))
        self.assertEqual(once(d, r"無改変の 51 行で (\d+) / (\d+) = [\d.]+%、注入の 39 行で (\d+) / (\d+) = [\d.]+%。P16 の材料は (\d+) / (\d+) = [\d.]+%"),
                         S(len([z for z in pp20 if z not in inj_ids]), 51, len([z for z in pp20 if z in inj_ids]), 39, len(pp16), 90))
        # 先頭 5.
        rws, g_ctl = self.ctl()
        self.assertEqual(once(d, r"当てた (\d+) 行のうち GROUNDED は (\d+) / (\d+) = [\d.]+%"), S(len(rws), len(g_ctl), len(rws)))
        self.assertEqual(once(d, r"率の行 (\d+) と単位が無い行 (\d+) は C1-3 の作りでは当てられない"), S(32, 3))
        # α-1 の表(書類ごと・行の種類ごと)
        s1 = sec(self.secs, u"α-1")
        for dd in EIGHT:
            rows = [x for x in self.p77 if x["doc"] == dd]
            sub = self.states(rows)
            line = once(s1, r"(?m)^(\| %s \|.*)$" % dd)
            self.assertEqual(cells_of(line), [dd, str(len(rows)), str(sub.get("GROUNDED", 0)), str(sub.get("VALUE_MISMATCH", 0)),
                                              str(sub.get("UNPROVABLE", 0))], dd)
        ratio = [x for x in self.p77 if x[u"PP の行"]]
        money = [x for x in self.p77 if not x[u"PP の行"] and x[u"材料の単位"] is not None]
        unitless = [x for x in self.p77 if x[u"材料の単位"] is None]
        for lab, rows in ((u"率の行(単位 %)", ratio), (u"金額の行", money), (u"単位が無い行", unitless)):
            sub = self.states(rows)
            line = once(s1, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            self.assertEqual(cells_of(line), [lab, str(len(rows)), str(sub.get("GROUNDED", 0)), str(sub.get("VALUE_MISMATCH", 0)),
                                              str(sub.get("UNPROVABLE", 0))], lab)
        self.assertEqual(once(s1, r"率の行の GROUNDED (\d+) / (\d+) = [\d.]+% は PP"), S(self.states(ratio).get("GROUNDED", 0), len(ratio)))
        off = {}
        for x in self.p77:
            off[x[u"engine(PP なし)"]["state"]] = off.get(x[u"engine(PP なし)"]["state"], 0) + 1
        self.assertEqual(once(s1, r"GROUNDED は (\d+)\(金額の行だけ\)・UNPROVABLE (\d+)・VALUE_MISMATCH (\d+) になる"),
                         S(off.get("GROUNDED", 0), off.get("UNPROVABLE", 0), off.get("VALUE_MISMATCH", 0)))
        self.assertEqual(once(s1, r"UNPROVABLE (\d+) の理由: \(d\)\(`ambiguous_dimension`\)(\d+) = 金額の行 (\d+) \+ 率の行 (\d+)、単位が無い (\d+)"),
                         S(st.get("UNPROVABLE", 0), n_d,
                           sum(1 for x in money if str(x[u"engine の reason"]).startswith("ambiguous_dimension")),
                           sum(1 for x in ratio if str(x[u"engine の reason"]).startswith("ambiguous_dimension")), n_unit))
        self.assertEqual(once(s1, r"製品の経路の held\(GROUNDED を保留に下げた行\)は (\d+)"), str(r[u"α-1"][u"held(製品の経路)"]))
        self.assertEqual(once(s1, r"state は VALUE_MISMATCH (\d+)・UNPROVABLE (\d+) で"),
                         S(self.states(self.inj25).get("VALUE_MISMATCH", 0), self.states(self.inj25).get("UNPROVABLE", 0)))
        # A 対 A+α の表
        s3 = sec(self.secs, u"腕 A 対 腕 A+α")
        for lab, ka, kb in ((u"誤認定", frac(a.wrong, a.pointed), frac(b.wrong, b.pointed)),
                            (u"見逃し", frac(a.miss, a.inj), frac(b.miss, b.inj)),
                            (u"特定", frac(a.ident, a.t5), frac(b.ident, b.t5)),
                            (u"保留", frac(a.held, a.n), frac(b.held, b.n)),
                            (u"偽警報", frac(a.fa, a.plain), frac(b.fa, b.plain)),
                            (u"軸A 停止判定", frac(a.stop, a.inj), frac(b.stop, b.inj))):
            line = once(s3, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            cl = cells_of(line)
            self.assertEqual((cl[0], cl[1], cl[2]), (lab, ka, kb), lab)
        self.assertEqual(once(s3, r"規則が掛かる行\(席が `確認済み` \+ 参照先\)は (\d+)。engine が VALUE_MISMATCH の (\d+) 行を"),
                         S(77, len(self.vm)))
        self.assertEqual(once(s3, r"分母が (\d+) から (\d+) に減るだけで率が ([\d.]+)% から ([\d.]+)% に動いた"),
                         S(a.pointed, b.pointed, "%.1f" % pctv(a.wrong, a.pointed), "%.1f" % pctv(b.wrong, b.pointed)))
        # α-4 の表
        s4 = sec(self.secs, u"α-4")
        n_pl = len([z for z in pp20 if z not in inj_ids])
        n_in = len([z for z in pp20 if z in inj_ids])
        for lab, num in ((u"Core-P(P20)が参照先を出す行", frac(len(pp20), 90)), (u"うち無改変", frac(n_pl, 51)),
                         (u"うち注入", frac(n_in, 39)), (u"(参考)Core-P(P16。記録の材料)が参照先を出す行", frac(len(pp16), 90))):
            line = once(s4, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            self.assertEqual(cells_of(line)[1], num, lab)
        self.assertEqual(once(s4, r"S100Z4GF の (\d+) 行\(R016・R017\)と S100YYUD の (\d+) 行\(R005・R007・R009・R012\)"),
                         S(len([z for z in pp20 if z[0] == "S100Z4GF"]), len([z for z in pp20 if z[0] == "S100YYUD"])))
        self.assertEqual(sorted(pp20), sorted([("S100Z4GF", "R016"), ("S100Z4GF", "R017"), ("S100YYUD", "R005"), ("S100YYUD", "R007"),
                                               ("S100YYUD", "R009"), ("S100YYUD", "R012")]))
        self.assertEqual(sorted(pp16), sorted([("S100YYUD", "R005"), ("S100YYUD", "R007"), ("S100YYUD", "R009"), ("S100YYUD", "R012")]))
        # cd8 の表
        s8 = sec(self.secs, u"cd8")
        c = r[u"cd8(S-C2)"]
        for lab, k, f in ((u"誤認定", u"誤認定", u"分母(参照先を出した件)"), (u"見逃し", u"見逃し", u"分母(注入の件)"),
                          (u"特定", u"正しい参照先の特定", u"分母(T5 の件)"), (u"保留", u"保留", u"分母(欠けを外した件)"),
                          (u"偽警報", u"偽警報", u"分母(無改変の件)")):
            line = once(s8, r"(?m)^(\| %s \|.*)$" % re.escape(lab))
            cl = cells_of(line)
            self.assertEqual(cl[1:3], [frac(c["A"][k][u"分子"], c["A"][k][f]), frac(c[u"A+α"][k][u"分子"], c[u"A+α"][k][f])], lab)
        sd = c[u"α-1: 確認済み + 参照先の無改変の行"]
        n8 = sd[u"行"]
        self.assertEqual(once(s8, r"席が `確認済み` \+ 参照先の無改変の行は (\d+)。state は GROUNDED (\d+) / (\d+) = [\d.]+%・VALUE_MISMATCH (\d+) / (\d+) = [\d.]+%・UNPROVABLE (\d+) / (\d+) = [\d.]+%。α が下げたのは (\d+) 行"),
                         S(n8, sd[u"state の分布"]["GROUNDED"], n8, sd[u"state の分布"]["VALUE_MISMATCH"], n8, sd[u"state の分布"]["UNPROVABLE"], n8, c[u"下げた行"]))
        self.assertEqual(once(s8, r"席が参照先を出した行\(判定語は問わない\)(\d+) の state は GROUNDED (\d+)・UNPROVABLE (\d+)・VALUE_MISMATCH (\d+)"),
                         S(c[u"席が参照先を出した行(判定語は問わない)"], c[u"全 state(席が参照先を出した行の全部)"]["GROUNDED"],
                           c[u"全 state(席が参照先を出した行の全部)"]["UNPROVABLE"], c[u"全 state(席が参照先を出した行の全部)"]["VALUE_MISMATCH"]))
        # 対照の節
        sc = sec(self.secs, u"対照")
        self.assertEqual(once(sc, r"S-C1\(期待 77 / 77、外れ\)\*\*: 『その fact 自身の値』を当てられる行は、金額の単位を持つ行 (\d+)。この (\d+) 行のうち GROUNDED は (\d+) / (\d+) = [\d.]+%"),
                         S(len(rws), len(rws), len(g_ctl), len(rws)))
        self.assertEqual(once(sc, r"当てた (\d+) 行で GROUNDED でなかった (\d+) 行は、全部 `ambiguous_dimension`"),
                         S(len(rws), len(rws) - len(g_ctl)))
        aux = [x for x in self.p77 if x[u"補助(率の行に recomputed を返した。封の外)"] is not None]
        aux_g = [x for x in aux if x[u"補助(率の行に recomputed を返した。封の外)"][u"state"] == "GROUNDED"]
        self.assertEqual(once(sc, r"当てた (\d+) 行のうち GROUNDED (\d+) / (\d+) = [\d.]+%\(残りは"),
                         S(len(aux), len(aux_g), len(aux)))
        n_pp = len([x for x in self.items if x[u"engine(PP あり)"] != x[u"engine(PP なし)"]])
        self.assertEqual(once(sc, r"PP あり/なしで結果が変わった行は (\d+)、全部率の行"), str(n_pp))
        self.assertEqual(once(d, r"P20 の run は (\d+) 行だけ Core の言うことが違う"), str(a4[u"P16 と P20 で参照先が違う行の件数"]))

    def test_10_controls_env_and_engine_pins(self):
        r = self.r
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
        self.assertTrue(r[u"対照"][u"α-C1(注入 25 行が C1-3 の記録と一致)"][u"一致"])
        self.assertTrue(r[u"対照"][u"α-C2(P16 で作り直した材料が記録の材料と一致)"][u"一致"])
        self.assertTrue(r[u"対照"][u"S-C2"][u"完走・欠け 0・A の再現"])
        d = self.doc
        self.assertIn(u"API key は 4 つとも未設定(0)", d)
        self.assertIn(u"席(LLM API)は 1 回も呼んでいない", d)
        self.assertEqual(once(d, r"ac8c3ff と sha256 が違う file (\d+)、"), str(len(pins[u"作業木で sha256 が違う file"])))
        # 記録の limits が主要な限界を言っている
        lim = u"".join(r["limits"])
        for lit in (u"無改変 77 行に正解の参照先は無い", u"席 1 席 × 1 便", u"S-7 の 0 は engine の独立した証拠ではない",
                    u"α-2 の読み", u"S-C1 は率の行"):
            self.assertIn(lit, lim, lit)

    def test_11_the_document_keeps_its_honesty_clauses(self):
        d = self.doc
        for lit in (u"**封は 1 文字も直していない。**", u"## 手順の正直な記録", u"## 迷った点", u"## 限界",
                    u"## 次の判断材料", u"「改善する」とは書かない", u"## 今回新しく分かったこと",
                    u"縛っていない数", u"**外れは外れのまま書く。**", u"**読みは記録の外・門で縛れない**",
                    u"当てた注入の行が 0 の空振り", u"**この採点では、α が行を下げても利益が数に出ない。**",
                    u"封 C-3 の条件(S-1 当たり ∧ S-3 当たり)は満たしていない",
                    u"S-7 の 0 は engine の独立した証拠ではない", u"**無改変の 77 行に正解の参照先は無い。**"):
            self.assertIn(lit, d, lit)
        i = d.index(u"## 今回新しく分かったこと")
        j = d.index(u"## 予測 S-1〜S-9 の照合")
        head = d[i:j]
        self.assertTrue(head.index(u"1. **S-1") < head.index(u"5. **S-8"))
        # 『良くなった』『改善した』『持ち直した』と書かない(肯定文として)
        for bad in (u"持ち直した。", u"改善した。", u"良くなった", u"上回った**", u"α を入れるべき", u"α は有効"):
            self.assertNotIn(bad, d, bad)
        self.assertNotIn(u"@@", d)


if __name__ == "__main__":
    unittest.main()
