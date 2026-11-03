# -*- coding: utf-8 -*-
u"""F5(標準ラベルを見せない書き手 ― 20 社 × 形 1 × model 2 = 40 本)の測定の駆動 script と結果の門。封 docs/XBRL_AI_FORMS_F5_SEAL_2026-11-03.md §0-2 の 7。

前の便の門 ``test_xbrl_aiforms_result.py`` の部品(``record_problems`` など)と、p28 の門の部品(``doc_blocks``・``prose_problems``・``order_problems``・``Repo``)を読み込んで使う
(門としては走らせない。前の便の部品は module の入れ物を F5 の実体に差し替えて呼ぶ ― 差し替えが使う側の実体に届かないと黙って効かない)。縛るもの:

  a  差し替えの字: 共通の指示文が前の便と 1 行だけ違いその行が封の字・形の指示が F1 と同じ字(同じ object)・表の見出しが 4 欄・2 席目 8 本・前の便の累計が前の便の記録と一致・
     封 §2 の幅の数と §2-1 の数が駆動 script の定数と一致・前の便の script 4 本と記録 5 つが byte 不変(sha256 を字で留めた)。
  b  差し替えが届いている: RUN.GEN is GEN など同一 instance・形が F5 だけで 40 本・表の行の集合が前の便と同じで標準ラベルの列だけ無い・
     走らせる前の止めも呼ぶ前の止めも前の便の累計を含む(偽の transport。通信しない)。
  c  記録の中身: 前の便の ``record_problems`` を流用(禁止欄・会社名・key_leaks・cache の前後・script の sha256)+ F5 の検査(差し替えの欄・会社の列が前の便と同じ・前の便の folder の前後・
     標準ラベルが付いた行 0・指示文の sha256)。
  d  文書: 表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 e564683 ⊏ 駆動 script ⊑ 記録・文書・門 ⊑ HEAD。未 commit は赤(skip にしない)。
  g  変異: 使い捨ての小さい流れ(1 書類・2 model。偽の書き手と偽の席。通信しない)で記録 5 つを作り、同じ検査が緑 → 変異(記録の数・文書の 1 字・順序・定数の 1 字・差し替えの 1 つを外す)で赤。

記録が無いときは (c)(d)(e) の記録の試験を skip する。(a)(b)(g) は走る。この file は docID の字を持たない。
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


OLD = load_module("tests/measure/test_xbrl_aiforms_result.py", "aiforms_result_helpers_for_f5")      # 前の便の門の部品。門としては走らせない
PR = OLD.PR
F5 = load_module("measure/xbrl_aiforms_f5_2026-11-03.py", "aiforms_f5_driver_for_gate")
GEN, RUN, LAB, TAL = F5.GEN, F5.RUN, F5.LAB, F5.TAL

SEAL_REL = "docs/XBRL_AI_FORMS_F5_SEAL_2026-11-03.md"
DOC_REL = "docs/XBRL_AI_FORMS_F5_RESULT_2026-11-03.md"
DRIVER_REL = "measure/xbrl_aiforms_f5_2026-11-03.py"
SEAL_COMMIT_SHORT = "e564683"
REC_REL = collections.OrderedDict([
    ("gen", "fixtures/xbrl/aiforms/f5_gen_2026-11-03.json"), ("claims", "fixtures/xbrl/aiforms/f5_claims_2026-11-03.json"),
    ("labels", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json"), ("inject", "fixtures/xbrl/aiforms/f5_inject_2026-11-03.json"),
    ("tally", "fixtures/xbrl/aiforms/f5_tally_2026-11-03.json")])
#: 記録の ``この script の sha256`` が指す script(gen・claims・inject・labels は差し替える前の script 自身の path。tally だけ駆動 script が作る)
SCRIPT_REL = collections.OrderedDict([("gen", "measure/xbrl_aiforms_gen_2026-11-03.py"), ("run", "measure/xbrl_aiforms_run_2026-11-03.py"),
                                      ("labels", "measure/xbrl_aiforms_labels_2026-11-03.py"), ("f5", DRIVER_REL)])
REC_SCRIPT = {"gen": "gen", "claims": "run", "inject": "run", "labels": "labels", "tally": "f5"}
GATE_FILES = ("tests/measure/test_xbrl_aiforms_f5_result.py",)
#: 前の便の script 4 本と記録 5 つ(封 §0-2 の 7: byte を変えない。2026-11-03 の e564683 の木の sha256 を字で留めた)
FROZEN = collections.OrderedDict([
    ("measure/xbrl_aiforms_gen_2026-11-03.py", "9e47c1814d2c8d0504e62be0508061abe8b98473977b42ff6c16b999a283a848"),
    ("measure/xbrl_aiforms_labels_2026-11-03.py", "4776c68c5ec64748447c2df68ca9a1c8db8904d13184899999a67f59d2149a9e"),
    ("measure/xbrl_aiforms_run_2026-11-03.py", "40dc664c21afeea733a6337e93114cb004cef267787a57a87975bafe849fd13e"),
    ("measure/xbrl_aiforms_tally_2026-11-03.py", "48e659c9d976b1d31fed44a5e1bae5dec6cd446d5b688c45d623f2ffc73609d1"),
    ("fixtures/xbrl/aiforms/claims_2026-11-03.json", "445bb77ce2a4aaae02655bc0af86d2b207856cd6d14bf8e23dd4112ba70c707b"),
    ("fixtures/xbrl/aiforms/gen_2026-11-03.json", "6be9e252f36dfeea5c5babf8986067fea223c715ef1a3dd2e7aaed606faa4e83"),
    ("fixtures/xbrl/aiforms/inject_2026-11-03.json", "3b2536f356ad7c4b3f64b3cce1ffa848634443317f8845b408ba3192ef8cc493"),
    ("fixtures/xbrl/aiforms/labels_2026-11-03.json", "9c11559f6bd65690632f991074e59fd46ad6012d256bbb31a27abeb434433415"),
    ("fixtures/xbrl/aiforms/tally_2026-11-03.json", "3de09f0b8521dc58a412d633f592be2b66249518264c9b2b0d6bdda5a470527f")])
HIT, MISS, NOJ = TAL.HIT, TAL.MISS, TAL.NOJ
DOCID_RE = OLD.DOCID_RE
HAVE_CACHE = OLD.HAVE_CACHE
Patch = OLD.Patch


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    return OLD.sha256_rel(rel)


def records_exist(keys=None):
    return all(os.path.exists(os.path.join(ROOT, REC_REL[k])) for k in (keys or REC_REL))


def load_records():
    return collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())


# ---------------------------------------------------------------- 封の字(a)
def seal_pred_rows(seal):
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| \*\*(B-\d+)\*\* \| (.*) \|$", line)
        if m:
            out[m.group(1)] = m.group(2).split(u" | ")[0]
    return out


def seal_pins(seal):
    u"""封 §2 の幅の字 → 駆動 script の定数と同じかを見るための (名前, 封の値, script の値) の列。"""
    P = seal_pred_rows(seal)
    out = []

    def pair(txt, pat):
        return tuple(float(x) for x in re.search(pat, txt).groups())
    t = P["B-1"]
    out.append(("B-1 claim", int(re.search(r"数の claim が (\d+) 以上", t).group(1)), F5.B1_MIN_CLAIMS))
    out.append(("B-1 本数", int(re.search(r"(\d+) 本とも生成でき", t).group(1)), F5.B1_BOOKS))
    out.append(("B-1 費用", pair(t, r"費用 \*\*(\d+)〜(\d+) USD\*\*"), F5.B1_COST))
    t = P["B-2"]
    out.append(("B-2 幅", pair(t, r"\*\*(\d+)〜(\d+)\*\*"), F5.B2_RANGE))
    out.append(("B-2 倍", int(re.search(r"\*\*(\d+) 倍以上\*\*", t).group(1)), F5.B2_RATIO))
    t = P["B-3"]
    out.append(("B-3 行", pair(t, r"決まった行 \*\*(\d+)〜(\d+)\*\*"), F5.B3_DECIDED))
    out.append(("B-3 率", pair(t, r"決まった率 \*\*(\d+)〜(\d+)%\*\*"), F5.B3_RATE))
    t = P["B-5"]
    out.append(("B-5 偽", pair(t, r"\*\*(\d+(?:\.\d+)?)〜(\d+)%\*\*"), F5.B5_FALSE))
    out.append(("B-5 真", float(re.search(r"真 \*\*(\d+)% 以上\*\*", t).group(1)), F5.B5_TRUE_MIN))
    t = P["B-6"]
    out.append(("B-6 幅", pair(t, r"\*\*(\d+)〜(\d+)%\*\*"), F5.B6_RANGE))
    out.append(("B-6 差", float(re.search(r"\*\*\+(\d+(?:\.\d+)?) ポイント以上\*\*", t).group(1)), F5.B6_DIFF_MIN))
    out.append(("B-7", float(re.search(r"\*\*(\d+)% 以上\*\*", P["B-7"]).group(1)), F5.B7_MIN))
    t = P["B-8"]
    out.append(("B-8 通した", float(re.search(r"\*\*(\d+)% 以下\*\*", t).group(1)), F5.B8_PASS_MAX))
    out.append(("B-8 原本", float(re.search(r"P28E \*\*(\d+)% 以上\*\*", t).group(1)), F5.B8_P28E_ORIG_MIN))
    sec21 = seal[seal.index("### §2-1"):seal.index("## §3")]
    out.append(("§2-1 決まった行", int(re.search(r"B-3 の決まった行 ≥ (\d+)", sec21).group(1)), F5.R_KEEP_DECIDED_MIN))
    out.append(("§2-1 B-7", float(re.search(r"B-7 ≥ (\d+)%", sec21).group(1)), F5.B7_MIN))
    return out


def norm(v):
    return OLD.norm(v)


def line_diff(a, b):
    la, lb = a.split(u"\n"), b.split(u"\n")
    return [i for i, (x, y) in enumerate(zip(la, lb)) if x != y] if len(la) == len(lb) else None


def const_problems(seal):
    u"""差し替えの字・費用・封の幅の字が封の文書・前の便の記録と同じか。問題の列。"""
    out = []
    old_gen = OLD.GEN                                            # 前の便の gen を別に読んだ実体(差し替えていない)
    # 共通の指示文: 前の便と 1 行だけ違い、その行が封の字
    d = line_diff(old_gen.WRITER_COMMON, GEN.WRITER_COMMON)
    if d is None or len(d) != 1:
        out.append(u"共通の指示文が前の便と 1 行だけ違うのでない")
    else:
        a, b = old_gen.WRITER_COMMON.split(u"\n")[d[0]], GEN.WRITER_COMMON.split(u"\n")[d[0]]
        if a.replace(u"各行は、項目の要素名・標準ラベル(日本語名)・値・単位・期間です。", u"各行は、項目の要素名・値・単位・期間です。") != b or a == b:
            out.append(u"違う 1 行が封の置換の字(標準ラベルの 1 文を落とす)でない")
    for s in (u"各行は、項目の要素名・標準ラベル(日本語名)・値・単位・期間です。", u"各行は、項目の要素名・値・単位・期間です。"):
        if s not in seal:
            out.append(u"封に %r が無い" % s)
    if u"標準ラベル" in GEN.WRITER_COMMON:
        out.append(u"F5 の共通の指示文に標準ラベルの語がある")
    for bad in (u"検証", u"照合", u"機械が", u"正確", u"幻覚", u"ハルシネーション", u"間違い", u"誤り"):
        if bad in GEN.WRITER_COMMON:
            out.append(u"書き手の指示文に %r がある" % bad)
    for ph in (u"{FACTS}", u"{FORM}"):
        if GEN.WRITER_COMMON.count(ph) != 1:
            out.append(u"WRITER_COMMON に %s が 1 回でない" % ph)
    # 形の指示は F1 と同じ字(同じ object)
    if list(GEN.WRITER_FORMS) != ["F5"] or GEN.WRITER_FORMS["F5"] is not F5.F1_FORM_TEXT or GEN.WRITER_FORMS["F5"] != old_gen.WRITER_FORMS["F1"]:
        out.append(u"形 F5 の指示が F1 と同じ字(同じ object)でない")
    if GEN.FORMS != ("F5",) or TAL.FORMS != ("F5",):
        out.append(u"形が F5 だけでない")
    # 表の見出しが 4 欄
    if F5.F5_HEADER != u"| 項目(要素名) | 値 | 単位 | 期間 |" or F5.F5_HEADER.count(u"|") != 5 or F5.F5_HEADER not in seal:
        out.append(u"表の見出しが封の 4 欄でない")
    # 2 席目 8 本
    if GEN.SEAT2_N != 8 or F5.F5_SEAT2_N != 8 or u"**8 本**" not in seal:
        out.append(u"2 席目が 8 本でない")
    # 前の便の累計
    pg = jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")
    if F5.PREV_TOTAL_USD != pg[u"累計"][u"費用 USD 合計(記録の外を含む)"] or u"29.46516" not in seal or F5.PREV_TOTAL_USD != 29.46516:
        out.append(u"前の便の累計 PREV_TOTAL_USD が前の便の記録・封の字と違う")
    if GEN.outside_cost() != F5.PREV_TOTAL_USD or abs(sum(c[u"cost_usd"] for c in GEN.outside_calls()) - F5.PREV_TOTAL_USD) > 1e-9:
        out.append(u"記録の外の費用が前の便の累計だけになっていない")
    # 費用・model・max_tokens・再試行・札の席は前の便と同じ(import で参照 = 同じ object)
    if GEN.COST_CAP_USD != 50.0 or u"上限 50 USD" not in seal:
        out.append(u"上限が 50 USD でない")
    if (GEN.PRICE_IN, GEN.PRICE_OUT, GEN.MAX_TOKENS, GEN.MODELS, GEN.RETRY_WAITS) != (old_gen.PRICE_IN, old_gen.PRICE_OUT, old_gen.MAX_TOKENS, old_gen.MODELS, old_gen.RETRY_WAITS):
        out.append(u"単価・max_tokens・model・再試行が前の便と違う")
    if GEN.THINKING != old_gen.THINKING:
        out.append(u"thinking の指定が前の便と違う")
    if RUN.LABELLER_PROMPT_SHA256 != OLD.RUN.LABELLER_PROMPT_SHA256 or hashlib.sha256(RUN.LABELLER_PROMPT.encode("utf-8")).hexdigest() != RUN.LABELLER_PROMPT_SHA256:
        out.append(u"札付けの席の指示文が前の便と違う")
    if (RUN.INJECT_CAP, tuple(RUN.PROFILES), tuple(RUN.INJECT_TYPES)) != (10, ("P27", "P27E", "P28", "P28E"), ("T1_VALUE", "T8_REL")):
        out.append(u"注入の上限・型・profile が前の便と違う")
    # 会社・置き場所・封の名
    if (GEN.N_COMPANIES, GEN.MIN_CLAIMS) != (20, 60):
        out.append(u"会社の数・claim の下限が前の便と違う")
    if GEN.NEW_CACHE == OLD.GEN.NEW_CACHE or os.path.basename(GEN.NEW_CACHE) != "aiforms-f5-2026-11-03" or GEN.NEW_CACHE.startswith(OLD.GEN.NEW_CACHE + os.sep):
        out.append(u"置き場所が新しい folder(aiforms-f5-2026-11-03)でない")
    if u"aiforms-f5-2026-11-03" not in seal:
        out.append(u"封に新しい folder の名が無い")
    if (GEN.SEAL_REL, RUN.SEAL_REL, GEN.SEAL_COMMIT, RUN.SEAL_COMMIT) != (SEAL_REL, SEAL_REL, SEAL_COMMIT_SHORT, SEAL_COMMIT_SHORT):
        out.append(u"封の名か commit が F5 の封でない")
    for obj, name, want in ((GEN, "GEN_REL", REC_REL["gen"]), (RUN, "CLAIMS_REL", REC_REL["claims"]), (RUN, "INJECT_REL", REC_REL["inject"]),
                            (LAB, "LABELS_REL", REC_REL["labels"]), (TAL, "TALLY_REL", REC_REL["tally"])):
        if getattr(obj, name) != want:
            out.append(u"%s が F5 の記録の path でない" % name)
    if dict(TAL.REC_REL) != dict((k, REC_REL[k]) for k in ("gen", "claims", "labels", "inject")):
        out.append(u"TAL.REC_REL が F5 の記録でない")
    # 差し替えの届き方
    out += [u"差し替え: " + x for x in F5.wiring_problems()]
    # 封の幅 = script の定数
    for name, seal_v, script_v in seal_pins(seal):
        if norm(seal_v) != norm(script_v):
            out.append(u"%s: 封の字 %r と駆動 script の定数 %r が違う" % (name, seal_v, script_v))
    if list(seal_pred_rows(seal)) != [u"B-%d" % i for i in range(1, 10)]:
        out.append(u"封 §2 の予測の行が B-1〜B-9 でない")
    if F5.KEEP != u"据え置く" or F5.REVERT != u"P27E に戻す" or F5.ASK_HUMAN != u"人間に判断を戻す":
        out.append(u"§2-1 の推奨の語が封と違う")
    for w in (F5.KEEP, F5.REVERT, F5.ASK_HUMAN):
        if w not in seal:
            out.append(u"封 §2-1 に %r が無い" % w)
    # 前の便の script 4 本・記録 5 つは byte 不変
    for rel, sha in FROZEN.items():
        if sha256_rel(rel) != sha:
            out.append(u"前の便の file が変わった: %s" % rel)
    return out


# ---------------------------------------------------------------- 記録(c)
class AsF5(object):
    u"""前の便の門の部品(OLD)を、F5 の実体・F5 の path・F5 の検査で呼ぶための入れ物。出れば戻す。"""

    def __enter__(self):
        self.p = Patch()
        for name, val in (("GEN", GEN), ("RUN", RUN), ("LAB", LAB), ("TAL", TAL), ("SEAL_REL", SEAL_REL), ("SEAL_COMMIT_SHORT", SEAL_COMMIT_SHORT),
                          ("REC_REL", REC_REL), ("SCRIPT_REL", SCRIPT_REL), ("REC_SCRIPT", REC_SCRIPT), ("tally_problems", tally_problems)):
            self.p.set(OLD, name, val)
        return self

    def __exit__(self, *a):
        self.p.undo()
        return False


def tally_problems(R, scripts, check_input_sha=False):
    out = []
    T = R["tally"]
    if check_input_sha:
        for k, rel in TAL.REC_REL.items():
            if T[u"入力の記録の sha256"].get(k) != sha256_rel(rel):
                out.append(u"tally: 入力の記録 %s の sha256 が現物と違う" % k)
        if T[u"前の便の記録の sha256"] != {"gen": FROZEN["fixtures/xbrl/aiforms/gen_2026-11-03.json"], "tally": FROZEN["fixtures/xbrl/aiforms/tally_2026-11-03.json"]}:
            out.append(u"tally: 前の便の記録の sha256 が留めた値と違う")
    try:
        built = F5.build_f5(R)
        J = F5.judge_f5(built, jload("fixtures/xbrl/aiforms/tally_2026-11-03.json"))
    except Exception as e:                           # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"tally: 記録から集計を作れない(%s)" % type(e).__name__]
    if json.loads(json.dumps(built)) != T[u"集計"]:
        out.append(u"tally: 集計が記録から作り直した値と違う")
    if json.loads(json.dumps(J)) != T[u"予測の判定"]:
        out.append(u"tally: 予測の判定が記録から作り直した判定と違う")
    c = collections.Counter(v[u"判定"] for v in J.values())
    if (T[u"当たり"], T[u"外れ"], T[u"判定しない"]) != (c.get(HIT, 0), c.get(MISS, 0), c.get(NOJ, 0)):
        out.append(u"tally: 当たり・外れの数が判定と違う")
    if T.get(u"封 §2-1 の推奨") != F5.recommendation(J):
        out.append(u"tally: 封 §2-1 の推奨が判定から作り直した値と違う")
    return out


def swap_problems(R):
    u"""全部の記録の ``差し替え`` の欄と step が、いまの駆動 script・指示文・前の便の gen script から作り直した値と同じか。"""
    out = []
    want = json.loads(json.dumps(F5.swap_field()))
    for k, rec in R.items():
        if rec.get(u"差し替え") != want:
            out.append(u"%s: 差し替えの欄が駆動 script から作り直した値と違う" % k)
        if u"F5" not in rec.get(u"step", u"") or u"4 × model 2" in rec.get(u"step", u""):
            out.append(u"%s: step の字が F5 でない" % k)
    return out


def f5_extra_problems(R, full, root=ROOT):
    out = swap_problems(R)
    pg = jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")
    prev_docs = pg[u"会社の選び"][u"docID"]
    gen = R.get("gen")
    if gen is not None:
        docs = gen[u"会社の選び"][u"docID"]
        if not set(docs) <= set(prev_docs) or (full and docs != prev_docs):
            out.append(u"gen: 会社の列が前の便の 会社の選び.docID と違う")
        if any(c[u"form"] != "F5" for c in gen[u"呼び出し"]):
            out.append(u"gen: F5 でない形の呼び出しがある")
        if gen[u"累計"][u"記録の外の費用 USD"] != F5.PREV_TOTAL_USD or gen[u"記録の外の呼び出し"] != json.loads(json.dumps(F5.outside_calls_f5())):
            out.append(u"gen: 前の便の累計が記録の外の欄に入っていない")
        if gen[u"累計"][u"費用 USD 合計(記録の外を含む)"] < F5.PREV_TOTAL_USD:
            out.append(u"gen: 累計(前の便を含む)が前の便の累計より小さい")
        ish = gen[u"指示文の sha256"]
        sw = json.loads(json.dumps(F5.swap_shas()))
        if ish[u"WRITER_COMMON"] != sw[u"WRITER_COMMON_F5"] or ish[u"WRITER_FORMS"] != sw[u"WRITER_FORMS"] or ish[u"WRITER_FORMS"].get("F5") != pg[u"指示文の sha256"][u"WRITER_FORMS"]["F1"] or ish[u"WRITER_COMMON"] == pg[u"指示文の sha256"][u"WRITER_COMMON"]:
            out.append(u"gen: 指示文の sha256 が F5 の差し替えと(F1 と同じ形の字・違う共通の指示文で)合わない")
        for d, t in gen[u"fact の表"].items():
            if t[u"標準ラベルが付いた行"] != 0:
                out.append(u"gen: 標準ラベルが付いた行が 0 でない")
            pt = pg[u"fact の表"].get(d)
            if pt is None or pt[u"fact の数(素の context)"] != t[u"fact の数(素の context)"] or pt[u"instance の fact の数"] != t[u"instance の fact の数"]:
                out.append(u"gen: 表の行数が前の便の同じ書類の表の行数と違う")
        if HAVE_CACHE:
            try:
                for d in gen[u"会社の選び"][u"docID"]:
                    row = {u"標本": gen[u"会社の選び"][u"標本"][d], "docID": d, u"zip の sha256": gen[u"会社の選び"][u"zip の sha256"][d]}
                    table = GEN.build_facts_table(GEN.read_zip(row))[0]
                    if GEN.sha256_text(table) != gen[u"fact の表"][d][u"表の sha256"]:
                        out.append(u"gen: 表の sha256 が作り直した 4 欄の表と違う")
            except Exception as e:                   # noqa: BLE001
                out.append(u"gen: 表を作り直せない(%s)" % type(e).__name__)
        cb = gen[u"cache の前後"]
        if cb[u"後"] is not None and (OLD_PREV not in cb[u"前"] or OLD_PREV not in cb[u"後"]):
            out.append(u"gen: cache の前後に前の便の folder が無い")
    for k in ("claims", "inject"):
        if R.get(k) is not None and (OLD_PREV not in R[k][u"cache の前後"][u"前"] or OLD_PREV not in R[k][u"cache の前後"][u"後"]):
            out.append(u"%s: cache の前後に前の便の folder が無い" % k)
    if full and os.path.isdir(F5.PREV_CACHE):
        live = GEN.names_snapshot(F5.PREV_CACHE)
        for k in ("gen", "claims", "inject"):
            if R.get(k) is not None and R[k][u"cache の前後"][u"前"].get(OLD_PREV) != live:
                out.append(u"%s: 前の便の folder の件数か名前が記録の前と違う" % k)
    return out


OLD_PREV = F5.PREV_CACHE_NAME


def record_problems(R, full=True, root=ROOT):
    with AsF5():
        out = OLD.record_problems(R, full=full, root=root)
    return out + f5_extra_problems(R, full, root)


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R):
    J = F5.judge_f5(F5.build_f5(R), jload("fixtures/xbrl/aiforms/tally_2026-11-03.json"))
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != F5.render_table(J).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if "reco" in got and got["reco"] != [F5.render_reco(J)]:
        out.append(u"表 reco が記録から作り直した推奨の行と違う")
    for k in got:
        if k not in ("pred", "reco"):
            out.append(u"知らない表 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"docID が文書にある")
    for w in OLD.FOR_RESULT_WORDS:
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


# ---------------------------------------------------------------- 順序(e)
def order_of(root, impl=None, others=None):
    impl = [DRIVER_REL] if impl is None else impl
    others = (list(REC_REL.values()) + [DOC_REL] + list(GATE_FILES)) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, impl, others)


# ================================================================ 偽の書き手・偽の transport
_LM = []


def label_map():
    if not _LM:
        from adapters.xbrl import instance as I
        _LM.append(I.taxonomy_label_map(None))
    return _LM[0]


def fake_body(prompt, tin=None, tout=None, stop="end_turn"):
    u"""偽の書き手。4 欄の表の要素名から日本語名を自分で引いて文を書く(本物の AI は標準名を知っている)。値の違う行だけ使う(同じ値だと注入の土台が作れない)。"""
    rows = []
    for ln in prompt.split("\n"):
        if ln.startswith("| ") and "JPY" in ln and "時点" not in ln:
            c = [x.strip() for x in ln.strip("|").split("|")]
            lab = label_map().get(c[0].split(":")[-1]) if len(c) == 4 else None
            if lab:
                rows.append((lab, float(c[1])))
    seen, uniq = set(), []
    for lab, v in rows:
        r = round(v / 1e6)
        if r not in seen and r > 0:
            seen.add(r)
            uniq.append((lab, v))
    text = u"\n".join([u"経営成績"] + [u"%s は %s 百万円でした。" % (lab, format(round(v / 1e6), ",")) for lab, v in uniq[:24]])
    return json.dumps({"content": [{"type": "text", "text": text}],
                       "usage": {"input_tokens": len(prompt) if tin is None else tin, "output_tokens": len(text) if tout is None else tout},
                       "stop_reason": stop}).encode("utf-8")


def fake_transport_factory(calls, scripted=None, tin=None, tout=None):
    scripted = list(scripted or [])

    def transport(prompt, model, key):
        calls.append((model, len(prompt)))
        if scripted:
            return scripted.pop(0)
        return 200, fake_body(prompt, tin, tout)
    return transport


def jload_abs(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def write_abs(p, obj):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


# ================================================================ (a)
class ConstantsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_constants_agree_with_the_seal_and_the_previous_run(self):
        self.assertEqual([], const_problems(self.seal))

    def test_a_2_the_common_text_differs_from_the_previous_by_one_line_only(self):
        a, b = OLD.GEN.WRITER_COMMON.split(u"\n"), GEN.WRITER_COMMON.split(u"\n")
        self.assertEqual(len(a), len(b))
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual(1, len(diff))
        self.assertIn(u"標準ラベル(日本語名)・", a[diff[0]])
        self.assertNotIn(u"標準ラベル", b[diff[0]])
        self.assertEqual(GEN.WRITER_COMMON, F5.common_f5())
        # 置換の対象が無い / 2 つある / 違う行が 2 行になる前の便の字では、駆動 script 自身が止まる
        with self.assertRaises(AssertionError):
            F5.common_f5(OLD.GEN.WRITER_COMMON.replace(F5.COMMON_OLD, u"別の文です。"))
        with self.assertRaises(AssertionError):
            F5.common_f5(OLD.GEN.WRITER_COMMON + u"\n" + F5.COMMON_OLD)
        # 置換の対象が 1 つでも、行をまたいで行数が変わる置換なら『違う行が 1 行だけ』の確かめで止まる
        p = Patch()
        try:
            p.set(F5, "COMMON_OLD", u"担当しています。\n\n以下は")
            self.assertEqual(1, OLD.GEN.WRITER_COMMON.count(F5.COMMON_OLD))
            with self.assertRaises(AssertionError):
                F5.common_f5()
        finally:
            p.undo()

    def test_a_3_the_form_text_is_the_F1_text_itself(self):
        self.assertIs(GEN.WRITER_FORMS["F5"], F5.F1_FORM_TEXT)
        self.assertEqual(OLD.GEN.WRITER_FORMS["F1"], F5.F1_FORM_TEXT)
        self.assertEqual(["F5"], list(GEN.WRITER_FORMS))

    def test_a_4_a_changed_constant_or_seal_character_turns_it_red(self):
        p = Patch()
        try:
            for mod, name, val in ((GEN, "SEAT2_N", 7), (F5, "PREV_TOTAL_USD", 29.46517), (GEN, "COST_CAP_USD", 51.0), (GEN, "PRICE_OUT", 24.0), (GEN, "MAX_TOKENS", 4001),
                                    (GEN, "MODELS", ("claude-sonnet-5-5",)), (F5, "F5_HEADER", u"| 項目(要素名) | 標準ラベル | 値 | 単位 | 期間 |"),
                                    (F5, "B3_DECIDED", (5, 61)), (F5, "B6_DIFF_MIN", 0.4), (F5, "B2_RATIO", 3), (F5, "B8_PASS_MAX", 4.0), (F5, "B1_COST", (4.0, 11.0)),
                                    (F5, "B5_FALSE", (3.6, 10.0)), (F5, "B7_MIN", 81.0), (F5, "R_KEEP_DECIDED_MIN", 6), (F5, "B3_RATE", (25.0, 71.0)),
                                    (F5, "B1_MIN_CLAIMS", 11), (F5, "B6_RANGE", (55.0, 76.0)), (F5, "B8_P28E_ORIG_MIN", 61.0),
                                    (GEN, "WRITER_COMMON", GEN.WRITER_COMMON.replace(u"レポートだけ", u"後で機械が検証するのでレポートだけ")),
                                    (GEN, "WRITER_FORMS", collections.OrderedDict([("F5", F5.F1_FORM_TEXT + u"。")])),
                                    (GEN, "NEW_CACHE", OLD.GEN.NEW_CACHE), (GEN, "FORMS", ("F1", "F5")), (GEN, "SEAL_COMMIT", "0b43a03"),
                                    (GEN, "outside_calls", OLD.GEN.outside_calls), (GEN, "outside_cost", OLD.GEN.outside_cost),
                                    (RUN, "CLAIMS_REL", "fixtures/xbrl/aiforms/claims_2026-11-03.json"), (TAL, "TALLY_REL", "x"),
                                    (F5, "KEEP", u"据え置き")):
                p.set(mod, name, val)
                self.assertNotEqual([], const_problems(self.seal), name)
                p.undo()
        finally:
            p.undo()
        for old, new in ((u"**8 本**", u"**9 本**"), (u"29.46516", u"29.46517"), (u"費用 **4〜10 USD**", u"費用 **4〜11 USD**"), (u"**2 倍以上**", u"**3 倍以上**"),
                         (u"決まった行 **5〜60**", u"決まった行 **5〜61**"), (u"**+0.3 ポイント以上**", u"**+0.4 ポイント以上**"), (u"B-3 の決まった行 ≥ 5", u"B-3 の決まった行 ≥ 6"),
                         (u"**3.5〜10%**", u"**3.6〜10%**"), (u"P28E **60% 以上**", u"P28E **61% 以上**"), (u"各行は、項目の要素名・値・単位・期間です。", u"各行は、項目の値・単位・期間です。")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], const_problems(self.seal.replace(old, new)), old)

    def test_a_5_previous_files_are_byte_identical(self):
        for rel, sha in FROZEN.items():
            self.assertEqual(sha, sha256_rel(rel), rel)
        p = Patch()
        try:
            p.set(sys.modules[__name__], "FROZEN", collections.OrderedDict(list(FROZEN.items())[:-1] + [("fixtures/xbrl/aiforms/tally_2026-11-03.json", "0" * 64)]))
            self.assertNotEqual([], const_problems(self.seal))
        finally:
            p.undo()

    def test_a_7_the_swap_field_says_what_was_swapped(self):
        f = F5.swap_field()
        self.assertEqual([u"差し替えた名前", u"指示文の sha256", u"前の便の gen script の sha256", u"駆動 script の sha256", u"前の便の累計 USD"], list(f))
        names = f[u"差し替えた名前"]
        self.assertEqual(len(names), len(set(names)))
        for m, a, _v in list(F5.SWAP_TABLE) + list(F5.SHARE_TABLE):
            self.assertIn(u"%s.%s" % (m, a), names)
        for n in (u"GEN.EXISTING_CACHES", u"GEN.new_record", u"RUN.header", u"TAL.REC_REL", u"GEN.FORMS", u"GEN.WRITER_COMMON", u"GEN.WRITER_FORMS", u"GEN.build_facts_table",
                  u"GEN.SEAT2_N", u"GEN.outside_cost", u"GEN.NEW_CACHE", u"GEN.GEN_REL", u"RUN.GEN", u"LAB.GEN", u"TAL.GEN", u"TAL.FORMS", u"GEN.key_leaks"):
            self.assertIn(n, names)
        self.assertEqual({u"WRITER_COMMON_F5": hashlib.sha256(GEN.WRITER_COMMON.encode("utf-8")).hexdigest(),
                          u"WRITER_FORMS": {"F5": hashlib.sha256(OLD.GEN.WRITER_FORMS["F1"].encode("utf-8")).hexdigest()}}, json.loads(json.dumps(f[u"指示文の sha256"])))
        self.assertEqual(FROZEN["measure/xbrl_aiforms_gen_2026-11-03.py"], f[u"前の便の gen script の sha256"])
        self.assertEqual(sha256_rel(DRIVER_REL), f[u"駆動 script の sha256"])
        self.assertEqual(29.46516, f[u"前の便の累計 USD"])
        self.assertIn(u"F5", F5.restep(u"AI の形 4 × model 2 ― x"))
        with self.assertRaises(AssertionError):
            F5.restep(u"別の step")

    def test_a_6_seal_says_each_prediction_row_once(self):
        self.assertEqual([u"B-%d" % i for i in range(1, 10)], list(seal_pred_rows(self.seal)))


# ================================================================ (b)
class WiringTest(unittest.TestCase):
    def test_b_1_every_user_sees_the_same_gen_instance(self):
        self.assertEqual([], F5.wiring_problems())
        self.assertIs(RUN.GEN, GEN)
        self.assertIs(LAB.GEN, GEN)
        self.assertIs(LAB.RUN, RUN)
        self.assertIs(TAL.GEN, GEN)
        self.assertIs(TAL.RUN, RUN)
        self.assertIs(TAL.LAB, LAB)
        for m in (RUN, LAB, TAL):
            self.assertIs(GEN.Stop, m.Stop)
        self.assertEqual(("F5",), TAL.FORMS)
        self.assertEqual(OLD.GEN.EXISTING_CACHES.keys() | {OLD_PREV}, GEN.EXISTING_CACHES.keys())

    def test_b_2_removing_one_swap_turns_the_wiring_check_red(self):
        p = Patch()
        try:
            for mod, name, val in ((RUN, "GEN", OLD.GEN), (LAB, "GEN", OLD.GEN), (LAB, "RUN", OLD.RUN), (TAL, "GEN", OLD.GEN), (TAL, "RUN", OLD.RUN), (TAL, "LAB", OLD.LAB),
                                    (GEN, "FORMS", OLD.GEN.FORMS), (GEN, "SEAT2_N", 32),
                                    (GEN, "WRITER_FORMS", collections.OrderedDict([("F5", u"".join(list(F5.F1_FORM_TEXT)))])), (GEN, "NEW_CACHE", OLD.GEN.NEW_CACHE), (GEN, "GEN_REL", OLD.GEN.GEN_REL),
                                    (GEN, "build_facts_table", OLD.GEN.build_facts_table), (GEN, "WRITER_COMMON", OLD.GEN.WRITER_COMMON), (GEN, "WRITER_FORMS", OLD.GEN.WRITER_FORMS),
                                    (GEN, "outside_cost", OLD.GEN.outside_cost), (GEN, "outside_calls", OLD.GEN.outside_calls), (GEN, "select_companies", OLD.GEN.select_companies),
                                    (GEN, "new_record", OLD.GEN.new_record), (GEN, "key_leaks", OLD.GEN.key_leaks), (RUN, "header", OLD.RUN.header), (RUN, "CLAIMS_REL", OLD.RUN.CLAIMS_REL), (RUN, "INJECT_REL", OLD.RUN.INJECT_REL),
                                    (RUN, "SEAL_REL", OLD.RUN.SEAL_REL), (LAB, "LABELS_REL", OLD.LAB.LABELS_REL), (TAL, "TALLY_REL", OLD.TAL.TALLY_REL), (TAL, "REC_REL", OLD.TAL.REC_REL),
                                    (GEN, "EXISTING_CACHES", OLD.GEN.EXISTING_CACHES), (GEN, "SEAL_COMMIT", OLD.GEN.SEAL_COMMIT)):
                p.set(mod, name, val)
                self.assertNotEqual([], F5.wiring_problems(), name)
                p.undo()
        finally:
            p.undo()
        self.assertEqual([], F5.wiring_problems())

    def test_b_3_a_driver_command_refuses_to_run_when_a_swap_is_missing(self):
        tmp = tempfile.mkdtemp(prefix="aiforms_f5_refuse_", dir=os.environ.get("TMPDIR"))
        cache = os.path.join(tmp, "cache")                       # 止まらなかった変異の世界でも、本物の置き場(~/.cache)には書かない
        try:
            p = Patch()
            try:
                p.set(RUN, "GEN", OLD.GEN)
                with self.assertRaises(GEN.Stop):
                    F5.run_tally(root=ROOT, out=os.path.join(tmp, "tally.json"))
                with self.assertRaises(GEN.Stop):
                    F5.run_labels(root=ROOT, out=os.path.join(tmp, "labels.json"))
                with self.assertRaises(GEN.Stop):
                    F5.run_gen(root=ROOT, dry_run=True, new_cache=cache, out=os.path.join(tmp, "gen.json"), say=lambda *a: None)
            finally:
                p.undo()
            # 前の便の累計の字が前の便の記録と違えば、gen は 1 回も呼ばず止まる(通信しない・鍵を読まない)
            p = Patch()
            try:
                p.set(F5, "PREV_TOTAL_USD", 29.4)
                with self.assertRaises(GEN.Stop):
                    F5.run_gen(root=ROOT, dry_run=True, new_cache=cache, out=os.path.join(tmp, "gen.json"), say=lambda *a: None)
            finally:
                p.undo()
            self.assertFalse(os.path.exists(cache))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_b_4_the_previous_total_matches_the_previous_record_and_the_company_list_is_checked(self):
        self.assertEqual([], F5.prev_problems(ROOT))
        p = Patch()
        try:
            p.set(F5, "PREV_TOTAL_USD", 29.4)
            self.assertNotEqual([], F5.prev_problems(ROOT))
        finally:
            p.undo()

    def test_b_4b_the_key_check_ignores_only_the_seal_path(self):
        self.assertEqual([], GEN.key_leaks(u'{"seal": "%s"}' % SEAL_REL))                                        # 32 字続く封の path だけは通る
        self.assertNotEqual([], OLD.GEN.key_leaks(u'{"seal": "%s"}' % SEAL_REL))                                  # 前の便の検査のままだと当たる(差し替えの訳)
        for bad in (u"x" * 32, u"abc" + SEAL_REL + u"def_ghijklmnopqrstuvwxyz0123456789", u"sk-" + u"a" * 12, u"Bearer " + u"a" * 20, u"x-api-key"):
            self.assertNotEqual([], GEN.key_leaks(bad), bad)
        self.assertNotEqual([], GEN.key_leaks(u"SECRET-VALUE-123", u"SECRET-VALUE-123"))
        self.assertIs(GEN.key_leaks, F5.key_leaks_f5)
        p = Patch()
        try:
            p.set(GEN, "key_leaks", OLD.GEN.key_leaks)
            self.assertNotEqual([], F5.wiring_problems())
        finally:
            p.undo()

    def test_b_5_the_tables_have_four_columns(self):
        t = u"| 項目(要素名) | 標準ラベル | 値 | 単位 | 期間 |\n|---|---|---|---|---|\n| jppfs_cor:NetSales | 売上高 | 100 | JPY | 2025-04-01〜2026-03-31 |\n" \
            u"| jppfs_cor:Cash | 現金 | と | 預金 | 1 | JPY | 2026-03-31 時点 |"
        got = F5.drop_label_column(t).split(u"\n")
        self.assertEqual([F5.F5_HEADER, F5.F5_RULE, u"| jppfs_cor:NetSales | 100 | JPY | 2025-04-01〜2026-03-31 |", u"| jppfs_cor:Cash | 1 | JPY | 2026-03-31 時点 |"], got)

    @unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
    def test_b_6_prepare_gives_one_form_forty_jobs_and_the_same_rows_as_the_previous_table(self):
        tmp = tempfile.mkdtemp(prefix="aiforms_f5_prep_", dir=os.environ.get("TMPDIR"))
        try:
            chosen, counts, _sm, tables, prompts, est = GEN.prepare(ROOT, GEN.EXISTING_CACHES, os.path.join(tmp, "cache"), lambda *a: None)
            docs = [r["docID"] for r in chosen]
            self.assertEqual(20, len(docs))
            jobs = GEN.jobs(docs)
            self.assertEqual(40, len(jobs))
            self.assertEqual(set(["F5"]), set(f for _d, f, _m in jobs))
            self.assertEqual(set(["F5"]), set(f for _d, f in prompts))
            self.assertTrue(all(t[u"標準ラベルが付いた行"] == 0 for t in tables.values()))
            self.assertEqual(est, sum(GEN.estimate_usd(len(p)) for p in prompts.values()) * 2)
            for (d, f), pr in prompts.items():
                self.assertIn(F5.F5_HEADER, pr)
                self.assertNotIn(u"標準ラベル", pr.split(F5.F5_HEADER)[0])
                self.assertIn(F5.F1_FORM_TEXT, pr)
                self.assertNotIn(u"{FACTS}", pr)
            # 同じ書類で前の便の表と行の集合・並び・値・単位・期間が同じ(標準ラベルの列だけ無い)。全 20 社
            for r in chosen:
                zb = GEN.read_zip(r)
                old_t, old_used, old_total, old_lab = OLD.GEN.build_facts_table(zb)
                new_t, used, total, lab = GEN.build_facts_table(zb)
                self.assertEqual((old_used, old_total), (used, total))
                self.assertEqual(0, lab)
                self.assertGreater(old_lab, 0)
                ol, nl = old_t.split(u"\n"), new_t.split(u"\n")
                self.assertEqual(len(ol), len(nl))
                self.assertEqual(used + 2, len(nl))
                self.assertEqual(F5.F5_HEADER, nl[0])
                for a, b in zip(ol[2:], nl[2:]):
                    parts = a.split(u" | ")
                    self.assertEqual(u" | ".join([parts[0]] + parts[2:]), b)
                self.assertTrue(all(l.count(u" | ") == 3 for l in nl[2:]))
                self.assertEqual(sorted(l.split(u" | ")[0] for l in nl[2:]), [l.split(u" | ")[0] for l in nl[2:]])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class CostStopTest(unittest.TestCase):
    u"""走らせる前の止めも呼ぶ前の止めも前の便の累計を含む(偽の transport。通信しない)。"""

    @classmethod
    def setUpClass(cls):
        seed, cls.seed_meta = GEN.seed_value(ROOT)
        cls.chosen, cls.counts = GEN.select_companies(ROOT, seed)       # F5 の選び(前の便の列と同じか確かめる関数を通る)
        cls.one = cls.chosen[:1]
        cls.doc = cls.one[0]["docID"]

    def setUp(self):
        self.p = Patch()
        self.p.set(GEN, "select_companies", lambda root, seed=None: (self.one, self.counts))        # 1 社(2 本)に絞る。会社の列の検査は test_b_7 が本物の関数で見る
        self.tmp = tempfile.mkdtemp(prefix="aiforms_f5_cost_", dir=os.environ.get("TMPDIR"))
        self.out = os.path.join(self.tmp, "gen.json")
        self.cache = os.path.join(self.tmp, "cache")
        os.environ.pop(GEN.KEY_ENV, None)

    def tearDown(self):
        self.p.undo()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop(GEN.KEY_ENV, None)

    def go(self, transport, dry_run=False, key="SECRETKEY-aaaaaaaaaaaaaaaaaaaa"):
        os.environ[GEN.KEY_ENV] = key
        return GEN.run(root=ROOT, dry_run=dry_run, only=None if dry_run else self.doc, out=self.out, new_cache=self.cache, key_value=key,
                       transport=transport, sleep=lambda s: None, say=lambda *a: None)

    def test_b_7_the_company_list_must_equal_the_previous_runs(self):
        seed, _m = GEN.seed_value(ROOT)
        p = Patch()
        try:
            p.set(F5, "prev_gen", lambda root=ROOT: {u"会社の選び": {u"docID": list(reversed([r["docID"] for r in self.chosen]))}})
            with self.assertRaises(GEN.Stop):
                F5.select_companies_f5(ROOT, seed)
        finally:
            p.undo()
        chosen, _c = F5.select_companies_f5(ROOT, seed)
        self.assertEqual(jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"], [r["docID"] for r in chosen])

    def test_b_8_dry_run_calls_nothing_and_counts_two_books_per_company(self):
        calls = []
        r = self.go(fake_transport_factory(calls), dry_run=True)
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(2, r["jobs"])

    def test_b_8b_the_driver_dry_run_over_the_real_twenty_calls_nothing(self):
        self.p.undo()                                                                   # 本物の選び(20 社 × 2 = 40 本)
        calls = []
        os.environ.pop(GEN.KEY_ENV, None)
        r = F5.run_gen(root=ROOT, dry_run=True, out=self.out, new_cache=self.cache, say=lambda *a: None)
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(40, r["jobs"])
        self.assertEqual(20, len(r["docs"]))
        self.assertEqual(jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"], r["docs"])
        self.assertLess(F5.PREV_TOTAL_USD + r["est_usd"], GEN.COST_CAP_USD)           # 封の見積り: 前の便の累計 + 40 本の見積りは上限の内
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "texts")))

    def test_b_9_the_plan_stop_includes_the_previous_total(self):
        calls = []
        self.p.set(GEN, "COST_CAP_USD", F5.PREV_TOTAL_USD + 0.05)          # F5 の見積り(2 本で約 0.5)を足すと上限を超えるが、F5 だけなら入る
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls))
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        # 前の便の累計を入れない版(変異)なら止まらず呼ぶ = この試験は前の便の累計で赤になる
        self.tearDown()
        self.setUp()
        self.p.set(GEN, "COST_CAP_USD", F5.PREV_TOTAL_USD + 0.05)
        self.p.set(GEN, "outside_cost", lambda: 0.0)
        self.p.set(GEN, "outside_calls", lambda: [])
        calls2 = []
        self.go(fake_transport_factory(calls2))
        self.assertEqual(2, len(calls2))

    def test_b_10_the_call_stop_includes_the_previous_total(self):
        calls = []
        self.p.set(GEN, "COST_CAP_USD", F5.PREV_TOTAL_USD + 3.5)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls, tin=0, tout=160000))          # 1 回 4 USD
        self.assertEqual(1, len(calls))                                            # 1 回目は入る。2 回目の前に(前の便の累計 + 4 + 見積り)が上限を超えて止まる
        rec = jload_abs(self.out)
        self.assertEqual(1, rec[u"累計"][u"呼び出しの数"])
        self.assertTrue(rec[u"止めた理由"].startswith(TAL.CAP_STOP_STARTS))
        self.assertAlmostEqual(F5.PREV_TOTAL_USD + 4.0, rec[u"累計"][u"費用 USD 合計(記録の外を含む)"], places=4)
        self.assertEqual(4.0, rec[u"累計"][u"費用 USD"])
        # 前の便の累計を入れない版(変異)なら 2 回目も呼ぶ
        self.tearDown()
        self.setUp()
        self.p.set(GEN, "COST_CAP_USD", F5.PREV_TOTAL_USD + 3.5)
        self.p.set(GEN, "outside_cost", lambda: 0.0)
        self.p.set(GEN, "outside_calls", lambda: [])
        calls2 = []
        self.go(fake_transport_factory(calls2, tin=0, tout=160000))
        self.assertEqual(2, len(calls2))

    def test_b_11_the_first_record_carries_the_swap_field_and_the_previous_total(self):
        calls = []
        self.go(fake_transport_factory(calls))
        rec = jload_abs(self.out)
        self.assertEqual(json.loads(json.dumps(F5.swap_field())), rec[u"差し替え"])
        self.assertEqual(SEAL_REL, rec["seal"])
        self.assertEqual(SEAL_COMMIT_SHORT, rec[u"封の commit"])
        self.assertIn(u"F5", rec[u"step"])
        self.assertEqual(F5.PREV_TOTAL_USD, rec[u"累計"][u"記録の外の費用 USD"])
        self.assertEqual(sorted(["F5"]), sorted(set(c["form"] for c in rec[u"呼び出し"])))
        self.assertIn(OLD_PREV, rec[u"cache の前後"][u"前"])
        self.assertEqual(rec[u"cache の前後"][u"前"], rec[u"cache の前後"][u"後"])
        self.assertTrue(os.path.isfile(os.path.join(self.cache, "texts", GEN.text_key(self.doc, "F5", "claude-sonnet-5-5") + ".txt")))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "texts", GEN.text_key(self.doc, "F1", "claude-sonnet-5-5") + ".txt")))


class SecF5Test(unittest.TestCase):
    u"""B-7・B-9 の追加の集計 ``sec_f5`` を、手で作った行で直接見る(smoke の集計は同じ関数を通すだけで循環する)。"""

    @staticmethod
    def row(doc, writer, o, label, state="GROUNDED"):
        return {u"docID": doc, u"writer": writer, "P28E": {"state": state, u"other_subject_2026_11_02": o}, u"label": label}

    def test_s_1_counts_decided_labelled_true_and_holds(self):
        rows = [self.row("A", "W1", [False, 1, True], (u"真", None, u"高", [])),
                self.row("A", "W2", [False, 1, True], (u"偽", u"計算の誤り", u"中", [])),
                self.row("B", "W1", [False, 2, False], (u"真", None, u"高", []), "UNVERIFIABLE"),
                self.row("B", "W2", [False, 0, False], (u"判定不能", None, u"低", [])),
                self.row("B", "W1", None, (u"真", None, u"高", [])),
                self.row("C", "W1", [False, 1, True], (u"真", None, u"高", [])),
                self.row("C", "W2", [False, 1, True], None)]
        X = F5.sec_f5(rows)
        self.assertEqual((6, 4, 3), (X[u"O の形の行"], X[u"決まった行"], X[u"決まった行のうち札のある行"]))
        self.assertEqual({u"真": 2, u"偽": 1, u"判定不能": 0}, dict(X[u"決まった行の札"]))
        self.assertEqual((2, 3, 66.7), (X[u"決まった行のうち札 真の行"][u"件"], X[u"決まった行のうち札 真の行"][u"分母"], X[u"決まった行のうち札 真の行"][u"率"]))
        self.assertEqual({"0": 1, "1": 4, "2": 1}, dict(X[u"候補の数の分布"]))
        self.assertEqual(1, X[u"候補 2 以上で保留の行"][u"件"])
        self.assertEqual({u"真": 1}, dict(X[u"候補 2 以上で保留の行"][u"札"]))
        self.assertEqual({"UNVERIFIABLE": 1}, dict(X[u"候補 2 以上で保留の行"][u"P28E の state"]))
        self.assertEqual({u"O の形の行": 3, u"決まった": 3 - 1}, dict(X[u"model 別"]["W1"]))
        self.assertEqual({u"O の形の行": 3, u"決まった": 2}, dict(X[u"model 別"]["W2"]))
        self.assertEqual({u"O の形の行": 2, u"決まった": 2}, dict(X[u"会社ごと"]["A"]))
        self.assertEqual({u"O の形の行": 2, u"決まった": 0}, dict(X[u"会社ごと"]["B"]))
        self.assertEqual({u"O の形の行": 2, u"決まった": 2}, dict(X[u"会社ごと"]["C"]))

    def test_s_2_nothing_decided_gives_no_rate(self):
        X = F5.sec_f5([self.row("A", "W1", [False, 0, False], (u"真", None, u"高", []))])
        self.assertEqual((1, 0, None), (X[u"O の形の行"], X[u"決まった行"], X[u"決まった行のうち札 真の行"][u"率"]))
        self.assertEqual({}, {k: v for k, v in X[u"候補の数の分布"].items() if k != "0"})


# ================================================================ (g) 使い捨ての小さい流れ
@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class SmokeFlow(unittest.TestCase):
    u"""1 書類・2 model(2 本)で gen → judge → inject → labels → tally を偽の書き手・偽の席で通し、記録の検査が緑 → 変異で赤になる。"""

    R = None

    @classmethod
    def setUpClass(cls):
        cls.p = Patch()
        cls.tmp = tempfile.mkdtemp(prefix="aiforms_f5_smoke_", dir=os.environ.get("TMPDIR"))
        seed, _m = GEN.seed_value(ROOT)
        chosen, counts = GEN.select_companies(ROOT, seed)
        cls.one, cls.doc = chosen[:1], chosen[0]["docID"]
        cls.p.set(GEN, "select_companies", lambda root, seed=None: (cls.one, counts))
        cls.gen_path = os.path.join(cls.tmp, "gen.json")
        cls.cache = os.path.join(cls.tmp, "cache")
        os.environ[GEN.KEY_ENV] = "SMOKEKEY-ccccccccccccccccccc"
        try:
            GEN.run(root=ROOT, only=cls.doc, out=cls.gen_path, new_cache=cls.cache, key_value=os.environ[GEN.KEY_ENV], transport=fake_transport_factory([]),
                    sleep=lambda s: None, say=lambda *a: None)
        finally:
            os.environ.pop(GEN.KEY_ENV, None)
        cls.claims_path = os.path.join(cls.tmp, "claims.json")
        RUN.run_judge(root=ROOT, procs=2, gen_path=cls.gen_path, new_cache=cls.cache, out=cls.claims_path, say=lambda *a: None)
        cls.inject_path = os.path.join(cls.tmp, "inject.json")
        RUN.run_inject(root=ROOT, procs=2, gen_path=cls.gen_path, new_cache=cls.cache, out=cls.inject_path, say=lambda *a: None)
        claims = jload_abs(cls.claims_path)
        ddir = os.path.join(cls.cache, "dossiers")
        for b in claims[u"本"]:
            d = jload_abs(os.path.join(ddir, b[u"札付けの束の鍵"] + ".json"))
            el = sorted(LAB.fact_names(d["facts"]))[0]
            labs = [{"id": c["id"], u"札": u"偽" if i % 6 == 5 else (u"判定不能" if i % 11 == 10 else u"真"), u"根拠": u"%s の当期の値と照合した。" % el,
                     u"誤りの型": u"計算の誤り" if i % 6 == 5 else None, u"確信": u"高"} for i, c in enumerate(d["claims"])]
            write_abs(os.path.join(ddir, b[u"札付けの束の鍵"] + ".seat1.json"), {u"札": labs})
            if b[u"name"] in claims[u"2 席目を立てる本"]:
                labs2 = [dict(x, 札=u"真", 誤りの型=None) if i % 3 == 0 else x for i, x in enumerate(labs)]
                write_abs(os.path.join(ddir, b[u"札付けの束の鍵"] + ".seat2.json"), {u"札": labs2})
        cls.labels_path = os.path.join(cls.tmp, "labels.json")
        F5.run_labels(root=ROOT, new_cache=cls.cache, claims_path=cls.claims_path, out=cls.labels_path, say=lambda *a: None)
        R = collections.OrderedDict([("gen", jload_abs(cls.gen_path)), ("claims", claims), ("labels", jload_abs(cls.labels_path)), ("inject", jload_abs(cls.inject_path))])
        R["tally"] = json.loads(json.dumps(F5.tally_record(R, {}, {}, None, jload("fixtures/xbrl/aiforms/tally_2026-11-03.json"))))
        cls.R = R

    @classmethod
    def tearDownClass(cls):
        cls.p.undo()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def probs(self, R=None):
        return record_problems(copy.deepcopy(self.R) if R is None else R, full=False)

    def mutate(self, key, fn):
        R = copy.deepcopy(self.R)
        fn(R[key])
        return self.probs(R)

    def test_g_0_the_flow_is_green(self):
        self.assertEqual([], self.probs())
        gen = self.R["gen"]
        self.assertEqual(2, gen[u"累計"][u"成功"])
        self.assertEqual(set(["F5"]), set(c["form"] for c in gen[u"呼び出し"]))
        self.assertTrue(self.R["claims"][u"本"])
        self.assertTrue(self.R["inject"][u"行"])
        for k, rec in self.R.items():
            self.assertEqual(json.loads(json.dumps(F5.swap_field())), rec[u"差し替え"], k)
            self.assertIn(u"F5", rec[u"step"], k)
        self.assertEqual(F5.PREV_TOTAL_USD, self.R["gen"][u"累計"][u"記録の外の費用 USD"])
        self.assertEqual(2, len(self.R["claims"][u"2 席目を立てる本"]))          # 8 本枠で 2 本中の抽選(min(8, 2))

    def test_g_1_no_free_text_reaches_a_record_and_the_facts_table_has_no_label_column(self):
        for k, rec in self.R.items():
            self.assertNotIn(u"の当期の値と照合した", json.dumps(rec, ensure_ascii=False), k)
        n = 0
        for fn in os.listdir(os.path.join(self.cache, "texts")):
            for line in open(os.path.join(self.cache, "texts", fn), encoding="utf-8").read().split("\n"):
                if len(line) < 8:
                    continue
                n += 1
                for k, rec in self.R.items():
                    self.assertNotIn(line, json.dumps(rec, ensure_ascii=False), k)
        self.assertGreater(n, 10)
        facts = open(os.path.join(self.cache, "facts", self.doc + ".md"), encoding="utf-8").read().split("\n")
        self.assertEqual(F5.F5_HEADER, facts[0])
        self.assertNotIn(u"標準ラベル", facts[0])
        self.assertTrue(all(l.count(u" | ") == 3 for l in facts[2:] if l))

    def test_g_2_the_swap_reaches_the_runner_scripts(self):
        # 差し替えが届いていれば、判定の script の名前の列は F5 だけ。RUN.GEN を前の便の実体に替えると 4 形になって数が変わる(黙って効かないことを防ぐ)
        names = RUN.prepare_run(ROOT, None, self.gen_path, self.cache, GEN.EXISTING_CACHES)[3]
        self.assertEqual(2, len(names))
        self.assertTrue(all("_F5_" in n for n in names))
        p = Patch()
        try:
            p.set(RUN, "GEN", OLD.GEN)
            self.assertNotEqual([], F5.wiring_problems())
            self.assertEqual(8, len(RUN.prepare_run(ROOT, None, self.gen_path, self.cache, GEN.EXISTING_CACHES)[3]))
        finally:
            p.undo()

    def test_g_3_record_mutations_turn_it_red(self):
        def kl(r): r[u"key_leaks"] = ["x"]
        def forb(r): r[u"呼び出し"][0][u"文"] = "x"
        def docid(r): r[u"会社の選び"][u"docID"].append("S100ZZZZ")
        def cost(r): r[u"呼び出し"][0][u"cost_usd"] = r[u"呼び出し"][0][u"cost_usd"] + 1
        def total(r): r[u"累計"][u"成功"] = 99
        def cap(r): r[u"費用"][u"上限 USD"] = 51.0
        def cache(r): r[u"cache の前後"][u"変化なし"] = False
        def scr(r): r[u"この script の sha256"] = "0" * 64
        def sw_drop(r): r[u"差し替え"][u"差し替えた名前"] = r[u"差し替え"][u"差し替えた名前"][:-1]
        def sw_prev(r): r[u"差し替え"][u"前の便の累計 USD"] = 29.4
        def sw_drv(r): r[u"差し替え"][u"駆動 script の sha256"] = "0" * 64
        def sw_gen(r): r[u"差し替え"][u"前の便の gen script の sha256"] = "0" * 64
        def sw_del(r): r.pop(u"差し替え")
        def step_old(r): r[u"step"] = r[u"step"].replace(u"F5(標準ラベルなし)", u"4")
        def outside(r): r[u"記録の外の呼び出し"][0][u"cost_usd"] = 0.0
        def total_wo_prev(r): r[u"累計"][u"費用 USD 合計(記録の外を含む)"] = r[u"累計"][u"費用 USD"]
        def labelled(r): next(iter(r[u"fact の表"].values()))[u"標準ラベルが付いた行"] = 5
        def common_sha(r): r[u"指示文の sha256"][u"WRITER_COMMON"] = jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"指示文の sha256"][u"WRITER_COMMON"]
        def forms_sha(r): r[u"指示文の sha256"][u"WRITER_FORMS"]["F5"] = "0" * 64
        def form_f1(r): r[u"呼び出し"][0][u"form"] = "F1"
        def no_prev_cache(r): r[u"cache の前後"][u"前"].pop(OLD_PREV)
        def other_company(r):
            prev = jload("fixtures/xbrl/aiforms/gen_2026-11-03.json")[u"会社の選び"][u"docID"]
            other = [x[u"docID"] for x in jload(OLD.GEN.REGRESS97_REL)[u"書類"] if x[u"docID"] not in prev][0]
            r[u"会社の選び"][u"docID"][0] = other
        def tbl_rows(r): next(iter(r[u"fact の表"].values()))[u"fact の数(素の context)"] += 1
        for fn in (kl, forb, docid, cost, total, cap, cache, scr, sw_drop, sw_prev, sw_drv, sw_gen, sw_del, step_old, outside, total_wo_prev, labelled, common_sha, forms_sha,
                   form_f1, no_prev_cache, other_company, tbl_rows):
            self.assertTrue(self.mutate("gen", fn), fn.__name__)
        def c_state(r): r[u"本"][0][u"行"][0][-1] = ["X", None, [], True, None, None, None]
        def c_cnt(r): r[u"本"][0][u"数の claim の数(P27)"] += 1
        def c_dup(r): r[u"本"][0][u"行"].append(list(r[u"本"][0][u"行"][0]))
        def c_sha(r): r[u"本"][0][u"文の sha256"] = "0" * 64
        def c_miss(r): r[u"欠けた本"].append("x")
        def c_s2(r): r[u"2 席目を立てる本"] = r[u"2 席目を立てる本"][:-1]
        def c_forb(r): r.__setitem__(u"文", "x")
        def c_prompt(r): r[u"札付けの席の指示文の sha256"] = "0" * 64
        def c_swap(r): r[u"差し替え"][u"指示文の sha256"][u"WRITER_COMMON_F5"] = "0" * 64
        def c_swdel(r): r.pop(u"差し替え")
        def c_step(r): r[u"step"] = u"AI の形 4 × model 2 ― 4 profile の判定(0 USD)"
        def c_seal(r): r["seal"] = OLD.SEAL_REL
        def c_nocache(r): r[u"cache の前後"][u"後"].pop(OLD_PREV)
        for fn in (c_state, c_cnt, c_dup, c_sha, c_miss, c_s2, c_forb, c_prompt, c_swap, c_swdel, c_step, c_seal, c_nocache):
            self.assertTrue(self.mutate("claims", fn), fn.__name__)

    def test_g_3b_table_hash_mutation_turns_it_red(self):
        def tbl_sha(r): next(iter(r[u"fact の表"].values()))[u"表の sha256"] = "0" * 64
        R = copy.deepcopy(self.R)
        tbl_sha(R["gen"])
        full_like = f5_extra_problems(R, False)
        self.assertTrue(full_like)

    def test_g_4_label_inject_tally_mutations_turn_it_red(self):
        def l_word(r): r[u"本"][0][u"札"][0][1] = "良"
        def l_id(r): r[u"本"][0][u"札"][0][0] = "N999"
        def l_dist(r): r[u"集計"][u"札の分布"][u"全体"][u"数の claim"] += 1
        def l_agree(r): r[u"集計"][u"2 席目との一致"][u"一致"] += 1
        def l_forb(r): r[u"本"][0][u"根拠"] = "x"
        def l_swap(r): r[u"差し替え"][u"前の便の累計 USD"] = 1.0
        def l_step(r): r[u"step"] = u"AI の形 4 × model 2 ― 盲検の席の札(0 USD)"
        for fn in (l_word, l_id, l_dist, l_agree, l_forb, l_swap, l_step):
            self.assertTrue(self.mutate("labels", fn), fn.__name__)
        def i_cell(r): r[u"行"][0]["P27"][u"結果"] = "通した?"
        def i_cap(r): r[u"行"] += [dict(r[u"行"][0], id=r[u"行"][0][u"id"] + "x%d" % i) for i in range(11)]
        def i_sum(r): r[u"集計"]["T1_VALUE"]["P27"][u"全体"][u"注入の行"] += 1
        def i_forb(r): r[u"行"][0][u"元の字"] = "x"
        def i_swap(r): r[u"差し替え"][u"差し替えた名前"] = []
        def i_book(r): r[u"行"][0][u"docID"] = "S100ZZZZ"
        for fn in (i_cell, i_cap, i_sum, i_forb, i_swap, i_book):
            self.assertTrue(self.mutate("inject", fn), fn.__name__)
        def t_sum(r): r[u"集計"][u"1 配線"][u"生成できた本"] += 1
        def t_judge(r): r[u"予測の判定"]["B-3"][u"判定"] = MISS if r[u"予測の判定"]["B-3"][u"判定"] != MISS else HIT
        def t_count(r): r[u"当たり"] += 1
        def t_forb(r): r[u"集計"][u"文"] = "x"
        def t_reco(r): r[u"封 §2-1 の推奨"] = F5.REVERT if r[u"封 §2-1 の推奨"] != F5.REVERT else F5.KEEP
        def t_swap(r): r[u"差し替え"][u"駆動 script の sha256"] = "0" * 64
        def t_extra(r): r[u"集計"][F5.EXTRA_KEY][u"決まった行"] += 1
        def t_scr(r): r[u"この script の sha256"] = sha256_rel("measure/xbrl_aiforms_tally_2026-11-03.py")       # 前の便の tally script を指す = 駆動 script でない
        for fn in (t_sum, t_judge, t_count, t_forb, t_reco, t_swap, t_extra, t_scr):
            self.assertTrue(self.mutate("tally", fn), fn.__name__)
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        name = GEN.text_key(row[u"docID"], row[u"form"], row[u"model"])
        b = next(x for x in R["claims"][u"本"] if x[u"name"] == name)
        for raw in b[u"行"]:
            if raw[0] == row[u"基準の claim"]:
                raw[len(RUN.CLAIM_COLS)] = ["VALUE_MISMATCH", None, [], True, None, None, None]
        self.assertTrue(self.probs(R))                                          # 土台が GROUNDED でなくなる

    def test_g_5_judgments_move_with_the_records(self):
        prev = jload("fixtures/xbrl/aiforms/tally_2026-11-03.json")
        base = F5.judge_f5(F5.build_f5(self.R), prev)
        R = copy.deepcopy(self.R)
        for row in R["inject"][u"行"]:
            for p in RUN.PROFILES:
                row[p] = {u"対応": True, u"結果": RUN.TUNE.LABEL_PASS, u"state": "GROUNDED", u"reason": None}
        self.assertEqual(MISS, F5.judge_f5(F5.build_f5(R), prev)["B-8"][u"判定"])
        R = copy.deepcopy(self.R)
        for b in R["labels"][u"本"]:
            for r in b[u"札"]:
                r[1], r[2] = u"偽", u"計算の誤り"
        self.assertEqual(MISS, F5.judge_f5(F5.build_f5(R), prev)["B-5"][u"判定"])
        self.assertEqual(NOJ, base["B-9"][u"判定"])
        self.assertEqual(list(base), [u"B-%d" % i for i in range(1, 10)])

    def test_g_6_each_judgment_flips_at_the_seal_boundary(self):
        prev0 = jload("fixtures/xbrl/aiforms/tally_2026-11-03.json")
        T0 = F5.build_f5(self.R)

        def judged(edit, prev=None):
            T = copy.deepcopy(T0)
            edit(T)
            return F5.judge_f5(T, prev if prev is not None else prev0)
        w = lambda T: T[u"1 配線"]
        key_books = u"生成できて P27 の数の claim が %d 以上ある本" % F5.B1_MIN_CLAIMS
        cost_key = u"費用 USD(記録の cost_usd の合計)"

        def b1(made, n, c, why=None):
            def e(T):
                w(T)[u"生成できた本"], w(T)[key_books], w(T)[cost_key], w(T)[u"止めた理由"] = made, n, c, why
                w(T)[u"上限で止まった"] = TAL.is_cap_stop(why)
            return judged(e)["B-1"][u"判定"]
        self.assertEqual((HIT, HIT, HIT, MISS, MISS, MISS, MISS, MISS, HIT, MISS),
                         (b1(40, 40, 4.0), b1(40, 40, 10.0), b1(40, 40, 7.0), b1(40, 40, 3.99), b1(40, 40, 10.01), b1(39, 40, 7.0), b1(40, 39, 7.0), b1(40, 40, 7.0, OLD.CAP_STOP_RUNNING_EXAMPLE),
                          b1(40, 40, 7.0, u"HTTP 401(鍵の問題)"), b1(40, 40, 7.0, OLD.CAP_STOP_ESTIMATE_EXAMPLE)))
        Sk = u"「その他」の形の行(provenance)"

        def b2(n, f1=9):
            def e(T):
                T[u"4 profile の差"][Sk]["P28E"][u"全体"][u"「その他」の形の行"] = n
            prev = copy.deepcopy(prev0)
            prev[u"集計"][u"4 profile の差"][Sk]["P28E"]["F1"][u"「その他」の形の行"] = f1
            return judged(e, prev)["B-2"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, MISS, HIT), (b2(20), b2(120), b2(19), b2(121), b2(30, f1=16), b2(32, f1=16)))

        def b3(n, rate):
            def e(T):
                c = T[u"4 profile の差"][Sk]["P28E"][u"全体"]
                c[u"決まった"][u"件"], c[u"決まった"][u"率"] = n, rate
            return judged(e)["B-3"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, HIT, HIT, MISS, MISS), (b3(5, 25.0), b3(60, 70.0), b3(4, 50.0), b3(61, 50.0), b3(10, 25.0), b3(10, 70.0), b3(10, 24.9), b3(10, 70.1)))
        Mv = u"P27E → P28E の state の動き(向き別)"

        def b4(moves):
            def e(T):
                T[u"4 profile の差"][Mv][u"全体"] = moves
            return judged(e)["B-4"][u"判定"]
        def b4v(moves):
            def e(T):
                T[u"4 profile の差"][Mv][u"全体"] = moves
            return judged(e)["B-4"][u"値"]
        v = b4v({u"GROUNDED → VALUE_MISMATCH": 2, u"UNVERIFIABLE → GROUNDED": 1, u"POINTER_NOT_FOUND → GROUNDED": 3})
        self.assertEqual((2, 3), (v[u"GROUNDED でなくなった行"], v[u"許した向き以外の行"]))
        self.assertEqual((HIT, HIT, HIT, MISS, MISS, MISS),
                         (b4({}), b4({u"POINTER_NOT_FOUND → GROUNDED": 3}), b4({u"POINTER_NOT_FOUND → GROUNDED": 3, u"VALUE_MISMATCH → GROUNDED": 2}),
                          b4({u"GROUNDED → VALUE_MISMATCH": 1}), b4({u"UNVERIFIABLE → GROUNDED": 1}), b4({u"VALUE_MISMATCH → UNVERIFIABLE": 1})))

        def b5(f, t, f1=2.5):
            def e(T):
                L = T[u"2 札"][u"札の分布"][u"全体"]
                L[u"偽"][u"率"], L[u"真"][u"率"] = f, t
            prev = copy.deepcopy(prev0)
            prev[u"集計"][u"2 札"][u"札の分布"]["F1"][u"偽"][u"率"] = f1
            return judged(e, prev)["B-5"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, HIT, MISS, MISS, MISS), (b5(3.5, 80.0), b5(10.0, 80.0), b5(3.4, 90.0), b5(10.1, 90.0), b5(5.0, 95.0), b5(5.0, 79.9), b5(5.0, None), b5(3.6, 90.0, f1=3.6)))
        E = u"3 engine の判定(無改変)"

        def b6(g28, g27):
            def e(T):
                T[E]["P28E"][u"全体"][u"札 真の行の GROUNDED 率"][u"率"] = g28
                T[E]["P27E"][u"全体"][u"札 真の行の GROUNDED 率"][u"率"] = g27
            return judged(e)["B-6"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, HIT, MISS, MISS, MISS), (b6(55.0, 54.7), b6(75.0, 60.0), b6(54.9, 50.0), b6(75.1, 70.0), b6(60.3, 60.0), b6(60.2, 60.0), b6(60.0, 60.0), b6(None, 60.0)))

        def b7(x):
            def e(T):
                T[F5.EXTRA_KEY][u"決まった行のうち札 真の行"][u"率"] = x
            return judged(e)["B-7"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS), (b7(80.0), b7(100.0), b7(79.9), b7(None)))

        def b8(p27, p28e, orig28):
            def e(T):
                for t in RUN.INJECT_TYPES:
                    T[u"5 注入"][t]["P27"][u"全体"][u"通した"][u"率"] = p27
                    T[u"5 注入"][t]["P28E"][u"全体"][u"通した"][u"率"] = p28e
                T[u"5 注入"]["T8_REL"]["P28E"][u"全体"][u"名指して原本の値を返した"][u"率"] = orig28
            return judged(e)["B-8"][u"判定"]
        self.assertEqual((HIT, MISS, MISS, MISS, MISS), (b8(3.0, 3.0, 60.0), b8(3.1, 3.0, 60.0), b8(3.0, 3.1, 60.0), b8(3.0, 3.0, 59.9), b8(3.0, 3.0, None)))

    def test_g_7_the_recommendation_follows_section_2_1(self):
        def J(decided, lost, r7):
            return {"B-3": {u"値": {u"決まった行": decided}}, "B-4": {u"値": {u"GROUNDED でなくなった行": lost}}, "B-7": {u"値": {u"率": r7}}}
        self.assertEqual(F5.KEEP, F5.recommendation(J(5, 0, 80.0)))
        self.assertEqual(F5.KEEP, F5.recommendation(J(40, 0, 100.0)))
        self.assertEqual(F5.REVERT, F5.recommendation(J(4, 0, 100.0)))
        self.assertEqual(F5.REVERT, F5.recommendation(J(0, 0, None)))
        self.assertEqual(F5.ASK_HUMAN, F5.recommendation(J(40, 1, 100.0)))
        self.assertEqual(F5.ASK_HUMAN, F5.recommendation(J(40, 0, 79.9)))
        self.assertEqual(F5.ASK_HUMAN, F5.recommendation(J(4, 1, 100.0)))          # 封に無い決め: 重なるときは人間に戻す
        self.assertEqual(F5.ASK_HUMAN, F5.recommendation(J(4, 0, 50.0)))
        self.assertEqual(F5.ASK_HUMAN, F5.recommendation(J(40, 0, None)))

    def test_g_7b_the_recommendation_line_is_fixed_text(self):
        J = {"B-3": {u"値": {u"決まった行": 5}}, "B-4": {u"値": {u"GROUNDED でなくなった行": 0}}, "B-7": {u"値": {u"率": 80.0}}}
        self.assertEqual(u"封 §2-1 の決め方による推奨: **据え置く**(決まった行 5・GROUNDED でなくなった行 0・B-7 80.0%)。最後に決めるのは人間。", F5.render_reco(J))

    def test_g_8_the_table_in_the_result_document_follows_the_records(self):
        J = F5.judge_f5(F5.build_f5(self.R), jload("fixtures/xbrl/aiforms/tally_2026-11-03.json"))
        table = F5.render_table(J)
        doc = u"# 結果\n\n<!-- 門:start pred -->\n%s\n<!-- 門:end -->\n\n<!-- 門:start reco -->\n%s\n<!-- 門:end -->\n\n本文。\n" % (table, F5.render_reco(J))
        self.assertEqual([], doc_problems(doc, self.R))
        self.assertTrue(doc_problems(doc.replace(u"B-3", u"B-4", 1), self.R))
        self.assertTrue(doc_problems(doc.replace(u"当たり", u"外れ", 1), self.R))
        self.assertTrue(doc_problems(doc.replace(F5.render_reco(J), F5.render_reco(J).replace(u"**", u"*", 1)), self.R))
        self.assertTrue(doc_problems(doc + u"\nS100ABCD\n", self.R))
        self.assertTrue(doc_problems(doc + u"\n精度が高い。\n", self.R))
        self.assertTrue(doc_problems(doc + u"\n本文に 1234 がある。\n", self.R))
        self.assertEqual([], doc_problems(doc + u"\n本文に 1234 がある。【門なし】\n", self.R))
        self.assertTrue(doc_problems(doc + u"\n<!-- 門:start other -->\nx\n<!-- 門:end -->\n", self.R))
        R = copy.deepcopy(self.R)
        R["gen"][u"呼び出し"][0][u"ok"] = True
        R["claims"][u"本"][0][u"数の claim の数(P27)"] = 0
        self.assertTrue(doc_problems(doc, R))


# ---------------------------------------------------------------- 宣言(docID を持つ記録 5 つは LATER_NAMING_FILES に宣言する)
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
        self.assertNotEqual([], naming_problems(src.replace('"fixtures/xbrl/aiforms/f5_tally_2026-11-03.json")', '"fixtures/xbrl/aiforms/f5_tally_2026-11-03.json", "%s")' % DRIVER_REL)))

    def test_h_2_the_previous_run_is_still_declared(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        for k in OLD.REC_REL.values():
            self.assertIn(k, later_naming_files(src))


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


# ---------------------------------------------------------------- 本番の記録(c)(d)(e)
@unittest.skipUnless(records_exist(), "記録が無い(生成・判定・札・注入・集計の後に走る)")
class RealRecordsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = load_records()

    def test_c_1_records_are_clean_and_consistent(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=True))

    def test_d_1_the_result_document_follows_the_records(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), self.R))

    def test_e_1_order_is_seal_then_driver_then_records(self):
        self.assertEqual([], order_of(REPO))


if __name__ == "__main__":
    unittest.main()
