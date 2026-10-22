# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼 段 2 の前半(下見と材料)の記録を縛る門。

記録: ``fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json``(``measure/xbrl_hybrid_s2_2026-10-20.py --stage material``)。
封: ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md`` §2(段 2)・§3・§4。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ):
  1. 型別の件数を、書類ごとの注入の明細から**数え直し**、記録の欄・合計・字で留めた表と一致させる。
     1 書類 8 注入 + 16 無改変、既存の型 T1/T3/T5 が 0 件。
  2. task file は repo の外。**本文から組み直し**(script の差し替えと同じ経路)、sha256・字数・見せない字・行を記録と突き合わせる。
     (キャッシュ ``~/.cache/audit-core/edinet/<docID>.zip`` が無い機械では組み直す試験だけ skip し、理由が行に出る。)
  3. 見せない字: 封の字の 9 語を組み直した task で数えて 0 件、検査自体が混ぜた語に反応すること。
     依頼文が足した 5 語(T6・T7・T2・前期・丸め)は封の外 = 補助。件数だけを組み直しと突き合わせる(C1 の task での件数も)。
  4. P-7 の判定(封の 9 語)を、書類ごとの字数・C1 の字数・見せない字から**門が自分で**再計算して記録と一致させる。
  5. T6 の後の値は refs に実在(組み直した refs で)、T7 は字面 3 桁以上・後の値が refs に無く・差は最後の桁の ±1。
     3 型で 8 に届かない書類を既存の T1_VALUE で埋める経路(``select(fallback=...)``)も合成の標本で縛る。
  6. トークンの見込みを、cd8 の下見の 2 点から再計算し、上限(合計 1,600,000・1 便 250,000)と突き合わせる。
  7. ``inject.py`` の既存の型は 1 字も変わらない: 親 commit の ``inject.py`` と ``select`` の結果が一致、``MACHINE_TYPES`` 等は字で留める。
  8. 材料の ``席の前に出せる分`` は既定 profile(P21)・engine の留め・環境(key の名前の有無)。
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
REC = os.path.join(GEN, "hybrid_s2_material_2026-10-20.json")
C1_MAT = os.path.join(GEN, "material_2026-10-20.json")
CD8_COST = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "cost_breakdown_2026-10-17.json")
SCRIPT = os.path.join(ROOT, "measure", "xbrl_hybrid_s2_2026-10-20.py")
INJECT = os.path.join(ROOT, "measure", "inject.py")

#: 字で留める(定数から作らない)。
DOCS = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]
#: 書類ごとの (T6, T7, T2) の件数。**記録の事実**。割当は (3, 3, 2) で、届かない型は他の型が埋めた。
COMP = {"S100Z0OS": (0, 0, 8), "S100YYN7": (1, 0, 7), "S100YYT8": (0, 0, 8), "S100Z42X": (0, 0, 8),
        "S100YYT4": (3, 3, 2), "S100Z4GF": (3, 3, 2), "S100Z4J8": (0, 1, 7), "S100YYUD": (3, 3, 2)}
#: 3 型で 8 に届かず既存の T1_VALUE で埋めた数(書類ごと)。いまの記録では全書類 0(T2 の site が 8 以上在った)。
T1_FILL = {d: 0 for d in COMP}
TOTAL_BY_TYPE = {"T6_PRIOR": 10, "T7_ROUND": 10, "T2_UNIT": 44}
#: 封の 24/24/16 に対する実数のずれ(採点の席が P-1 の型別の分母に使う)
QUOTA_TOTAL = {"T6_PRIOR": 24, "T7_ROUND": 24, "T2_UNIT": 16}
#: T7 の絞りの段ごとの site の数(8 書類の合計。記録の事実)
T7_STAGES = {u"1 データを運ぶ数(値が refs に在る)": 151, u"2 最後の桁 ±1 で桁数が変わらず正": 151,
             u"3 (a) 字面の桁が 3 桁以上(±1 が 1% 以下)": 106, u"4 (b) 後の値が refs のどの fact の値とも一致しない": 106}
QUOTA = {"T6_PRIOR": 3, "T7_ROUND": 3, "T2_UNIT": 2}
SHA_TASK = {
    "S100Z0OS": "5c0b0fb6e3ea19f14efd451b6f6cabcad2287049f27ef1fdd792ce90776dcf52",
    "S100YYN7": "f4c3faa2df3de81aa882340768b24b24a36a5bffcd3caa55feaf31324fa23601",
    "S100YYT8": "3ae668742e17eb12065c2f9ffc08bc5976db0f225fc14227989a4ebf2391e5aa",
    "S100Z42X": "6864e3e55c97c89fdebdbabcec8930d66f566deca7ed2c165af325d39174aa02",
    "S100YYT4": "fa3f093f2382687ee3697072aa462442771b1251c7e45050b84c11129a3ee1e0",
    "S100Z4GF": "1c898d60086e72f0c5de9caa94444429a78a3a51e4369ea0a6b810a173566dd5",
    "S100Z4J8": "e0275a58a656954b668bc1d49337fe2b2619b0b48ee2965f18526ea1fd06bc24",
    "S100YYUD": "270a3cbc3256fccf8cba1646e3af5709cb978242865be49badd70a0d77adc528"}
SPEC_BANNED = ["注入", "正解", "Core", "engine", "GROUNDED", "pointer", "T1", "T3", "T5"]
EXTRA_BANNED = ["T6", "T7", "T2", "前期", "丸め"]
#: 組み直した task に在る封の字の 9 語(P-7 の主)。全書類 0 件。
BANNED_IN_TASK = {d: {} for d in COMP}
#: 補助(封の外。依頼文が足した 5 語): この task での件数。「前期」は有価証券報告書の本文の字(判定行の抜粋にも写る)。
AUX_IN_TASK = {"S100Z0OS": {}, "S100YYN7": {"前期": 6}, "S100YYT8": {"前期": 30}, "S100Z42X": {"前期": 4},
               "S100YYT4": {"前期": 5}, "S100Z4GF": {}, "S100Z4J8": {}, "S100YYUD": {"前期": 38}}
#: C1 の task(sha256 が C1 の材料の記録と一致するもの)での同じ語の件数(司令塔が scratchpad/gen_c1/tasks/ で数えた 79 件と一致)
AUX_IN_C1_TASK = {"S100Z0OS": {}, "S100YYN7": {"前期": 6}, "S100YYT8": {"前期": 25}, "S100Z42X": {"前期": 6},
                  "S100YYT4": {"前期": 5}, "S100Z4GF": {}, "S100Z4J8": {}, "S100YYUD": {"前期": 37}}
PROMPT_SHA = "4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb"
ENGINE_BUNDLE = "5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee"
#: 親 commit(段 1 の結果。HEAD だった)の ``measure/inject.py`` の sha256。
PARENT_COMMIT = "1eb342ac9af326df2b01ecb3755a04f8d65c7262"
PARENT_INJECT_SHA = "92d34774c4cc76bbd87fce517d5c16491b791ac6e0e0873af5728f93ecb15c8a"
TOKEN_TOTAL_CAP, TOKEN_RUN_CAP = 1600000, 250000


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def banned14(blob):
    return {w: blob.count(w) for w in SPEC_BANNED + EXTRA_BANNED if w in blob}


def banned9(blob):
    return {w: blob.count(w) for w in SPEC_BANNED if w in blob}


def banned5(blob):
    return {w: blob.count(w) for w in EXTRA_BANNED if w in blob}


AUX_KEY = u"補助(封の外。依頼文が足した 5 語 T6・T7・T2・前期・丸め)"
NINE_KEY = u"task file を読み直して見つかった(封の字の 9 語)"
ALL_TYPES = ("T6_PRIOR", "T7_ROUND", "T2_UNIT", "T1_VALUE")


def load_script():
    sp = importlib.util.spec_from_file_location("hybrid_s2_for_gate", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    with contextlib.redirect_stdout(io.StringIO()):
        sp.loader.exec_module(m)
    return m


_CACHE = {}


def rebuilt():
    u"""8 書類を本文から組み直す(script の差し替えと同じ経路)。1 回だけ。キャッシュが無ければ None。"""
    if "r" in _CACHE:
        return _CACHE["r"]
    S = load_script()
    if not all(os.path.exists(S.C1.ED.cache_path(d)) for d in DOCS):
        _CACHE["r"] = None
        return None
    seed, _meta = S.IJ.verify_seed_sealed(S.MB.SEED_FILE)
    work = tempfile.mkdtemp(prefix="hybrid_s2_gate_")
    assert not os.path.realpath(work).startswith(os.path.realpath(ROOT) + os.sep)
    out = {}
    with S.patched(), contextlib.redirect_stdout(io.StringIO()):
        for d in DOCS:
            out[d] = S.rebuild(d, work, seed)
    _CACHE["r"] = (S, out)
    return _CACHE["r"]


def need_cache(test):
    r = rebuilt()
    if r is None:
        test.skipTest(u"EDINET のキャッシュ ~/.cache/audit-core/edinet/<docID>.zip が無い(組み直せない)")
    return r


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.per = {r["docID"]: r for r in cls.rec[u"書類ごと(段 2)"]}
        cls.mat = {p["docID"]: p for p in cls.rec[u"書類ごと"]}

    def test_1_documents_are_the_eight_in_order(self):
        self.assertEqual([r["docID"] for r in self.rec[u"書類ごと(段 2)"]], DOCS)
        self.assertEqual([p["docID"] for p in self.rec[u"書類ごと"]], DOCS)
        self.assertEqual(self.rec[u"引いた 8 件"], DOCS)

    def test_2_type_counts_recounted_from_the_injection_rows(self):
        total = {t: 0 for t in ALL_TYPES}
        for d in DOCS:
            det = self.per[d][u"注入"][u"明細"]
            got = {t: sum(1 for x in det if x[u"型"] == t) for t in ALL_TYPES}
            self.assertEqual(len(det), 8, d)
            self.assertEqual(sum(got.values()), 8, d)           # 4 型の外の型が 1 件も無い
            self.assertEqual((got["T6_PRIOR"], got["T7_ROUND"], got["T2_UNIT"]), COMP[d], d)
            self.assertEqual(got["T1_VALUE"], T1_FILL[d], d)
            self.assertEqual(self.per[d][u"注入"][u"作れた型の数(T6/T7/T2)"], {t: got[t] for t in QUOTA}, d)
            self.assertEqual(self.per[d][u"注入"][u"T1_VALUE で埋めた数"], got["T1_VALUE"], d)
            self.assertEqual(self.per[d][u"注入"][u"型の内訳"], {t: n for t, n in sorted(got.items()) if n}, d)
            self.assertEqual(self.mat[d][u"注入"][u"型の内訳"], {t: n for t, n in got.items() if n}, d)
            self.assertEqual(self.per[d][u"注入"][u"割当どおりか(T6 3・T7 3・T2 2)"],
                             {t: got[t] for t in QUOTA} == QUOTA and got["T1_VALUE"] == 0, d)
            for t in ALL_TYPES:
                total[t] += got[t]
        self.assertEqual({t: total[t] for t in QUOTA}, TOTAL_BY_TYPE)
        self.assertEqual(total["T1_VALUE"], sum(T1_FILL.values()))
        self.assertEqual(self.rec[u"合計(段 2)"][u"型別の注入"], dict(TOTAL_BY_TYPE, T1_VALUE=0))
        self.assertEqual(sum(total.values()), 64)
        self.assertEqual(self.rec[u"合計(段 2)"][u"割当どおりだった書類"], sum(1 for d in DOCS if COMP[d] == (3, 3, 2)))
        # 割当とのずれ(封の 24/24/16 対 実数)。採点の席が P-1 の型別の分母に使う
        gap = {t: {u"割当(封の 24/24/16)": QUOTA_TOTAL[t], u"実数": TOTAL_BY_TYPE[t], u"差": TOTAL_BY_TYPE[t] - QUOTA_TOTAL[t]}
               for t in QUOTA}
        self.assertEqual(self.rec[u"割当とのずれ"], gap)
        self.assertEqual(self.rec[u"合計(段 2)"][u"割当とのずれ"], gap)
        self.assertEqual(self.rec[u"合計(段 2)"][u"T1_VALUE で埋めた書類"], [d for d in DOCS if T1_FILL[d]])
        for d in DOCS:
            self.assertEqual(self.per[d][u"注入"][u"割当とのずれ"],
                             {t: {u"割当": QUOTA[t], u"実数": COMP[d][i], u"差": COMP[d][i] - QUOTA[t]}
                              for i, t in enumerate(("T6_PRIOR", "T7_ROUND", "T2_UNIT"))}, d)
        self.assertEqual(self.rec[u"合計(段 2)"][u"T6 を 1 件も作れなかった書類"], [d for d in DOCS if COMP[d][0] == 0])

    def test_3_shortfall_is_recorded_per_document_and_never_dropped(self):
        for d in DOCS:
            inj = self.per[d][u"注入"]
            made = inj[u"作れた型の数(T6/T7/T2)"]
            short = {t: {u"割当": QUOTA[t], u"採れた": made[t], u"作れる site": inj[u"型ごと(作れる site・割当・採った)"][t][u"作れる site"]}
                     for t in QUOTA if made[t] < QUOTA[t]}
            self.assertEqual(inj[u"割当に届かなかった型"], short, d)
            self.assertEqual(inj[u"届かなかった型を埋めた型"], {t: made[t] - QUOTA[t] for t in QUOTA if made[t] > QUOTA[t]}, d)
            for t in QUOTA:                               # 作れた数は site の数を超えない・割当の分母は外さない
                cell = inj[u"型ごと(作れる site・割当・採った)"][t]
                self.assertEqual(cell[u"割当"], QUOTA[t])
                self.assertEqual(cell[u"採った"], made[t])
                self.assertLessEqual(made[t], cell[u"作れる site"])
            # site が 0 の型は絞り込みの各段の件数(理由)が記録に在る
            why = self.per[d][u"理由(site の絞り込みの各段)"]
            self.assertEqual(set(why), {u"T6_PRIOR の絞り込み(各段を通った数。出ない段は 0)", u"T7_ROUND の絞り込み(各段を通った数)"})
            if made["T6_PRIOR"] < QUOTA["T6_PRIOR"]:
                self.assertLessEqual(inj[u"型ごと(作れる site・割当・採った)"]["T6_PRIOR"][u"作れる site"], made["T6_PRIOR"])

    def test_4_rows_are_24_with_8_injections_and_128_plain_in_total(self):
        inj_n = plain_n = 0
        for d in DOCS:
            pre = self.mat[d][u"席の前に出せる分"]
            inj = {rid for rid, v in pre.items() if v[u"注入か"]}
            self.assertEqual(len(pre), 24, d)
            self.assertEqual(len(inj), 8, d)
            inj_n += len(inj)
            plain_n += len(pre) - len(inj)
            det_rows = [x[u"行 id"] for x in self.per[d][u"注入"][u"明細"]]
            self.assertTrue(all(det_rows), d)             # どの注入にも行が在る(T2 の行が無改変に数えられていない)
            self.assertEqual(sorted(det_rows), sorted(inj), d)
            self.assertEqual(self.per[d][u"行"][u"注入の行"], 8)
            self.assertEqual(self.per[d][u"行"][u"無改変の行"], 16)
            for rid, v in pre.items():
                self.assertEqual(v[u"正解"] is not None, v[u"注入か"], (d, rid))
        self.assertEqual((inj_n, plain_n), (64, 128))
        t = self.rec[u"合計(段 2)"]
        self.assertEqual((t[u"注入の行"], t[u"無改変の行"]), (64, 128))

    def test_5_only_t3_t5_are_absent_and_t1_only_as_filler(self):
        n_t1 = 0
        for d in DOCS:
            for x in self.per[d][u"注入"][u"明細"]:
                self.assertIn(x[u"型"], ALL_TYPES, (d, x[u"id"]))
                self.assertNotIn(x[u"型"], ("T3_ABSENT", "T5_COINCIDENT"))
                n_t1 += x[u"型"] == "T1_VALUE"
            for rid, v in self.mat[d][u"席の前に出せる分"].items():
                if v[u"注入か"]:
                    # 参照先が在る(T5)・参照先は無い(T3)は 0。「値がどこにも無い」は T1 を埋めた数だけ
                    self.assertNotIn(v[u"正解"][u"種類"], (u"参照先が在る", u"参照先は無い"), (d, rid))
        self.assertEqual(n_t1, sum(T1_FILL.values()))
        self.assertEqual(sum(1 for d in DOCS for v in self.mat[d][u"席の前に出せる分"].values()
                             if v[u"注入か"] and v[u"正解"][u"種類"] == u"値がどこにも無い"), n_t1)
        self.assertEqual(self.rec[u"注入の型"][u"既存の型が材料に在る件数"], {"T1_VALUE": n_t1, "T3_ABSENT": 0, "T5_COINCIDENT": 0})
        self.assertEqual(self.rec[u"注入の型"][u"T7 の絞りの段ごとの site の数(8 書類の合計)"], T7_STAGES)

    def test_6_t6_record_shape(self):
        for d in DOCS:
            for x in self.per[d][u"注入"][u"明細"]:
                if x[u"型"] != "T6_PRIOR":
                    continue
                dt = x[u"detail"]
                elem, _, ctx = dt["true_ref_key"].partition("@")
                self.assertTrue(ctx.startswith("CurrentYear"), x[u"id"])
                self.assertEqual(dt["prior_ref_key"], "%s@Prior1Year%s" % (elem, ctx[len("CurrentYear"):]), x[u"id"])
                self.assertEqual(dt["element"], elem)
                self.assertTrue(dt["replacement_present_in_reference_numbers"])
                self.assertNotEqual(x[u"元の値"], x[u"後の値"])
                self.assertEqual(x[u"後の値"], dt["prior_value"])
                self.assertEqual(x[u"元の値"], dt["original_value"])

    def test_7_t7_difference_is_one_in_the_last_digit(self):
        for d in DOCS:
            for x in self.per[d][u"注入"][u"明細"]:
                if x[u"型"] != "T7_ROUND":
                    continue
                a, b = x[u"元の字"], x[u"後の字"]
                self.assertEqual(len(a), len(b), x[u"id"])                    # 桁数(区切りを含む字数)が変わらない
                self.assertEqual([i for i, ch in enumerate(a) if not ch.isdigit()],
                                 [i for i, ch in enumerate(b) if not ch.isdigit()], x[u"id"])   # 区切り・小数点の位置が同じ
                self.assertTrue(a[-1].isdigit() and b[-1].isdigit(), x[u"id"])
                # (a) 字面の桁(区切りと小数点を除いた数字の並びを整数にしたもの)が 3 桁以上 = ±1 が 1% 以下
                self.assertGreaterEqual(len(str(int(a.replace(",", "").replace(".", "")))), 3, x[u"id"])
                self.assertLessEqual(abs(x[u"後の値"] - x[u"元の値"]) / abs(x[u"元の値"]), 0.01 + 1e-12, x[u"id"])
                # (b) 後の値は refs のどの fact の値とも一致しない(記録の旗。組み直した refs での確かめは RebuildTest)
                self.assertFalse(x[u"detail"]["replacement_present_in_reference_numbers"], x[u"id"])
                self.assertEqual(abs(int(a[-1]) - int(b[-1])) in (1, 9), True, x[u"id"])   # 最後の桁が動く(9.0 -> 8.9 のように下の桁から借りる)
                self.assertEqual(x[u"detail"]["last_digit_delta"] in (1, -1), True, x[u"id"])
                frac = len(a.split(".")[1]) if "." in a else 0
                # 値の差は、最後の桁の位(10^-小数桁)のちょうど ±1
                self.assertAlmostEqual(x[u"後の値"] - x[u"元の値"], x[u"detail"]["last_digit_delta"] * 10.0 ** (-frac), places=9)
                self.assertEqual(float(b.replace(",", "")), x[u"後の値"], x[u"id"])
                self.assertEqual(float(a.replace(",", "")), x[u"元の値"], x[u"id"])
                self.assertAlmostEqual(x[u"detail"]["difference"], x[u"後の値"] - x[u"元の値"], places=9)

    def test_8_engine_profile_env_and_prompt(self):
        r = self.rec
        self.assertEqual(r["profile"], "P21")
        self.assertEqual(r[u"問いの sha256"], PROMPT_SHA)
        self.assertTrue(r[u"問いの sha256 が C1 の字(PROMPT_SHA)と一致"])
        pins = r[u"engine の留め"]
        self.assertTrue(pins[u"一致"])
        self.assertEqual(pins[u"vocabulary.DEFAULT_PROFILE"], "P21")
        self.assertEqual(pins[u"作業木で HEAD と sha256 が違う file"], [])
        self.assertEqual(pins[u"git diff HEAD --numstat -- core adapters"], "")
        self.assertEqual(pins[u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)"], ENGINE_BUNDLE)
        self.assertEqual(r[u"環境"][u"設定されている key の数"], 0)
        self.assertEqual(sorted(r[u"環境"][u"4 つの key の名前が設定されているか"]),
                         ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"])
        self.assertFalse(any(r[u"環境"][u"4 つの key の名前が設定されているか"].values()))
        self.assertTrue(r[u"task file の置き場"][u"repo の外か"])
        self.assertFalse(os.path.realpath(r[u"task file の置き場"][u"絶対 path"]).startswith(os.path.realpath(ROOT) + os.sep))
        self.assertEqual(r[u"task file の置き場"][u"file 数"], 8)

    def test_9_task_sha_pinned_and_recorded_twice(self):
        for d in DOCS:
            self.assertEqual(self.per[d][u"task"][u"sha256"], SHA_TASK[d], d)
            self.assertEqual(self.mat[d][u"材料"][u"sha256"], SHA_TASK[d], d)
            self.assertEqual(self.per[d][u"task"][u"字数"], self.mat[d][u"材料"][u"字数"], d)
            self.assertTrue(self.per[d][u"task"][u"記録と一致"], d)

    def test_10_p7_recomputed_from_the_numbers(self):
        c1 = {p["docID"]: p[u"材料"][u"字数"] for p in jload(C1_MAT)[u"書類ごと"]}
        r = self.rec[u"**P-7**"]
        len_ok = True
        any9 = False
        aux_total = {}
        for d in DOCS:
            chars = self.per[d][u"task"][u"字数"]
            ok = abs(chars / float(c1[d]) - 1.0) <= 0.30
            self.assertEqual(self.per[d][u"task"][u"C1 の task の字数"], c1[d], d)
            self.assertEqual(self.per[d][u"task"][u"C1 の ±30% の中"], ok, d)
            len_ok = len_ok and ok
            f = self.per[d][u"見せない字"][NINE_KEY]
            self.assertEqual(f, BANNED_IN_TASK[d], d)
            self.assertTrue(all(w in SPEC_BANNED for w in f), d)
            any9 = any9 or bool(f)
            self.assertEqual(self.per[d][u"見せない字"][u"**0 件か**(封の字の 9 語)"], not f, d)
            aux = self.per[d][u"見せない字"][AUX_KEY][u"task file を読み直して見つかった"]
            self.assertEqual(aux, AUX_IN_TASK[d], d)                       # 補助は数の一致だけ縛る
            for w, n in aux.items():
                aux_total[w] = aux_total.get(w, 0) + n
        aux_rec = r[u"補助(封の外。依頼文が足した 5 語。判定には使わない)"]
        self.assertEqual(aux_total, {"前期": 83})
        self.assertEqual(aux_rec[u"この task で見つかった語の合計"], aux_total)
        self.assertEqual(aux_rec[u"C1 の task(sha256 が C1 の記録と一致)での件数"], AUX_IN_C1_TASK)
        self.assertEqual(aux_rec[u"C1 の task での合計"], {"前期": 79})
        self.assertEqual(aux_rec[u"14 語(封の 9 語 + 5 語)で 0 件か(参考)"], (not any9) and not aux_total)
        ctrl = self.rec[u"見せない字の検査の対照(故障を作って当てた)"]
        ctrl9 = all(x[u"当たった"] for x in ctrl[u"語ごと"] if x[u"混ぜた語"] in SPEC_BANNED)
        self.assertTrue(ctrl9)
        p7 = u"緑" if (not any9 and len_ok and ctrl9) else u"赤"
        self.assertEqual(r[u"**P-7 の判定**"], p7)
        self.assertEqual(p7, u"緑")                                         # いまの記録の事実(封の 9 語で 0 件)
        self.assertEqual(r[u"見せない字 0(8 書類とも。封の字の 9 語)"], not any9)
        self.assertEqual(r[u"字数が C1 の ±30% の中(8 書類とも)"], len_ok)
        tok_ok = (sum(self.per[d][u"トークン見込み"][u"傾き(席の往復 + 傾き × 字数)"] for d in DOCS) <= TOKEN_TOTAL_CAP
                  and max(self.per[d][u"トークン見込み"][u"傾き(席の往復 + 傾き × 字数)"] for d in DOCS) <= TOKEN_RUN_CAP)
        rows_ok = all(self.per[d][u"行"][u"**24 行そろったか**"] for d in DOCS)
        self.assertEqual(self.rec[u"**下見の総合**"][u"段 2 に進めるか"], bool(p7 == u"緑" and tok_ok and rows_ok))

    def test_11_token_estimate_recomputed_from_the_cd8_points(self):
        c = jload(CD8_COST)[u"2 1 便のトークンの分け方"][u"過去の 2 点"]
        s1, s2 = c
        slope = float(s2[u"トークン(実測)"] - s1[u"トークン(実測)"]) / (s2[u"材料の字数"] - s1[u"材料の字数"])
        loop = s1[u"トークン(実測)"] - slope * s1[u"材料の字数"]
        est = {d: int(loop + slope * self.per[d][u"task"][u"字数"]) for d in DOCS}
        for d in DOCS:
            self.assertEqual(self.per[d][u"トークン見込み"][u"傾き(席の往復 + 傾き × 字数)"], est[d], d)
        v = self.rec[u"トークンの見込み"]
        self.assertEqual(v[u"見込み(傾き)の合計"], sum(est.values()))
        self.assertEqual(v[u"見込み(傾き)の 1 便の最大"], max(est.values()))
        self.assertEqual(v[u"上限"], {u"合計": TOKEN_TOTAL_CAP, u"1 便": TOKEN_RUN_CAP})
        self.assertEqual(v[u"**上限の中か**"], sum(est.values()) <= TOKEN_TOTAL_CAP and max(est.values()) <= TOKEN_RUN_CAP)
        self.assertTrue(v[u"**上限の中か**"])


class RebuildTest(unittest.TestCase):
    u"""本文から組み直した値で、記録を突き合わせる(task file は repo の外なので、これが sha256 の正本の確かめ)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.per = {r["docID"]: r for r in cls.rec[u"書類ごと(段 2)"]}
        cls.mat = {p["docID"]: p for p in cls.rec[u"書類ごと"]}

    def test_1_task_sha256_and_chars_match_the_record(self):
        S, rb = need_cache(self)
        for d in DOCS:
            task = rb[d]["task"]
            self.assertEqual(sha_bytes(task.encode("utf-8")), SHA_TASK[d], d)
            self.assertEqual(sha_bytes(task.encode("utf-8")), self.per[d][u"task"][u"sha256"], d)
            self.assertEqual(len(task), self.per[d][u"task"][u"字数"], d)

    def test_2_rows_rebuilt_are_24_with_8_injections_and_ids_match(self):
        S, rb = need_cache(self)
        for d in DOCS:
            rows = rb[d]["rows"]
            self.assertEqual(len(rows), 24, d)
            self.assertEqual(sum(1 for r in rows if r.get("**注入**")), 8, d)
            self.assertEqual(sorted(r["id"] for r in rows), sorted(self.mat[d][u"席の前に出せる分"]), d)
            self.assertEqual(sorted(r["**注入**"] for r in rows if r.get("**注入**")),
                             sorted(x[u"id"] for x in self.per[d][u"注入"][u"明細"]), d)

    def test_3_banned_words_counted_on_the_rebuilt_task(self):
        S, rb = need_cache(self)
        for d in DOCS:
            task = rb[d]["task"]
            self.assertEqual(banned9(task), BANNED_IN_TASK[d], d)           # 封の字の 9 語は 0 件(P-7 の主)
            self.assertEqual(banned5(task), AUX_IN_TASK[d], d)              # 補助(封の外)
            # 注入が持ち込んだ語は 0(改変後の本文の語 = 原文の本文の語)。task の語は本文とその抜粋(判定する行)に在る
            self.assertEqual(banned14(rb[d]["tampered"]), banned14(rb[d]["text"]), d)
            where = S.banned_by_place(task)
            self.assertEqual(where[u"問いの文"], {}, d)
            self.assertEqual(where[u"数値データの一覧"], {}, d)
            self.assertEqual(where, self.per[d][u"見せない字"][AUX_KEY][u"見つかった語の task の中の場所(件数)"], d)
            self.assertEqual(where[u"文章"], banned14(rb[d]["tampered"]), d)

    def test_3b_aux_words_in_the_c1_task_rebuilt_unpatched(self):
        S, rb = need_cache(self)
        seed, _m = S.IJ.verify_seed_sealed(S.MB.SEED_FILE)
        work = tempfile.mkdtemp(prefix="hybrid_s2_gate_c1_")
        c1 = {p["docID"]: p for p in jload(C1_MAT)[u"書類ごと"]}
        with contextlib.redirect_stdout(io.StringIO()):
            for d in DOCS:
                task = S.c1_task(d, work, seed, c1[d])                      # sha256 が C1 の記録と合わなければここで止まる
                self.assertEqual(banned9(task), {}, d)
                self.assertEqual(banned5(task), AUX_IN_C1_TASK[d], d)

    def test_4_banned_check_reacts_to_a_planted_word(self):
        S, rb = need_cache(self)
        blob = rb[DOCS[0]]["task"]
        base = banned14(blob)
        for w in SPEC_BANNED + EXTRA_BANNED:
            planted = S.banned_found(blob + w)
            self.assertEqual(planted.get(w, 0), base.get(w, 0) + 1, w)
        c = self.rec[u"見せない字の検査の対照(故障を作って当てた)"]
        self.assertEqual(sorted(x[u"混ぜた語"] for x in c[u"語ごと"]), sorted(SPEC_BANNED + EXTRA_BANNED))
        self.assertTrue(all(x[u"当たった"] for x in c[u"語ごと"]))

    def test_5_t6_replacement_is_a_prior_value_that_exists_in_refs(self):
        S, rb = need_cache(self)
        n = 0
        for d in DOCS:
            refs = {r["key"]: r for r in rb[d]["refs"]}
            values = {round(r["value"], 6) for r in rb[d]["refs"]}
            for c in rb[d]["chosen"]:
                if c["type"] != "T6_PRIOR":
                    continue
                n += 1
                dt = c["detail"]
                true_ref, prior = refs[dt["true_ref_key"]], refs[dt["prior_ref_key"]]
                self.assertEqual(true_ref["unit"], prior["unit"])
                self.assertIn(round(prior["value"], 6), values)               # 置き換え後の値は書類の中に実在する
                digits = float(c["replacement"].replace(",", ""))
                tok_unit = rb[d]["text"][c["span"][1]:c["span"][1] + 4]
                factor = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000, "兆円": 1000000000000}
                u = next((k for k in sorted(factor, key=len, reverse=True) if tok_unit.lstrip(" 　").startswith(k)), None)
                self.assertAlmostEqual(digits * factor.get(u, 1), prior["value"], delta=max(1e-6, abs(prior["value"]) * 1e-9))
                self.assertGreater(true_ref["value"], 0)
                self.assertNotAlmostEqual(true_ref["value"], prior["value"], places=6)
        self.assertEqual(n, TOTAL_BY_TYPE["T6_PRIOR"])

    def test_7_gold_of_each_injection_row_equals_the_record(self):
        S, rb = need_cache(self)
        for d in DOCS:
            row_of = {r["**注入**"]: r["id"] for r in rb[d]["rows"] if r.get("**注入**")}
            for c in rb[d]["chosen"]:
                self.assertEqual(self.mat[d][u"席の前に出せる分"][row_of[c["id"]]][u"正解"], S.gold_s2(c), c["id"])
                self.assertEqual(self.mat[d][u"席の前に出せる分"][row_of[c["id"]]][u"注入か"], True)

    def test_5b_t7_rebuilt_filters_hold(self):
        S, rb = need_cache(self)
        n = 0
        for d in DOCS:
            values = {round(r["value"], 6) for r in rb[d]["refs"]}
            scaled = {round(S.IJ.SC.scaled_value(r["value"], r.get("unit")), 6) for r in rb[d]["refs"]}
            for c in rb[d]["chosen"]:
                if c["type"] != "T7_ROUND":
                    continue
                n += 1
                orig = rb[d]["text"][c["span"][0]:c["span"][1]]
                self.assertGreaterEqual(len(str(int(orig.replace(",", "").replace(".", "")))), 3, c["id"])   # (a)
                unit_text = rb[d]["text"][c["span"][1]:c["span"][1] + 4].lstrip(" \u3000")
                factor = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000, "兆円": 1000000000000}
                u = next((k for k in sorted(factor, key=len, reverse=True) if unit_text.startswith(k)), None)
                after = round(c["new_value"] * factor.get(u, 1), 6)
                self.assertNotIn(after, scaled, c["id"])                                                      # (b)
                self.assertNotIn(round(c["new_value"], 6), values if u is None else set(), c["id"])
        self.assertEqual(n, TOTAL_BY_TYPE["T7_ROUND"])

    def test_6_rebuilt_details_equal_the_record(self):
        S, rb = need_cache(self)
        for d in DOCS:
            mine = sorted((c["id"], c["type"], c["span"], c["replacement"]) for c in rb[d]["chosen"])
            rec = sorted((x[u"id"], x[u"型"], x[u"元の span"], x[u"後の字"]) for x in self.per[d][u"注入"][u"明細"])
            self.assertEqual(mine, rec, d)


class InjectUnchangedTest(unittest.TestCase):
    u"""``measure/inject.py`` の既存の型は 1 字も変わらない。親 commit の版と ``select`` の結果が一致する。"""

    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["git", "show", "%s:./measure/inject.py" % PARENT_COMMIT], cwd=ROOT, capture_output=True)
        cls.blob = out.stdout
        cls.ok = out.returncode == 0

    def load(self, path, name):
        sys.path.insert(0, os.path.join(ROOT, "measure"))
        try:
            sp = importlib.util.spec_from_file_location(name, path)
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
        finally:
            sys.path.pop(0)
        return m

    def test_1_parent_blob_is_the_pinned_one(self):
        self.assertTrue(self.ok, u"親 commit の inject.py を git から読めない")
        self.assertEqual(sha_bytes(self.blob), PARENT_INJECT_SHA)

    def test_2_select_is_identical_for_the_existing_types(self):
        self.assertTrue(self.ok)
        d = tempfile.mkdtemp(prefix="inject_parent_")
        old_path = os.path.join(d, "inject_parent.py")
        with io.open(old_path, "wb") as fh:
            fh.write(self.blob)
        old = self.load(old_path, "inject_parent_for_gate")
        new = self.load(INJECT, "inject_new_for_gate")
        text = (u"当連結会計年度の売上高は12,345百万円となり、営業利益は2,206百万円でした。従業員数は 345 人です。\n"
                u"設備投資額は 1,500 百万円、研究開発費は 800 百万円、自己資本比率は 45.5 % でした。前期の売上高は 11,000 百万円。\n"
                u"当期の手数は 33 手、局数は 25 局でした。借入金は 5,000 百万円です。\n")
        refs = [
            {"key": "NetSales@CurrentYearDuration", "label": "NetSales", "value": 12345000000.0, "unit": "円"},
            {"key": "OperatingIncome@CurrentYearDuration", "label": "OperatingIncome", "value": 2206000000.0, "unit": "円"},
            {"key": "Capex@CurrentYearDuration", "label": "Capex", "value": 1500000000.0, "unit": "円"},
            {"key": "RD@CurrentYearDuration", "label": "RD", "value": 800000000.0, "unit": "円"},
            {"key": "Borrow@CurrentYearInstant", "label": "Borrow", "value": 5000000000.0, "unit": "円"},
            {"key": "NetSales@Prior1YearDuration", "label": "NetSales", "value": 11000000000.0, "unit": "円"},
            {"key": "Emp@CurrentYearInstant", "label": "Emp", "value": 345.0, "unit": "人"}]
        n = 0
        for types in (None, ["T1_VALUE"], ["T2_UNIT"], ["T3_ABSENT"], ["T5_COINCIDENT"],
                      ["T5_COINCIDENT", "T3_ABSENT", "T1_VALUE"], ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"]):
            for kind in ("xbrl", "shogi"):
                for count in (3, 8):
                    a = old.select(text, refs, kind, "gate-seed", "DOC1", count, types)
                    b = new.select(text, refs, kind, "gate-seed", "DOC1", count, types)
                    self.assertEqual(json.dumps(a, default=str, sort_keys=True), json.dumps(b, default=str, sort_keys=True),
                                     (types, kind, count))
                    n += 1
        self.assertEqual(n, 28)

    def test_3_machine_types_and_policy_are_pinned_literally(self):
        new = self.load(INJECT, "inject_new_for_gate2")
        self.assertEqual(new.MACHINE_TYPES, ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"])
        self.assertEqual(new.TYPE_POLICY, {"shogi": ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"],
                                           "xbrl": ["T2_UNIT", "T3_ABSENT"]})
        self.assertEqual(new.EXTRA_TYPES, ["T6_PRIOR", "T7_ROUND"])
        self.assertFalse(set(new.EXTRA_TYPES) & set(new.MACHINE_TYPES))
        self.assertEqual(sorted(new.BUILDERS), sorted(new.MACHINE_TYPES + new.EXTRA_TYPES))

    def test_5_t7_filters_a_and_b(self):
        new = self.load(INJECT, "inject_new_for_gate4")
        # 2 桁の数(12)・3 桁の数(345)・後の値(346 か 344)が refs の別の fact の値と一致する数(500: 499 と 501 が refs に在る)
        text = u"売上高は 12 百万円、営業利益は 345 百万円、設備投資は 500 百万円でした。\n"
        refs = [{"key": "A@CurrentYearDuration", "label": "A", "value": 12000000.0, "unit": "円"},
                {"key": "B@CurrentYearDuration", "label": "B", "value": 345000000.0, "unit": "円"},
                {"key": "C@CurrentYearDuration", "label": "C", "value": 500000000.0, "unit": "円"},
                {"key": "D@CurrentYearDuration", "label": "D", "value": 499000000.0, "unit": "円"},
                {"key": "E@CurrentYearDuration", "label": "E", "value": 501000000.0, "unit": "円"}]
        diag = {}
        sites = new.t7_sites(text, refs, random.Random(0), diag)
        self.assertEqual([s["token"].text for s in sites], ["345"])         # 12 は 2 桁で外れ、500 は後の値が refs に在るので外れる
        self.assertEqual(diag[u"1 データを運ぶ数(値が refs に在る)"], 3)
        self.assertEqual(diag[u"3 (a) 字面の桁が 3 桁以上(±1 が 1% 以下)"], 2)
        self.assertEqual(diag[u"4 (b) 後の値が refs のどの fact の値とも一致しない"], 1)
        self.assertIn(sites[0]["rendered"], ("344", "346"))

    def test_6_fallback_fills_with_t1_only_as_the_last_resort(self):
        new = self.load(INJECT, "inject_new_for_gate5")
        # T6・T7 の site が無く、T2 の site が 1 つだけ。T1 の site は 3 つ(値が refs に在る数)
        text = u"設備投資は 345 億円でした。人数は 12 人、件数は 7 件、借入は 99 回でした。\n"
        refs = [{"key": "A@CurrentYearDuration", "label": "A", "value": 34500000000.0, "unit": "円"},
                {"key": "B@CurrentYearInstant", "label": "B", "value": 12.0, "unit": "人"},
                {"key": "C@CurrentYearInstant", "label": "C", "value": 7.0, "unit": "件"},
                {"key": "D@CurrentYearInstant", "label": "D", "value": 99.0, "unit": "回"}]
        types = ["T6_PRIOR", "T7_ROUND", "T2_UNIT"]
        q = {"T6_PRIOR": 3, "T7_ROUND": 3, "T2_UNIT": 2}
        a, _c, _al, _w = new.select(text, refs, "xbrl", "gate-seed", "DOC1", 8, types=types, quota=q)
        self.assertFalse({c["type"] for c in a} & {"T1_VALUE"})                # fallback を渡さなければ T1 は使われない
        b, _c, _al, _w = new.select(text, refs, "xbrl", "gate-seed", "DOC1", 8, types=types, quota=q, fallback=["T1_VALUE"])
        kinds = [c["type"] for c in b]
        self.assertEqual([c["id"] for c in b][:len(a)], [c["id"] for c in a])  # 3 型で採れた分は fallback の有無で変わらない
        self.assertGreater(len(b), len(a))
        self.assertTrue(set(kinds[len(a):]) == {"T1_VALUE"})                   # 足された分は全部 T1(最後の手段)
        self.assertTrue(set(kinds[:len(a)]) <= set(types))
        # 3 型だけで 8 に届くなら T1 は 1 件も使われない
        text2 = u"".join(u"項目%d は %d 百万円でした。\n" % (i, 100 + i) for i in range(20))
        refs2 = [{"key": "X%d@CurrentYearDuration" % i, "label": "X%d" % i, "value": (100 + i) * 1000000.0, "unit": "円"}
                 for i in range(20)]
        c, _c, _al, _w = new.select(text2, refs2, "xbrl", "gate-seed", "DOC2", 8, types=types, quota=q, fallback=["T1_VALUE"])
        self.assertEqual(len(c), 8)
        self.assertNotIn("T1_VALUE", [x["type"] for x in c])

    def test_7_quota_phase_then_fill_in_the_fixed_order(self):
        new = self.load(INJECT, "inject_new_for_gate6")
        # T6 の site が無く、T7(3 桁・±1 が refs に無い)と T2 が十分在る。quota(T6 3・T7 3・T2 2)の後、足りない分を T6 -> T7 -> T2 の巡回で埋める
        text = u"".join(u"項目%d は %d 百万円でした。\n" % (i, 100 + 10 * i) for i in range(20))
        refs = [{"key": "X%d@CurrentYearDuration" % i, "label": "X%d" % i, "value": (100 + 10 * i) * 1000000.0, "unit": "円"}
                for i in range(20)]
        q = {"T6_PRIOR": 3, "T7_ROUND": 3, "T2_UNIT": 2}
        types = ["T6_PRIOR", "T7_ROUND", "T2_UNIT"]
        ch, cat, _a, _w = new.select(text, refs, "xbrl", "gate-seed", "DOC3", 8, types=types, quota=q, fallback=["T1_VALUE"])
        n = {t: sum(1 for c in ch if c["type"] == t) for t in types + ["T1_VALUE"]}
        self.assertEqual(cat["T6_PRIOR"], 0)
        self.assertGreaterEqual(cat["T7_ROUND"], 8)
        self.assertEqual(n, {"T6_PRIOR": 0, "T7_ROUND": 5, "T2_UNIT": 3, "T1_VALUE": 0})   # quota なしの巡回なら T7 4・T2 4
        ch2, _c, _a, _w = new.select(text, refs, "xbrl", "gate-seed", "DOC3", 8, types=types, fallback=["T1_VALUE"])
        n2 = {t: sum(1 for c in ch2 if c["type"] == t) for t in types}
        self.assertEqual(n2, {"T6_PRIOR": 0, "T7_ROUND": 4, "T2_UNIT": 4})

    def test_4_new_types_are_used_only_when_named(self):
        new = self.load(INJECT, "inject_new_for_gate3")
        text = u"売上高は 12,345 百万円でした。前期は 11,000 百万円でした。営業利益は 2,206 百万円でした。\n"
        refs = [{"key": "NetSales@CurrentYearDuration", "label": "NetSales", "value": 12345000000.0, "unit": "円"},
                {"key": "NetSales@Prior1YearDuration", "label": "NetSales", "value": 11000000000.0, "unit": "円"},
                {"key": "OI@CurrentYearDuration", "label": "OI", "value": 2206000000.0, "unit": "円"}]
        for kind in ("xbrl", "shogi"):
            ch, counts, allowed, _w = new.select(text, refs, kind, "gate-seed", "DOC1", 8)
            self.assertFalse({c["type"] for c in ch} & set(new.EXTRA_TYPES))
            self.assertFalse(set(counts) & set(new.EXTRA_TYPES))
        ch, counts, allowed, _w = new.select(text, refs, "xbrl", "gate-seed", "DOC1", 8, types=["T6_PRIOR", "T7_ROUND"])
        self.assertTrue({c["type"] for c in ch} <= set(new.EXTRA_TYPES))
        self.assertIn("T6_PRIOR", {c["type"] for c in ch})
        self.assertIn("T7_ROUND", {c["type"] for c in ch})


class ScriptWiringTest(unittest.TestCase):
    u"""script の差し替え(``pick_s2``)が割当と fallback を渡していること。実書類では quota と巡回が同じ並びになるので、合成の標本で縛る。"""

    def test_1_pick_s2_passes_quota_and_fallback(self):
        S = load_script()
        text = u"".join(u"項目%d は %d 百万円でした。\n" % (i, 100 + 10 * i) for i in range(20))
        refs = [{"key": "X%d@CurrentYearDuration" % i, "label": "X%d" % i, "value": (100 + 10 * i) * 1000000.0, "unit": "円"}
                for i in range(20)]
        chosen, counts = S.pick_s2(text, refs, "gate-seed", "DOC3")
        n = {t: sum(1 for c in chosen if c["type"] == t) for t in ("T6_PRIOR", "T7_ROUND", "T2_UNIT", "T1_VALUE")}
        self.assertEqual(n, {"T6_PRIOR": 0, "T7_ROUND": 5, "T2_UNIT": 3, "T1_VALUE": 0})
        self.assertEqual({t: counts[t][u"割当"] for t in counts}, {"T6_PRIOR": 3, "T7_ROUND": 3, "T2_UNIT": 2, "T1_VALUE": 0})
        self.assertEqual({t: counts[t][u"採った"] for t in counts}, n)
        # T6・T7・T2 が全部足りない標本では T1 で埋める(fallback が渡っている)
        text2 = u"人数は 12 人、件数は 7 件でした。\n"
        refs2 = [{"key": "B@CurrentYearInstant", "label": "B", "value": 12.0, "unit": "人"},
                 {"key": "C@CurrentYearInstant", "label": "C", "value": 7.0, "unit": "件"}]
        ch2, c2 = S.pick_s2(text2, refs2, "gate-seed", "DOC4")
        self.assertTrue(ch2)
        self.assertTrue(all(c["type"] in ("T2_UNIT", "T1_VALUE") for c in ch2))
        self.assertGreaterEqual(sum(1 for c in ch2 if c["type"] == "T1_VALUE"), 1)


if __name__ == "__main__":
    unittest.main()
