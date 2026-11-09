# -*- coding: utf-8 -*-
u"""FX(AI の文の形を増やす: F6 社長メッセージ・F7 ニュース記事・F8 百万円単位・F9 前期を主語にした対比 ― 20 社 × 形 4 × model 2 = 160 本)の駆動 script と結果の門。
封 docs/XBRL_AI_FORMS_FX_SEAL_2026-11-09.md §0-2 の 9。

前の便の門 ``test_xbrl_aiforms_result.py`` の部品(``Patch``・``PR``)を読み込んで使う(門としては走らせない)。縛るもの:

  a  字: 形 4 つの 1 文が封 §0-2 の 2 の字・F8 は F1 の字 + 封の 1 文・共通の指示文が前の便と byte 同じ・費用の上限 40 と実測の平均(前の便の記録から引き直す)・profile の並び・
     2 席目 32 本・封 §2 の幅の数が駆動 script の定数と一致・前の便の script 4 本と F5 の駆動 script と注入の段の script 3 本と記録の sha256 が不変・封の file が履歴に 1 回だけ在る。
  b  差し替えが届いている: 同一 instance・差し替えを 1 つ外すと配線の検査が赤・駆動 script の command が差し替えの欠けで止まる・走らせる前の止め(実測の平均の和)と
     呼ぶたびの止め(累計 + 次の 1 本の実測の平均 × 1.5)が封の字どおりに効く(偽の transport。通信しない)・dry-run が 160 本と見積り 2 つを出す。
  c  記録の中身(``record_problems``): 禁止欄・鍵・会社名・行の長さ(手がかりの 2 欄を含む)・札と行の id・差し替えの欄・集計と X-1〜X-10 の判定を行から数え直して一致。
     手で作った 160 本の記録(割合を仕込んだ)で、緑 → 変異(行の state・禁止欄・手がかりの欄・札)で赤。X-n ごとに幅の端で当たり / 外れが替わる。
  d  文書: 表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 ad65426 ⊏ 駆動 script ⊑ 記録・文書・門 ⊑ HEAD。未 commit は赤(skip にしない)。
  g  使い捨ての流れ(1 本。偽の書き手。通信しない): 生成 → 判定 → 注入 → 集計の列が動き、手がかりの 2 欄・4 profile・注入 4 型が出る。

記録が無いときは (c)(d)(e) の本物の記録の試験を skip する。(a)(b)(g) は走る。この file は docID の字を持たない。
"""
import ast
import collections
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = load_module("tests/measure/test_xbrl_aiforms_result.py", "aiforms_result_helpers_for_fx")      # 前の便の門の部品。門としては走らせない
PR = OLD.PR
Patch = OLD.Patch
FX = load_module("measure/xbrl_aiforms_fx_2026-11-09.py", "aiforms_fx_driver_for_gate")
GEN, RUN, LAB, TAL = FX.GEN, FX.RUN, FX.LAB, FX.TAL
PREV = load_module("measure/xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_previous_for_fx_gate")       # 差し替える前の gen の実体(門の比べ先)

SEAL_REL = "docs/XBRL_AI_FORMS_FX_SEAL_2026-11-09.md"
DOC_REL = "docs/XBRL_AI_FORMS_FX_RESULT_2026-11-09.md"
DRIVER_REL = "measure/xbrl_aiforms_fx_2026-11-09.py"
SEAL_COMMIT_SHORT = "ad65426"
REC_REL = collections.OrderedDict([
    ("gen", "fixtures/xbrl/aiforms/fx_gen_2026-11-09.json"), ("claims", "fixtures/xbrl/aiforms/fx_claims_2026-11-09.json"),
    ("labels", "fixtures/xbrl/aiforms/fx_labels_2026-11-09.json"), ("inject", "fixtures/xbrl/aiforms/fx_inject_2026-11-09.json"),
    ("tally", "fixtures/xbrl/aiforms/fx_tally_2026-11-09.json")])
#: 記録 → それを作った script(gen・claims・inject・labels は差し替える前の script 自身の path。tally と inject の本体は駆動 script が作る)
REC_SCRIPT = {"gen": "measure/xbrl_aiforms_gen_2026-11-03.py", "claims": "measure/xbrl_aiforms_run_2026-11-03.py",
              "labels": "measure/xbrl_aiforms_labels_2026-11-03.py"}
GATE_FILES = ("tests/measure/test_xbrl_aiforms_fx_result.py",)
#: byte を変えない file(封 §0-2 の 9・§4: 前の便の script 4 本と F5 の駆動 script・注入の段が importlib で読む script 3 本・前の便の記録。ad65426 の木の sha256 を字で留めた)
FROZEN = collections.OrderedDict([
    ("measure/xbrl_aiforms_gen_2026-11-03.py", "9e47c1814d2c8d0504e62be0508061abe8b98473977b42ff6c16b999a283a848"),
    ("measure/xbrl_aiforms_run_2026-11-03.py", "40dc664c21afeea733a6337e93114cb004cef267787a57a87975bafe849fd13e"),
    ("measure/xbrl_aiforms_labels_2026-11-03.py", "4776c68c5ec64748447c2df68ca9a1c8db8904d13184899999a67f59d2149a9e"),
    ("measure/xbrl_aiforms_tally_2026-11-03.py", "48e659c9d976b1d31fed44a5e1bae5dec6cd446d5b688c45d623f2ffc73609d1"),
    ("measure/xbrl_aiforms_f5_2026-11-03.py", "60499c9e0065d0683fd5a94770bda65547b2c9f632a83f2e299b510979b3f290"),
    ("measure/xbrl_t5y_2026-11-06.py", "8d3eea83550e6ac88c379d7182b3ed2bbd90b7c81454c6a4ced99643e9f884f6"),
    ("measure/xbrl_pswap_idmap_2026-11-06.py", "d987d82577d934a356df36b4aa8696e17b59732872321f6864dc7dae74f4418d"),
    ("measure/xbrl_pbind_2026-11-06.py", "53490dfec93f3bb48e193c8761ec13228088479225eb196d6e680c13fb2b8e82"),
    ("fixtures/xbrl/aiforms/gen_2026-11-03.json", "6be9e252f36dfeea5c5babf8986067fea223c715ef1a3dd2e7aaed606faa4e83"),
    ("fixtures/xbrl/aiforms/claims_2026-11-03.json", "445bb77ce2a4aaae02655bc0af86d2b207856cd6d14bf8e23dd4112ba70c707b"),
    ("fixtures/xbrl/aiforms/tally_2026-11-03.json", "3de09f0b8521dc58a412d633f592be2b66249518264c9b2b0d6bdda5a470527f"),
    ("fixtures/xbrl/pbind/moves_200_2026-11-06.json", "06d75363046f156a388d7c5a83cc60f181a98944a6a01352075c0dfbcc52fc8c")])
HIT, MISS, NOJ = TAL.HIT, TAL.MISS, TAL.NOJ
FORMS = FX.FX_FORMS
PASS, NAMED = FX.PASS, FX.RUN.TUNE.LABEL_NAMED_ORIGINAL
DOCID_RE = OLD.DOCID_RE
HAVE_CACHE = OLD.HAVE_CACHE
FORBIDDEN_KEYS = OLD.FORBIDDEN_KEYS
COMPANY_WORDS = OLD.COMPANY_WORDS
FOR_RESULT_WORDS = OLD.FOR_RESULT_WORDS


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def jload_abs(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha256_rel(rel):
    return OLD.sha256_rel(rel)


def records_exist(keys=None):
    return all(os.path.exists(os.path.join(ROOT, REC_REL[k])) for k in (keys or REC_REL))


def load_records():
    return collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())


def norm(v):
    return json.loads(json.dumps(v))


# ---------------------------------------------------------------- 封の字(a)
def seal_form_texts(seal):
    u"""封 §0-2 の 2 の形の 1 文 {F6: 字, F7: 字, F8: (F1 の字に続ける 1 文), F9: 字}。「」の中の字。"""
    sec = seal[seal.index("2. **形 4**"):seal.index("3. **model 2")]
    out = collections.OrderedDict()
    for m in re.finditer(r"^   - \*\*(F\d)[^*]*\*\*: (.*)$", sec, re.M):
        body = m.group(2)
        quoted = re.findall(u"「(.*?)」$", body)
        out[m.group(1)] = quoted[0] if m.group(1) != "F8" else re.search(u"続けて「(.*)」$", body).group(1)
    return out


def seal_pred_rows(seal):
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| \*\*(X-\d+)\*\* \| (.*) \|$", line)
        if m:
            out[m.group(1)] = m.group(2).split(u" | ")[0]
    return out


def seal_pins(seal):
    u"""封 §2 の幅の字 → 駆動 script の定数と同じかを見るための (名前, 封の値, script の値) の列。"""
    P = seal_pred_rows(seal)
    out = []

    def nums(txt, pat):
        return tuple(float(x) for x in re.search(pat, txt).groups())

    def bounds(txt, unit):
        return collections.OrderedDict((u"F%s" % f, (float(a), float(b))) for f, a, b in re.findall(r"F(\d) \*\*(\d+)〜(\d+)%s\*\*" % unit, txt))
    t = P["X-1"]
    out.append(("X-1 本数", int(re.search(r"\*\*(\d+) 以上\*\*", t).group(1)), FX.X1_MIN_BOOKS))
    out.append(("X-1 claim", int(re.search(r"数の claim (\d+) 以上", t).group(1)), FX.X1_MIN_CLAIMS))
    out.append(("X-1 費用", nums(t, r"\*\*(\d+)〜(\d+) USD\*\*"), FX.X1_COST))
    t = P["X-2"]
    out.append(("X-2", collections.OrderedDict((u"F%s" % f, (int(a), int(b))) for f, a, b in re.findall(r"F(\d) \*\*(\d+)〜(\d+)\*\*", t)), FX.X2_BOUNDS))
    out.append(("X-3", bounds(P["X-3"], "%"), collections.OrderedDict((k, (float(a), float(b))) for k, (a, b) in FX.X3_BOUNDS.items())))
    out.append(("X-4", float(re.search(r"\*\*(\d+)% 以上\*\*", P["X-4"]).group(1)), FX.X4_MIN))
    t = P["X-5"]
    out.append(("X-5 前期", nums(t, r"Prior1Year \*\*(\d+)〜(\d+)%\*\*"), FX.X5_PRIOR))
    out.append(("X-5 窓", nums(t, r"窓の手がかりが真 (\d+)〜(\d+)%"), FX.X5_WINDOW))
    out.append(("X-5 節", nums(t, r"窓の外\)\*\*(\d+)〜(\d+)%\*\*"), FX.X5_CLAUSE))
    t = P["X-6"]
    out.append(("X-6 F9", nums(t, r"F9 \*\*(\d+)〜(\d+)%\*\*"), FX.X6_F9))
    out.append(("X-6 他", nums(t, r"F6・F7・F8 \*\*(\d+)〜(\d+)%\*\*"), FX.X6_OTHER))
    t = P["X-7"]
    out.append(("X-7", collections.OrderedDict((u"F%s" % f, (float(a), float(b))) for f, a, b in re.findall(r"F(\d) \*\*(\d+)〜(\d+)%\*\*", t)), FX.X7_BOUNDS))
    out.append(("X-7 真", float(re.search(r"札 真 \*\*(\d+)% 以上\*\*", t).group(1)), FX.X7_TRUE_MIN))
    out.append(("X-8", float(re.search(r"\*\*(\d+)% 以下\*\*", P["X-8"]).group(1)), FX.X8_PASS_MAX))
    t = P["X-9"]
    out.append(("X-9 対", float(re.search(r"\*\*(\d+) ポイント以下\*\*", t).group(1)), FX.X9_PAIR_MAX))
    out.append(("X-9 幅", float(re.search(r"\*\*(\d+) ポイント以上\*\*", t).group(1)), FX.X9_SPREAD_MIN))
    out.append(("X-10", int(re.search(r"\*\*(\d+) 倍以上\*\*", P["X-10"]).group(1)), FX.X10_RATIO))
    out.append(("費用の上限", float(re.search(r"上限 \*\*(\d+) USD\*\*", seal).group(1)), FX.COST_CAP_USD))
    out.append(("2 席目", int(re.search(r"種で引いた (\d+) 本", seal).group(1)), FX.FX_SEAT2_N))
    return out


def const_problems(seal):
    u"""駆動 script の定数が封の字・前の便の字・前の便の記録と同じか。問題の列。"""
    out = []
    forms = seal_form_texts(seal)
    if list(forms) != list(FORMS):
        out.append(u"封の形が F6〜F9 でない")
    for f in ("F6", "F7", "F9"):
        if FX.WRITER_FORMS_FX.get(f) != forms.get(f):
            out.append(u"%s の字が封と違う" % f)
    if FX.WRITER_FORMS_FX.get("F8") != PREV.WRITER_FORMS["F1"] + forms.get("F8", u"?"):
        out.append(u"F8 の字が F1 の字 + 封の 1 文でない")
    if FX.F1_FORM_TEXT != PREV.WRITER_FORMS["F1"]:
        out.append(u"F1 の字が前の便と違う")
    if GEN.WRITER_COMMON != PREV.WRITER_COMMON or GEN.sha256_text(GEN.WRITER_COMMON) != PREV.sha256_text(PREV.WRITER_COMMON):
        out.append(u"WRITER_COMMON が前の便と byte 同じでない")
    for name in ("MODELS", "MODEL_TAG", "MAX_TOKENS", "THINKING", "RETRY_WAITS", "API_VERSION"):
        if getattr(GEN, name) != getattr(PREV, name):
            out.append(u"%s が前の便と違う" % name)
    if GEN.COST_CAP_USD != 40.0 or FX.COST_CAP_USD != 40.0:
        out.append(u"COST_CAP_USD が 40.0 でない")
    if dict(FX.AVG_COST_USD) != {"claude-sonnet-5-5": 0.178, "claude-haiku-5-5": 0.166}:
        out.append(u"AVG_COST_USD が封の 2 値でない")
    if FX.NEXT_FACTOR != 1.5:
        out.append(u"NEXT_FACTOR が 1.5 でない")
    for s, v, w in seal_pins(seal):
        if v != w:
            out.append(u"封の %s が script の定数と違う: %r %r" % (s, v, w))
    want_p4 = "P33E" if "P33E" in FX.V.PROFILES else "P27E"
    if FX.FX_PROFILES != ("P27", "P30E", "P32E", want_p4) or tuple(RUN.PROFILES) != FX.FX_PROFILES or tuple(TAL.PROFILES) != FX.FX_PROFILES:
        out.append(u"profile の並びが (P27, P30E, P32E, P33E か P27E) でない")
    if FX.AXIS != "P32E":
        out.append(u"行の軸が P32E でない")
    if RUN.INJECT_CAP != 10:
        out.append(u"注入の cap が 10 でない")
    if tuple(FX.CLAIM_COLS_FX[-2:]) != (u"窓の手がかり", u"節の手がかり") or tuple(RUN.CLAIM_COLS) != FX.CLAIM_COLS_FX:
        out.append(u"claim の欄の末尾が手がかりの 2 欄でない")
    if os.path.basename(GEN.NEW_CACHE) != "aiforms-fx-2026-11-09":
        out.append(u"置き場所が aiforms-fx-2026-11-09 でない")
    if (GEN.GEN_REL, RUN.CLAIMS_REL, LAB.LABELS_REL, RUN.INJECT_REL, TAL.TALLY_REL) != tuple(REC_REL.values()):
        out.append(u"記録の path が fx_*_2026-11-09.json でない")
    if (GEN.SEAL_REL, RUN.SEAL_REL) != (SEAL_REL, SEAL_REL) or (GEN.SEAL_COMMIT, RUN.SEAL_COMMIT) != (SEAL_COMMIT_SHORT, SEAL_COMMIT_SHORT):
        out.append(u"封の名か commit が違う")
    if GEN.SEAT2_N != 32 or tuple(GEN.FORMS) != FORMS or tuple(TAL.FORMS) != FORMS:
        out.append(u"2 席目の本数か形の並びが違う")
    return out


# ================================================================ (a)
class ConstantsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_constants_agree_with_the_seal_and_the_previous_run(self):
        self.assertEqual([], const_problems(self.seal))

    def test_a_2_a_changed_constant_or_seal_character_turns_it_red(self):
        p = Patch()
        try:
            for mod, name, val in ((FX, "F6_TEXT", FX.F6_TEXT.replace(u"1,000", u"1,001")), (FX, "F8_ADD", FX.F8_ADD + u"。"), (FX, "COST_CAP_USD", 50.0), (GEN, "COST_CAP_USD", 50.0),
                                   (FX, "AVG_COST_USD", collections.OrderedDict([("claude-sonnet-5-5", 0.3), ("claude-haiku-5-5", 0.166)])),
                                   (FX, "X3_BOUNDS", collections.OrderedDict(list(FX.X3_BOUNDS.items())[:3] + [("F9", (55, 81))])),
                                   (FX, "X1_MIN_BOOKS", 149), (FX, "X10_RATIO", 3), (FX, "FX_PROFILES", ("P27", "P30E", "P30E", "P27E")), (GEN, "SEAT2_N", 8)):
                if name == "F6_TEXT":
                    p.set(FX, "WRITER_FORMS_FX", collections.OrderedDict([("F6", val)] + list(FX.WRITER_FORMS_FX.items())[1:]))
                elif name == "F8_ADD":
                    p.set(FX, "WRITER_FORMS_FX", collections.OrderedDict(list(FX.WRITER_FORMS_FX.items())[:2] + [("F8", FX.F1_FORM_TEXT + val)] + list(FX.WRITER_FORMS_FX.items())[3:]))
                else:
                    p.set(mod, name, val)
                self.assertNotEqual([], const_problems(self.seal), name)
                p.undo()
            for ch in (self.seal.replace(u"1,000〜1,800", u"1,000〜1,801"), self.seal.replace(u"**150 以上**", u"**149 以上**"), self.seal.replace(u"**18〜35 USD**", u"**18〜36 USD**"),
                       self.seal.replace(u"**68〜85%**", u"**68〜86%**"), self.seal.replace(u"上限 **40 USD**", u"上限 **41 USD**"), self.seal.replace(u"**2 倍以上**", u"**3 倍以上**"),
                       self.seal.replace(u"窓の手がかりが真 50〜85%", u"窓の手がかりが真 50〜86%"), self.seal.replace(u"種で引いた 32 本", u"種で引いた 31 本")):
                self.assertNotEqual(self.seal, ch)
                self.assertNotEqual([], const_problems(ch))
        finally:
            p.undo()
        self.assertEqual([], const_problems(self.seal))

    def test_a_3_the_form_texts_are_what_the_seal_says(self):
        self.assertEqual(list(FORMS), list(GEN.WRITER_FORMS))
        self.assertEqual(FX.F1_FORM_TEXT + FX.F8_ADD, GEN.WRITER_FORMS["F8"])
        self.assertIs(GEN.WRITER_COMMON, FX.ORIG["WRITER_COMMON"])
        for f, t in GEN.WRITER_FORMS.items():
            self.assertNotIn(u"検証", t)
            self.assertNotIn(u"{", t)

    def test_a_4_previous_files_are_byte_identical(self):
        for rel, sha in FROZEN.items():
            self.assertEqual(sha, sha256_rel(rel), rel)
        p = Patch()
        try:
            old = FROZEN["measure/xbrl_aiforms_gen_2026-11-03.py"]
            FROZEN["measure/xbrl_aiforms_gen_2026-11-03.py"] = old[:-1] + ("0" if old[-1] != "0" else "1")
            self.assertNotEqual(FROZEN["measure/xbrl_aiforms_gen_2026-11-03.py"], sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py"))
        finally:
            FROZEN["measure/xbrl_aiforms_gen_2026-11-03.py"] = old
            p.undo()

    def test_a_5_the_average_cost_comes_from_the_previous_record(self):
        self.assertEqual([], FX.prev_problems(ROOT))
        self.assertEqual(FX.AVG_COST_USD["claude-sonnet-5-5"], FX.prev_avg_costs(ROOT)["claude-sonnet-5-5"])
        p = Patch()
        try:
            p.set(FX, "AVG_COST_USD", collections.OrderedDict([("claude-sonnet-5-5", 0.3), ("claude-haiku-5-5", 0.166)]))
            self.assertNotEqual([], FX.prev_problems(ROOT))
        finally:
            p.undo()

    def test_a_6_seal_says_each_prediction_row_once_and_is_in_history_once(self):
        self.assertEqual(["X-%d" % i for i in range(1, 12)], list(seal_pred_rows(self.seal)))
        added = PR.added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(added))
        self.assertTrue(added[0].startswith(SEAL_COMMIT_SHORT))

    def test_a_7_the_swap_field_says_what_was_swapped(self):
        f = FX.swap_field()
        names = f[u"差し替えた名前"]
        for n in ("GEN.FORMS", "GEN.WRITER_FORMS", "GEN.COST_CAP_USD", "GEN.estimate_usd", "GEN.plan_problem", "GEN.prepare", "RUN.PROFILES", "RUN.judge_text", "RUN.CLAIM_COLS", "TAL.FORMS"):
            self.assertIn(n, names)
        self.assertEqual(FX.COST_CAP_USD, f[u"費用"][u"上限 USD"])
        self.assertEqual(dict(FX.AVG_COST_USD), f[u"費用"][u"実測の平均 USD"])
        self.assertEqual(list(FX.FX_PROFILES), f[u"profile"])
        shas = f[u"sha256"][u"差し替えた関数"]
        self.assertEqual(sorted(shas), sorted(list(FX.SWAPPED_FUNCS) + ["GEN.new_record", "RUN.header"]))
        self.assertTrue(all(re.match(r"^[0-9a-f]{64}$", v) for v in shas.values()))
        self.assertEqual(f[u"駆動 script の sha256"], sha256_rel(DRIVER_REL))


# ================================================================ (b)
def fake_body(tin=None, tout=None, stop="end_turn"):
    text = u"経営成績の説明です。売上高は 100 百万円でした。"
    return json.dumps({"content": [{"type": "text", "text": text}], "usage": {"input_tokens": 100 if tin is None else tin, "output_tokens": 100 if tout is None else tout},
                       "stop_reason": stop}).encode("utf-8")


def fake_transport_factory(calls, tin=None, tout=None):
    def transport(prompt, model, key):
        calls.append((model, len(prompt)))
        return 200, fake_body(tin, tout)
    return transport


class WiringTest(unittest.TestCase):
    def test_b_1_every_user_sees_the_same_gen_instance(self):
        self.assertEqual([], FX.wiring_problems())
        self.assertIs(RUN.GEN, GEN)
        self.assertIs(LAB.GEN, GEN)
        self.assertIs(LAB.RUN, RUN)
        self.assertIs(TAL.GEN, GEN)
        self.assertIs(TAL.RUN, RUN)
        self.assertIs(TAL.LAB, LAB)
        for m in (RUN, LAB, TAL):
            self.assertIs(GEN.Stop, m.Stop)
        self.assertEqual(FORMS, TAL.FORMS)
        self.assertEqual([FX.PREV_CACHE_NAME, FX.F5_CACHE_NAME], list(GEN.EXISTING_CACHES)[-2:])
        self.assertEqual(OLD.GEN.EXISTING_CACHES.keys() | {FX.PREV_CACHE_NAME, FX.F5_CACHE_NAME}, GEN.EXISTING_CACHES.keys())

    def test_b_2_removing_one_swap_turns_the_wiring_check_red(self):
        p = Patch()
        try:
            for mod, name, val in ((RUN, "GEN", OLD.GEN), (LAB, "GEN", OLD.GEN), (LAB, "RUN", OLD.RUN), (TAL, "GEN", OLD.GEN), (TAL, "RUN", OLD.RUN), (TAL, "LAB", OLD.LAB),
                                    (GEN, "FORMS", OLD.GEN.FORMS), (GEN, "SEAT2_N", 8), (GEN, "WRITER_FORMS", OLD.GEN.WRITER_FORMS), (GEN, "NEW_CACHE", OLD.GEN.NEW_CACHE),
                                    (GEN, "GEN_REL", OLD.GEN.GEN_REL), (GEN, "COST_CAP_USD", 50.0), (GEN, "estimate_usd", OLD.GEN.estimate_usd), (GEN, "plan_problem", OLD.GEN.plan_problem),
                                    (GEN, "prepare", OLD.GEN.prepare), (GEN, "outside_cost", OLD.GEN.outside_cost), (GEN, "outside_calls", OLD.GEN.outside_calls),
                                    (GEN, "select_companies", OLD.GEN.select_companies), (GEN, "new_record", OLD.GEN.new_record), (GEN, "key_leaks", OLD.GEN.key_leaks),
                                    (GEN, "EXISTING_CACHES", OLD.GEN.EXISTING_CACHES), (GEN, "SEAL_COMMIT", OLD.GEN.SEAL_COMMIT), (GEN, "SEAL_REL", OLD.GEN.SEAL_REL),
                                    (RUN, "header", OLD.RUN.header), (RUN, "CLAIMS_REL", OLD.RUN.CLAIMS_REL), (RUN, "INJECT_REL", OLD.RUN.INJECT_REL), (RUN, "SEAL_REL", OLD.RUN.SEAL_REL),
                                    (RUN, "PROFILES", OLD.RUN.PROFILES), (RUN, "CLAIM_COLS", OLD.RUN.CLAIM_COLS), (RUN, "judge_text", OLD.RUN.judge_text),
                                    (RUN, "write_record", OLD.RUN.write_record), (LAB, "LABELS_REL", OLD.LAB.LABELS_REL), (TAL, "TALLY_REL", OLD.TAL.TALLY_REL),
                                    (TAL, "REC_REL", OLD.TAL.REC_REL), (TAL, "FORMS", OLD.TAL.FORMS), (TAL, "PROFILES", OLD.TAL.PROFILES)):
                p.set(mod, name, val)
                self.assertNotEqual([], FX.wiring_problems(), name)
                p.undo()
            p.set(GEN, "WRITER_COMMON", GEN.WRITER_COMMON + u"\n")
            self.assertNotEqual([], FX.wiring_problems())
            p.undo()
        finally:
            p.undo()
        self.assertEqual([], FX.wiring_problems())

    def test_b_3_a_driver_command_refuses_to_run_when_a_swap_is_missing(self):
        tmp = tempfile.mkdtemp(prefix="aiforms_fx_refuse_", dir=os.environ.get("TMPDIR"))
        cache = os.path.join(tmp, "cache")                       # 止まらなかった変異の世界でも、本物の置き場(~/.cache)には書かない
        try:
            p = Patch()
            try:
                p.set(RUN, "GEN", OLD.GEN)
                with self.assertRaises(GEN.Stop):
                    FX.run_tally(root=ROOT, out=os.path.join(tmp, "tally.json"))
                with self.assertRaises(GEN.Stop):
                    FX.run_labels(root=ROOT, out=os.path.join(tmp, "labels.json"))
                with self.assertRaises(GEN.Stop):
                    FX.run_inject_fx(root=ROOT, out=os.path.join(tmp, "inject.json"), new_cache=cache)
                with self.assertRaises(GEN.Stop):
                    FX.run_gen(root=ROOT, dry_run=True, new_cache=cache, out=os.path.join(tmp, "gen.json"), say=lambda *a: None)
            finally:
                p.undo()
            p = Patch()
            try:
                p.set(FX, "AVG_COST_USD", collections.OrderedDict([("claude-sonnet-5-5", 0.3), ("claude-haiku-5-5", 0.166)]))
                with self.assertRaises(GEN.Stop):
                    FX.run_gen(root=ROOT, dry_run=True, new_cache=cache, out=os.path.join(tmp, "gen.json"), say=lambda *a: None)
            finally:
                p.undo()
            self.assertFalse(os.path.exists(cache))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_b_4_the_key_check_ignores_only_the_seal_path(self):
        self.assertEqual([], GEN.key_leaks(u'{"seal": "%s"}' % SEAL_REL))                                        # 32 字続く封の path だけは通る
        self.assertNotEqual([], OLD.GEN.key_leaks(u'{"seal": "%s"}' % SEAL_REL))                                  # 前の便の検査のままだと当たる(差し替えの訳)
        for bad in (u"x" * 32, u"abc" + SEAL_REL + u"def_ghijklmnopqrstuvwxyz0123456789", u"sk-" + u"a" * 12, u"Bearer " + u"a" * 20, u"x-api-key"):
            self.assertNotEqual([], GEN.key_leaks(bad), bad)
        self.assertNotEqual([], GEN.key_leaks(u"SECRET-VALUE-123", u"SECRET-VALUE-123"))
        self.assertIs(GEN.key_leaks, FX.key_leaks_fx)

    def test_b_5b_the_plan_stop_is_the_sum_of_the_averages_of_the_remaining_books(self):
        jobs = [(d, f, m) for d in DOCS for f in FORMS for m in GEN.MODELS]
        prompts = dict(((d, f), u"x" * 1000) for d in DOCS for f in FORMS)
        lines = []
        p = Patch()
        try:
            p.set(GEN, "COST_CAP_USD", 27.5)                                              # 160 本の和 27.52 は上限を超える
            self.assertIsNotNone(FX.plan_problem_fx(None, jobs, prompts, lines.append))
            p.undo()
            p.set(GEN, "COST_CAP_USD", 27.53)
            self.assertIsNone(FX.plan_problem_fx(None, jobs, prompts, lines.append))
            p.undo()
            p.set(GEN, "COST_CAP_USD", 27.53)                                             # 実費の累計を足すと超える(この便の累計だけが入る)
            rec = {u"呼び出し": [{u"name": u"x", u"cost_usd": 0.02, u"ok": False}], u"費用": {}}
            p.set(GEN, "recorded_cost", lambda r: 0.02)
            self.assertIsNotNone(FX.plan_problem_fx(rec, jobs, prompts, lines.append))
            self.assertAlmostEqual(27.52, rec[u"費用"][u"見積り(実測の平均)USD"], places=6)
            self.assertAlmostEqual(160 * FX.conservative_usd(1000), rec[u"費用"][u"見積り(保守的な単価。止めには使わない)USD"], places=6)
            self.assertEqual(160, rec[u"費用"][u"見積りの本数"])
        finally:
            p.undo()
        self.assertEqual(3, len([x for x in lines if x.startswith(u"見積りの 2 つ")]))

    def test_b_5_the_estimates(self):
        # 走らせる前の見積り = 実測の平均の和(160 本で 27.52 USD)。呼ぶたびの余裕 = 実測の平均 × 1.5
        jobs = [(d, f, m) for d in ("DOC%d" % i for i in range(20)) for f in FORMS for m in GEN.MODELS]
        self.assertEqual(160, len(jobs))
        self.assertAlmostEqual(27.52, sum(FX.est_book_usd(m) for _d, _f, m in jobs), places=6)
        self.assertLess(sum(FX.est_book_usd(m) for _d, _f, m in jobs), FX.COST_CAP_USD)
        self.assertGreater(sum(FX.conservative_usd(100000) for _ in jobs), FX.COST_CAP_USD)      # 保守的な単価の見積りは上限を超える(止めには使わない訳)
        self.assertAlmostEqual(0.178 * 1.5, FX.estimate_usd_fx(12345), places=9)
        self.assertEqual(FX.estimate_usd_fx(1), FX.estimate_usd_fx(10 ** 6))
        self.assertEqual([], FX.outside_calls_fx())
        self.assertEqual(0.0, FX.outside_cost_fx())


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class CostStopTest(unittest.TestCase):
    u"""走らせる前の止めも呼ぶたびの止めも封の字どおり(偽の transport。通信しない)。"""

    @classmethod
    def setUpClass(cls):
        seed, cls.seed_meta = GEN.seed_value(ROOT)
        cls.chosen, cls.counts = GEN.select_companies(ROOT, seed)       # FX の選び(前の便の列と同じか確かめる関数を通る)
        cls.one = cls.chosen[:1]
        cls.doc = cls.one[0]["docID"]

    def setUp(self):
        self.p = Patch()
        self.p.set(GEN, "select_companies", lambda root, seed=None: (self.one, self.counts))        # 1 社(8 本)に絞る。会社の列の検査は test_b_7 が本物の関数で見る
        self.tmp = tempfile.mkdtemp(prefix="aiforms_fx_cost_", dir=os.environ.get("TMPDIR"))
        self.out = os.path.join(self.tmp, "gen.json")
        self.cache = os.path.join(self.tmp, "cache")
        os.environ.pop(GEN.KEY_ENV, None)

    def tearDown(self):
        self.p.undo()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop(GEN.KEY_ENV, None)

    def go(self, transport, dry_run=False, key="SECRETKEY-aaaaaaaaaaaaaaaaaaaa", lines=None):
        os.environ[GEN.KEY_ENV] = key
        say = (lambda *a: None) if lines is None else (lambda s: lines.append(s))
        return GEN.run(root=ROOT, dry_run=dry_run, only=None if dry_run else self.doc, out=self.out, new_cache=self.cache, key_value=key,
                       transport=transport, sleep=lambda s: None, say=FX.say_fx(say))

    def test_b_7_the_company_list_must_equal_the_previous_runs(self):
        seed, _m = GEN.seed_value(ROOT)
        p = Patch()
        try:
            p.set(FX, "prev_gen", lambda root=ROOT: {u"会社の選び": {u"docID": list(reversed([r["docID"] for r in self.chosen]))}})
            with self.assertRaises(GEN.Stop):
                FX.select_companies_fx(ROOT, seed)
        finally:
            p.undo()
        chosen, _c = FX.select_companies_fx(ROOT, seed)
        self.assertEqual(jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"], [r["docID"] for r in chosen])

    def test_b_8_dry_run_over_the_real_twenty_calls_nothing_and_prints_two_estimates(self):
        self.p.undo()                                                                   # 本物の選び(20 社 × 形 4 × model 2 = 160 本)
        calls, lines = [], []
        os.environ.pop(GEN.KEY_ENV, None)
        r = FX.run_gen(root=ROOT, dry_run=True, out=self.out, new_cache=self.cache, say=lambda s: lines.append(s))
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(160, r["jobs"])
        self.assertEqual(20, len(r["docs"]))
        self.assertEqual(jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"], r["docs"])
        text = u"\n".join(lines)
        self.assertIn(u"= 160 本", text)
        self.assertIn(u"本数 160", text)
        self.assertIn(u"27.5200", text)                                                 # 実測の平均の見積り(止めに使う)
        self.assertIn(u"止めには使わない", text)                                         # 保守的な単価の見積り(並べるだけ)
        self.assertEqual(1, text.count(u"見積りの 2 つ"))
        self.assertNotIn(u"見積り(保守的な単価 入力", text)                               # 前の便の行(上限と比べる意味が替わった)は出さない
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "texts")))

    def test_b_9_nothing_is_called_when_the_estimate_exceeds_the_cap(self):
        calls = []
        self.p.set(GEN, "COST_CAP_USD", 1.0)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls))
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.tearDown()
        self.setUp()
        calls2 = []
        self.p.set(GEN, "COST_CAP_USD", 2.2)              # --only の見積り(8 本 × 余裕 0.267 = 2.136)を上回れば走る(8 本)
        self.go(fake_transport_factory(calls2, tin=0, tout=100))
        self.assertEqual(8, len(calls2))

    def test_b_10_the_call_stop_is_the_running_cost_plus_one_and_a_half_averages(self):
        # 1 回 2.0 USD(出力 80,000 token)。上限 4.3・余裕 0.267 → 1 回目・2 回目(2.0 + 0.267)・3 回目(4.0 + 0.267 = 4.267 ≤ 4.3)は呼び、4 回目の前(6.0 + 0.267)で止まる
        calls = []
        self.p.set(GEN, "COST_CAP_USD", 4.3)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls, tin=0, tout=80000))
        self.assertEqual(3, len(calls))
        rec = jload_abs(self.out)
        self.assertEqual(3, rec[u"累計"][u"呼び出しの数"])
        self.assertTrue(rec[u"止めた理由"].startswith(TAL.CAP_STOP_STARTS))
        self.assertAlmostEqual(6.0, rec[u"累計"][u"費用 USD 合計(記録の外を含む)"], places=4)
        self.assertEqual(0.0, rec[u"累計"][u"記録の外の費用 USD"])                         # 前の便の累計は加えない
        self.assertAlmostEqual(FX.estimate_usd_fx(1), rec[u"呼び出し"][0][u"est_usd"], places=6)
        # 実測の平均を 0.3 に替えた版(変異)なら 3 回目の前(4.0 + 0.45 = 4.45 > 4.3)で止まる = 回数が替わる
        self.tearDown()
        self.setUp()
        self.p.set(GEN, "COST_CAP_USD", 4.3)
        self.p.set(FX, "AVG_COST_USD", collections.OrderedDict([("claude-sonnet-5-5", 0.3), ("claude-haiku-5-5", 0.166)]))
        calls3 = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls3, tin=0, tout=80000))
        self.assertEqual(2, len(calls3))
        # 余裕を 1.5 倍でなく 1 倍にした版(変異)なら 3 回目の前(4.0 + 0.178 ≤ 4.3)も 4 回目の前(6.0 + 0.178 > 4.3)も同じ = 回数は同じなので、余裕の大きさは b_5 の値で縛る
        self.tearDown()
        self.setUp()
        self.p.set(GEN, "COST_CAP_USD", 6.2)              # 6.0 + 0.267 = 6.267 > 6.2 → 4 回目の前で止まる。余裕 1.0 倍(6.178 ≤ 6.2)なら 4 回目も呼ぶ
        calls4 = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls4, tin=0, tout=80000))
        self.assertEqual(3, len(calls4))

    def test_b_11_the_first_record_carries_the_swap_field_and_both_estimates(self):
        calls = []
        self.go(fake_transport_factory(calls, tin=0, tout=100))
        rec = jload_abs(self.out)
        self.assertEqual(json.loads(json.dumps(FX.swap_field())), rec[u"差し替え"])
        self.assertEqual(SEAL_REL, rec["seal"])
        self.assertEqual(SEAL_COMMIT_SHORT, rec[u"封の commit"])
        self.assertIn(u"F6〜F9", rec[u"step"])
        self.assertEqual(0.0, rec[u"累計"][u"記録の外の費用 USD"])
        self.assertEqual(sorted(FORMS), sorted(set(c["form"] for c in rec[u"呼び出し"])))
        self.assertEqual(8, len(rec[u"呼び出し"]))
        cost = rec[u"費用"]
        self.assertEqual(40.0, cost[u"上限 USD"])
        self.assertEqual(dict(FX.AVG_COST_USD), cost[u"実測の平均 USD"])
        self.assertAlmostEqual(1.376, cost[u"見積り(実測の平均)USD"], places=6)
        self.assertGreater(cost[u"見積り(保守的な単価。止めには使わない)USD"], cost[u"見積り(実測の平均)USD"])
        self.assertIn(FX.PREV_CACHE_NAME, rec[u"cache の前後"][u"前"])
        self.assertIn(FX.F5_CACHE_NAME, rec[u"cache の前後"][u"前"])
        self.assertEqual(rec[u"cache の前後"][u"前"], rec[u"cache の前後"][u"後"])
        self.assertTrue(os.path.isfile(os.path.join(self.cache, "texts", GEN.text_key(self.doc, "F9", "claude-sonnet-5-5") + ".txt")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "texts", GEN.text_key(self.doc, "F1", "claude-sonnet-5-5") + ".txt")))
        self.assertEqual(rec[u"会社の選び"][u"docID"], [self.doc])


# ================================================================ 手で作った記録(割合を仕込んだ 160 本)
MODEL = collections.OrderedDict([("W1", "claude-sonnet-5-5"), ("W2", "claude-haiku-5-5")])
DOCS = ["DOC%02d" % i for i in range(20)]
CUR, PRI = ["jppfs_cor:NetSales@当期"], ["jppfs_cor:NetSales@前期"]


def comp(tg, ts, fa, nj, ym=0, yo=0, pw=0, pc=0, pn=0, mv=0, pwc=0):
    u"""1 本の行の組み立て。tg = 札 真で P32E が GROUNDED / ts = 札 真で止めた / fa = 札 偽 / nj = 札 判定不能 / ym・yo = tg のうち百万円・円の書き方 /
    pw・pc・pn = tg のうち前期を名指す(窓の手がかり真・節だけ真・どちらも偽)/ pwc = pw のうち節の手がかりも真の行(重なり)/ mv = 前期を名指す tg のうち P30E では当期を名指していた(動いた行)。"""
    assert pw + pc + pn <= tg and ym + yo <= tg and mv <= pw + pc + pn and pwc <= pw
    return dict(tg=tg, ts=ts, fa=fa, nj=nj, ym=ym, yo=yo, pw=pw, pc=pc, pn=pn, mv=mv, pwc=pwc)


def good_spec():
    u"""封 §2 の X-1〜X-10 が全部当たる作り(形ごとに 2 model で同じ組み立て)。"""
    base = {"F6": comp(6, 4, 1, 1, yo=3), "F7": comp(9, 5, 1, 1, yo=3), "F8": comp(32, 6, 1, 1, ym=20, yo=2),
            "F9": comp(24, 14, 1, 1, yo=3, pw=11, pc=3, pn=2, mv=1, pwc=2)}
    inj = {}
    for t in FX.FX_INJECT_TYPES:
        for f in FORMS:
            for w in MODEL:
                if t == "T9_PRIOR_TO_CURRENT":
                    passed, win_false = (3, 2) if f == "F9" else (1, 1)
                else:
                    passed, win_false = (1 if w == "W1" else 0), 0
                inj[(t, f, w)] = dict(n=20, passed=passed, win_false=win_false)
    return dict(comp={(f, w): dict(base[f]) for f in FORMS for w in MODEL}, inj=inj, cost_per_call=0.17, short_books=0, stop=None)


def cell(state, ptrs, reason=None):
    return [state, reason, list(ptrs), True, None, None, None]


def make_rows(c, n_cut=None):
    u"""(行の列, 札の列)。行 = claim の欄 + 手がかり 2 欄 + 4 profile の欄。"""
    items = []
    n_prior = c["pw"] + c["pc"] + c["pn"]
    for i in range(c["tg"]):
        unit = u"百万円" if i < c["ym"] else (u"円" if i < c["ym"] + c["yo"] else u"%")
        if i < c["pw"]:
            win, clause, prior = True, i < c["pwc"], True
        elif i < c["pw"] + c["pc"]:
            win, clause, prior = False, True, True
        elif i < n_prior:
            win, clause, prior = False, False, True
        else:
            win, clause, prior = False, False, False
        c32 = cell("GROUNDED", PRI if prior else CUR)
        c30 = cell("GROUNDED", CUR if (prior and i < c["mv"]) else (PRI if prior else CUR))
        items.append((unit, win, clause, c32, c30, u"真"))
    for _ in range(c["ts"]):
        items.append((u"%", False, False, cell("VALUE_MISMATCH", CUR), cell("VALUE_MISMATCH", CUR), u"真"))
    for _ in range(c["fa"]):
        items.append((u"%", False, False, cell("VALUE_MISMATCH", CUR), cell("VALUE_MISMATCH", CUR), u"偽"))
    for _ in range(c["nj"]):
        items.append((u"%", False, False, cell("UNVERIFIABLE", []), cell("UNVERIFIABLE", []), u"判定不能"))
    if n_cut is not None:
        items = items[:n_cut]
    rows, labels = [], []
    for k, (unit, win, clause, c32, c30, lab) in enumerate(items):
        cid = "N%03d" % (k + 1)
        p27 = copy.deepcopy(c32) if k % 2 == 0 else None
        cells = [p27, c30, c32, copy.deepcopy(p27)]
        rows.append([cid, "num", "direct_value", unit, False, u"他", win, clause] + RUN.encode_cells(cells))
        labels.append([cid, lab, u"数値の違い" if lab == u"偽" else None, u"高", []])
    return rows, labels


def sum_states(rows):
    out = collections.OrderedDict()
    for j, p in enumerate(FX.FX_PROFILES):
        c = collections.Counter()
        for r in rows:
            d = RUN.decode_row(r)
            if d[p] is not None:
                c[d[p]["state"]] += 1
        out[p] = collections.OrderedDict((s, c.get(s, 0)) for s in RUN.STATES)
    return out


def synth_records(spec):
    u"""手で作った記録 4 つ(gen・claims・labels・inject)。"""
    calls, books, lbooks = [], [], []
    n = 0
    for d in DOCS:
        for f in FORMS:
            for w, model in MODEL.items():
                name = GEN.text_key(d, f, model)
                n_cut = 5 if n < spec["short_books"] else None
                n += 1
                rows, labels = make_rows(spec["comp"][(f, w)], n_cut)
                calls.append(collections.OrderedDict([
                    (u"name", name), (u"docID", d), (u"form", f), (u"model", model), (u"writer", w), (u"prompt_chars", 1000), (u"prompt_sha256", u"0" * 64), (u"est_usd", 0.267),
                    (u"script_sha256", u"0" * 16), (u"thinking", GEN.THINKING[model]), (u"retries", 0), (u"http_status", 200), (u"ok", True), (u"sha256", u"1" * 64), (u"chars", 1500),
                    (u"blocks", [u"text"]), (u"usage", {u"input_tokens": 1, u"output_tokens": 1}), (u"cost_usd", spec["cost_per_call"]), (u"stop_reason", u"end_turn")]))
                books.append(collections.OrderedDict([
                    (u"name", name), (u"docID", d), (u"form", f), (u"model", model), (u"writer", w), (u"文の sha256", u"1" * 64), (u"字数", 1500), (u"対応", True), (u"行数", 30),
                    (u"claim の数", len(rows)), (u"数の claim の数", collections.OrderedDict((p, len(rows)) for p in FX.FX_PROFILES)),
                    (u"行の軸に無い鍵の数", collections.OrderedDict((p, 0) for p in FX.FX_PROFILES)), (u"4 state", sum_states(rows)), (u"札付けの束の鍵", u"k%d" % n), (u"行", rows)]))
                lbooks.append(collections.OrderedDict([(u"name", name), (u"docID", d), (u"form", f), (u"model", model), (u"writer", w), (u"札付けの束の鍵", u"k%d" % n), (u"札", labels)]))
    gen = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"会社の選び", {u"docID": list(DOCS)}),
        (u"費用", collections.OrderedDict([(u"上限 USD", 40.0), (u"見積り(実測の平均)USD", 27.52), (u"見積り(保守的な単価。止めには使わない)USD", 47.9)])),
        (u"呼び出し", calls), (u"止めた理由", spec["stop"])])
    claims = collections.OrderedDict([(u"profile", list(FX.FX_PROFILES)), (u"本", books), (u"欠けた本", [])])
    labels = collections.OrderedDict([(u"本", lbooks), (u"集計", {u"2 席目との一致": {u"一致率": 95.0}})])
    inj_rows = []
    for (t, f, w), s in spec["inj"].items():
        for i in range(s["n"]):
            ok = i < s["passed"]
            res = PASS if ok else NAMED
            st = "GROUNDED" if ok else "VALUE_MISMATCH"
            c = collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", st), (u"reason", None)])
            row = collections.OrderedDict([(u"docID", DOCS[i % 20]), (u"form", f), (u"model", MODEL[w]), (u"writer", w), (u"id", u"%s-%s-%s-%d" % (t, f, w, i)), (u"型", t),
                                           (u"P30E", copy.deepcopy(c)), (u"P32E", copy.deepcopy(c))])
            if t == "T9_PRIOR_TO_CURRENT":
                row[u"窓の手がかり"] = (i >= s["win_false"]) if ok else False        # 通した行のうち先頭の win_false 件が 窓の手がかり偽
            inj_rows.append(row)
    inject = collections.OrderedDict([(u"profile", list(FX.INJECT_PROFILES)), (u"行", inj_rows)])
    return collections.OrderedDict([("gen", gen), ("claims", claims), ("labels", labels), ("inject", inject)])


def synth_judge(spec):
    R = synth_records(spec)
    refs = FX.load_refs(ROOT)
    T = FX.build_fx(R, refs)
    return R, T, FX.judge_fx(T)


class SynthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = good_spec()
        cls.R, cls.T, cls.J = synth_judge(cls.spec)

    def test_c_0_the_good_records_hit_every_prediction(self):
        for k in ["X-%d" % i for i in range(1, 11)]:
            self.assertEqual(HIT, self.J[k][u"判定"], (k, self.J[k][u"値"]))
        self.assertEqual(NOJ, self.J["X-11"][u"判定"])

    def test_c_1_the_aggregates_equal_the_counts_the_builder_put_in(self):
        T, c = self.T, self.spec["comp"]
        E = T[u"3 engine の判定(無改変)"]["P32E"]
        for f in FORMS:
            s = c[(f, "W1")]
            self.assertEqual(round(100.0 * s["tg"] / (s["tg"] + s["ts"]), 1), E[f][u"札 真の行の GROUNDED 率"][u"率"], f)
            self.assertEqual(40 * s["tg"], E[f][u"札 真の行の GROUNDED 率"][u"件"])
            self.assertEqual(2 * 20 * (s["tg"] + s["ts"] + s["fa"] + s["nj"]), E[f][u"claim"])
            self.assertEqual(0, E[f][u"対応が付かない行"])
        L = T[u"2 札"][u"札の分布"]
        s = c[("F6", "W1")]
        self.assertEqual(round(100.0 * s["fa"] / (s["tg"] + s["ts"] + s["fa"] + s["nj"]), 1), L["F6"][u"偽"][u"率"])
        S8, S9 = T[u"6 形の性質"]["F8"], T[u"6 形の性質"]["F9"]
        self.assertEqual(40 * 22, S8[u"円族の数"])
        self.assertEqual(round(100.0 * 20 / 22, 1), S8[u"うち百万円の書き方"][u"率"])
        self.assertEqual(40 * 16, S9[u"前期を名指す数の手がかり"][u"前期の数"])
        self.assertEqual(round(100.0 * 16 / 40, 1), S9[u"前期を名指す数の割合"][u"率"])
        self.assertEqual(round(100.0 * 11 / 16, 1), S9[u"前期を名指す数の手がかり"][u"窓の手がかりが真"][u"率"])
        self.assertEqual(round(100.0 * 3 / 16, 1), S9[u"前期を名指す数の手がかり"][u"節の手がかりだけが真"][u"率"])
        self.assertEqual(round(100.0 * 2 / 16, 1), S9[u"前期を名指す数の手がかり"][u"どちらも偽"][u"率"])
        M = T[u"4 profile の差"][u"P30E → P32E"]
        self.assertEqual(40, M["F9"][u"動いた行"])
        self.assertEqual(40, M["F9"][u"本"])
        self.assertEqual(1.0, M["F9"][u"1 本あたりの動いた行"])
        self.assertEqual(0, M["F6"][u"動いた行"])
        self.assertEqual(40, M["全体"][u"動いた行"])
        self.assertEqual({}, dict(M["F9"][u"向き別"]))                    # pointer の期だけ違う行は state が変わった行に数えない
        P = T[u"5-1 T9 の通した行の窓の手がかり"]["F9"]
        self.assertEqual((6, 4, 2), (P[u"通した行"], P[u"通した行のうち窓の手がかり偽"], P[u"通した行のうち窓の手がかり真"]))
        w = T[u"1 配線"]
        self.assertEqual(160, w[u"生成できた本"])
        self.assertEqual(160, w[u"生成できて P32E の数の claim が 6 以上ある本"])
        self.assertAlmostEqual(27.2, w[u"費用 USD(実費。記録の cost_usd の合計)"], places=4)
        self.assertEqual(12, w[u"形 × model"]["F6"][u"P32E の数の claim の数"][u"中央値"])
        self.assertEqual(40, w[u"形 × model"]["F9"][u"P32E の数の claim の数"][u"中央値"])
        I = T[u"5 注入"]
        self.assertEqual(round(100.0 * 6 / 40, 1), I["T9_PRIOR_TO_CURRENT"]["P32E"][u"形別"]["F9"][PASS][u"率"])
        self.assertEqual(round(100.0 * 1 / 40, 1), I["T1_VALUE"]["P32E"][u"形別"]["F6"][PASS][u"率"])
        self.assertEqual(0.27, round(T[u"7 F1〜F5 との並べ"][u"F1〜F5 全体の 1 本あたりの動いた行"][u"1 本あたり"], 2))

    def test_c_2_none_pointers_do_not_break_the_profile_columns(self):
        E = self.T[u"3 engine の判定(無改変)"]
        for p in ("P27", FX.FX_PROFILES[3]):
            self.assertGreater(E[p][u"全体"][u"対応が付かない行"], 0)           # 欄の無い行は分母に入れず数えるだけ
            self.assertEqual(E[p][u"全体"][u"claim"], E["P32E"][u"全体"][u"claim"])

    def test_c_3_the_table_is_rendered_from_the_judgments(self):
        t = FX.render_table(self.J).split(u"\n")
        self.assertEqual(u"| # | 判定 | 値 |", t[0])
        self.assertEqual(11 + 3, len(t))
        self.assertTrue(t[-1].startswith(u"| 計 | 当たり 10・外れ 0・判定しない 1"))


def perturbed(fn):
    spec = good_spec()
    fn(spec)
    _R, _T, J = synth_judge(spec)
    return J


def set_comp(spec, form, **kw):
    for w in MODEL:
        c = dict(spec["comp"][(form, w)])
        c.update(kw)
        spec["comp"][(form, w)] = c


def set_inj(spec, t, f=None, w=None, **kw):
    for (tt, ff, ww), s in spec["inj"].items():
        if tt == t and (f is None or ff == f) and (w is None or ww == w):
            s.update(kw)


class BoundaryTest(unittest.TestCase):
    u"""封 §2 の X-n ごとに、幅の端(中)で当たり・端のすぐ外で外れ。分母 0 は None = 外れ。"""

    def check(self, x, fn_hit, fn_miss, key=None):
        j_hit, j_miss = perturbed(fn_hit), perturbed(fn_miss)
        self.assertEqual(HIT, j_hit[x][u"判定"], (x, j_hit[x][u"値"]))
        self.assertEqual(MISS, j_miss[x][u"判定"], (x, j_miss[x][u"値"]))
        return j_hit, j_miss

    def test_g_1_X1_books_and_cost_and_cap(self):
        self.check("X-1", lambda s: s.update(short_books=10), lambda s: s.update(short_books=11))                 # 150 本は当たり・149 本は外れ
        self.check("X-1", lambda s: s.update(cost_per_call=0.1125), lambda s: s.update(cost_per_call=0.112))     # 18.0 USD は当たり・17.92 は外れ
        self.check("X-1", lambda s: s.update(cost_per_call=0.21875), lambda s: s.update(cost_per_call=0.2190))   # 35.0 は当たり・35.04 は外れ
        self.check("X-1", lambda s: s.update(stop=None), lambda s: s.update(stop=u"累計 39.9000 + 次の見積り 0.2670 が上限 40.00 USD を超える(x の前)"))
        self.check("X-1", lambda s: s.update(stop=u"HTTP 401(鍵の問題)", short_books=0), lambda s: s.update(stop=u"累計 1.0 + 次の見積り 0.2 が上限"))   # 上限でない停止は止まりに数えない

    def test_g_2_X2_median_of_the_claims_per_book(self):
        self.check("X-2", lambda s: set_comp(s, "F7", tg=5, ts=3), lambda s: set_comp(s, "F7", tg=4, ts=3))        # 10 本は当たり・9 は外れ
        self.check("X-2", lambda s: set_comp(s, "F6", tg=13, ts=10), lambda s: set_comp(s, "F6", tg=14, ts=10))   # 25 は当たり・26 は外れ

    def test_g_3_X3_label_true_grounded_rate(self):
        self.check("X-3", lambda s: set_comp(s, "F8", tg=34, ts=16), lambda s: set_comp(s, "F8", tg=33, ts=16))   # 68.0 は当たり・67.3 は外れ
        self.check("X-3", lambda s: set_comp(s, "F8", tg=17, ts=3), lambda s: set_comp(s, "F8", tg=18, ts=3))     # 85.0 は当たり・85.7 は外れ
        j, _ = self.check("X-3", lambda s: set_comp(s, "F8", tg=28, ts=12), lambda s: set_comp(s, "F9", tg=28, ts=12) or set_comp(s, "F8", tg=28, ts=12))
        self.assertEqual(70.0, j["X-3"][u"値"]["F8"])                                                                 # F8 が最高 → 同率の F9(70.0)があれば外れ

    def test_g_4_X4_million_yen_share(self):
        self.check("X-4", lambda s: set_comp(s, "F8", ym=8, yo=2), lambda s: set_comp(s, "F8", ym=7, yo=2))       # 80.0 は当たり・77.8 は外れ
        j = perturbed(lambda s: set_comp(s, "F8", ym=0, yo=0))                                                       # 円族の数が 0 = 分母 0 は None = 外れ
        self.assertEqual(MISS, j["X-4"][u"判定"])
        self.assertIsNone(j["X-4"][u"値"][u"百万円の書き方の率"])

    def test_g_5_X5_prior_share_and_cues(self):
        self.check("X-5", lambda s: set_comp(s, "F9", pw=8, pc=2, pn=2), lambda s: set_comp(s, "F9", pw=8, pc=2, pn=1))        # 前期の割合 30.0 は当たり・27.5 は外れ
        self.check("X-5", lambda s: set_comp(s, "F9", pw=8, pc=4, pn=4), lambda s: set_comp(s, "F9", pw=7, pc=5, pn=4))        # 窓 50.0 は当たり・43.8 は外れ
        self.check("X-5", lambda s: set_comp(s, "F9", pw=14, pc=2, pn=4), lambda s: set_comp(s, "F9", pw=15, pc=1, pn=4))      # 節だけ 10.0 は当たり・5.0 は外れ
        self.check("X-5", lambda s: set_comp(s, "F9", pw=11, pc=3, pn=2), lambda s: set_comp(s, "F9", pw=0, pc=0, pn=0, mv=0, pwc=0))  # 前期の数が 0 = 分母 0 は外れ

    def test_g_6_X6_t9_pass_rate_and_majority(self):
        t9 = "T9_PRIOR_TO_CURRENT"

        def f9(s, w1, w2, wf1, wf2):
            set_inj(s, t9, "F9", w="W1", passed=w1, win_false=wf1)
            set_inj(s, t9, "F9", w="W2", passed=w2, win_false=wf2)
        self.check("X-6", lambda s: f9(s, 1, 1, 1, 1), lambda s: f9(s, 1, 0, 1, 0))               # 2/40 = 5.0 は当たり・1/40 = 2.5 は外れ
        self.check("X-6", lambda s: f9(s, 5, 5, 3, 3), lambda s: f9(s, 6, 5, 3, 3))               # 10/40 = 25.0 は当たり・11/40 = 27.5 は外れ
        self.check("X-6", lambda s: f9(s, 2, 2, 2, 2), lambda s: f9(s, 2, 2, 1, 1))               # 通した 4 行のうち窓の手がかり偽 4(過半)は当たり・2(半分)は外れ
        self.check("X-6", lambda s: set_inj(s, t9, "F6", passed=3, win_false=3), lambda s: set_inj(s, t9, "F6", passed=0, win_false=0))     # F6 の 6/40 = 15.0 は当たり・0.0 は外れ
        self.check("X-6", lambda s: set_inj(s, t9, "F8", passed=4, win_false=4), lambda s: set_inj(s, t9, "F8", passed=5, win_false=5))     # F8 の 8/40 = 20.0 は当たり・25.0 は外れ

    def test_g_7_X7_label_false_rate(self):
        self.check("X-7", lambda s: set_comp(s, "F6", tg=28, ts=20, fa=1, nj=1), lambda s: set_comp(s, "F6", tg=28, ts=22, fa=1, nj=1))       # 2.0 は当たり・1/52 = 1.9 は外れ
        self.check("X-7", lambda s: set_comp(s, "F8", tg=32, ts=6, fa=1, nj=1), lambda s: set_comp(s, "F8", tg=32, ts=6, fa=0, nj=2))          # 2.5 → 0.0
        self.check("X-7", lambda s: set_comp(s, "F9", nj=1), lambda s: set_comp(s, "F9", nj=100))                                              # 全体の札 真 80% 以上 → 未満

    def test_g_8_X8_injection_pass_rates(self):
        self.check("X-8", lambda s: set_inj(s, "T1_VALUE", "F6", w="W1", passed=2) or set_inj(s, "T1_VALUE", "F6", w="W2", passed=0),
                   lambda s: set_inj(s, "T1_VALUE", "F6", w="W1", passed=3))                                                                   # 2/40 = 5.0 は当たり・3/40 = 7.5 は外れ
        self.check("X-8", lambda s: None, lambda s: set_inj(s, "T5_COINCIDENT", "F7", n=0, passed=0))                                         # T5 の F7 の行が 0 = 分母 0 は外れ
        self.check("X-8", lambda s: None, lambda s: set_inj(s, "T8_REL", "F9", w="W2", passed=2) or set_inj(s, "T8_REL", "F9", w="W1", passed=2))

    def test_g_9_X9_writer_gap_and_spread(self):
        def wide(s, rate_w2):
            s["comp"][("F6", "W2")] = comp(rate_w2, 100 - rate_w2, 1, 1, yo=3)
        self.check("X-9", lambda s: wide(s, 72) or s["comp"].update({("F6", "W1"): comp(60, 40, 1, 1, yo=3)}),
                   lambda s: wide(s, 73) or s["comp"].update({("F6", "W1"): comp(60, 40, 1, 1, yo=3)}))                                        # 差 12.0 は当たり・13.0 は外れ

        def flat(s):
            for f in FORMS:
                s["comp"][(f, "W2")] = comp(6, 4, 1, 1, yo=3, ym=0, pw=0, pc=0, pn=0, mv=0)
        _h, m = self.check("X-9", lambda s: None, flat)                                                                                      # W2 の形の幅が 0 → 外れ
        self.assertEqual(0.0, m["X-9"][u"値"][u"model ごとの形の幅"]["W2"])

    def test_g_10_X10_moved_rows_per_book(self):
        j, m = self.check("X-10", lambda s: set_comp(s, "F9", mv=1), lambda s: set_comp(s, "F9", mv=0))
        self.assertEqual(1.0, j["X-10"][u"値"][u"F9 の 1 本あたり"])
        self.assertEqual(0.0, m["X-10"][u"値"][u"F9 の 1 本あたり"])
        self.assertEqual(0.27, round(j["X-10"][u"値"][u"F1〜F5 の 1 本あたり"], 2))                                                            # 54 / 200


# ================================================================ (c) 記録の中身
def walk_keys(obj):
    return list(RUN.walk_keys(obj))


def record_problems(R, full=True, root=ROOT, docs_expected=None):
    u"""記録 5 つ(gen・claims・labels・inject・tally)の検査。問題の列。tally は無くてもよい(R に無ければ集計の検査は飛ばす)。"""
    out = []
    for k, rec in R.items():
        bad = sorted(set(x for x in walk_keys(rec) if x in FORBIDDEN_KEYS))
        if bad:
            out.append(u"%s: 禁止欄 %s" % (k, u",".join(bad)))
        text = json.dumps(rec, ensure_ascii=False)
        if GEN.key_leaks(text, None, long_alnum=False):
            out.append(u"%s: 鍵らしい字" % k)
        for w in COMPANY_WORDS:
            if w in text:
                out.append(u"%s: 会社名らしい字 %s" % (k, w))
        if rec.get(u"key_leaks"):
            out.append(u"%s: key_leaks が空でない" % k)
        if u"差し替え" in rec and norm(rec[u"差し替え"]) != norm(FX.swap_field()):
            out.append(u"%s: 差し替えの欄が駆動 script から作り直した値と違う" % k)
        if u"step" in rec and (u"F6〜F9" not in rec[u"step"]):
            out.append(u"%s: step の字が FX でない" % k)
    gen, claims, labels, inj = R["gen"], R["claims"], R["labels"], R["inject"]
    docs = gen[u"会社の選び"][u"docID"]
    if docs_expected is not None and docs != docs_expected:
        out.append(u"gen: 会社の列が前の便と違う")
    cost = gen.get(u"費用", {})
    if cost.get(u"上限 USD") != 40.0:
        out.append(u"gen: 費用の上限が 40 でない")
    if full and cost.get(u"実測の平均 USD") not in (None, norm(FX.AVG_COST_USD)):
        out.append(u"gen: 実測の平均が駆動 script の定数と違う")
    for c in gen[u"呼び出し"]:
        if c[u"form"] not in FORMS or c[u"model"] not in MODEL.values():
            out.append(u"gen: 形か model が封の外: %s" % c[u"name"])
    total = round(sum(c[u"cost_usd"] for c in gen[u"呼び出し"]), 6)
    if full and u"累計" in gen and (gen[u"累計"][u"費用 USD"] != total or gen[u"累計"][u"記録の外の費用 USD"] != 0.0):
        out.append(u"gen: 累計が呼び出しの和と違う(この便は記録の外の費用を持たない)")
    if total > 40.0:
        out.append(u"gen: 費用の合計が上限を超える")
    if list(claims.get(u"profile", [])) != list(FX.FX_PROFILES):
        out.append(u"claims: profile の並びが違う")
    width = len(FX.CLAIM_COLS_FX) + len(FX.FX_PROFILES)
    row_ids = {}
    for b in claims[u"本"]:
        if b.get(u"欠け"):
            continue
        if b[u"docID"] not in docs:
            out.append(u"claims: 選んだ会社の外の docID")
        n = len(b[u"行"])
        if not (n == b[u"claim の数"] == b[u"数の claim の数"][FX.AXIS]):
            out.append(u"claims: %s の行の数が claim の数と違う" % b[u"name"])
        for r in b[u"行"]:
            if len(r) != width:
                out.append(u"claims: %s の行の長さが %d でない(手がかりの 2 欄を含む)" % (b[u"name"], width))
                break
            if r[6] not in (True, False, None) or r[7] not in (True, False, None):
                out.append(u"claims: %s の手がかりの欄が真偽でない" % b[u"name"])
                break
        row_ids[b[u"name"]] = [r[0] for r in b[u"行"]]
        if full and b[u"4 state"].keys() != set(FX.FX_PROFILES):
            out.append(u"claims: %s の 4 state の profile が違う" % b[u"name"])
        if b[u"行の軸に無い鍵の数"].keys() != set(FX.FX_PROFILES):
            out.append(u"claims: %s の行の軸に無い鍵の数の profile が違う" % b[u"name"])
    for b in labels[u"本"]:
        if [x[0] for x in b[u"札"]] != row_ids.get(b[u"name"]):
            out.append(u"labels: %s の札の id が claims の行の id と 1 対 1 でない" % b[u"name"])
    if re.search(r"(?:jppfs|jpcrp|jpigp|jpdei)_cor:", json.dumps(inj, ensure_ascii=False)):
        out.append(u"inject: 記録に要素名の字がある(注入の記録は持たない)")
    for r in inj[u"行"]:
        if r[u"型"] not in FX.FX_INJECT_TYPES or r[u"form"] not in FORMS:
            out.append(u"inject: 型か形が封の外")
            break
        if not all(p in r for p in FX.INJECT_PROFILES):
            out.append(u"inject: 行に P30E・P32E の欄が無い")
            break
        if r[u"型"] == "T9_PRIOR_TO_CURRENT" and r.get(u"窓の手がかり") not in (True, False):
            out.append(u"inject: T9 の行に窓の手がかりが無い")
            break
    if "tally" in R:
        T = R["tally"]
        try:
            built = FX.build_fx(dict((k, R[k]) for k in ("gen", "claims", "labels", "inject")), FX.load_refs(root))
            J = FX.judge_fx(built)
        except Exception as e:                           # noqa: BLE001  壊れた記録は集計できない = 赤
            return out + [u"tally: 記録から集計を作れない(%s)" % type(e).__name__]
        if norm(built) != T[u"集計"]:
            out.append(u"tally: 集計が記録から作り直した値と違う")
        if norm(J) != T[u"予測の判定"]:
            out.append(u"tally: 予測の判定が記録から作り直した判定と違う")
        c = collections.Counter(v[u"判定"] for v in J.values())
        if (T[u"当たり"], T[u"外れ"], T[u"判定しない"]) != (c.get(HIT, 0), c.get(MISS, 0), c.get(NOJ, 0)):
            out.append(u"tally: 当たり・外れの数が判定と違う")
    return out


def synth_full(spec=None):
    R = synth_records(spec or good_spec())
    R = copy.deepcopy(R)
    T = FX.build_fx(R, FX.load_refs(ROOT))
    J = FX.judge_fx(T)
    R["tally"] = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"step", FX.restep(u"AI の形 4 × model 2 ― 集計")), (u"差し替え", FX.swap_field()), (u"集計", norm(T)), (u"予測の判定", norm(J)),
        (u"当たり", sum(1 for v in J.values() if v[u"判定"] == HIT)), (u"外れ", sum(1 for v in J.values() if v[u"判定"] == MISS)),
        (u"判定しない", sum(1 for v in J.values() if v[u"判定"] == NOJ)), (u"key_leaks", [])])
    for k in ("gen", "claims", "labels", "inject"):
        R[k][u"step"] = FX.restep(u"AI の形 4 × model 2 ― x")
        R[k][u"差し替え"] = FX.swap_field()
    R["gen"][u"累計"] = {u"費用 USD": round(sum(c[u"cost_usd"] for c in R["gen"][u"呼び出し"]), 6), u"記録の外の費用 USD": 0.0}
    return R


class RecordMutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = synth_full()

    def probe(self, fn):
        R = copy.deepcopy(self.base)
        fn(R)
        return record_problems(R, full=True, docs_expected=DOCS)

    def test_c_4_good_records_are_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.base), full=True, docs_expected=DOCS))

    def test_c_5_one_changed_state_turns_the_tally_check_red(self):
        def flip(R):
            row = R["claims"][u"本"][0][u"行"][0]
            for j in range(len(FX.CLAIM_COLS_FX), len(row)):
                if isinstance(row[j], list) and row[j][0] == "GROUNDED":
                    row[j] = ["VALUE_MISMATCH"] + row[j][1:]
                    break
        got = self.probe(flip)
        self.assertTrue(any(u"tally: 集計が記録から作り直した値と違う" in g for g in got), got)

    def test_c_6_a_forbidden_key_or_a_dropped_cue_column_turns_it_red(self):
        def span(R):
            R["claims"][u"本"][3][u"span"] = u"x"
        self.assertTrue(any(u"禁止欄" in g for g in self.probe(span)))

        def inject_value(R):
            R["inject"][u"行"][0][u"value"] = 1
        self.assertTrue(any(u"禁止欄" in g for g in self.probe(inject_value)))

        def drop_cue(R):
            for b in R["claims"][u"本"][:1]:
                for r in b[u"行"]:
                    del r[6:8]
        got = self.probe(drop_cue)
        self.assertTrue(any(u"行の長さ" in g for g in got), got)

        def bad_cue(R):
            R["claims"][u"本"][0][u"行"][0][6] = u"真"
        self.assertTrue(any(u"手がかりの欄が真偽でない" in g for g in self.probe(bad_cue)))

    def test_c_7_labels_claims_and_inject_mutations_turn_it_red(self):
        def label_id(R):
            R["labels"][u"本"][0][u"札"][0][0] = u"N999"
        self.assertTrue(any(u"1 対 1 でない" in g for g in self.probe(label_id)))

        def label_word(R):
            R["labels"][u"本"][0][u"札"][0][1] = u"偽" if R["labels"][u"本"][0][u"札"][0][1] != u"偽" else u"真"
        self.assertTrue(any(u"tally" in g for g in self.probe(label_word)))

        def drop_row(R):
            R["claims"][u"本"][0][u"行"].pop()
        self.assertTrue(any(u"行の数が claim の数と違う" in g for g in self.probe(drop_row)))

        def inj_pass(R):
            for r in R["inject"][u"行"]:
                if r[u"型"] == "T8_REL" and r[u"P32E"][u"結果"] == NAMED:
                    r[u"P32E"][u"結果"] = PASS
                    break
        self.assertTrue(any(u"tally" in g for g in self.probe(inj_pass)))

        def window_flag(R):
            for r in R["inject"][u"行"]:
                if r[u"型"] == "T9_PRIOR_TO_CURRENT" and r[u"P32E"][u"結果"] == PASS and r[u"窓の手がかり"] is False:
                    r[u"窓の手がかり"] = True
                    break
        self.assertTrue(any(u"tally" in g for g in self.probe(window_flag)))

        def judgement(R):
            R["tally"][u"予測の判定"]["X-3"][u"判定"] = MISS
        self.assertTrue(any(u"予測の判定" in g for g in self.probe(judgement)))

        def swap(R):
            R["gen"][u"差し替え"][u"費用"][u"上限 USD"] = 50.0
        self.assertTrue(any(u"差し替えの欄" in g for g in self.probe(swap)))

        def cap(R):
            R["gen"][u"費用"][u"上限 USD"] = 50.0
        self.assertTrue(any(u"費用の上限" in g for g in self.probe(cap)))

        def docid(R):
            R["claims"][u"本"][0][u"docID"] = u"XX"
        self.assertTrue(any(u"選んだ会社の外" in g for g in self.probe(docid)))

        def element_name(R):
            R["inject"][u"行"][0][u"相手の要素"] = u"jppfs_cor:NetSales"
        self.assertTrue(any(u"要素名" in g for g in self.probe(element_name)))

        def leak(R):
            R["gen"][u"呼び出し"][0][u"error"] = u"sk-" + u"a" * 20
        self.assertTrue(any(u"鍵らしい字" in g for g in self.probe(leak)))


# ================================================================ (c) 行の欄の部品
class PartsTest(unittest.TestCase):
    def cells(self, state, ptrs):
        return dict(zip(RUN.PROFILE_COLS, cell(state, ptrs)))

    def test_c_8_period_of_cell_and_moved(self):
        self.assertEqual(u"前期", FX.period_of_cell(self.cells("GROUNDED", PRI)))
        self.assertEqual(u"当期", FX.period_of_cell(self.cells("GROUNDED", CUR + PRI)))               # 先頭の pointer の期
        self.assertEqual(u"他", FX.period_of_cell(self.cells("GROUNDED", [u"(xbrl 以外)"])))
        self.assertEqual(u"なし", FX.period_of_cell(self.cells("UNVERIFIABLE", [])))
        self.assertIsNone(FX.period_of_cell(None))
        a, b = self.cells("GROUNDED", CUR), self.cells("GROUNDED", PRI)
        self.assertTrue(FX.moved(a, b))                                                                # pointer の期だけ違う = 動いた行
        self.assertFalse(FX.moved(a, dict(a)))
        self.assertTrue(FX.moved(a, self.cells("VALUE_MISMATCH", CUR)))                                # state だけ違う
        self.assertFalse(FX.moved(a, None))
        self.assertFalse(FX.moved(None, b))

    def test_c_9_the_cue_functions_are_the_engine_ones(self):
        R_ = FX.R
        s = u"売上高は前期は50億円、当期は60億円でした。"
        a_prior, a_cur = s.index(u"50"), s.index(u"60")
        self.assertTrue(R_._prior_cue_window_2026_11_06(s, a_prior))
        self.assertFalse(R_._prior_cue_window_2026_11_06(s, a_cur))
        s2 = u"前期は原材料の高騰を受けて50億円でした。"
        a2 = s2.index(u"50")
        self.assertFalse(R_._prior_cue_window_2026_11_06(s2, a2))                                      # 12 字の窓の外
        self.assertTrue(R_._prior_cue_clause(s2, a2))                                                  # 同じ節に「前期は」
        s3 = u"前期は売上が伸びた。原材料の高騰を受けて50億円でした。"
        self.assertFalse(R_._prior_cue_clause(s3, s3.index(u"50")))                                    # 句点で節が切れる


# ================================================================ (g) 使い捨ての流れ(1 本)
def fake_text(prompt):
    u"""偽の書き手: 5 欄の表の円の fact から『前期は … 百万円』『当期は … 百万円』の文を書く(手がかりの 2 欄・注入が動くように)。"""
    rows = []
    for ln in prompt.split(u"\n"):
        if ln.startswith(u"| ") and u"JPY" in ln and u"時点" not in ln:
            c = [x.strip() for x in ln.strip(u"|").split(u"|")]
            if len(c) == 5 and c[1]:
                rows.append((c[1], float(c[2])))
    seen, uniq = set(), []
    for lab, v in rows:
        r = round(v / 1e6)
        if r not in seen and r > 0:
            seen.add(r)
            uniq.append((lab, v))
    lines = [u"経営成績"]
    for lab, v in uniq[:20]:
        lines.append(u"%sは、前期は %s百万円でした。" % (lab, format(round(v / 1e6), u",")))
        lines.append(u"%sは、当期は %s百万円でした。" % (lab, format(round(v * 1.1 / 1e6), u",")))
    lines.append(u"補足として、前期は 1,234万円、当期は 82億9,480万円でした。")             # 万円のコンマ書きは P27 が読まず P30E 以降が読む(行の軸に P27 の欄が無い行を作る)
    return u"\n".join(lines)


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class SmokeFlow(unittest.TestCase):
    u"""1 社 1 本(F9 × haiku。偽の書き手・通信しない)で 生成 → 判定 → 注入 → 札(偽の席)→ 集計 を通す。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="aiforms_fx_smoke_", dir=os.environ.get("TMPDIR"))
        cls.cache = os.path.join(cls.tmp, "cache")
        seed, cls.seed_meta = GEN.seed_value(ROOT)
        chosen, counts = GEN.select_companies(ROOT, seed)
        cls.doc = chosen[0]["docID"]
        cls.model = "claude-haiku-5-5"
        cls.name = GEN.text_key(cls.doc, "F9", cls.model)
        p = Patch()
        cls.p = p
        p.set(GEN, "select_companies", lambda root, seed=None: (chosen[:1], counts))
        p.set(GEN, "FORMS", ("F9",))
        p.set(GEN, "MODELS", (cls.model,))
        p.set(FX, "NOT_NEEDED_AFTER_GEN", ("GEN.select_companies", "GEN.FORMS"))           # 生成を 1 本に絞るために GEN.FORMS だけ替える(集計の形 4 つ・TAL.FORMS はそのまま)
        os.environ[GEN.KEY_ENV] = "SECRETKEY-aaaaaaaaaaaaaaaaaaaa"

        def transport(prompt, model, key):
            text = fake_text(prompt)
            return 200, json.dumps({"content": [{"type": "text", "text": text}], "usage": {"input_tokens": len(prompt), "output_tokens": len(text)}, "stop_reason": "end_turn"}).encode("utf-8")
        cls.gen_path = os.path.join(cls.tmp, "gen.json")
        FX.GEN.run(root=ROOT, only=cls.doc, out=cls.gen_path, new_cache=cls.cache, key_value=os.environ[GEN.KEY_ENV], transport=transport, sleep=lambda s: None, say=FX.say_fx(lambda *a: None))
        os.environ.pop(GEN.KEY_ENV, None)
        cls.claims_path = os.path.join(cls.tmp, "claims.json")
        cls.claims = RUN.run_judge(root=ROOT, only=cls.doc, gen_path=cls.gen_path, new_cache=cls.cache, out=cls.claims_path, say=lambda *a: None)
        cls.inject_path = os.path.join(cls.tmp, "inject.json")
        cls.inject = FX.run_inject_fx(root=ROOT, only=cls.doc, gen_path=cls.gen_path, new_cache=cls.cache, out=cls.inject_path, say=lambda *a: None, work_root=os.path.join(cls.tmp, "work"))
        # 偽の席: 札は全部 真(束の id と 1 対 1)
        ddir = os.path.join(cls.cache, "dossiers")
        book = [b for b in cls.claims[u"本"] if not b.get(u"欠け")][0]
        dossier = jload_abs(os.path.join(ddir, book[u"札付けの束の鍵"] + ".json"))
        cls.labels = collections.OrderedDict([(u"本", [collections.OrderedDict([
            (u"name", book[u"name"]), (u"docID", book[u"docID"]), (u"form", book[u"form"]), (u"model", book[u"model"]), (u"writer", book[u"writer"]),
            (u"札付けの束の鍵", book[u"札付けの束の鍵"]), (u"札", [[c["id"], u"真", None, u"高", []] for c in dossier["claims"]])])]),
            (u"集計", {u"2 席目との一致": {u"一致率": None}})])
        cls.gen = jload_abs(cls.gen_path)

    @classmethod
    def tearDownClass(cls):
        cls.p.undo()
        os.environ.pop(GEN.KEY_ENV, None)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_g_0_the_flow_is_green(self):
        R = collections.OrderedDict([("gen", self.gen), ("claims", self.claims), ("labels", self.labels), ("inject", self.inject)])
        T = FX.build_fx(R, FX.load_refs(ROOT))
        J = FX.judge_fx(T)
        self.assertEqual(sorted(["X-%d" % i for i in range(1, 12)]), sorted(J))
        self.assertEqual(1, T[u"1 配線"][u"生成できた本"])
        self.assertEqual([], [g for g in record_problems(copy.deepcopy(R), full=False) if u"tally" not in g and u"差し替え" not in g and u"step" not in g])

    def test_g_1_the_claims_record_has_four_profiles_and_the_cue_columns(self):
        book = [b for b in self.claims[u"本"] if not b.get(u"欠け")][0]
        self.assertEqual(list(FX.FX_PROFILES), self.claims[u"profile"])
        self.assertEqual(list(FX.CLAIM_COLS_FX), self.claims[u"欄"][u"claim"])
        self.assertEqual(list(FX.FX_PROFILES), list(book[u"数の claim の数"]))
        self.assertGreater(len(book[u"行"]), 0)
        self.assertEqual(len(book[u"行"]), book[u"数の claim の数"][FX.AXIS])
        rows = [RUN.decode_row(r) for r in book[u"行"]]
        self.assertTrue(all(d[u"窓の手がかり"] in (True, False) and d[u"節の手がかり"] in (True, False) for d in rows))
        self.assertTrue(any(d[u"窓の手がかり"] for d in rows))                 # 偽の書き手は「前期は …」で書く
        self.assertTrue(all(d[FX.AXIS] is not None for d in rows))             # 行の軸 = P32E の数の claim
        self.assertTrue(any(d["P27"] is None for d in rows))                   # P27 が読まない数(万円の複合など)は欄が無い
        self.assertEqual(FX.ROW_ORDER_TEXT, self.claims[u"欄"][u"行の並び"])
        self.assertEqual(FX.CUE_TEXT, self.claims[u"欄"][u"手がかりの欄"])
        self.assertEqual(0, sum(book[u"行の軸に無い鍵の数"].values()))

    def test_g_2_the_cue_columns_are_what_the_engine_functions_say(self):
        zb = GEN.read_zip(dict((r["docID"], r) for r in RUN.company_rows(self.gen, ROOT))[self.doc])
        text = open(os.path.join(self.cache, "texts", self.name + ".txt"), encoding="utf-8").read()
        zm = FX.PR.build_modified_zip(zb, text)[0]
        view = FX.profile_view_fx(zb, text, zm, FX.AXIS)
        book = [b for b in self.claims[u"本"] if not b.get(u"欠け")][0]
        by_id = dict((r[0], r) for r in book[u"行"])
        n = 0
        for key, (c, r) in view["rows"].items():
            s = view["sents"][r["sentence"]]
            self.assertEqual(bool(FX.R._prior_cue_window_2026_11_06(s, r["pos"])), by_id[c["id"]][6])
            self.assertEqual(bool(FX.R._prior_cue_clause(s, r["pos"])), by_id[c["id"]][7])
            n += 1
        self.assertEqual(len(book[u"行"]), n)

    def test_g_3_the_inject_record_has_the_four_types_and_both_profiles(self):
        types = set(r[u"型"] for r in self.inject[u"行"])
        self.assertTrue(types <= set(FX.FX_INJECT_TYPES))
        self.assertGreaterEqual(len(types), 3)
        self.assertEqual(list(FX.INJECT_PROFILES), self.inject[u"profile"])
        for r in self.inject[u"行"]:
            for p in FX.INJECT_PROFILES:
                self.assertIn(u"結果", r[p])
        self.assertEqual([u"W2"], sorted(set(r[u"writer"] for r in self.inject[u"行"])))
        t9 = [r for r in self.inject[u"行"] if r[u"型"] == "T9_PRIOR_TO_CURRENT"]
        self.assertTrue(all(r[u"窓の手がかり"] in (True, False) for r in t9))
        self.assertEqual(norm(FX.swap_field()), self.inject[u"差し替え"])
        self.assertEqual(SEAL_REL, self.inject["seal"])
        self.assertFalse(getattr(FX.TY.N, FX.TY.FLAG))
        self.assertFalse(getattr(FX.TY.S, FX.TY.FLAG2))

    def test_g_4_mutating_the_smoke_records_turns_the_check_red(self):
        R = collections.OrderedDict([("gen", self.gen), ("claims", self.claims), ("labels", self.labels), ("inject", self.inject)])
        R2 = copy.deepcopy(R)
        R2["claims"][u"本"][0][u"span"] = u"x" if not R2["claims"][u"本"][0].get(u"欠け") else u"x"
        self.assertTrue(any(u"禁止欄" in g for g in record_problems(R2, full=False)))
        R3 = copy.deepcopy(R)
        b = [b for b in R3["claims"][u"本"] if not b.get(u"欠け")][0]
        b[u"行"][0] = b[u"行"][0][:6] + b[u"行"][0][8:]
        self.assertTrue(any(u"行の長さ" in g for g in record_problems(R3, full=False)))


# ================================================================ (d) 文書
def doc_problems(doc, R):
    J = FX.judge_fx(FX.build_fx(dict((k, R[k]) for k in ("gen", "claims", "labels", "inject")), FX.load_refs(ROOT)))
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != FX.render_table(J).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    for k in got:
        if k != "pred":
            out.append(u"知らない表 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"docID が文書にある")
    for w in FOR_RESULT_WORDS:
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = synth_full()
        cls.table = FX.render_table(FX.judge_fx(FX.build_fx(cls.R, FX.load_refs(ROOT))))
        cls.doc = u"# 結果\n\n<!-- 門:start pred -->\n%s\n<!-- 門:end -->\n\n散文です。数は 12 と 8 だけ。\n" % cls.table

    def test_d_0_the_good_doc_is_green(self):
        self.assertEqual([], doc_problems(self.doc, self.R))

    def test_d_1_one_character_in_the_table_a_docid_a_word_or_a_bare_number_turn_it_red(self):
        for bad in (self.doc.replace(u"当たり", u"当り", 1), self.doc.replace(u"| X-3 |", u"| X-4 |", 1), self.doc + u"\nS100AB12 を見た。\n", self.doc + u"\n精度が高い。\n",
                    self.doc + u"\n全部で 160 本だった。\n", self.doc.replace(u"<!-- 門:start pred -->", u"<!-- 門:start other -->")):
            self.assertNotEqual(self.doc, bad)
            self.assertNotEqual([], doc_problems(bad, self.R), bad[-40:])
        self.assertEqual([], doc_problems(self.doc + u"\n全部で 160 本だった。" + PR.NOT_GATED + u"\n", self.R))


# ================================================================ 宣言
def later_naming_files(src):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "LATER_NAMING_FILES":
            return list(ast.literal_eval(n.value))
    return None


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in REC_REL.values() if rel not in got] + \
        [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in [DRIVER_REL, DOC_REL] + list(GATE_FILES) if rel in got]


class DeclarationTest(unittest.TestCase):
    def test_h_1_the_five_records_are_declared_as_naming_files(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        self.assertNotEqual([], naming_problems(src.replace('"fixtures/xbrl/aiforms/fx_tally_2026-11-09.json",', '"fixtures/xbrl/aiforms/fx_tally_2026-11-09.json", "%s",' % DRIVER_REL)))

    def test_h_2_the_previous_runs_are_still_declared(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        for k in OLD.REC_REL.values():
            self.assertIn(k, later_naming_files(src))
        self.assertIn("fixtures/xbrl/aiforms/f5_tally_2026-11-03.json", later_naming_files(src))


# ---------------------------------------------------------------- 順序(e)の変異(使い捨ての repo)
OTHERS = list(REC_REL.values()) + [DOC_REL] + list(GATE_FILES)
IMPLS = [DRIVER_REL]


class OrderMutationTest(unittest.TestCase):
    def _good(self):
        r = PR.Repo()
        r.put(SEAL_REL)
        s = r.commit(SEAL_REL)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        for f in OTHERS:
            r.put(f)
        r.commit(*OTHERS)
        return r, s

    def probe(self, r, s):
        return PR.order_problems(r.d, PREFIX, SEAL_REL, s[:7], IMPLS, OTHERS)

    def test_e_1_good_order_is_green(self):
        r, s = self._good()
        self.assertEqual([], self.probe(r, s))

    def test_e_2_uncommitted_before_seal_or_before_the_driver_is_red(self):
        r = PR.Repo()
        r.put(SEAL_REL)
        s = r.commit(SEAL_REL)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(self.probe(r, s)))
        r2 = PR.Repo()
        r2.put(OTHERS[0])
        r2.commit(OTHERS[0])
        r2.put(SEAL_REL)
        s2 = r2.commit(SEAL_REL)
        for f in IMPLS:
            r2.put(f)
        r2.commit(*IMPLS)
        for f in OTHERS[1:]:
            r2.put(f)
        r2.commit(*OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], self.probe(r2, s2))
        r3 = PR.Repo()
        r3.put(SEAL_REL)
        s3 = r3.commit(SEAL_REL)
        r3.put(OTHERS[0])
        r3.commit(OTHERS[0])
        for f in IMPLS:
            r3.put(f)
        r3.commit(*IMPLS)
        for f in OTHERS[1:]:
            r3.put(f)
        r3.commit(*OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], self.probe(r3, s3))
        r4 = PR.Repo()
        r4.put(SEAL_REL)
        s4 = r4.commit(SEAL_REL)
        for f in OTHERS:
            r4.put(f)
        r4.commit(*OTHERS)
        self.assertIn("IMPL_UNCOMMITTED:" + DRIVER_REL, self.probe(r4, s4))

    def test_e_3_a_wrong_seal_is_red(self):
        r, _s = self._good()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r.d, PREFIX, SEAL_REL, "abcdef0", IMPLS, OTHERS))


# ---------------------------------------------------------------- 本物の記録(c)(d)(e)
@unittest.skipUnless(records_exist(), "記録が無い(生成・判定・札・注入・集計の後に走る)")
class RealRecordsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = load_records()

    def test_c_1_records_are_clean_and_consistent(self):
        prev_docs = jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"]
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=True, docs_expected=prev_docs))
        for k, rel in REC_SCRIPT.items():
            self.assertEqual(sha256_rel(rel), self.R[k][u"この script の sha256"], k)
        self.assertEqual(sha256_rel(DRIVER_REL), self.R["tally"][u"この script の sha256"])
        for k in ("gen", "claims", "inject"):
            cache = self.R[k][u"cache の前後"]
            self.assertTrue(cache[u"変化なし"], k)
            self.assertEqual(cache[u"前"], cache[u"後"])
            self.assertIn(FX.PREV_CACHE_NAME, cache[u"前"])
        for k in ("gen", "claims", "labels", "inject", "tally"):
            self.assertIn(self.R[k]["seal"], (SEAL_REL,))
        self.assertEqual(SEAL_COMMIT_SHORT, self.R["gen"][u"封の commit"])

    def test_d_1_the_result_document_follows_the_records(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), self.R))

    def test_e_1_order_is_seal_then_driver_then_records(self):
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, IMPLS, OTHERS))


if __name__ == "__main__":
    unittest.main()
