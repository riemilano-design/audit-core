# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)段 1 の結果文書(docs/XBRL_HYBRID_TRUST_RESULT_2026-10-20.md)の数を記録に縛る門。

記録: ``fixtures/xbrl/gen_c/hybrid_trust_2026-10-20.json``(``measure/xbrl_hybrid_trust_2026-10-20.py`` の出力)。
封: ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md``(予測の幅は**封の字から読む**。この門に写さない)。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 記録の行 384 本を、入力(席の字の記録・材料)と突き合わせる(席の判定・注入か・正解・P16 の Core)。
  2. 合成 H の規則・3 群を**行から再適用**して、記録の ``H の出力``・``群`` の欄と一致させる(欄を信じない)。
  3. 記録の集計の欄を、行から数え直した値と突き合わせる。
  4. 予測 H-1〜H-8 の当たり/外れを、行と封の幅から**門が自分で**判定し、記録の判定・文書の判定の 3 つが一致する。
  5. 文書の予測表の予測欄は封の字と同じ。実測欄の数は、行から数えた値と順序つきで一致。
  6. 文書の表の行(§2〜§6)は、行から作った字と完全一致。分数 ``a / b = x.x%`` は算術として合い、許可集合に入る。
  7. 入力の sha256 を**字で留める**。engine の留めは記録の**事実**として縛る(いまの作業木との生の比較は置かない)。
  8. VALUE_MISMATCH の読みのラベルは**この門が字で持つ**(人の読み)。縛るのは行の対応と機械的な目印だけ。
"""
import ast
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
REC = os.path.join(GEN, "hybrid_trust_2026-10-20.json")
DOC = os.path.join(ROOT, "docs", "XBRL_HYBRID_TRUST_RESULT_2026-10-20.md")
SEAL = os.path.join(ROOT, "docs", "XBRL_HYBRID_TRUST_SEAL_2026-10-20.md")
SCRIPT = os.path.join(ROOT, "measure", "xbrl_hybrid_trust_2026-10-20.py")
ALPHA = os.path.join(GEN, "alpha_2026-10-20.json")
SEAT_REC = {u"gen_c": os.path.join(GEN, "c1_2026-10-20.json"), u"cd8": os.path.join(CD8, "score_2026-10-17.json")}
MAT = {u"gen_c": os.path.join(GEN, "material_2026-10-20.json"), u"cd8": os.path.join(CD8, "material_2026-10-17.json")}
SETS = (u"gen_c", u"cd8")

#: commit 済みの file の sha256。**字で留める**(定数から作らない)。
SHA_ANS = {
    u"gen_c": {
        "S100YYN7_answer.json": "784a40dbcb7e037b719aed0a7c9f500fd8078f90af22692ed5293d9bab1fdc98",
        "S100YYT4_answer.json": "02aa3cc939ed7fbe85fcd7975ba260c8b551c6a1f4680f4247c593d1bf43ae8a",
        "S100YYT8_answer.json": "6a6453aad09154dfdd71e84e6f6710280bc30d6c5e2b7540d02a38c7ce3bf4fc",
        "S100YYUD_answer.json": "04bca508a8dbbca062daff1e3c7f0e7ab9aae6362753252a5b3ccdacb50e8a8a",
        "S100Z0OS_answer.json": "82d846ff004a0303fde95d1c745bf89f5387b98c60ce16f6f965792ad0610a23",
        "S100Z42X_answer.json": "a515ace495c1a790dde7b5f8fd12449ee103d02033c318dd0723b0d0a9966831",
        "S100Z4GF_answer.json": "252fbe466dffb6de48ea1d4517605f5ce060063c53517deb24884dcdc4cc0262",
        "S100Z4J8_answer.json": "16dc09e69c5a4b99021981758573a5c86ba0c129d735bf384a69f3b1fa932c67"},
    u"cd8": {
        "S100YWGX_answer.json": "52aeac8183593533b7d9dd470bebd18195f11421b672603aab4279c4973dcd16",
        "S100YXF5_answer.json": "864f7e507b7de1be1d1200b44a3244d76fab9787d0605157082fec6ee09aed53",
        "S100YXMA_answer.json": "775bf942c2620360fcc0d6ac26b20637892eb617fc281f6a3f349748844784a4",
        "S100YYRG_answer.json": "9bc7db15998b4939bf9542bf4e695135d4e2e618558a5ebf68d8995559d78a66",
        "S100YYRV_answer.json": "f643a928c800cfa74aeff034f5f001d980ef746a55d0d17adf8536db5edf5587",
        "S100YZ7E_answer.json": "1e06e97bf694cd8afff4f3d1f6a6381915dd4ee45563734f1c5f7bfe3baf0105",
        "S100YZCT_answer.json": "97e06eee0f1a70dea605a147d984a1e2a1c4d7dc16d7b0379bff116cf0952a86",
        "S100YZEV_answer.json": "eba2f890515176b691c810d477c4cc27792a77a4526525d7440736a35fcc6f80"}}
SHA_MAT = {u"gen_c": "2a33dd21f252de15651168a015147c5206bf92ec676a6f8142a4ecd14f067d37",
           u"cd8": "d0538c551627e13dc14df513c401009ac58b722163aaa6523a3256dd099a06b4"}
SHA_SEAT_REC = {u"gen_c": "4f6141aaeffa87ded81247902d498a6591270bc7036390ea22d8d9bc8683f0d4",
                u"cd8": "27dba615e3800ccfd06082564911ee4f9b974715115364738d611fdb9b33cda5"}
SHA_ALPHA = "a03eb125624f8aeb53f7ffad70b70fa5c19432f9442cf19b266fed91c9872347"
SHA_DRAW = {u"gen_c": "025945ccb39bac8e63d801d871ec55e77442746344ce02af327c6219843a7a8c",
            u"cd8": "773c58e3f44879f817fb7a3fc1e8f71c5309f6ba7352191e07d8a0008aa16919"}
SHA_SEAL = "4ca1b7b7ad47a152e6efc30a9758001ebdbf1a3e44e1ee06bdf322a80bb69ba8"
ENGINE_BUNDLE = "5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee"

#: VALUE_MISMATCH の読み(**この門が字で持つラベル。人の読みで、記録の外・門で縛れない**)。
READING = {
    (u"gen_c", "S100YYN7", "R006"): u"Core の側",
    (u"gen_c", "S100YYT4", "R002"): u"席の側",
    (u"gen_c", "S100YYT4", "R004"): u"席の側",
    (u"gen_c", "S100Z4J8", "R002"): u"席の側",
    (u"gen_c", "S100Z4J8", "R006"): u"席の側",
    (u"gen_c", "S100Z4J8", "R009"): u"席の側",
    (u"gen_c", "S100Z4J8", "R012"): u"席の側",
    (u"gen_c", "S100Z4J8", "R015"): u"席の側",
    (u"gen_c", "S100Z4J8", "R017"): u"席の側",
    (u"cd8", "S100YZEV", "R017"): u"席の側",
}
ORDER = (u"GROUNDED", u"VALUE_MISMATCH", u"UNPROVABLE", u"UNVERIFIABLE", u"POINTER_NOT_FOUND", u"対応なし", u"参照先なし")
NUM_RE = re.compile(r"(?<![A-Za-z\d§])\d[\d,]*(?:\.\d+)?")
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")


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
    u"""``F`` の 3 つの数の字。"""
    return [str(a), str(b), "%.1f" % (100.0 * a / b)]


def nums(cell):
    return NUM_RE.findall(cell)


def inr(x, lo_hi):
    return lo_hi[0] <= x <= lo_hi[1]


def pairs(s):
    u"""封の予測の字の ``**a〜b`` を順に拾う。"""
    return [(int(a), int(b)) for a, b in re.findall(r"\*\*(\d+)〜(\d+)", s)]


def seal_pred(seal, h):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % h):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")][1]
    raise AssertionError(h)


def brk(counter):
    return u"・".join(u"%s %d" % (k, counter[k]) for k in ORDER if counter.get(k))


def h_of(seat, ok):
    if seat == u"誤りが在る":
        return u"誤り(席)"
    if seat == u"確認済み":
        return u"二重確認" if ok else u"警告"
    if seat == u"判定できない":
        return u"Core のみ確認" if ok else u"保留"
    raise AssertionError(seat)


def cell_row(doc, h):
    for l in doc.splitlines():
        if l.startswith(u"| **%s** |" % h):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(h)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rows = cls.rec[u"行"]
        cls.doc = text(DOC)
        cls.seal = text(SEAL)
        cls.agg = cls.rec[u"集計"]
        cls.con = cls.rec[u"対照(P16 明示)"]
        cls.vm = cls.rec[u"VALUE_MISMATCH の行(α 型・G3。読みの材料つき)"]
        cls.preds = {p[u"記号"]: p for p in cls.rec[u"**予測 H-1〜H-8**"]}

    def of(self, n):
        return [r for r in self.rows if r[u"集合"] == n]

    def groups(self, n, field):
        g1 = [r for r in self.of(n) if r[u"席の判定"] == u"確認済み"]
        return {u"G1": g1, u"G2": [r for r in g1 if r[field] == u"GROUNDED"],
                u"G3": [r for r in g1 if r[field] != u"GROUNDED"]}

    @property
    def alpha_f(self):
        return u"α 型の state"

    @property
    def self_f(self):
        return u"Core 自身(既定)の state"

    def GA(self, n):
        return self.groups(n, self.alpha_f)

    def GS(self, n):
        return self.groups(n, self.self_f)

    def prec(self, m):
        return F(sum(1 for r in m if not r[u"注入か"]), len(m))


class InputsTest(Base):
    def test_1_inputs_pinned_literally(self):
        inp = self.rec[u"入力の sha256(読むだけ。1 文字も直していない)"]
        for n, d in ((u"gen_c", GEN), (u"cd8", CD8)):
            self.assertEqual(inp[u"席の答え"][n], SHA_ANS[n], n)
            for fn, h in SHA_ANS[n].items():
                self.assertEqual(sha(os.path.join(d, "seat_answers", fn)), h, fn)
            self.assertEqual(inp[u"材料"][n], SHA_MAT[n])
            self.assertEqual(sha(MAT[n]), SHA_MAT[n])
            self.assertEqual(sha(SEAT_REC[n]), SHA_SEAT_REC[n])
            self.assertEqual(inp[u"draw"][n], SHA_DRAW[n])
        self.assertEqual(sorted(inp[u"席の字の記録(rows の 席)"].values()), sorted(SHA_SEAT_REC.values()))
        self.assertEqual(inp[u"α 型の記録(読むだけ)"], SHA_ALPHA)
        self.assertEqual(sha(ALPHA), SHA_ALPHA)
        self.assertEqual(inp[u"封"], SHA_SEAL)
        self.assertEqual(sha(SEAL), SHA_SEAL)

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
        self.assertTrue(pins[u"HEAD"].startswith("4a4df01"))
        self.assertEqual(pins[u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)"], ENGINE_BUNDLE)
        self.assertEqual(pins[u"core/ と adapters/ の追跡 file 数"], 36)


class RowsTest(Base):
    def test_3_rows_match_the_inputs(self):
        self.assertEqual(len(self.rows), 384)
        for n in SETS:
            seat = {(r["doc"], r["id"]): r for r in jload(SEAT_REC[n])["rows"]}
            mat = jload(MAT[n])
            core = {}
            gold = {}
            for p in mat[u"書類ごと"]:
                for rid, pre in p[u"席の前に出せる分"].items():
                    core[(p["docID"], rid)] = pre["Core"]
                    gold[(p["docID"], rid)] = pre[u"正解"]
            mine = self.of(n)
            self.assertEqual(len(mine), 192, n)
            self.assertEqual({(r["doc"], r["id"]) for r in mine}, set(seat), n)
            for r in mine:
                k = (r["doc"], r["id"])
                self.assertEqual(r[u"注入か"], bool(seat[k][u"注入か"]), k)
                self.assertEqual(r[u"席の判定"], seat[k][u"席"][u"判定"], k)
                self.assertEqual(r[u"席の参照先"], seat[k][u"席"][u"参照先"], k)
                self.assertEqual(r[u"正解"], gold[k], k)
                c = core[k]
                self.assertEqual(r[u"Core 自身(P16 明示)の state"], c.get("state") or u"対応なし", k)   # H-7 前半
                self.assertEqual((r[u"α 型の state"] == u"参照先なし"), seat[k][u"席"][u"参照先"] is None, k)

    def test_4_rule_h_and_groups_reapplied_from_rows(self):
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
        # 0 を疑う: G1 の行は全部 α 型が効く(参照先を出している)。注入の行にも α 型は当たっている
        for n in SETS:
            self.assertEqual(sum(1 for r in self.of(n) if r[u"G1(席が確認済み)"] and r[u"α 型の state"] == u"参照先なし"), 0)
        self.assertEqual(sum(1 for r in self.of(u"gen_c") if r[u"注入か"] and r[u"α 型の state"] != u"参照先なし"), 25)
        self.assertEqual(sum(1 for r in self.of(u"cd8") if r[u"注入か"] and r[u"α 型の state"] != u"参照先なし"), 43)

    def test_5_aggregates_recounted_from_rows(self):
        for n in SETS:
            rs = self.of(n)
            inj = [r for r in rs if r[u"注入か"]]
            a = self.agg[n]
            c = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
            self.assertEqual(a[u"席の字(事実 1)"], {
                u"行": len(rs), u"注入": len(inj), u"無改変": len(rs) - len(inj),
                u"席が確認済みにした注入": c(inj, u"確認済み"), u"席が判定できないにした注入": c(inj, u"判定できない"),
                u"席が確認済みにした無改変": c([r for r in rs if not r[u"注入か"]], u"確認済み"),
                u"席が判定できないにした無改変": c([r for r in rs if not r[u"注入か"]], u"判定できない"),
                u"席の偽警報(無改変で誤りが在る)": c([r for r in rs if not r[u"注入か"]], u"誤りが在る")})
            for key, G, f in ((u"3 群(α 型)", self.GA(n), self.alpha_f), (u"3 群(Core 自身)", self.GS(n), self.self_f)):
                for g in (u"G1", u"G2", u"G3"):
                    m = G[g]
                    self.assertEqual(a[key][g], {
                        u"行": len(m), u"注入": sum(1 for r in m if r[u"注入か"]),
                        u"無改変": sum(1 for r in m if not r[u"注入か"]),
                        u"精度(注入でない行 / 群)": {u"分子": sum(1 for r in m if not r[u"注入か"]), u"分母": len(m),
                                              u"率": round(100.0 * sum(1 for r in m if not r[u"注入か"]) / len(m), 1)}}, (n, key, g))
                self.assertEqual(a[key][u"G3 の state の内訳"], dict(sorted(
                    {k: sum(1 for r in G[u"G3"] if r[f] == k) for k in set(r[f] for r in G[u"G3"])}.items())), (n, key))
            h = {}
            for kind, m in ((u"無改変", [r for r in rs if not r[u"注入か"]]), (u"注入", inj), (u"全部", rs)):
                h[kind] = dict(sorted({k: sum(1 for r in m if r[u"H の出力"] == k) for k in set(r[u"H の出力"] for r in m)}.items()))
            self.assertEqual(a[u"H の出力"], h)
            conf = sum(1 for r in rs if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
            self.assertEqual(a[u"H の確認(二重確認 + Core のみ確認)"][u"分子"], conf)
            self.assertEqual(a[u"H の確認(二重確認 + Core のみ確認)"][u"分母"], 192)
            thr = sum(1 for r in inj if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
            self.assertEqual((a[u"誤りを通した(注入の行が二重確認か Core のみ確認)"][u"分子"], a[u"誤りを通した(注入の行が二重確認か Core のみ確認)"][u"分母"]), (thr, 64))
            self.assertEqual(a[u"注入で Core(α 型)が GROUNDED"][u"分子"], sum(1 for r in inj if r[self.alpha_f] == u"GROUNDED"))
            self.assertEqual(a[u"注入で Core 自身が GROUNDED"][u"分子"], sum(1 for r in inj if r[self.self_f] == u"GROUNDED"))
            hold = [r for r in inj if r[u"席の判定"] == u"判定できない"]
            self.assertEqual(a[u"席が迷った注入"][u"行"], len(hold))
            self.assertEqual(a[u"席が迷った注入"][u"Core 自身が VALUE_MISMATCH で止めた"][u"分子"],
                             sum(1 for r in hold if r[self.self_f] == u"VALUE_MISMATCH"))
            self.assertEqual(a[u"席が迷った注入"][u"Core 自身が見ていない(対応なし)"][u"分子"],
                             sum(1 for r in hold if r[self.self_f] == u"対応なし"))
            self.assertEqual(a[u"Core 自身が対応なし(192 行。既定)"], sum(1 for r in rs if r[self.self_f] == u"対応なし"))
            self.assertEqual(a[u"Core 自身が対応なし(192 行。P16 明示)"], sum(1 for r in rs if r[u"Core 自身(P16 明示)の state"] == u"対応なし"))

    def test_6_control_p16_recounted(self):
        for n in SETS:
            c = self.con[n]
            rs = self.of(n)
            mism = [r for r in rs if r[u"Core 自身(P16 明示)の state"] != self._mat_state(n, r)]
            self.assertEqual(mism, [])
            self.assertTrue(c[u"P16 明示で回した Core が記録の材料の Core と全行一致(192 行)"])
            self.assertEqual(c[u"一致しなかった行"], [])
            gd = {(r["doc"], r["id"]) for r in rs if r[self.self_f] == u"GROUNDED"}
            g16 = {(r["doc"], r["id"]) for r in rs if r[u"Core 自身(P16 明示)の state"] == u"GROUNDED"}
            self.assertEqual(sorted(map(tuple, c[u"GROUNDED の集合: 既定 と P16 で違う行"])), sorted(gd ^ g16))
            self.assertEqual(sorted(map(tuple, c[u"補助(封の外): P16 → 既定(P21)で GROUNDED に増えた行"])), sorted(gd - g16))
            self.assertEqual(c[u"補助(封の外): P16 → 既定(P21)で GROUNDED から減った行"], [])
            self.assertEqual(c[u"補助(封の外): 増えた行のうち注入の行"], sum(1 for r in rs if r[u"注入か"] and (r["doc"], r["id"]) in gd - g16))
            self.assertEqual(c[u"補助(封の外): P20 明示で回した GROUNDED の集合 と 既定で違う行"], [])
            self.assertEqual(c[u"GROUNDED の行の数(記録の材料 / P16 で回した / 既定)"], [len(g16), len(g16), len(gd)])
            self.assertEqual(c[u"記録の材料の profile"], "P16")
            self.assertEqual(c[u"既定で回した材料の profile"], "P21")
            for k in (u"材料の不変(P16 で回した材料。task の sha256・注入 id・行 id・注入か・正解)", u"材料の不変(既定で回した材料)",
                      u"補助(封の外): P20 明示の材料の不変"):
                self.assertEqual(c[k], [], k)

    def _mat_state(self, n, r):
        if not hasattr(self, "_mc"):
            self._mc = {}
        if n not in self._mc:
            self._mc[n] = {(p["docID"], rid): (pre["Core"].get("state") or u"対応なし")
                           for p in jload(MAT[n])[u"書類ごと"] for rid, pre in p[u"席の前に出せる分"].items()}
        return self._mc[n][(r["doc"], r["id"])]


    def test_15_alpha_state_and_pointer_per_row_match_the_alpha_record(self):
        u"""記録の行ごとの α 型の state・参照先を、α の記録(alpha_2026-10-20.json)の行に (doc, id) で突き合わせる。
        gen_c は 102 行の全部に相手が在る(相手の無い行 0・漏れ 0)。cd8 の α の記録は行の一覧を持たないので、
        state の分布・VALUE_MISMATCH の行の id と参照先・下げた行の id で突き合わせる。"""
        al = jload(ALPHA)
        theirs = {(x["doc"], x["id"]): x for x in al[u"α-1 の行(席が参照先を出した 102 行。α-2 の読みの材料つき)"]}
        mine = {(r["doc"], r["id"]): r for r in self.of(u"gen_c") if r[self.alpha_f] != u"参照先なし"}
        self.assertEqual(len(theirs), 102)
        self.assertEqual(sorted(mine), sorted(theirs))
        bad = [k for k in mine if mine[k][self.alpha_f] != theirs[k][u"engine の state"] or mine[k][u"α 型の参照先"] != theirs[k][u"参照先(原文)"]]
        self.assertEqual(bad, [])
        c = al[u"cd8(S-C2)"]
        m8 = [r for r in self.of(u"cd8") if r[self.alpha_f] != u"参照先なし"]
        self.assertEqual(len(m8), 85)
        cnt = {}
        for r in m8:
            cnt[r[self.alpha_f]] = cnt.get(r[self.alpha_f], 0) + 1
        self.assertEqual(cnt, c[u"全 state(席が参照先を出した行の全部)"])
        g1 = {}
        for r in m8:
            if r[u"G1(席が確認済み)"]:
                g1[r[self.alpha_f]] = g1.get(r[self.alpha_f], 0) + 1
        self.assertEqual(g1, c[u"α-1: 確認済み + 参照先の無改変の行"][u"state の分布"])
        self.assertEqual(c[u"α-1: 確認済み + 参照先の注入の行(= 見逃し)"][u"行"], 0)
        vm_theirs = sorted((x["doc"], x["id"], x[u"席の参照先"]) for x in c[u"VALUE_MISMATCH の行(無改変)"])
        vm_mine = sorted((r["doc"], r["id"], r[u"α 型の参照先"]) for r in m8 if r[u"G1(席が確認済み)"] and r[self.alpha_f] == u"VALUE_MISMATCH")
        self.assertEqual(vm_mine, vm_theirs)
        self.assertEqual(sorted((x["doc"], x["id"]) for x in c[u"下げた行の ids"]), [(d, i) for d, i, _ in vm_mine])

    def test_16_the_added_grounded_rows_were_all_pointer_not_found_in_p16(self):
        gained = [r for r in self.rows if r[self.self_f] == u"GROUNDED" and r[u"Core 自身(P16 明示)の state"] != u"GROUNDED"]
        self.assertEqual(len(gained), 16)
        self.assertEqual({r[u"Core 自身(P16 明示)の state"] for r in gained}, {u"POINTER_NOT_FOUND"})
        by = {}
        for r in gained:
            by[(r[u"集合"], r["doc"])] = by.get((r[u"集合"], r["doc"]), 0) + 1
        self.assertEqual(by, {(u"gen_c", "S100Z4GF"): 5, (u"gen_c", "S100Z4J8"): 7, (u"cd8", "S100YZEV"): 4})
        line = (u"- **追記(2026-10-20)**: 増えた GROUNDED 16 行(gen_c 12 = S100Z4GF 5・S100Z4J8 7、cd8 4 = S100YZEV 4)の P16 側の state は"
                u" 16 行とも POINTER_NOT_FOUND だった(記録の行の `Core 自身(P16 明示)の state` から数えた。記録に欄は足していない)。"
                u"上の「P20 明示と既定の差 0」は補助測定で、封の外。")
        self.assertIn(line, self.doc)
        self.assertIn(u"補助測定で、封の外", self.doc)
        self.assertIn(u"席が確認済みにした無改変の行 = 正解(注入でない)と合う判定を", self.doc)
        self.assertNotIn(u"席が正しく確認済みにした", self.doc)


class PredictionTest(Base):
    def ranges(self, h):
        return pairs(seal_pred(self.seal, h))

    def judge(self):
        r = {}
        rg = self.ranges
        GA = {n: self.GA(n) for n in SETS}
        GS = {n: self.GS(n) for n in SETS}
        pr = lambda m: round(100.0 * sum(1 for x in m if not x[u"注入か"]) / len(m), 1) if m else None
        r[u"H-1"] = (len(GA[u"gen_c"][u"G1"]) == 77 and len(GA[u"cd8"][u"G1"]) == 41 and all(
            pr(G[n][g]) == 100.0 for G in (GA, GS) for n in SETS for g in (u"G1", u"G2", u"G3")))
        h2 = rg(u"H-2")
        r[u"H-2"] = inr(len(GA[u"gen_c"][u"G2"]), h2[0]) and inr(len(GA[u"cd8"][u"G2"]), h2[1])
        h3 = rg(u"H-3")
        hold = lambda n: sum(1 for x in GA[n][u"G3"] if x[self.alpha_f] in (u"UNPROVABLE", u"POINTER_NOT_FOUND"))
        vmn = lambda n: sum(1 for x in GA[n][u"G3"] if x[self.alpha_f] == u"VALUE_MISMATCH")
        rng3 = (inr(hold(u"gen_c"), h3[0]) and inr(vmn(u"gen_c"), h3[1]) and inr(hold(u"cd8"), h3[2]) and inr(vmn(u"cd8"), h3[3]))
        seat_side = sum(1 for v in READING.values() if v == u"席の側")
        r[u"H-3"] = bool(rng3 and 2 * seat_side > len(READING))
        h4 = rg(u"H-4")
        nm = {n: sum(1 for x in self.of(n) if x[self.self_f] == u"対応なし") for n in SETS}
        r[u"H-4"] = bool(inr(len(GS[u"gen_c"][u"G2"]), h4[0]) and inr(len(GS[u"cd8"][u"G2"]), h4[1])
                         and nm == {u"gen_c": 80, u"cd8": 51}
                         and nm == {n: sum(1 for x in self.of(n) if x[u"Core 自身(P16 明示)の state"] == u"対応なし") for n in SETS})
        r[u"H-5"] = all(not any(x[f] == u"GROUNDED" for x in self.of(n) if x[u"注入か"]) for n in SETS for f in (self.alpha_f, self.self_f))
        h6 = rg(u"H-6")
        hv = lambda n: sum(1 for x in self.of(n) if x[u"注入か"] and x[u"席の判定"] == u"判定できない" and x[self.self_f] == u"VALUE_MISMATCH")
        hn = lambda n: sum(1 for x in self.of(n) if x[u"注入か"] and x[u"席の判定"] == u"判定できない")
        r[u"H-6"] = bool(hn(u"gen_c") == 39 and hn(u"cd8") == 13 and inr(hv(u"gen_c"), h6[0]) and inr(hv(u"cd8"), h6[1]))
        gset = lambda n, f: {(x["doc"], x["id"]) for x in self.of(n) if x[f] == u"GROUNDED"}
        r[u"H-7"] = all(gset(n, self.self_f) == gset(n, u"Core 自身(P16 明示)の state") for n in SETS)
        h8 = rg(u"H-8")
        cf = lambda n: sum(1 for x in self.of(n) if x[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        r[u"H-8"] = bool(inr(cf(u"gen_c"), h8[0]) and cf(u"gen_c") < 77 and inr(cf(u"cd8"), h8[1]))
        return r

    def test_7_seal_wording_is_what_the_script_holds(self):
        # 幅は封の字から読んだ。スクリプトの定数と同じ
        tree = ast.parse(text(SCRIPT))
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                try:
                    consts[node.targets[0].id] = ast.literal_eval(node.value)
                except Exception:
                    pass
        g, c = u"gen_c", u"cd8"
        exp = {"H2": {g: self.ranges(u"H-2")[0], c: self.ranges(u"H-2")[1]},
               "H3_HOLD": {g: self.ranges(u"H-3")[0], c: self.ranges(u"H-3")[2]},
               "H3_VM": {g: self.ranges(u"H-3")[1], c: self.ranges(u"H-3")[3]},
               "H4_G2": {g: self.ranges(u"H-4")[0], c: self.ranges(u"H-4")[1]},
               "H6": {g: self.ranges(u"H-6")[0], c: self.ranges(u"H-6")[1]},
               "H8": {g: self.ranges(u"H-8")[0], c: self.ranges(u"H-8")[1]}}
        for k, v in exp.items():
            self.assertEqual(consts[k], v, k)
        self.assertEqual(consts["H4_NOMATCH"], {g: 80, c: 51})
        self.assertEqual(consts["FACT_G1"], {g: 77, c: 41})
        self.assertEqual(consts["FACT_HOLD_INJ"], {g: 39, c: 13})

    def test_8_judgments_recomputed_equal_record_and_doc(self):
        j = self.judge()
        self.assertEqual(sorted(j), [u"H-%d" % i for i in range(1, 9)])
        for h, v in j.items():
            self.assertEqual(self.preds[h][u"当たり"], v, h)
            jd = cell_row(self.doc, h)[3]
            self.assertEqual(jd, u"**当たり**" if v else u"**外れ**", h)
        hit = sum(1 for v in j.values() if v)
        self.assertIn(u"**予測 当たり %d / 外れ %d**" % (hit, 8 - hit), self.doc)
        self.assertIn(u"**当たり %d / 外れ %d**。外れ" % (hit, 8 - hit), self.doc)
        self.assertEqual({h for h, v in j.items() if not v}, {u"H-4", u"H-7"})

    def test_9_prediction_table_wording_and_numbers(self):
        for h in sorted(self.preds):
            cells = cell_row(self.doc, h)
            self.assertEqual(cells[1], seal_pred(self.seal, h), h)
        GA = {n: self.GA(n) for n in SETS}
        GS = {n: self.GS(n) for n in SETS}
        f3 = lambda G: [x for n in SETS for g in (u"G1", u"G2", u"G3")
                        for x in fr(sum(1 for r in G[n][g] if not r[u"注入か"]), len(G[n][g]))]
        alpha = jload(ALPHA)
        p20 = [alpha[u"α-1"][u"state の分布"]["GROUNDED"],
               alpha[u"cd8(S-C2)"][u"α-1: 確認済み + 参照先の無改変の行"][u"state の分布"]["GROUNDED"]]
        g1 = {n: len(GA[n][u"G1"]) for n in SETS}
        n_vm = len(READING)
        n_seat = sum(1 for v in READING.values() if v == u"席の側")
        c3 = lambda n: collections_count(GA[n][u"G3"], self.alpha_f)
        rg = self.ranges
        nm = {n: sum(1 for x in self.of(n) if x[self.self_f] == u"対応なし") for n in SETS}
        nm16 = {n: sum(1 for x in self.of(n) if x[u"Core 自身(P16 明示)の state"] == u"対応なし") for n in SETS}
        inj = lambda n: [r for r in self.of(n) if r[u"注入か"]]
        z = lambda n, f: [str(sum(1 for r in inj(n) if r[f] == u"GROUNDED")), "64", "%.1f" % (100.0 * sum(1 for r in inj(n) if r[f] == u"GROUNDED") / 64)]
        hv = lambda n: [r for r in inj(n) if r[u"席の判定"] == u"判定できない"]
        hvm = lambda n: sum(1 for r in hv(n) if r[self.self_f] == u"VALUE_MISMATCH")
        gs = lambda n: {(x["doc"], x["id"]) for x in self.of(n) if x[self.self_f] == u"GROUNDED"}
        g16 = lambda n: {(x["doc"], x["id"]) for x in self.of(n) if x[u"Core 自身(P16 明示)の state"] == u"GROUNDED"}
        cf = lambda n: sum(1 for x in self.of(n) if x[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        exp = {
            u"H-1": [str(g1[u"gen_c"]), str(g1[u"cd8"])] + f3(GA) + f3(GS),
            u"H-2": fr(len(GA[u"gen_c"][u"G2"]), g1[u"gen_c"]) + fr(len(GA[u"cd8"][u"G2"]), g1[u"cd8"]) + [str(p20[0]), str(p20[1])],
            u"H-3": [str(c3(u"gen_c")[0]), str(c3(u"gen_c")[1]), str(c3(u"cd8")[0]), str(c3(u"cd8")[1]), str(n_vm), "1", str(n_seat), str(n_vm - n_seat)],   # "1 件ずつ" の 1
            u"H-4": (fr(len(GS[u"gen_c"][u"G2"]), g1[u"gen_c"]) + [str(rg(u"H-4")[0][0]), str(rg(u"H-4")[0][1])]
                     + fr(len(GS[u"cd8"][u"G2"]), g1[u"cd8"]) + [str(rg(u"H-4")[1][0]), str(rg(u"H-4")[1][1])]
                     + ["192", str(nm[u"gen_c"]), str(nm[u"cd8"]), str(nm16[u"gen_c"]), str(nm16[u"cd8"])]),
            u"H-5": z(u"gen_c", self.alpha_f) + z(u"gen_c", self.self_f) + z(u"cd8", self.alpha_f) + z(u"cd8", self.self_f),
            u"H-6": [str(hvm(u"gen_c")), str(len(hv(u"gen_c"))), "0.0", str(hvm(u"cd8")), str(len(hv(u"cd8"))), "0.0"],
            u"H-7": ["192", "192", "100.0", "192", "192", "100.0", "384", "0", str(len(gs(u"gen_c") ^ g16(u"gen_c"))), str(len(gs(u"cd8") ^ g16(u"cd8")))],
            u"H-8": [str(cf(u"gen_c")), "77", str(77 - cf(u"gen_c")), str(cf(u"cd8"))]}
        for h, e in exp.items():
            self.assertEqual(nums(cell_row(self.doc, h)[2]), e, h)
        # 「0 / 39」「0 / 13」は VALUE_MISMATCH の数が 0 でも分母が席が迷った注入の数(39・13)であること
        self.assertEqual((len(hv(u"gen_c")), len(hv(u"cd8"))), (39, 13))
        # 判定語: H-3 の幅と読みの両方
        self.assertEqual(self.preds[u"H-3"][u"実測"][u"VALUE_MISMATCH の行(両集合)"], n_vm)
        self.assertEqual(self.preds[u"H-3"][u"実測"][u"うち席の側"], n_seat)


def collections_count(rows, f):
    c = {}
    for r in rows:
        c[r[f]] = c.get(r[f], 0) + 1
    return (c.get(u"UNPROVABLE", 0) + c.get(u"POINTER_NOT_FOUND", 0), c.get(u"VALUE_MISMATCH", 0))


class DocTest(Base):
    def lines(self):
        return set(self.doc.splitlines())

    def expect_lines(self):
        L = []
        for n in SETS:
            rs = self.of(n)
            inj = [r for r in rs if r[u"注入か"]]
            unc = [r for r in rs if not r[u"注入か"]]
            c = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
            L.append(u"| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
                n, len(rs), len(inj), len(unc), c(inj, u"確認済み"), c(inj, u"判定できない"),
                c(unc, u"確認済み"), c(unc, u"判定できない"), c(unc, u"誤りが在る")))
        names = {u"G1": u"G1(席が確認済み)", u"G2": u"G2(Core も GROUNDED)", u"G3": u"G3(Core が GROUNDED にしない)"}
        for G, lab, f in ((self.GA, u"α 型", self.alpha_f), (self.GS, u"Core 自身", self.self_f)):
            for n in SETS:
                g = G(n)
                for k in (u"G1", u"G2", u"G3"):
                    m = g[k]
                    L.append(u"| %s | %s | %d | %d | %s |" % (n, names[k], len(m), sum(1 for r in m if r[u"注入か"]), self.prec(m)))
                cnt = {}
                for r in g[u"G3"]:
                    cnt[r[f]] = cnt.get(r[f], 0) + 1
                L.append(u"| %s | %s | %s |" % (n, lab, brk(cnt)))
        for n in SETS:
            g1 = self.GA(n)[u"G1"]
            a = lambda r: r[self.alpha_f] == u"GROUNDED"
            s = lambda r: r[self.self_f] == u"GROUNDED"
            both = sum(1 for r in g1 if a(r) and s(r))
            ao = sum(1 for r in g1 if a(r) and not s(r))
            so = sum(1 for r in g1 if not a(r) and s(r))
            L.append(u"| %s | %d | %d | %d | %d | %d |" % (n, both, ao, so, len(g1) - both - ao - so, len(g1)))
        for n in SETS:
            rs = self.of(n)
            for kind, m in ((u"無改変", [r for r in rs if not r[u"注入か"]]), (u"注入", [r for r in rs if r[u"注入か"]]), (u"全部", rs)):
                k = lambda w: sum(1 for r in m if r[u"H の出力"] == w)
                L.append(u"| %s | %s | %d | %d | %d | %d | %d | %d |" % (
                    n, kind, len(m), k(u"二重確認"), k(u"Core のみ確認"), k(u"警告"), k(u"保留"), k(u"誤り(席)")))
            thr = sum(1 for r in rs if r[u"注入か"] and r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
            L.append(u"- **誤りを通した行**(注入の行が二重確認か Core のみ確認): %s %s。" % (n, F(thr, 64)))
            hold = [r for r in rs if r[u"席の判定"] == u"判定できない"]
            L.append(u"- **Core のみ確認が 0 件の理由を測った**: %s の席が判定できないの %d 行のうち Core 自身が GROUNDED の行は %d(Core 自身の GROUNDED %d 行は全部 G1 の中)。"
                     u"Core のみ確認が 0 件なのは、Core 自身が GROUNDED にした行がすべて席も確認済みにした行だったため。" % (
                         n, len(hold), sum(1 for r in hold if r[self.self_f] == u"GROUNDED"),
                         sum(1 for r in rs if r[self.self_f] == u"GROUNDED")))
            hi = [r for r in rs if r[u"注入か"] and r[u"席の判定"] == u"判定できない"]
            k = lambda w: sum(1 for r in hi if r[self.self_f] == w)
            L.append(u"| %s | %d | %d | %d | %d | %d | %d |" % (n, len(hi), k(u"VALUE_MISMATCH"), k(u"対応なし"), k(u"POINTER_NOT_FOUND"), k(u"UNVERIFIABLE"), k(u"GROUNDED")))
            g = self.con[n][u"GROUNDED の行の数(記録の材料 / P16 で回した / 既定)"]
            gained = [r for r in rs if r[self.self_f] == u"GROUNDED" and r[u"Core 自身(P16 明示)の state"] != u"GROUNDED"]
            lost = [r for r in rs if r[self.self_f] != u"GROUNDED" and r[u"Core 自身(P16 明示)の state"] == u"GROUNDED"]
            L.append(u"| %s | %d | %d | %d | %d | %d | %d | %d |" % (n, g[0], g[1], g[2], len(gained), len(lost), sum(1 for r in gained if r[u"注入か"]), 0))
            byd = {}
            for r in gained:
                byd[r["doc"]] = byd.get(r["doc"], 0) + 1
            sj = {}
            for r in gained:
                sj[r[u"席の判定"]] = sj.get(r[u"席の判定"], 0) + 1
            L.append(u"- %s: 増えた %d 行の書類は %s。席の判定は %s。" % (
                n, len(gained), u"・".join(u"%s %d 行" % (d, byd[d]) for d in sorted(byd)),
                u"・".join(u"%s %d" % (kk, v) for kk, v in sorted(sj.items()))))
        # §4 の Q
        qa = lambda f: [F(sum(1 for r in self.rows if r[u"集合"] == n and r[u"注入か"] and r[f] == u"GROUNDED"), 64) for n in SETS]
        ai, si = qa(self.alpha_f), qa(self.self_f)
        n_alpha = {n: sum(1 for r in self.of(n) if r[u"注入か"] and r[self.alpha_f] != u"参照先なし") for n in SETS}
        L.append(u"- **Q-2 精度の土台(Core が注入を GROUNDED にしないか)**: 注入 64 行で GROUNDED にした行は gen_c の α 型 %s・Core 自身 %s、cd8 の α 型 %s・Core 自身 %s。"
                 u"ただし α 型を当てられた注入の行(席が参照先を名指した注入)は gen_c %d・cd8 %d にとどまり、席が確認済みにした注入は 0 件なので G1 に入る注入が無い。" % (
                     ai[0], si[0], ai[1], si[1], n_alpha[u"gen_c"], n_alpha[u"cd8"]))
        hq = {}
        for n in SETS:
            hi = [r for r in self.of(n) if r[u"注入か"] and r[u"席の判定"] == u"判定できない"]
            hq[n] = (len(hi), sum(1 for r in hi if r[self.self_f] == u"VALUE_MISMATCH"), sum(1 for r in hi if r[self.self_f] == u"対応なし"))
        L.append(u"- **Q-3a 止めた件数**: 席が判定できないとした注入のうち Core 自身が VALUE_MISMATCH で止めたのは gen_c %s・cd8 %s、対応なし(見ていない)は gen_c %s・cd8 %s。"
                 u"席が確認済みにした行を Core(α 型)が GROUNDED にしなかった G3 は gen_c %d 行・cd8 %d 行で、全部無改変(注入 0)。" % (
                     F(hq[u"gen_c"][1], hq[u"gen_c"][0]), F(hq[u"cd8"][1], hq[u"cd8"][0]), F(hq[u"gen_c"][2], hq[u"gen_c"][0]), F(hq[u"cd8"][2], hq[u"cd8"][0]),
                     len(self.GA(u"gen_c")[u"G3"]), len(self.GA(u"cd8")[u"G3"])))
        L.append(u"- **Q-3b 一致の信頼(3 群の精度)**: 精度は G1・G2・G3 とも 100.0%% で差が出ない(G1 の注入が 0 件)。差を測る標本が無いので、G2 の精度が G1 より高いとも低いとも言えない。"
                 u"一致の広さは G2 が gen_c %s・cd8 %s。" % (F(len(self.GA(u"gen_c")[u"G2"]), len(self.GA(u"gen_c")[u"G1"])), F(len(self.GA(u"cd8")[u"G2"]), len(self.GA(u"cd8")[u"G1"]))))
        return L

    def test_10_doc_lines_equal_lines_built_from_rows(self):
        have = self.lines()
        for l in self.expect_lines():
            self.assertIn(l, have, l)

    def test_11_summary_lines(self):
        GA = {n: self.GA(n) for n in SETS}
        self.assertIn(u"G2 は gen_c %s、cd8 %s。G3 は gen_c %d 行・cd8 %d 行で、**全部が無改変の行**" % (
            F(len(GA[u"gen_c"][u"G2"]), 77), F(len(GA[u"cd8"][u"G2"]), 41), len(GA[u"gen_c"][u"G3"]), len(GA[u"cd8"][u"G3"])), self.doc)
        for n in SETS:
            self.assertEqual(sum(1 for r in GA[n][u"G3"] if r[u"注入か"]), 0)
        hv = lambda n: sum(1 for r in self.of(n) if r[u"注入か"] and r[u"席の判定"] == u"判定できない" and r[self.self_f] == u"VALUE_MISMATCH")
        self.assertIn(u"止めたのは gen_c %s、cd8 %s。" % (F(hv(u"gen_c"), 39), F(hv(u"cd8"), 13)), self.doc)
        self.assertIn(u"所要 %s 秒(全体)" % self.rec[u"所要秒"][u"全体"], self.doc)
        self.assertIn(u"束ねた sha256 `%s`" % ENGINE_BUNDLE, self.doc)
        self.assertIn(u"core/ と adapters/ の追跡 36 file", self.doc)

    def test_12_every_fraction_is_arithmetic_and_in_the_allowed_set(self):
        allowed = set()
        for n in SETS:
            for G in (self.GA(n), self.GS(n)):
                for k in (u"G1", u"G2", u"G3"):
                    m = G[k]
                    allowed.add((sum(1 for r in m if not r[u"注入か"]), len(m)))
            allowed.add((77 if n == u"gen_c" else 41, 77 if n == u"gen_c" else 41))
            hi = sum(1 for r in self.of(n) if r[u"注入か"] and r[u"席の判定"] == u"判定できない")
            allowed.add((sum(1 for r in self.of(n) if r[u"注入か"] and r[u"席の判定"] == u"判定できない" and r[self.self_f] == u"VALUE_MISMATCH"), hi))
            allowed.add((sum(1 for r in self.of(n) if r[u"注入か"] and r[u"席の判定"] == u"判定できない" and r[self.self_f] == u"対応なし"), hi))
            allowed.add((sum(1 for r in self.of(n) if r[u"注入か"] and r[self.alpha_f] == u"GROUNDED"), 64))
            allowed.add((sum(1 for r in self.of(n) if r[u"注入か"] and r[self.self_f] == u"GROUNDED"), 64))
            allowed.add((sum(1 for r in self.of(n) if r[u"注入か"] and r[u"H の出力"] in (u"二重確認", u"Core のみ確認")), 64))
            allowed.add((192, 192))
            allowed.add((len(self.GA(n)[u"G2"]), len(self.GA(n)[u"G1"])))
            allowed.add((len(self.GS(n)[u"G2"]), len(self.GS(n)[u"G1"])))
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 40)
        for a, b, p in found:
            a_, b_ = int(a.replace(",", "")), int(b.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * a_ / b_), p, (a, b, p))
            self.assertIn((a_, b_), allowed, (a, b, p))
        # G2 の 46 / 77・32 / 41 は G1 の中の割合(許可集合の外なので別に縛る)
        for n, g in ((u"gen_c", 77), (u"cd8", 41)):
            s1 = F(len(self.GA(n)[u"G2"]), g)
            self.assertIn(s1, self.doc)
            s2 = F(len(self.GS(n)[u"G2"]), g)
            self.assertIn(s2, self.doc)

    def test_13_value_mismatch_rows_and_readings(self):
        keys = {(r[u"集合"], r["doc"], r["id"]) for r in self.rows if r[u"G1(席が確認済み)"] and r[self.alpha_f] == u"VALUE_MISMATCH"}
        self.assertEqual(keys, set(READING))
        self.assertEqual({(v[u"集合"], v["doc"], v["id"]) for v in self.vm}, set(READING))
        self.assertEqual(len(self.vm), 10)
        for v in self.vm:
            k = (v[u"集合"], v["doc"], v["id"])
            self.assertEqual(v[u"読み"], READING[k], k)
            self.assertFalse(v[u"注入か"])
            m = v[u"読みの材料(α-2)"]
            if READING[k] == u"席の側":
                # 機械的な目印: 増減額の文 + 同じ枠で期間だけ違う fact との差が主張の数に合う
                self.assertTrue(any(w in v[u"抜粋"] for w in (u"増加し", u"減少し", u"増収", u"増益")), k)
                self.assertTrue(m[u"同じ枠で期間だけ違う fact との差が主張の値に合う(差の差が 1 単位以内)"], k)
            else:
                self.assertIn(v[u"材料の単位"], (u"％", u"%"), k)
                self.assertIsNotNone(v[u"engine の recomputed"], k)
        for v in self.vm:
            num = (u"{:,.0f}".format(v[u"材料の値"]) if float(v[u"材料の値"]) == int(v[u"材料の値"]) else u"%s" % v[u"材料の値"])
            line = u"| %s %s-%s | %s%s | `%s` | %s | %s |" % (v[u"集合"], v["doc"], v["id"], num, v[u"材料の単位"], v[u"席の参照先"].split(u"@")[0],
                                                            u"{:,.0f}".format(v[u"参照先の fact の値"]), READING[(v[u"集合"], v["doc"], v["id"])])
            self.assertIn(line, self.doc.splitlines())
        n_seat = sum(1 for x in READING.values() if x == u"席の側")
        self.assertIn(u"**席の側 %d 行**" % n_seat, self.doc)
        self.assertIn(u"G3 の VALUE_MISMATCH %d 行の 1 件ずつ" % len(READING), self.doc)

    def test_14_limits_and_the_zero_guard_wording_exist(self):
        for s in (u"**G1 に注入が 0 件。3 群の精度が 100 / 100 / 100 なのは標本が無いため**",
                  u"## 7. 限界", u"## 8. 迷った点", u"## 9. 再現",
                  u"**席は 1 回も呼んでいない・通信していない・engine(`core/`・`adapters/`)0 行。**",
                  u"**縛っていないもの**: §5 の読みの正しさ、本文の文章。"):
            self.assertIn(s, self.doc, s)
        self.assertTrue(self.rec["limits"][1].startswith(u"G1 に注入が 0 件なので、3 群の精度の差は測れない"))


if __name__ == "__main__":
    unittest.main()
