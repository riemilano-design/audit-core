# -*- coding: utf-8 -*-
u"""AI の形 4 × model 2(20 社 × 形 4 × model 2 = 160 本)の測定の結果の門。封 docs/XBRL_AI_FORMS_SEAL_2026-11-03.md §4。

記録 5 つ(``fixtures/xbrl/aiforms/``: gen・claims・labels・inject・tally)から、封 §2 の予測 A-1〜A-12 の判定を**機械で求め**、結果の文書
``docs/XBRL_AI_FORMS_RESULT_2026-11-03.md`` の表(``<!-- 門:start 予測の判定 -->`` の中)を記録から作り直した表と一行も違わないことを見る。縛るもの:

  a  指示文の定数の字: 書き手の指示文(``WRITER_COMMON``・``WRITER_FORMS``)が封 §0-2 の 2 の形の字(幅の数・「・」「|」・Q&A)を持ち、検証されることを知らせる語を持たない。
     札付けの席の指示文(``LABELLER_PROMPT``)が封の札の語を持つ。費用・model・max_tokens・再試行の定数が封の字と同じ。封 §2 の幅の数が tally の script の定数と同じ。
  b  生成の振る舞い(偽の transport。通信しない): 見積りが上限を超えれば 1 回も呼ばない・累計 + 次の見積りが上限を超えたら止める・429 / 5xx だけ最大 2 回・401 で全体を止める・
     鍵は記録に出ない・既に在る文は --resume なしでは二度呼ばない・鍵が無ければ呼ばない。
  c  記録の中身: 禁止欄(span・文・数の字・value・recomputed・根拠の自由文)が無い・会社名が無い・key_leaks が空・docID が 97 の中の選んだ 20 社で P27 の調整用・評価用 20 社に無い・
     cache の前後が同じ(281・40・94)・script の sha256 が現物と一致・注入の土台は 4 profile 全部 GROUNDED の claim・札は 1 席目と 2 席目の規則どおり・集計が行から作り直せる。
  d  判定: tally の判定を記録から作り直して一致。結果の文書の表 = 記録から作り直した表。門の外の散文は 3 桁以上の数を持たない(持つ行には【門なし】)。docID が文書に無い。
  e  順序: 封 S の commit ⊏ script 4 本 ⊑ 記録・文書・門の commit ⊑ HEAD。S が engine を触らない。未 commit は赤(skip にしない)。
  g  変異: 記録の数・文書の 1 字・順序・定数の 1 字を壊した標本で赤になる。使い捨ての小さい流れ(1 書類・1 model。偽の書き手と偽の席。通信しない)で記録 5 つを作り、同じ検査が緑 → 変異で赤になることを見る。

記録が無いときは (c)(d)(e) の記録の試験を skip する(a)(b)(g) は走る。この file は docID の字を持たない。
"""
import ast
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request

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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_aiforms")        # 前の便の門の部品(doc_blocks・prose_problems・order_problems・Repo)。門としては走らせない
GEN = load_module("measure/xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_gate")
RUN = load_module("measure/xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_gate")
LAB = load_module("measure/xbrl_aiforms_labels_2026-11-03.py", "aiforms_labels_for_gate")
TAL = load_module("measure/xbrl_aiforms_tally_2026-11-03.py", "aiforms_tally_for_gate")

SEAL_REL = "docs/XBRL_AI_FORMS_SEAL_2026-11-03.md"
DOC_REL = "docs/XBRL_AI_FORMS_RESULT_2026-11-03.md"
SEAL_COMMIT_SHORT = "0b43a03"
REC_REL = collections.OrderedDict([
    ("gen", "fixtures/xbrl/aiforms/gen_2026-11-03.json"), ("claims", "fixtures/xbrl/aiforms/claims_2026-11-03.json"),
    ("labels", "fixtures/xbrl/aiforms/labels_2026-11-03.json"), ("inject", "fixtures/xbrl/aiforms/inject_2026-11-03.json"),
    ("tally", "fixtures/xbrl/aiforms/tally_2026-11-03.json")])
SCRIPT_REL = collections.OrderedDict([
    ("gen", "measure/xbrl_aiforms_gen_2026-11-03.py"), ("run", "measure/xbrl_aiforms_run_2026-11-03.py"),
    ("labels", "measure/xbrl_aiforms_labels_2026-11-03.py"), ("tally", "measure/xbrl_aiforms_tally_2026-11-03.py")])
REC_SCRIPT = {"gen": "gen", "claims": "run", "inject": "run", "labels": "labels", "tally": "tally"}      # 記録 → それを作った script
GATE_FILES = ("tests/measure/test_xbrl_aiforms_result.py",)
NOT_GATED = PR.NOT_GATED
HIT, MISS, NOJ = TAL.HIT, TAL.MISS, TAL.NOJ
FORBIDDEN_KEYS = ("span", "value", "recomputed", u"文", u"理由", u"根拠", u"sentence", u"text", u"数", u"元の字", u"後の字", u"新しい値", u"周り", u"content")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
EXPECT_CACHES = collections.OrderedDict([("edinet", 281), ("edinet-fresh-2026-10-21", 40), ("edinet-prior-2026-11-02", 94)])
# 上限の停止の字の例(gen script の 2 つの止めの書式に値を入れた形。実物との一致は test_th_15 が gen の source で照らす)
CAP_STOP_ESTIMATE_EXAMPLE = u"見積り 50.3000 USD が上限 50.00 USD を超える。1 回も呼ばずに止める"
CAP_STOP_RUNNING_EXAMPLE = u"累計 49.9000 + 次の見積り 0.3000 が上限 50.00 USD を超える(S100AAAA_F1_x の前)"
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in GEN.EXISTING_CACHES.values()) and os.path.isdir(GEN.EXISTING_CACHES["edinet"])


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def records_exist(keys=None):
    return all(os.path.exists(os.path.join(ROOT, REC_REL[k])) for k in (keys or REC_REL))


def load_records():
    return collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())


# ---------------------------------------------------------------- 封の字(a)
def seal_pred_rows(seal):
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| \*\*(A-\d+)\*\* \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = cells[0]
    return out


def seal_pins(seal):
    u"""封 §2 の幅の字 → tally の script の定数と同じかを見るための (名前, 封の値, script の値) の列。"""
    P = seal_pred_rows(seal)
    out = []

    def rng(txt, pat=r"\*\*(\d+)〜(\d+)(?:%| USD)?\*\*"):
        return [(int(a), int(b)) for a, b in re.findall(pat, txt)]
    t = P["A-1"]
    out.append(("A-1 本数", int(re.search(r"\*\*(\d+) 以上\*\*", t).group(1)), TAL.A1_MIN_BOOKS))
    out.append(("A-1 claim", int(re.search(r"claim が (\d+) 以上", t).group(1)), TAL.A1_MIN_CLAIMS))
    out.append(("A-1 費用", tuple(float(x) for x in re.search(r"\*\*(\d+)〜(\d+) USD\*\*", t).groups()), TAL.A1_COST))
    t = P["A-2"]
    out.append(("A-2", collections.OrderedDict((u"F%s" % f, (int(a), int(b))) for f, a, b in re.findall(r"F(\d) \*\*(\d+)〜(\d+)\*\*", t)), TAL.A2_BOUNDS))
    t = P["A-3"]
    out.append(("A-3 真", float(re.search(r"真 \*\*(\d+)% 以上\*\*", t).group(1)), TAL.A3_TRUE_MIN))
    out.append(("A-3 偽", tuple(float(x) for x in re.search(r"偽 \*\*(\d+)〜(\d+)%\*\*", t).groups()), TAL.A3_FALSE))
    out.append(("A-3 一致", float(re.search(r"一致率 \*\*(\d+)% 以上\*\*", t).group(1)), TAL.A3_AGREE_MIN))
    t = P["A-4"]
    out.append(("A-4", collections.OrderedDict((u"F%s" % f, (int(a), int(b))) for f, a, b in re.findall(r"F(\d) \*\*(\d+)〜(\d+)%\*\*", t)), TAL.A4_BOUNDS))
    out.append(("A-5", float(re.search(r"\*\*(\d+)% 以上\*\*", P["A-5"]).group(1)), TAL.A5_MIN))
    t = P["A-6"]
    out.append(("A-6 止める", float(re.search(r"\*\*(\d+)% 以上\*\*", t).group(1)), TAL.A6_STOP_MIN))
    out.append(("A-6 通した", int(re.search(r"全体で (\d+) 以下", t).group(1)), TAL.A6_PASS_MAX))
    out.append(("A-7", rng(P["A-7"])[0], TAL.A7_RANGE))
    out.append(("A-8", rng(P["A-8"])[0], TAL.A8_RANGE))
    t = P["A-9"]
    out.append(("A-9 通した", float(re.search(r"\*\*(\d+)% 以下\*\*", t).group(1)), TAL.A9_PASS_MAX))
    out.append(("A-9 P28E", float(re.search(r"P28E \*\*(\d+)% 以上\*\*", t).group(1)), TAL.A9_P28E_ORIG_MIN))
    out.append(("A-9 P27", float(re.search(r"P27 \*\*(\d+)% 以下\*\*", t).group(1)), TAL.A9_P27_ORIG_MAX))
    t = P["A-10"]
    out.append(("A-10 差", float(re.search(r"\*\*(\d+) ポイント以下\*\*", t).group(1)), TAL.A10_PAIR_MAX))
    out.append(("A-10 幅", float(re.search(r"\*\*(\d+) ポイント以上\*\*", t).group(1)), TAL.A10_SPREAD_MIN))
    t = P["A-11"]
    out.append(("A-11 行", rng(t)[0], TAL.A11_RANGE))
    out.append(("A-11 率", tuple(float(x) for x in re.search(r"率 \*\*(\d+)〜(\d+)%\*\*", t).groups()), TAL.A11_DECIDED))
    return out


def norm(v):
    if isinstance(v, dict):
        return collections.OrderedDict((k, norm(x)) for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def const_problems(seal, gen=GEN, run=RUN, tal=TAL):
    u"""指示文・費用・札の語・封の幅の字が、封の文書と同じか。問題の列。"""
    out = []
    forms, common = gen.WRITER_FORMS, gen.WRITER_COMMON
    # 形の字(封 §0-2 の 2)
    need = {"F1": [u"見出しつきの段落", u"経営成績", u"財政状態", u"キャッシュ・フロー", u"1,500〜2,500 字"],
            "F2": [u"箇条書き", u"「・」で始まる", u"12〜25 個", u"1 項目は 1 文"],
            "F3": [u"「|」区切りの表", u"項目・当期・前期・増減", u"5〜12 行", u"注記の文を 5〜10 文", u"注記の文には数を含める"],
            "F4": [u"Q&A", u"6〜10 組", u"答えには数を含める"]}
    for f, words in need.items():
        for w in words:
            if w not in forms.get(f, u""):
                out.append(u"形 %s の指示に %r が無い" % (f, w))
    for f, words in (("F1", [u"1,500〜2,500 字", u"見出しつきの段落"]), ("F2", [u"12〜25 個", u"「・」"]), ("F3", [u"5〜12 行", u"5〜10 文", u"|"]), ("F4", [u"6〜10 組", u"Q&A"])):
        for w in words:
            if w not in seal:
                out.append(u"封に %r が無い(形 %s)" % (w, f))
    if list(forms) != ["F1", "F2", "F3", "F4"]:
        out.append(u"形の並びが F1〜F4 でない")
    # 検証されることを知らせない・「正確に」と書かない(封 §0-2 の 2)
    for t in [common] + list(forms.values()):
        for bad in (u"検証", u"照合", u"機械が", u"正確", u"幻覚", u"ハルシネーション", u"間違い", u"誤り"):
            if bad in t:
                out.append(u"書き手の指示文に %r がある" % bad)
    for ph in (u"{FACTS}", u"{FORM}"):
        if common.count(ph) != 1:
            out.append(u"WRITER_COMMON に %s が 1 回でない" % ph)
    if u"材料は" not in common or u"表に無い事実" not in common:
        out.append(u"共通の指示に『材料は表だけ・表に無い事実は書かない』が無い")
    # 費用・model・max_tokens・再試行(封 §0-2 の 3・4)
    if gen.COST_CAP_USD != 50.0 or not re.search(r"上限 \*\*50 USD\*\*", seal):
        out.append(u"上限が 50 USD でない")
    if (gen.PRICE_IN, gen.PRICE_OUT) != (5.0, 25.0) or u"入力 5 USD / M tokens・出力 25 USD / M tokens" not in seal:
        out.append(u"単価が封と違う")
    if gen.MAX_TOKENS != 4000 or u"`max_tokens` 4,000" not in seal:
        out.append(u"max_tokens が封と違う")
    if gen.MODELS != ("claude-sonnet-5-5", "claude-haiku-5-5") or any((u"`%s`" % m) not in seal for m in gen.MODELS):
        out.append(u"model が封と違う")
    if gen.RETRY_WAITS != (2, 8) or u"最大 2 回" not in seal:
        out.append(u"再試行が封と違う")
    if gen.FORMS != ("F1", "F2", "F3", "F4") or gen.SEAT2_N != 32 or gen.N_COMPANIES != 20 or gen.MIN_CLAIMS != 60:
        out.append(u"形・2 席目・会社の数が封と違う")
    if run.INJECT_CAP != 10 or u"型ごと上限 **10**" not in seal or tuple(run.PROFILES) != ("P27", "P27E", "P28", "P28E") or tuple(run.INJECT_TYPES) != ("T1_VALUE", "T8_REL"):
        out.append(u"注入の上限・型・profile が封と違う")
    # 札付けの席の指示文(封 §0-2 の 6・2026-10-09 の札の作法)
    for w in (u"真", u"偽", u"判定不能", u"根拠", u"誤りの型", u"確信", u"fact の表", u"Read"):
        if w not in run.LABELLER_PROMPT:
            out.append(u"札付けの指示に %r が無い" % w)
    for w in (u"engine の出力は見ない", u"sgogi-coach-handoff", u"edinetdb-p27"):
        if w not in run.LABELLER_PROMPT.replace(u"道具(engine)の出力は見ない", u"engine の出力は見ない"):
            out.append(u"札付けの指示に席の禁止『%s』が無い" % w)
    if tuple(run.LABEL_WORDS) != (u"真", u"偽", u"判定不能"):
        out.append(u"札の語が封と違う")
    if hashlib.sha256(run.LABELLER_PROMPT.encode("utf-8")).hexdigest() != run.LABELLER_PROMPT_SHA256:
        out.append(u"LABELLER_PROMPT_SHA256 が現物と違う")
    # 封の幅 = script の定数
    for name, seal_v, script_v in seal_pins(seal):
        if norm(seal_v) != norm(script_v):
            out.append(u"%s: 封の字 %r と tally の定数 %r が違う" % (name, seal_v, script_v))
    # 封の予測の行が A-1〜A-12 の全部
    if list(seal_pred_rows(seal)) != [u"A-%d" % i for i in range(1, 13)]:
        out.append(u"封 §2 の予測の行が A-1〜A-12 でない")
    return out


# ---------------------------------------------------------------- 記録(c)
def walk(o, fn, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            fn(k, v, path)
            walk(v, fn, path + (k,))
    elif isinstance(o, list):
        for v in o:
            walk(v, fn, path)


def all_strings(o):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out.append(k) if isinstance(k, str) else None
            out += all_strings(v)
    elif isinstance(o, list):
        for v in o:
            out += all_strings(v)
    elif isinstance(o, str):
        out.append(o)
    return out


def sha_ok(s):
    return isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s) is not None


def record_problems(R, full=True, root=ROOT, scripts=None):
    u"""記録 5 つ(R の key: gen・claims・labels・inject・tally のうち在るもの)の問題の列。full = 本番の 20 社・160 本・cache 281/40/94。"""
    out = []
    scripts = scripts or dict((k, sha256_rel(v)) for k, v in SCRIPT_REL.items())
    # 全記録に共通
    for k, rec in R.items():
        bad = set()

        def fk(key, val, path):
            if key in FORBIDDEN_KEYS:
                bad.add(key)
        walk(rec, fk)
        for b in sorted(bad):
            out.append(u"%s: 禁止欄 %s" % (k, b))
        strings = all_strings(rec)
        if any(w in s for s in strings for w in COMPANY_WORDS):
            out.append(u"%s: 会社名らしい字がある" % k)
        text = json.dumps(rec, ensure_ascii=False)
        if GEN.key_leaks(text, None, long_alnum=False):
            out.append(u"%s: 鍵らしい字がある" % k)
        if rec.get(u"key_leaks"):
            out.append(u"%s: key_leaks が空でない" % k)
        want = scripts.get(REC_SCRIPT[k])
        if rec.get(u"この script の sha256") != want:
            out.append(u"%s: この script の sha256 が現物と違う" % k)
        if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
            out.append(u"%s: 封の名・commit が違う" % k)
    gen, claims, labels, inj, tally = (R.get(x) for x in ("gen", "claims", "labels", "inject", "tally"))
    docs = None
    if gen is not None:
        docs = gen[u"会社の選び"][u"docID"]
        out += gen_problems(gen, full, root)
    for k in ("claims", "inject"):
        if R.get(k) is not None:
            cb = R[k][u"cache の前後"]
            if not cb[u"変化なし"] or cb[u"前"] != cb[u"後"]:
                out.append(u"%s: cache の前後が違う" % k)
            if full:
                for name, n in EXPECT_CACHES.items():
                    if cb[u"前"][name][u"件数"] != n:
                        out.append(u"%s: cache %s の件数が %d でない" % (k, name, n))
    if gen is not None and claims is not None:
        out += claims_problems(gen, claims, full)
    if claims is not None and labels is not None:
        out += labels_problems(claims, labels, full)
    if claims is not None and inj is not None:
        out += inject_problems(claims, inj)
    if all(x is not None for x in (gen, claims, labels, inj, tally)):
        out += tally_problems(R, scripts, check_input_sha=full)
    # docID は選んだ 20 社の中だけ
    if docs is not None:
        for k, rec in R.items():
            found = set(DOCID_RE.findall(json.dumps(rec, ensure_ascii=False)))
            if not found <= set(docs):
                out.append(u"%s: 選んだ 20 社の外の docID がある" % k)
    return out


def script_history_problems(gen):
    u"""記録の上の欄 = 最後の script。``script の履歴`` の各行 {sha256, HEAD, 呼び出しの番号の範囲} の形と、呼び出しの ``script_sha256``(先頭 16 字)が範囲の script と合うこと。"""
    out = []
    hist, calls, top = gen.get(u"script の履歴"), gen[u"呼び出し"], gen.get(u"この script の sha256")
    if not isinstance(hist, list):
        return [u"gen: script の履歴が無い"]
    spans, prev_end = [], 0
    for row in hist:
        if not isinstance(row, dict) or set(row) != set([u"sha256", u"HEAD", u"呼び出しの番号の範囲"]):
            out.append(u"gen: script の履歴の行の欄がおかしい")
            continue
        if not sha_ok(row[u"sha256"]) or not (isinstance(row[u"HEAD"], str) and row[u"HEAD"]):
            out.append(u"gen: script の履歴の sha256 か HEAD がおかしい")
        rng = row[u"呼び出しの番号の範囲"]
        if rng == []:
            continue
        if not (isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, int) for x in rng)) or rng[0] != prev_end + 1 or not (rng[0] <= rng[1] <= len(calls)):
            out.append(u"gen: script の履歴の番号の範囲が 1 から途切れず並んでいない")
            continue
        spans.append((rng[0], rng[1], row[u"sha256"]))
        prev_end = rng[1]
    for i, c in enumerate(calls, 1):
        owner = next((sha for a, b, sha in spans if a <= i <= b), None)
        want = (owner if owner is not None else top)
        got = c.get(u"script_sha256")
        if got is None:
            if owner is None:
                out.append(u"gen: 呼び出し %d に script_sha256 が無い(履歴の範囲の外)" % i)
        elif not isinstance(want, str) or got != want[:16]:
            out.append(u"gen: 呼び出し %d の script_sha256 が、その番号を持つ script(履歴か記録の上の欄)と合わない" % i)
    return out


def gen_problems(gen, full, root):
    out = []
    docs = gen[u"会社の選び"][u"docID"]
    if len(set(docs)) != len(docs):
        out.append(u"gen: 会社が重複している")
    r97 = dict((r["docID"], r) for r in jload(GEN.REGRESS97_REL)[u"書類"])
    p27 = set(c["docID"] for c in jload(GEN.P27_REPORTS_REL)[u"会社"])
    if not set(docs) <= set(r97):
        out.append(u"gen: 会社が手元の 97 の中にない")
    if set(docs) & p27:
        out.append(u"gen: P27 の調整用・評価用 20 社の会社が入っている")
    if any(r97[d]["claims"] < GEN.MIN_CLAIMS for d in docs if d in r97):
        out.append(u"gen: claims が %d 未満の会社が入っている" % GEN.MIN_CLAIMS)
    if full:
        if len(docs) != GEN.N_COMPANIES:
            out.append(u"gen: 会社が %d 社でない" % GEN.N_COMPANIES)
        try:
            seed, _m = GEN.seed_value(root)
            chosen, _c = GEN.select_companies(root, seed)
            if [r["docID"] for r in chosen] != docs:
                out.append(u"gen: 会社の選びが規則から作り直した選びと違う")
        except Exception as e:                        # noqa: BLE001
            out.append(u"gen: 会社の選びを作り直せない(%s)" % type(e).__name__)
    cb = gen[u"cache の前後"]
    if cb[u"後"] is not None and (not cb[u"変化なし"] or cb[u"前"] != cb[u"後"]):
        out.append(u"gen: cache の前後が違う")
    if full and cb[u"後"] is not None:
        for name, n in EXPECT_CACHES.items():
            if cb[u"前"][name][u"件数"] != n:
                out.append(u"gen: cache %s の件数が %d でない" % (name, n))
    if full and cb[u"後"] is None:
        out.append(u"gen: cache の後が書かれていない(生成が最後まで走っていない)")
    c = gen[u"費用"]
    if (c[u"上限 USD"], c[u"単価 入力 USD / M tokens"], c[u"単価 出力 USD / M tokens"]) != (GEN.COST_CAP_USD, GEN.PRICE_IN, GEN.PRICE_OUT):
        out.append(u"gen: 費用の定数が script と違う")
    if gen[u"model"] != list(GEN.MODELS) or gen[u"max_tokens"] != GEN.MAX_TOKENS:
        out.append(u"gen: model か max_tokens が script と違う")
    ish = GEN.instruction_shas()
    if gen[u"指示文の sha256"] != json.loads(json.dumps(ish)):
        out.append(u"gen: 指示文の sha256 が現物の定数と違う")
    if gen.get(u"記録の外の呼び出し") != json.loads(json.dumps(GEN.outside_calls())):
        out.append(u"gen: 記録の外の呼び出しが script の定数と違う")
    if gen.get(u"thinking") != dict((m, GEN.THINKING[m]) for m in GEN.MODELS):
        out.append(u"gen: thinking の欄が script の定数と違う")
    seen, total, n_ok = set(), 0.0, 0
    for c in gen[u"呼び出し"]:
        n = c[u"name"]
        if n != GEN.text_key(c[u"docID"], c[u"form"], c[u"model"]) or c[u"form"] not in GEN.FORMS or c[u"model"] not in GEN.MODELS or c[u"docID"] not in docs:
            out.append(u"gen: 呼び出しの名前・形・model・会社が規則に合わない")
            continue
        if c[u"writer"] != GEN.MODEL_TAG[c[u"model"]] or not (0 <= c[u"retries"] <= len(GEN.RETRY_WAITS)):
            out.append(u"gen: writer か retries がおかしい")
        if c[u"ok"]:
            n_ok += 1
            if GEN.is_current_ok(c):
                if n in seen:
                    out.append(u"gen: 現行の成功した呼び出しが同じ名前で 2 回ある")
                seen.add(n)
                if not isinstance(c.get(u"blocks"), list) or u"text" not in c[u"blocks"]:
                    out.append(u"gen: 現行の成功した呼び出しの blocks に text が無い")
            u = c[u"usage"]
            if not sha_ok(c[u"sha256"]) or not isinstance(c[u"chars"], int) or not (isinstance(u[u"input_tokens"], int) and isinstance(u[u"output_tokens"], int)):
                out.append(u"gen: 成功した呼び出しの欄がおかしい")
            elif abs(c[u"cost_usd"] - round(GEN.cost_usd(u[u"input_tokens"], u[u"output_tokens"]), 6)) > 1e-9:
                out.append(u"gen: 費用が usage と単価から作り直した値と違う")
            if u[u"output_tokens"] is not None and u[u"output_tokens"] > GEN.MAX_TOKENS:
                out.append(u"gen: 出力が max_tokens を超えている")
        else:
            u = c.get(u"usage")
            want = round(GEN.cost_usd(u[u"input_tokens"], u[u"output_tokens"]), 6) if u else 0.0
            if c[u"sha256"] is not None or abs(c[u"cost_usd"] - want) > 1e-9:
                out.append(u"gen: 失敗した呼び出しに sha256 がある。費用が usage と合わない")
            if u and not c.get(u"error"):
                out.append(u"gen: usage があるのに ok でない呼び出しに理由(error)が無い")
        total += c[u"cost_usd"]
    out += script_history_problems(gen)
    t = gen[u"累計"]
    if (t[u"呼び出しの数"], t[u"成功"], t[u"失敗"]) != (len(gen[u"呼び出し"]), n_ok, sum(1 for c in gen[u"呼び出し"] if not c[u"ok"])) or abs(t[u"費用 USD"] - round(total, 6)) > 1e-5:
        out.append(u"gen: 累計が呼び出しの行と合わない")
    if abs(t.get(u"記録の外の費用 USD", -1) - GEN.outside_cost()) > 1e-9 or abs(t.get(u"費用 USD 合計(記録の外を含む)", -1) - round(total + GEN.outside_cost(), 6)) > 1e-5 or t.get(u"現行の ok の本数") != len(seen):
        out.append(u"gen: 累計に記録の外の費用か現行の本数が入っていない")
    if total + GEN.outside_cost() > GEN.COST_CAP_USD + 1e-9:
        out.append(u"gen: 累計の費用(記録の外を含む)が上限を超えている")
    for m in gen.get(u"文の移動", []):
        old = [c for c in gen[u"呼び出し"] if c[u"name"] == m[u"name"] and c[u"ok"] and not GEN.is_current_ok(c) and c[u"sha256"] == m[u"sha256"]]
        if not old or m[u"移した先"] != GEN.SUPERSEDED_DIR + u"/" + m[u"name"] + u".txt":
            out.append(u"gen: 文の移動の行が現行でない ok の呼び出しと合わない(%s)" % m[u"name"])
    if full:
        stale_names = set(c[u"name"] for c in gen[u"呼び出し"] if c[u"ok"]) - seen
        if stale_names:
            out.append(u"gen: 現行の ok が無い本がある(作り直しが終わっていない)")
    if full and len(seen) > len(docs) * len(GEN.FORMS) * len(GEN.MODELS):
        out.append(u"gen: 成功が 160 を超えている")
    return out


def claims_problems(gen, claims, full):
    out = []
    ok = dict((c[u"name"], c) for c in gen[u"呼び出し"] if c[u"ok"])
    docs = gen[u"会社の選び"][u"docID"]
    if claims[u"欄"][u"claim"] != list(RUN.CLAIM_COLS) or claims[u"欄"][u"profile ごと"] != list(RUN.PROFILE_COLS) or claims[u"profile"] != list(RUN.PROFILES):
        out.append(u"claims: 欄か profile が script と違う")
    if claims[u"札付けの席の指示文の sha256"] != RUN.LABELLER_PROMPT_SHA256:
        out.append(u"claims: 札付けの席の指示文の sha256 が現物と違う")
    if full and claims[u"生成の記録の sha256"] != sha256_rel(REC_REL["gen"]):
        out.append(u"claims: 生成の記録の sha256 が現物と違う")
    if claims[u"engine の指紋"].get(u"git_commit") is None:
        out.append(u"claims: engine の指紋の commit が無い")
    names, keys = [], []
    allnames = [GEN.text_key(d, f, m) for d in docs for f in GEN.FORMS for m in GEN.MODELS]
    for b in claims[u"本"]:
        n = b[u"name"]
        names.append(n)
        if n not in allnames:
            out.append(u"claims: 規則にない本 %s" % n)
            continue
        if b.get(u"欠け"):
            if n in ok:
                out.append(u"claims: 生成できた本が欠けになっている")
            continue
        if n not in ok:
            out.append(u"claims: 生成できていない本に判定がある")
            continue
        if b[u"文の sha256"] != ok[n][u"sha256"] or b[u"字数"] != ok[n][u"chars"]:
            out.append(u"claims: 文の sha256 か字数が生成の記録と違う")
        if b[u"対応"] is not True:
            out.append(u"claims: 4 profile で claim の並びが合わない本がある")
        keys.append(b[u"札付けの束の鍵"])
        ids, cnt = set(), dict((p, collections.Counter()) for p in RUN.PROFILES)
        nnum = 0
        for raw in b[u"行"]:
            if len(raw) != len(RUN.CLAIM_COLS) + len(RUN.PROFILES):
                out.append(u"claims: 行の長さがおかしい")
                break
            d = RUN.decode_row(raw)
            if d[u"id"] in ids:
                out.append(u"claims: 同じ id が 2 回ある")
            ids.add(d[u"id"])
            nnum += 1 if d[u"kind"] == "num" else 0
            if d[u"lead"] is not None and d[u"lead"] not in list(RUN.LEADS) + [RUN.LEAD_OTHER]:
                out.append(u"claims: 行頭の語がおかしい")
            for p in RUN.PROFILES:
                c = d[p]
                if c is None:
                    out.append(u"claims: profile の欄が欠けている")
                    continue
                cnt[p][c[u"state"]] += 1
                if c[u"state"] not in RUN.STATES:
                    out.append(u"claims: state が語でない")
                if not RUN.reason_ok(c[u"reason"]):
                    out.append(u"claims: reason が符号の形でない")
                for ptr in c[u"pointers"]:
                    if ptr != u"(xbrl 以外)" and not re.fullmatch(r"[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+@(当期|前期|他)", ptr):
                        out.append(u"claims: pointers の字が形に合わない")
                if c[u"other_subject_2026_11_02"] is not None and (not isinstance(c[u"other_subject_2026_11_02"], list) or len(c[u"other_subject_2026_11_02"]) != 3):
                    out.append(u"claims: other_subject の欄の形がおかしい")
        if nnum != b[u"数の claim の数(P27)"] or len(b[u"行"]) != b[u"claim の数"]:
            out.append(u"claims: claim の数が行と合わない")
        for p in RUN.PROFILES:
            if dict((s, cnt[p].get(s, 0)) for s in RUN.STATES) != b[u"4 state"][p]:
                out.append(u"claims: 4 state が行から数えた値と違う")
    if len(set(names)) != len(names) or len(set(keys)) != len(keys):
        out.append(u"claims: 本の名前か鍵が重複している")
    if sorted(names) != sorted(allnames):
        out.append(u"claims: 本の一覧が 20 社 × 形 × model と違う")
    if sorted(claims[u"欠けた本"]) != sorted(n for n in allnames if n not in ok):
        out.append(u"claims: 欠けた本の一覧が生成の記録と違う")
    s2 = claims[u"2 席目を立てる本"]
    present = [n for n in allnames if n in ok]
    if s2 != sorted(s2) or not set(s2) <= set(present) or len(s2) != min(GEN.SEAT2_N, len(present)):
        out.append(u"claims: 2 席目の本の数・並びがおかしい")
    try:
        if full and s2 != RUN.seat2_names(present, GEN.jload(os.path.join(ROOT, GEN.SEED_REL))["seed"]):
            out.append(u"claims: 2 席目の本が種から引き直した 32 本と違う")
    except Exception as e:                           # noqa: BLE001
        out.append(u"claims: 2 席目の本を引き直せない(%s)" % type(e).__name__)
    return out


def num_ids(claims):
    d = collections.OrderedDict()
    for b in claims[u"本"]:
        if b.get(u"欠け"):
            continue
        d[b[u"name"]] = [r[0] for r in b[u"行"] if r[1] == "num"]
    return d


def labels_problems(claims, labels, full):
    out = []
    ids = num_ids(claims)
    s2 = set(claims[u"2 席目を立てる本"])
    if labels[u"札付けの席の指示文の sha256"] != RUN.LABELLER_PROMPT_SHA256:
        out.append(u"labels: 指示文の sha256 が現物と違う")
    if full and labels[u"判定の記録の sha256"] != sha256_rel(REC_REL["claims"]):
        out.append(u"labels: 判定の記録の sha256 が現物と違う")
    if labels[u"語"][u"札"] != list(RUN.LABEL_WORDS) or labels[u"語"][u"誤りの型"] != list(RUN.ERROR_TYPES) or labels[u"語"][u"確信"] != list(RUN.CONFIDENCE):
        out.append(u"labels: 語が script と違う")
    names = []
    for b in labels[u"本"]:
        n = b[u"name"]
        names.append(n)
        if n not in ids or [r[0] for r in b[u"札"]] != ids[n]:
            out.append(u"labels: 札の id が判定の記録の数の claim と 1 対 1 でない")
            continue
        for r in b[u"札"]:
            if len(r) != 5:
                out.append(u"labels: 札の行の長さがおかしい")
                continue
            _id, word, etype, conf, els = r
            if word not in RUN.LABEL_WORDS or conf not in RUN.CONFIDENCE or (word == u"偽") != (etype is not None) or (etype is not None and etype not in RUN.ERROR_TYPES):
                out.append(u"labels: 札・誤りの型・確信の語がおかしい")
            if not isinstance(els, list) or any(not re.fullmatch(r"[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+", x) for x in els):
                out.append(u"labels: 根拠の要素名の形がおかしい")
        if (n in s2) != (u"2 席目" in b):
            out.append(u"labels: 2 席目の有無が 2 席目を立てる本の一覧と違う")
        if u"2 席目" in b:
            if [r[0] for r in b[u"2 席目"]] != ids[n]:
                out.append(u"labels: 2 席目の id が 1 対 1 でない")
            if not sha_ok(b.get(u"seat2 の sha256")):
                out.append(u"labels: seat2 の sha256 がおかしい")
        if not sha_ok(b.get(u"seat1 の sha256")):
            out.append(u"labels: seat1 の sha256 がおかしい")
    if full and sorted(names) != sorted(ids):
        out.append(u"labels: 本の一覧が判定の記録の本と違う")
    if LAB.tally_labels(labels[u"本"]) != json.loads(json.dumps(labels[u"集計"][u"札の分布"])):
        out.append(u"labels: 札の分布が行から作り直した値と違う")
    if LAB.agreement(labels[u"本"]) != json.loads(json.dumps(labels[u"集計"][u"2 席目との一致"])):
        out.append(u"labels: 2 席目との一致が行から作り直した値と違う")
    return out


def inject_problems(claims, inj):
    out = []
    by_name = {}
    for b in claims[u"本"]:
        if b.get(u"欠け"):
            continue
        by_name[b[u"name"]] = dict((r[0], RUN.decode_row(r)) for r in b[u"行"])
    if inj[u"profile"] != list(RUN.PROFILES):
        out.append(u"inject: profile が違う")
    cnt = collections.Counter()
    seen = set()
    for r in inj[u"行"]:
        name = GEN.text_key(r[u"docID"], r[u"form"], r[u"model"])
        if name not in by_name or r[u"writer"] != GEN.MODEL_TAG.get(r[u"model"]):
            out.append(u"inject: 行の本が判定の記録にない")
            continue
        if r[u"型"] not in RUN.INJECT_TYPES:
            out.append(u"inject: 型が語でない")
        if r[u"id"] in seen:
            out.append(u"inject: 同じ注入の id が 2 回ある")
        seen.add(r[u"id"])
        cnt[(name, r[u"型"])] += 1
        base = by_name[name].get(r[u"基準の claim"])
        if base is None or any(base[p] is None or base[p][u"state"] != "GROUNDED" for p in RUN.PROFILES):
            out.append(u"inject: 土台の claim が 4 profile 全部 GROUNDED でない")
        if r[u"型"] == "T8_REL" and (r.get("r") not in RUN.TUNE.T8_R_VALUES or not (1 <= r[u"r を決めた回"] <= RUN.TUNE.T8_TRIES)):
            out.append(u"inject: T8_REL の r が決めた値でない")
        for p in RUN.PROFILES:
            c = r[p]
            if c[u"結果"] not in (RUN.TUNE.LABEL_PASS, RUN.TUNE.LABEL_NAMED_ORIGINAL, RUN.TUNE.LABEL_NAMED_OTHER, RUN.TUNE.LABEL_PNF, RUN.TUNE.LABEL_UNV, RUN.TUNE.LABEL_UNMAPPED):
                out.append(u"inject: 結果が classify の語でない")
            if not RUN.reason_ok(c[u"reason"]):
                out.append(u"inject: reason が符号の形でない")
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたり型ごとの上限 %d を超えている" % RUN.INJECT_CAP)
    if json.loads(json.dumps(RUN.inject_summary(inj[u"行"]))) != inj[u"集計"] or inj[u"注入の行の数"] != len(inj[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    return out


def tally_problems(R, scripts, check_input_sha=False):
    out = []
    T = R["tally"]
    if check_input_sha:
        for k, rel in TAL.REC_REL.items():
            if T[u"入力の記録の sha256"].get(k) != sha256_rel(rel):
                out.append(u"tally: 入力の記録 %s の sha256 が現物と違う" % k)
    try:
        built = TAL.build(R)
        J = TAL.judge(built)
    except Exception as e:                           # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"tally: 記録から集計を作れない(%s)" % type(e).__name__]
    if json.loads(json.dumps(built)) != T[u"集計"]:
        out.append(u"tally: 集計が記録から作り直した値と違う")
    if json.loads(json.dumps(J)) != T[u"予測の判定"]:
        out.append(u"tally: 予測の判定が記録から作り直した判定と違う")
    c = collections.Counter(v[u"判定"] for v in J.values())
    if (T[u"当たり"], T[u"外れ"], T[u"判定しない"]) != (c.get(HIT, 0), c.get(MISS, 0), c.get(NOJ, 0)):
        out.append(u"tally: 当たり・外れの数が判定と違う")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R):
    J = TAL.judge(TAL.build(R))
    want = TAL.render_table(J).split(u"\n")
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != want:
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


# ---------------------------------------------------------------- 順序(e)
def order_of(root, impl=None, others=None):
    impl = list(SCRIPT_REL.values()) if impl is None else impl
    others = (list(REC_REL.values()) + [DOC_REL] + list(GATE_FILES)) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, impl, others)


# ================================================================ 偽の流れ(g)
def fake_transport_factory(calls, scripted=None):
    u"""偽の書き手。prompt の表から行を拾って、形ごとの見かけの文を返す。scripted = 先に返す (status, body) の列。"""
    scripted = list(scripted or [])

    def transport(prompt, model, key):
        calls.append((model, len(prompt)))
        if scripted:
            return scripted.pop(0)
        return 200, fake_body(prompt)
    return transport


def fake_body(prompt, tin=None, tout=None, stop="end_turn"):
    rows = []
    for ln in prompt.split("\n"):
        if ln.startswith("| ") and "JPY" in ln and "時点" not in ln:
            c = [x.strip() for x in ln.strip("|").split("|")]
            if len(c) >= 5 and c[1]:
                rows.append((c[1], float(c[2])))
    seen, uniq = set(), []
    for lab, v in rows:                                   # 同じ値の数が何度も出ると注入の土台(値で 1 件に決まる claim)が作れない = 値の違う行だけ使う
        r = round(v / 1e6)
        if r not in seen and r > 0:
            seen.add(r)
            uniq.append((lab, v))
    rows = uniq[:24]
    if u"Q&A" in prompt:
        lines = []
        for lab, v in rows[:6]:
            lines += [u"Q: %sはいくらですか。" % lab, u"A: %s は %s 百万円です。" % (lab, format(round(v / 1e6), ","))]
    elif u"表と注記" in prompt:
        lines = [u"| 項目 | 当期 | 前期 | 増減 |", u"|---|---|---|---|"] + [u"| %s | %s 百万円 | - | - |" % (lab, format(round(v / 1e6), ",")) for lab, v in rows[:6]]
        lines += [u"%s は %s 百万円でした。" % (lab, format(round(v / 1e6), ",")) for lab, v in rows[6:12]]
    elif u"箇条書き" in prompt:
        lines = [u"・%s は %s 百万円でした。" % (lab, format(round(v / 1e6), ",")) for lab, v in rows[:14]]
    else:
        lines = [u"経営成績"] + [u"%s は %s 百万円でした。" % (lab, format(round(v / 1e6), ",")) for lab, v in rows[:10]]
    text = u"\n".join(lines)
    return json.dumps({"content": [{"type": "text", "text": text}],
                       "usage": {"input_tokens": len(prompt) if tin is None else tin, "output_tokens": len(text) if tout is None else tout},
                       "stop_reason": stop}).encode("utf-8")


class Patch(object):
    u"""module の属性を差し替えて、終わりに戻す(試験の入れ物)。"""

    def __init__(self):
        self.saved = []

    def set(self, mod, name, value):
        self.saved.append((mod, name, getattr(mod, name)))
        setattr(mod, name, value)

    def undo(self):
        for mod, name, old in reversed(self.saved):
            setattr(mod, name, old)
        self.saved = []


def gen_instances():
    u"""gen の module の実体は、他の script が importlib で別に読んでいる(差し替えは使う側の実体に届かないと黙って効かない)。全部の実体。"""
    seen, out = set(), []
    for mod in (GEN, RUN, LAB, TAL, RUN.GEN, LAB.GEN, LAB.RUN, TAL.GEN, TAL.RUN, TAL.LAB):
        g = mod if hasattr(mod, "WRITER_FORMS") else getattr(mod, "GEN", None)
        if g is not None and id(g) not in seen:
            seen.add(id(g))
            out.append(g)
    return out


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class GenBehaviourTest(unittest.TestCase):
    u"""(b) 生成の振る舞い。偽の transport。通信しない。"""

    @classmethod
    def setUpClass(cls):
        seed, cls.seed_meta = GEN.seed_value(ROOT)
        cls.chosen, cls.counts = GEN.select_companies(ROOT, seed)
        cls.one = cls.chosen[:1]
        cls.doc = cls.one[0]["docID"]

    def setUp(self):
        self.p = Patch()
        self.p.set(GEN, "select_companies", lambda root, seed=None: (self.one, self.counts))
        self.tmp = tempfile.mkdtemp(prefix="aiforms_gen_", dir=os.environ.get("TMPDIR"))
        self.out = os.path.join(self.tmp, "gen.json")
        self.cache = os.path.join(self.tmp, "cache")
        os.environ.pop(GEN.KEY_ENV, None)

    def tearDown(self):
        self.p.undo()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop(GEN.KEY_ENV, None)

    def go(self, transport, key="SECRETKEY-aaaaaaaaaaaaaaaaaaaa", resume=False, dry_run=False, **kw):
        if key is not None:
            os.environ[GEN.KEY_ENV] = key
        return GEN.run(root=ROOT, dry_run=dry_run, only=None if dry_run else self.doc, resume=resume, out=self.out, new_cache=self.cache, key_value=key,
                       transport=transport, sleep=kw.get("sleep", lambda s: None), say=lambda *a: None)

    def test_b_1_dry_run_never_calls_and_writes_no_record(self):
        calls = []
        r = self.go(fake_transport_factory(calls), dry_run=True)
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(8, r["jobs"])

    def test_b_2_an_estimate_over_the_cap_calls_nothing(self):
        calls = []
        self.p.set(GEN, "COST_CAP_USD", 0.5)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls))
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))

    def test_b_3_cumulative_plus_next_estimate_over_the_cap_stops_and_keeps_the_record(self):
        calls = []
        self.p.set(GEN, "COST_CAP_USD", 5.0)

        def tr(prompt, model, key):
            calls.append(model)
            return 200, fake_body(prompt, tin=0, tout=120000)          # 1 回 3 USD
        with self.assertRaises(GEN.Stop):
            self.go(tr)
        self.assertEqual(2, len(calls))                                  # 3 → (3 + 見積り < 5 で 2 回目を呼ぶ) 6 → 3 回目の前で止まる
        rec = json.load(open(self.out, encoding="utf-8"))
        self.assertEqual(2, rec[u"累計"][u"呼び出しの数"])
        self.assertIsNotNone(rec[u"止めた理由"])

    def test_b_4_retries_only_on_429_or_5xx_at_most_twice(self):
        calls, waits = [], []
        sc = [(429, b"{}"), (503, b"{}")]
        self.go(fake_transport_factory(calls, sc), sleep=waits.append)
        rec = json.load(open(self.out, encoding="utf-8"))
        first = rec[u"呼び出し"][0]
        self.assertEqual((2, True), (first[u"retries"], first[u"ok"]))
        self.assertEqual([2, 8], waits[:2])
        # 3 回続けて 5xx なら失敗として記録(再試行は 2 回まで)して次へ
        self.tearDown()
        self.setUp()
        calls2 = []
        self.go(fake_transport_factory(calls2, [(500, b"{}")] * 3))
        rec2 = json.load(open(self.out, encoding="utf-8"))
        self.assertFalse(rec2[u"呼び出し"][0][u"ok"])
        self.assertEqual(2, rec2[u"呼び出し"][0][u"retries"])
        self.assertEqual(3 + 7, len(calls2))
        # 400 は再試行しない
        self.tearDown()
        self.setUp()
        calls3 = []
        self.go(fake_transport_factory(calls3, [(400, b"{}")]))
        rec3 = json.load(open(self.out, encoding="utf-8"))
        self.assertEqual((False, 0), (rec3[u"呼び出し"][0][u"ok"], rec3[u"呼び出し"][0][u"retries"]))
        self.assertEqual(8, len(calls3))

    def test_b_5_401_stops_everything(self):
        calls = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls, [(401, b"{}")]))
        self.assertEqual(1, len(calls))

    def test_b_6_the_key_never_reaches_the_record(self):
        key = "SECRETKEY-bbbbbbbbbbbbbbbbbbbb"
        calls = []
        self.go(fake_transport_factory(calls, [(500, key.encode())] * 3), key=key)
        self.assertNotIn(key, open(self.out, encoding="utf-8").read())
        self.assertEqual([], GEN.key_leaks(open(self.out, encoding="utf-8").read(), key, long_alnum=False))

    def test_b_7_no_key_means_no_call(self):
        calls = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), key=None)
        self.assertEqual([], calls)

    def test_b_8_existing_text_is_not_called_twice_without_resume(self):
        calls = []
        self.go(fake_transport_factory(calls))
        n = len(calls)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls))
        self.assertEqual(n, len(calls))
        self.go(fake_transport_factory(calls), resume=True)          # 全部在るので何も呼ばない
        self.assertEqual(n, len(calls))
        # 文は在るが記録に ok が無い(記録が壊れた)なら、二度呼ばずに止める(費用の記録を失わない)
        rec = json.load(open(self.out, encoding="utf-8"))
        dropped = rec[u"呼び出し"].pop(0)
        GEN.write_text(self.out, GEN.dumps(rec))
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual(n, len(calls))
        # 記録の sha256 と文が合わないときも止める
        rec[u"呼び出し"].insert(0, dropped)
        GEN.write_text(self.out, GEN.dumps(rec))
        with open(os.path.join(self.cache, "texts", dropped[u"name"] + ".txt"), "a", encoding="utf-8") as fh:
            fh.write(u"改ざん")
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual(n, len(calls))

    def test_b_9_usage_and_cost_come_from_the_api_not_the_estimate(self):
        calls = []
        self.go(fake_transport_factory(calls))
        rec = json.load(open(self.out, encoding="utf-8"))
        for c in rec[u"呼び出し"]:
            self.assertTrue(c[u"ok"])
            self.assertAlmostEqual(c[u"cost_usd"], GEN.cost_usd(c[u"usage"][u"input_tokens"], c[u"usage"][u"output_tokens"]), places=6)
        self.assertEqual([], gen_problems(rec, False, ROOT))


def thinking_body(prompt, text=u"新しい文", tin=26435, tout=1326, stop="end_turn", blocks=("thinking", "text")):
    u"""5.5 の model の返事の形(thinking の block + text の block)。blocks に text が無ければ text なし。"""
    content = []
    for b in blocks:
        content.append({"type": "thinking", "thinking": u""} if b == "thinking" else {"type": "text", "text": text})
    return json.dumps({"content": content, "usage": {"input_tokens": tin, "output_tokens": tout}, "stop_reason": stop}).encode("utf-8")


class FakeResponse(object):
    def __init__(self, status=200, body=b"{}"):
        self.status, self.body = status, body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def getcode(self):
        return self.status

    def read(self):
        return self.body


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class ThinkingTest(unittest.TestCase):
    u"""(th) 2026-11-03 の直し: 思考の指定・text 0 字は ok にしない・作り直し・記録の外の費用。偽の transport / 偽の urlopen。通信しない。"""

    @classmethod
    def setUpClass(cls):
        seed, cls.seed_meta = GEN.seed_value(ROOT)
        cls.chosen, cls.counts = GEN.select_companies(ROOT, seed)
        cls.one = cls.chosen[:1]
        cls.doc = cls.one[0]["docID"]

    def setUp(self):
        self.p = Patch()
        self.p.set(GEN, "select_companies", lambda root, seed=None: (self.one, self.counts))
        self.tmp = tempfile.mkdtemp(prefix="aiforms_th_", dir=os.environ.get("TMPDIR"))
        self.out = os.path.join(self.tmp, "gen.json")
        self.cache = os.path.join(self.tmp, "cache")
        os.environ.pop(GEN.KEY_ENV, None)

    def tearDown(self):
        self.p.undo()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop(GEN.KEY_ENV, None)

    def go(self, transport, key="SECRETKEY-aaaaaaaaaaaaaaaaaaaa", resume=False, dry_run=False, only="default", head=None):
        os.environ[GEN.KEY_ENV] = key
        only = (None if dry_run else self.doc) if only == "default" else only
        return GEN.run(root=ROOT, dry_run=dry_run, only=only, resume=resume, out=self.out, new_cache=self.cache, key_value=key,
                       transport=transport, sleep=lambda s: None, say=lambda *a: None, head=head)

    def rec(self):
        return json.load(open(self.out, encoding="utf-8"))

    def put(self, rec):
        GEN.write_text(self.out, GEN.dumps(rec))

    def texts(self, sub="texts"):
        d = os.path.join(self.cache, sub)
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    def test_th_1_the_thinking_literal_per_model(self):
        self.assertEqual({"claude-sonnet-5-5": {"type": "between_tools"}, "claude-haiku-5-5": {"type": "disabled"}}, GEN.THINKING)
        self.assertEqual((4000, "2023-06-01", "https://api.anthropic.com/v1/messages"), (GEN.MAX_TOKENS, GEN.API_VERSION, GEN.API_URL))
        self.assertEqual(set(GEN.MODELS), set(GEN.THINKING))

    def test_th_2_the_thinking_goes_into_the_request_body(self):
        sent = []

        def fake_urlopen(req, timeout=None):
            sent.append((req.full_url, json.loads(req.data.decode("utf-8"))))
            return FakeResponse(200, b"{}")
        self.p.set(urllib.request, "urlopen", fake_urlopen)
        for model, want in (("claude-sonnet-5-5", {"type": "between_tools"}), ("claude-haiku-5-5", {"type": "disabled"})):
            self.assertEqual((200, b"{}"), GEN.call_api(u"問い", model, "KEY-not-a-secret"))
            url, body = sent[-1]
            self.assertEqual("https://api.anthropic.com/v1/messages", url)
            self.assertEqual(want, body["thinking"])
            self.assertEqual((model, 4000, [{"role": "user", "content": u"問い"}]), (body["model"], body["max_tokens"], body["messages"]))

    def test_th_3_text_of_zero_chars_is_not_ok_and_the_cost_stays(self):
        calls = []

        def tr(prompt, model, key):
            calls.append(model)
            if len(calls) == 1:                                    # 思考の block だけで text なし・max_tokens
                return 200, thinking_body(prompt, tin=26437, tout=4000, stop="max_tokens", blocks=("thinking",))
            return 200, thinking_body(prompt, text=u"文 %d" % len(calls))
        self.go(tr)
        rec = self.rec()
        first, second = rec[u"呼び出し"][0], rec[u"呼び出し"][1]
        self.assertFalse(first[u"ok"])
        self.assertIn(u"0 字", first[u"error"])
        self.assertEqual((["thinking"], 0, None, "max_tokens", GEN.THINKING[first[u"model"]]), (first[u"blocks"], first[u"chars"], first[u"sha256"], first[u"stop_reason"], first[u"thinking"]))
        self.assertAlmostEqual(0.232185, first[u"cost_usd"], places=6)          # usage どおり(26437 × 5 + 4000 × 25)/ 1e6
        self.assertNotIn(first[u"name"] + ".txt", self.texts())
        self.assertTrue(second[u"ok"])
        self.assertEqual((["thinking", "text"], GEN.THINKING[second[u"model"]]), (second[u"blocks"], second[u"thinking"]))
        self.assertEqual(7, len(self.texts()))
        self.assertEqual([], gen_problems(rec, False, ROOT))
        # 続きでは ok でなかった本をもう一度呼ぶ(文が無いので二度呼びの止めに当たらない)
        n = len(calls)
        self.go(tr, resume=True)
        self.assertEqual(n + 1, len(calls))
        self.assertEqual(8, len(self.texts()))
        self.assertEqual([], gen_problems(self.rec(), False, ROOT))

    def make_legacy(self):
        u"""8 本を作り、呼び出しのうち 0 番目の thinking を消し(古い記録)、3 番目の thinking を今の指定と違う値にする。"""
        calls = []
        self.go(fake_transport_factory(calls))
        rec = self.rec()
        a, b = rec[u"呼び出し"][0], rec[u"呼び出し"][3]
        del a[u"thinking"]
        b[u"thinking"] = {"type": "disabled"} if b[u"model"] == "claude-sonnet-5-5" else {"type": "between_tools"}
        self.put(rec)
        return rec, a, b

    def test_th_4_a_stale_ok_is_rebuilt_and_its_text_is_moved_before_the_call(self):
        rec0, a, b = self.make_legacy()
        self.assertEqual(8, len(self.texts()))
        self.assertEqual(6, len(GEN.current_ok_by_name(rec0[u"呼び出し"])))
        before_cost = GEN.recorded_cost(rec0)
        seen = []

        def tr(prompt, model, key):
            i = len(seen)
            on_disk = self.rec()
            seen.append(1)
            # 呼ぶ前に: 古い文は texts から texts_superseded へ移り済み、移した事実は記録に書き済み
            if len(self.texts()) != 7 or len(self.texts("texts_superseded")) != i + 1 or len(on_disk[u"文の移動"]) != i + 1:
                raise AssertionError("移動が呼ぶ前に済んでいない")
            return 200, thinking_body(prompt, text=u"新しい文 %d" % i)
        self.go(tr, resume=True)
        self.assertEqual(2, len(seen))
        rec = self.rec()
        self.assertEqual(10, len(rec[u"呼び出し"]))                                # 古い 8 つは残る
        self.assertEqual(sorted([a[u"name"], b[u"name"]]), sorted(self.texts("texts_superseded")[i][:-4] for i in range(2)))
        self.assertEqual(sorted([a[u"name"], b[u"name"]]), sorted(m[u"name"] for m in rec[u"文の移動"]))
        for m in rec[u"文の移動"]:
            moved = io.open(os.path.join(self.cache, "texts_superseded", m[u"name"] + ".txt"), encoding="utf-8").read()
            self.assertEqual(m[u"sha256"], GEN.sha256_text(moved))                    # 消さずに移した(中身が古い呼び出しの sha256 と同じ)
            self.assertTrue(os.path.exists(os.path.join(self.cache, "texts", m[u"name"] + ".txt")))
        cur = GEN.current_ok_by_name(rec[u"呼び出し"])
        self.assertEqual(8, len(cur))
        for n in (a[u"name"], b[u"name"]):
            self.assertEqual(GEN.THINKING[cur[n][u"model"]], cur[n][u"thinking"])
            self.assertNotEqual((a if n == a[u"name"] else b)[u"sha256"], cur[n][u"sha256"])
        self.assertEqual(8, len(self.texts()))
        # 古い呼び出しの cost_usd は累計と上限の計算に入ったまま
        t = rec[u"累計"]
        self.assertAlmostEqual(before_cost + sum(c[u"cost_usd"] for c in rec[u"呼び出し"][8:]), GEN.recorded_cost(rec), places=6)
        self.assertEqual((10, 10, 8, 2), (t[u"呼び出しの数"], t[u"成功"], t[u"現行の ok の本数"], t[u"現行でない ok の呼び出し"]))
        self.assertEqual([], gen_problems(rec, False, ROOT))
        n = []
        self.go(lambda prompt, model, key: n.append(1) or (200, thinking_body(prompt)), resume=True)          # 全部現行 = 何も呼ばない
        self.assertEqual([], n)

    def test_th_5_a_stale_text_that_does_not_match_the_record_stops_with_no_move_and_no_call(self):
        rec0, a, b = self.make_legacy()
        with open(os.path.join(self.cache, "texts", a[u"name"] + ".txt"), "a", encoding="utf-8") as fh:
            fh.write(u"改ざん")
        calls = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual([], calls)
        self.assertEqual([], self.texts("texts_superseded"))
        # 記録に ok が無い本の文は、古くなった ok も無いので二度呼ばずに止める
        rec = self.rec()
        rec[u"呼び出し"] = [c for c in rec[u"呼び出し"] if c[u"name"] != b[u"name"]]
        self.put(rec)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual([], calls)

    def test_th_6_before_any_call_recorded_cost_plus_remaining_estimate_over_the_cap_stops(self):
        rec0, a, b = self.make_legacy()
        recorded = GEN.recorded_cost(rec0)
        self.p.set(GEN, "COST_CAP_USD", recorded + a[u"est_usd"] + b[u"est_usd"] / 2.0)      # 1 本目までは入るが 2 本合わせると超える
        calls = []
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual([], calls)                                                          # 1 回も呼ばない
        self.assertEqual([], self.texts("texts_superseded"))                                 # 文も動かさない
        self.assertEqual(8, len(self.texts()))
        self.assertEqual(rec0[u"呼び出し"], self.rec()[u"呼び出し"])

    def test_th_7_the_outside_calls_are_written_from_the_constants_and_enter_the_total(self):
        calls = []
        self.go(fake_transport_factory(calls))
        rec = self.rec()
        out = rec[u"記録の外の呼び出し"]
        self.assertEqual(["1-a", "1-b", "1-c", "1-d", "2-a", "2-b", "2-c"], [c[u"番号"] for c in out])
        by = dict((c[u"番号"], c) for c in out)
        self.assertEqual((400, None, 0.0), (by["1-d"][u"http_status"], by["1-d"][u"usage"], by["1-d"][u"cost_usd"]))      # HTTP 400 は費用なし
        self.assertEqual({"input_tokens": 26437, "output_tokens": 4000}, by["2-a"][u"usage"])
        self.assertAlmostEqual(0.232185, by["2-a"][u"cost_usd"], places=6)
        self.assertAlmostEqual(0.165325, by["2-b"][u"cost_usd"], places=6)
        self.assertAlmostEqual(0.19425, by["2-c"][u"cost_usd"], places=6)
        self.assertAlmostEqual(0.59495, GEN.outside_cost(), places=6)
        t = rec[u"累計"]
        self.assertAlmostEqual(0.59495, t[u"記録の外の費用 USD"], places=6)
        self.assertAlmostEqual(t[u"費用 USD"] + 0.59495, t[u"費用 USD 合計(記録の外を含む)"], places=5)
        # 記録に書かれた値を信じない: 書き換えた記録でも次に書くとき定数に戻る
        rec[u"記録の外の呼び出し"] = []
        self.put(rec)
        self.go(fake_transport_factory(calls), resume=True)
        self.assertEqual(json.loads(json.dumps(GEN.outside_calls())), self.rec()[u"記録の外の呼び出し"])

    def test_th_8_the_outside_cost_counts_for_the_cap_before_and_during_the_run(self):
        calls = []
        r = self.go(fake_transport_factory(calls), dry_run=True)
        est_total = r["est_usd"]
        # 走らせる前: 見積りだけなら入るが、記録の外を足すと超える
        self.p.set(GEN, "COST_CAP_USD", est_total + GEN.outside_cost() / 2.0)
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory(calls))
        self.assertEqual([], calls)
        self.assertFalse(os.path.exists(self.out))
        self.p.undo()
        self.tearDown()
        self.setUp()
        # 走っている間: 1 本目の費用 c1(見積りの合計より大きい)。記録の外を数えなければ 2 本目の前の累計 + 見積りは上限に入ってしまう
        probe = []
        self.go(fake_transport_factory(probe))
        ests = [c[u"est_usd"] for c in self.rec()[u"呼び出し"]]
        self.tearDown()
        self.setUp()
        c1 = est_total + 1.0
        self.p.set(GEN, "COST_CAP_USD", c1 + ests[1] + GEN.outside_cost() / 2.0)
        n = []

        def tr(prompt, model, key):
            n.append(1)
            return 200, thinking_body(prompt, tin=0, tout=int(round(c1 / GEN.PRICE_OUT * 1e6)))
        with self.assertRaises(GEN.Stop):
            self.go(tr)
        self.assertEqual(1, len(n))
        self.assertIsNotNone(self.rec()[u"止めた理由"])

    def test_th_9_run_and_tally_read_only_the_last_current_ok_per_name(self):
        def call(name, model, ok, thinking, sha, chars, cost=0.5, stop="end_turn"):
            return {"name": name, "docID": "S100AAAA", "form": "F1", "model": model, "ok": ok, "thinking": thinking, "sha256": sha, "chars": chars,
                    "cost_usd": cost, "stop_reason": stop, "retries": 0, "usage": {"input_tokens": 1, "output_tokens": 1}}
        h, s_ = "claude-haiku-5-5", "claude-sonnet-5-5"
        good_h, good_s = GEN.THINKING[h], GEN.THINKING[s_]
        calls = [call("S100AAAA_F1_" + h, h, True, None, "a" * 64, 100),                         # 古い(thinking の欄なし)
                 call("S100AAAA_F1_" + h, h, True, good_h, "b" * 64, 200),                        # 現行
                 call("S100AAAA_F1_" + h, h, True, good_h, "e" * 64, 250),                        # 現行(同じ名前でもう 1 つ = こちらが最後)
                 call("S100AAAA_F1_" + s_, s_, True, {"type": "disabled"}, "c" * 64, 300),        # 今の指定と違う = 古い。これしか無い
                 call("S100AAAA_F2_" + h, h, True, good_h, "d" * 64, 0)]                           # text 0 字 = 現行でない
        calls[3]["name"] = "S100AAAA_F2_" + h
        gen = {u"呼び出し": calls, u"会社の選び": {u"docID": ["S100AAAA"]}}
        cur = GEN.current_ok_by_name(calls)
        self.assertEqual(["S100AAAA_F1_" + h], list(cur))
        self.assertEqual("e" * 64, cur["S100AAAA_F1_" + h][u"sha256"])                           # 名前ごとに最後の現行
        self.assertEqual(list(cur), list(RUN.gen_items(gen)))
        w = TAL.sec_wiring({"gen": gen, "claims": {u"本": []}})
        self.assertEqual(1, w[u"生成できた本"])
        self.assertEqual(0, w[u"max_tokens で打ち切られた本"])
        self.assertEqual(2.5, w[u"費用 USD(記録の cost_usd の合計)"])                              # 古い呼び出しの費用は残る
        self.assertAlmostEqual(0.59495, w[u"記録の外の費用 USD(司令塔の確かめ。上の費用に含まない)"], places=6)

    def test_th_10_a_rebuild_flow_record_passes_the_record_checks_and_keeps_the_script_history(self):
        # 古い script が作った記録(script_sha256 の欄なし・script の sha256 と HEAD は別の値)を、今の script で作り直す。本番と同じ形に record_problems を当てる
        rec0, a, b = self.make_legacy()
        rec = self.rec()
        old_sha, old_head = "3fc95b6d" + "0" * 56, "6c08572" + "0" * 33
        rec[u"この script の sha256"], rec[u"HEAD の commit"] = old_sha, old_head
        for c in rec[u"呼び出し"]:
            c.pop(u"script_sha256", None)
        rec.pop(u"script の履歴", None)
        rec.pop(u"文の移動", None)
        self.put(rec)
        self.go(lambda prompt, model, key: (200, thinking_body(prompt, text=u"新しい文")), resume=True, head="a" * 40)
        rec = self.rec()
        now = GEN.sha256_file(os.path.abspath(GEN.__file__))
        self.assertEqual((now, "a" * 40), (rec[u"この script の sha256"], rec[u"HEAD の commit"]))                  # 記録の上の欄 = 最後の script
        self.assertEqual([{"sha256": old_sha, "HEAD": old_head, "呼び出しの番号の範囲": [1, 8]}], rec[u"script の履歴"])
        self.assertEqual([None] * 8 + [now[:16]] * 2, [c.get(u"script_sha256") for c in rec[u"呼び出し"]])
        self.assertEqual(2, len(rec[u"文の移動"]))
        for m in rec[u"文の移動"]:
            self.assertEqual(set([u"name", u"sha256", u"移した先", u"移した訳"]), set(m))
        self.assertEqual([], record_problems({"gen": rec}, full=False, root=ROOT))
        # もう一度(同じ script・同じ HEAD)呼ぶ回では履歴を増やさない
        rec[u"呼び出し"][1][u"thinking"] = {"type": "other"}                                     # もう 1 本古い ok にして再び呼ばせる
        self.put(rec)
        self.go(lambda prompt, model, key: (200, thinking_body(prompt, text=u"さらに新しい文")), resume=True, head="a" * 40)
        rec2 = self.rec()
        self.assertEqual(rec[u"script の履歴"], rec2[u"script の履歴"])
        self.assertEqual([], record_problems({"gen": rec2}, full=False, root=ROOT))
        # 履歴の形が壊れた記録・script_sha256 が合わない記録は赤
        bad = json.loads(json.dumps(rec2))
        bad[u"script の履歴"][0][u"呼び出しの番号の範囲"] = [2, 8]
        self.assertTrue(any(u"途切れず" in x for x in record_problems({"gen": bad}, full=False, root=ROOT)))
        bad = json.loads(json.dumps(rec2))
        bad[u"呼び出し"][-1][u"script_sha256"] = u"0" * 16
        self.assertTrue(any(u"script_sha256" in x for x in record_problems({"gen": bad}, full=False, root=ROOT)))
        bad = json.loads(json.dumps(rec2))
        bad[u"この script の sha256"] = old_sha
        self.assertTrue(any(u"現物と違う" in x for x in record_problems({"gen": bad}, full=False, root=ROOT)))

    def test_th_11_the_stop_before_a_call_is_at_the_boundary_cum_plus_estimate(self):
        calls = []
        est_total = self.go(fake_transport_factory(calls), dry_run=True)["est_usd"]
        probe = []
        self.go(fake_transport_factory(probe))
        ests = [c[u"est_usd"] for c in self.rec()[u"呼び出し"]]
        self.tearDown()
        self.setUp()
        tout = int(est_total * 1e6 / GEN.PRICE_OUT) + 40000                              # 1 本 est_total より大きい費用
        cum1 = GEN.outside_cost() + tout * GEN.PRICE_OUT / 1e6
        for delta, want in ((-0.0005, 1), (+0.0005, 2)):                                  # 累計 ≤ 上限 < 累計 + 次の見積り なら止まる / 見積りぎりぎり入るなら呼ぶ
            n = []
            self.p.set(GEN, "COST_CAP_USD", cum1 + ests[1] + delta)

            def tr(prompt, model, key):
                n.append(1)
                return 200, thinking_body(prompt, tin=0, tout=tout)
            with self.assertRaises(GEN.Stop):
                self.go(tr)
            self.assertEqual(want, len(n), delta)
            self.p.undo()
            self.tearDown()
            self.setUp()

    def test_th_12_the_stale_ok_to_move_is_the_last_ok_of_the_name(self):
        rec0, a, b = self.make_legacy()
        rec = self.rec()
        older = json.loads(json.dumps(rec[u"呼び出し"][0]))
        older[u"sha256"] = u"f" * 64                                                        # 同じ名前のもっと古い ok(文の sha256 はこちらと合わない)
        rec[u"呼び出し"].insert(0, older)
        self.put(rec)
        self.assertEqual(a[u"sha256"], GEN.last_stale_ok(rec[u"呼び出し"], a[u"name"])[u"sha256"])
        n = []
        self.go(lambda prompt, model, key: n.append(1) or (200, thinking_body(prompt)), resume=True)
        self.assertEqual(2, len(n))
        self.assertIn(a[u"name"], [m[u"name"] for m in self.rec()[u"文の移動"]])

    def test_th_13_only_works_on_dry_run_too(self):
        seed_chosen = self.chosen[:2]
        self.p.set(GEN, "select_companies", lambda root, seed=None: (seed_chosen, self.counts))
        doc_a, doc_b = seed_chosen[0]["docID"], seed_chosen[1]["docID"]
        r_a = self.go(lambda *a: (500, b""), dry_run=True, only=doc_a)
        r_b = self.go(lambda *a: (500, b""), dry_run=True, only=doc_b)
        self.assertEqual((8, 8), (r_a["jobs"], r_b["jobs"]))
        self.assertAlmostEqual(r_a["est_usd"] + r_b["est_usd"], self.go(lambda *a: (500, b""), dry_run=True)["est_usd"], places=6)
        # 記録が在る: 1 社目は済み(1 本 0.5 USD)。上限は 済み + 2 社目の見積りの半分 → 全部の下見は止まり、--only 1 社目 の下見は通る
        self.go(lambda prompt, model, key: (200, thinking_body(prompt, tin=0, tout=20000)), only=doc_a)
        rec = self.rec()
        self.p.set(GEN, "COST_CAP_USD", GEN.recorded_cost(rec) + r_b["est_usd"] / 2.0)
        with self.assertRaises(GEN.Stop):
            self.go(lambda *a: (500, b""), dry_run=True)
        r = self.go(lambda *a: (500, b""), dry_run=True, only=doc_a)
        self.assertEqual(8, r["jobs"])
        self.assertAlmostEqual(r_a["est_usd"], r["est_usd"], places=6)
        with self.assertRaises(GEN.Stop):
            self.go(lambda *a: (500, b""), dry_run=True, only="S100NOPE")

    def test_th_14_the_recorded_stop_words_match_the_constants_tally_reads(self):
        # 上限の停止: 記録の止めた理由は gen の止めの字で、tally の is_cap_stop に当たる
        self.p.set(GEN, "COST_CAP_USD", 5.0)

        def tr(prompt, model, key):
            return 200, fake_body(prompt, tin=0, tout=120000)
        with self.assertRaises(GEN.Stop):
            self.go(tr)
        why = self.rec()[u"止めた理由"]
        self.assertTrue(TAL.is_cap_stop(why), why)
        self.assertTrue(why.startswith(TAL.CAP_STOP_STARTS[1]))
        self.p.undo()
        self.tearDown()
        self.setUp()
        # 401: 記録の止めた理由は上限の停止でない
        with self.assertRaises(GEN.Stop):
            self.go(fake_transport_factory([], [(401, b"{}")]))
        why = self.rec()[u"止めた理由"]
        self.assertTrue(why.startswith(u"HTTP 401"))
        self.assertFalse(TAL.is_cap_stop(why))
        self.tearDown()
        self.setUp()
        # 走らせる前の見積りの止め: 例外の字が見積りの止めの字で、その始まりは tally の定数に入っている
        self.p.set(GEN, "COST_CAP_USD", 0.5)
        with self.assertRaises(GEN.Stop) as cm:
            self.go(fake_transport_factory([]))
        self.assertTrue(str(cm.exception.code if hasattr(cm.exception, "code") else cm.exception).lstrip("*").startswith(TAL.CAP_STOP_STARTS[0]))
        self.assertTrue((CAP_STOP_ESTIMATE_EXAMPLE).startswith(TAL.CAP_STOP_STARTS[0]))
        self.assertTrue((CAP_STOP_RUNNING_EXAMPLE).startswith(TAL.CAP_STOP_STARTS[1]))
        self.assertFalse(TAL.is_cap_stop(None))
        self.assertFalse(TAL.is_cap_stop(u"HTTP 401(鍵の問題)"))


class ReasonTest(unittest.TestCase):
    u"""(r) judge が止まった件(2026-11-03): reason は None・SAFE_REASON・engine が宣言した固定の符号のどれかなら通し、それ以外(数を含む任意の字)は止める。"""

    def test_r_1_none_and_engine_codes_pass(self):
        self.assertIsNone(RUN.safe_reason(None))
        self.assertTrue(RUN.reason_ok(None))                                                            # GROUNDED の行は reason を持たない = 記録の検査も通す
        for r in (u"no_element(no prior2 for prior-year diff)", u"no_element", u"no_subject", u"ambiguous(member)", u"prior is 0", u"no_same_value", u"other_concept",
                  u"no_element(unit not in XBRL)", u"other_frame", u"per_unit_counter", u"no_prior_member_context"):
            self.assertEqual(r, RUN.safe_reason(r), r)
            self.assertTrue(RUN.reason_ok(r), r)
        for r in sorted(RUN.engine_reasons()):                                                           # engine が宣言した固定の符号は全部通る
            self.assertEqual(r, RUN.safe_reason(r), r)
        self.assertGreaterEqual(len(RUN.engine_reasons()), 20)

    def test_r_2_a_number_in_a_free_string_still_stops(self):
        for r in (u"no_element(12345)", u"no_element(no prior2 for prior-year diff) 3", u"値は 1234 です", u"", 5, b"no_element", [u"no_element"]):
            with self.assertRaises(RUN.Stop):
                RUN.safe_reason(r)
            self.assertFalse(RUN.reason_ok(r), r)

    def test_r_3_safe_reason_itself_is_not_loosened_and_the_engine_set_is_read_not_copied(self):
        self.assertIsNone(RUN.SAFE_REASON.fullmatch(u"no_element(no prior2 for prior-year diff)"))      # 数字の 2 は SAFE_REASON に当たらない(緩めない)
        self.assertIsNone(RUN.SAFE_REASON.fullmatch(u"no_element(12345)"))
        from adapters.xbrl import recipes as R
        self.assertTrue(set(R.UNBOUND_REASON_STATE) <= RUN.engine_reasons())
        self.assertIn(u"no_element(no prior2 for prior-year diff)", R.UNBOUND_REASON_STATE)
        src = io.open(os.path.join(ROOT, "measure", "xbrl_aiforms_run_2026-11-03.py"), encoding="utf-8").read()
        self.assertNotIn(u"prior2 for prior-year diff", src)                                              # 字をコピーしていない


class WorkFolderTest(unittest.TestCase):
    u"""(w) inject を --procs 8 で 160 本に回したとき JSONDecodeError で止まった件: 同じ書類の本を別の worker が同時に取ると、reference_numbers.json の作業 folder が衝突する。"""

    def test_w_1_the_refs_work_folder_differs_per_process(self):
        seen = []

        class FakeBackend(object):
            def refs(self, zip_path, doc, work):
                seen.append(work)
                return []
        p = Patch()
        tmp = tempfile.mkdtemp(prefix="aiforms_w_", dir=os.environ.get("TMPDIR"))
        try:
            p.set(RUN.TUNE, "RealBackend", FakeBackend)
            p.set(RUN.GEN, "zip_path", lambda row, caches: "zip")
            for pid in (1111, 2222):
                RUN._REFS.clear()
                p.set(os, "getpid", lambda pid=pid: pid)
                RUN.refs_for({"docID": "S100AAAA"}, {}, tmp)
                p.undo()
                p.set(RUN.TUNE, "RealBackend", FakeBackend)
                p.set(RUN.GEN, "zip_path", lambda row, caches: "zip")
            self.assertEqual(2, len(seen))
            self.assertNotEqual(seen[0], seen[1])
            self.assertTrue(all(w.startswith(os.path.join(tmp, "S100AAAA")) for w in seen))
        finally:
            p.undo()
            RUN._REFS.clear()
            shutil.rmtree(tmp, ignore_errors=True)


def cap_words_problems(gen_source, starts):
    u"""gen script の source(ast)に、tally の ``CAP_STOP_STARTS`` の 2 つの字で始まる(1)走らせる前の見積りの ``Stop(...)`` と(2)記録の ``rec["止めた理由"] = ...`` の文言が在り、
    ほかの ``止めた理由`` の代入(401 など)はどちらの字でも始まらないこと。問題の列。"""
    out = []
    tree = ast.parse(gen_source)

    def consts(node):
        return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    stops = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "Stop"]
    if not any(c.lstrip("*").startswith(starts[0]) and u"上限" in c for call in stops for c in consts(call)):
        out.append(u"gen に %r で始まる上限の Stop が無い" % starts[0])
    cap, other = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) and isinstance(getattr(t, "slice", None), ast.Constant) and t.slice.value == u"止めた理由" for t in n.targets):
            for c in consts(n.value):
                (cap if c.startswith(starts[1]) and u"上限" in c else other).append(c)
    if not cap:
        out.append(u"gen に %r で始まる 止めた理由 の代入が無い" % starts[1])
    if any(c.startswith(tuple(starts)) for c in other):
        out.append(u"上限でない止めた理由が上限の停止の字で始まっている")
    return out


class CapStopWordsTest(unittest.TestCase):
    u"""(c) A-1 の「上限で止まる」の字は tally の定数。gen script(生成の後は変えない)の実在の文言と照らす。"""

    def src(self):
        return io.open(os.path.join(ROOT, "measure", "xbrl_aiforms_gen_2026-11-03.py"), encoding="utf-8").read()

    def test_c_1_gen_source_has_the_stop_words_tally_reads(self):
        self.assertEqual((u"見積り ", u"累計 "), TAL.CAP_STOP_STARTS)
        self.assertEqual([], cap_words_problems(self.src(), TAL.CAP_STOP_STARTS))

    def test_c_2_a_changed_stop_word_in_gen_or_tally_turns_it_red(self):
        src = self.src()
        for a, b in ((u'u"累計 %.4f + 次の見積り', u'u"合計 %.4f + 次の見積り'), (u'u"**見積り %.4f USD が上限', u'u"**予想 %.4f USD が上限'),
                     (u'rec[u"止めた理由"] = u"HTTP %s(鍵の問題)"', u'rec[u"止めた理由"] = u"累計 HTTP %s(鍵の問題)"')):
            self.assertEqual(1, src.count(a), a)
            self.assertNotEqual([], cap_words_problems(src.replace(a, b), TAL.CAP_STOP_STARTS), a)
        for starts in ((u"見積り", u"合計 "), (u"予想 ", u"累計 ")):
            self.assertNotEqual([], cap_words_problems(src, starts))


class SelectionTest(unittest.TestCase):
    u"""会社の選び(封 §0-2 の 1)。記録だけを読む(cache の ZIP は読まない)。"""

    def test_s_1_the_20_follow_the_rule(self):
        p27 = set(c["docID"] for c in jload(GEN.P27_REPORTS_REL)[u"会社"])
        r97 = dict((r["docID"], r) for r in jload(GEN.REGRESS97_REL)[u"書類"])
        for seed in ("a", "b", "audit-core-injection-2026-10-08-a7f3"):
            chosen, counts = GEN.select_companies(ROOT, seed)
            ids = [r["docID"] for r in chosen]
            self.assertEqual(20, len(set(ids)))
            self.assertFalse(set(ids) & p27)
            self.assertTrue(all(r97[d]["claims"] >= 60 for d in ids))
            self.assertEqual(97, counts[u"手元の書類"])
            self.assertEqual(77, counts[u"除いた後の書類"])
        a = [r["docID"] for r in GEN.select_companies(ROOT, "a")[0]]
        self.assertEqual(a, [r["docID"] for r in GEN.select_companies(ROOT, "a")[0]])
        self.assertNotEqual(a, [r["docID"] for r in GEN.select_companies(ROOT, "b")[0]])         # 種で混ぜている(docID の昇順の先頭 20 ではない)
        self.assertNotEqual(a, sorted(a))

    def test_s_2_the_second_seat_draw_is_32_sorted_and_reproducible(self):
        names = [GEN.text_key("S100%04d" % i, "F1", "claude-sonnet-5-5") for i in range(160)]
        s2 = RUN.seat2_names(names, "seed")
        self.assertEqual((32, s2), (len(set(s2)), sorted(s2)))
        self.assertTrue(set(s2) <= set(names))
        self.assertEqual(s2, RUN.seat2_names(list(reversed(names)), "seed"))
        self.assertNotEqual(s2, RUN.seat2_names(names, "seed2"))
        self.assertEqual(4, len(RUN.seat2_names(names[:4], "seed")))


class KeyAndSeatTest(unittest.TestCase):
    def test_k_1_the_key_net_catches_a_key(self):
        key = "SECRET-key-12345"
        self.assertTrue(GEN.key_leaks(u"x %s y" % key, key))
        self.assertTrue(GEN.key_leaks(u"sk-ant-api03-abcdefghijklmnop"))
        self.assertTrue(GEN.key_leaks(u"ANTHROPIC_API_KEY=abcdefgh1234"))
        self.assertTrue(GEN.key_leaks(u"x-api-key: abc"))
        self.assertTrue(GEN.key_leaks(u"k" * 40))
        self.assertEqual([], GEN.key_leaks(u"k" * 40, None, long_alnum=False))
        self.assertEqual([], GEN.key_leaks(u"0123456789abcdef" * 4))                 # sha256 は鍵ではない
        self.assertEqual([], GEN.key_leaks(u"0" * 40))                                 # git の commit も
        self.assertEqual([], GEN.key_leaks(u"S100AAAA 売上高 jppfs_cor:NetSales"))

    def test_k_4_a_full_width_digit_text_is_not_injected(self):
        rows, counts = RUN.inject_text(b"", u"売上は１２億円でした。", [], "seed", "k")
        self.assertEqual(([], True), (rows, u"注入しない" in counts))

    def test_k_2_the_seat_answer_is_checked_one_to_one(self):
        ids = ["N001", "N002"]

        def lab(i, w=u"真", e=None, c=u"高", b=u"根拠。"):
            return {"id": i, u"札": w, u"誤りの型": e, u"確信": c, u"根拠": b}
        good = {u"札": [lab("N001"), lab("N002", u"偽", u"計算の誤り")]}
        self.assertEqual(2, len(LAB.validate_seat(good, ids, "k", "seat1")))
        for bad in ({u"札": [lab("N001")]}, {u"札": [lab("N001"), lab("N002"), lab("N003")]}, {u"札": [lab("N001"), lab("N001")]},
                    {u"札": [lab("N001", u"良"), lab("N002")]}, {u"札": [lab("N001", u"偽"), lab("N002")]}, {u"札": [lab("N001", u"偽", u"謎"), lab("N002")]},
                    {u"札": [lab("N001", u"真", u"計算の誤り"), lab("N002")]}, {u"札": [lab("N001", c=u"超"), lab("N002")]}, {u"札": [lab("N001", b=u" "), lab("N002")]},
                    {u"札": "x"}, {}):
            with self.assertRaises(SystemExit):                    # Stop は script ごとの module の実体で別の class(どれも SystemExit)
                LAB.validate_seat(bad, ids, "k", "seat1")

    def test_k_3_basis_elements_keep_only_names_in_the_facts_table(self):
        q = set(["jppfs_cor:NetSales", "jppfs_cor:OperatingIncome", "jpcrp_cor:A", "jppfs_cor:Dup", "jpigp_cor:Dup"])
        self.assertEqual(["jppfs_cor:NetSales", "jppfs_cor:OperatingIncome"], LAB.basis_elements(u"jppfs_cor:NetSales と OperatingIncome と jppfs_cor:Other と Dup", q))
        self.assertEqual([], LAB.basis_elements(u"売上高の当期の値", q))


class ShapeFunctionsTest(unittest.TestCase):
    def test_h_1_lead_symbol_and_multi_number_line(self):
        lines = RUN.lines_nfkc(u"・売上高は 12 億円でした。\n| 売上高 | 12 億円 | 11 億円 | 1 億円 |\nＱ: 利益は?\nA: 利益は 3 億円で、前期は 2 億円です。\n普通の文です。売上は 5 億円。")
        self.assertEqual((u"・", False), RUN.line_info(lines, u"・売上高は 12 億円でした。", None))
        self.assertEqual((u"|", True), RUN.line_info(lines, None, u"| 売上高 | 12 億円"))
        self.assertEqual((u"A", True), RUN.line_info(lines, u"A: 利益は 3 億円で、前期は 2 億円です。", None))
        self.assertEqual((RUN.LEAD_OTHER, False), RUN.line_info(lines, u"普通の文です。売上は 5 億円。", None))
        self.assertEqual((None, None), RUN.line_info(lines, u"どこにも無い文", None))
        self.assertEqual((None, None), RUN.line_info(lines, 3, 7))

    def test_h_2_the_base_needs_all_four_profiles_grounded_on_the_same_claim(self):
        class Tok(object):
            start, end, value, unit = 0, 3, 223.0, u"百万円"
        text = u"223 百万円"
        def claim(state, span=u"223 百万円", value=223.0):
            return {"id": "N001", "value": value, "unit": u"百万円", "span": span, "state": state}
        def run(states, spans=None):
            bc = dict((p, [claim(s, **({"span": spans[p]} if spans else {}))]) for p, s in zip(RUN.PROFILES, states))
            by = dict((p, dict((c["id"], c) for c in bc[p])) for p in RUN.PROFILES)
            return RUN.base_status4(bc, by, Tok, text)
        st, bc = run(["GROUNDED"] * 4)
        self.assertIsNotNone(bc)
        for i in range(4):
            states = ["GROUNDED"] * 4
            states[i] = "VALUE_MISMATCH"
            st, bc = run(states)
            self.assertIsNone(bc, RUN.PROFILES[i])
            self.assertEqual(u"一部の profile だけ GROUNDED", st)
        self.assertEqual(u"どの profile も GROUNDED でない", run(["UNVERIFIABLE"] * 4)[0])
        spans = dict((p, u"223 百万円") for p in RUN.PROFILES)
        spans["P28E"] = u"x 223 百万円"
        self.assertEqual(u"profile 間で claim が合わない", run(["GROUNDED"] * 4, spans)[0])

    def test_h_3_the_dossier_key_hides_the_form_and_the_model(self):
        for n in (GEN.text_key("S100AAAA", f, m) for f in GEN.FORMS for m in GEN.MODELS):
            k = RUN.dossier_key(n)
            self.assertRegex(k, r"^S100AAAA_[0-9a-f]{10}$")
            for bad in ("claude", "sonnet", "haiku", "F1", "F2", "F3", "F4"):
                self.assertNotIn(bad, k)
        self.assertEqual(8, len(set(RUN.dossier_key(GEN.text_key("S100AAAA", f, m)) for f in GEN.FORMS for m in GEN.MODELS)))


@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class FactsTableTest(unittest.TestCase):
    def test_t_1_the_table_has_labels_next_to_the_element_names(self):
        seed, _m = GEN.seed_value(ROOT)
        chosen, _c = GEN.select_companies(ROOT, seed)
        zb = GEN.read_zip(chosen[0])
        table, used, total, labelled = GEN.build_facts_table(zb)
        lines = table.split(u"\n")
        self.assertEqual(u"| 項目(要素名) | 標準ラベル | 値 | 単位 | 期間 |", lines[0])
        self.assertEqual(used + 2, len(lines))
        self.assertGreater(used, 100)
        self.assertGreaterEqual(labelled, used - 3)                         # 標準ラベル(日本語名)が要素名の横に付く
        self.assertLessEqual(used, total)
        keys = [(l.split(u" | ")[0], l.split(u" | ")[4]) for l in lines[2:]]
        self.assertEqual(sorted(k[0] for k in keys), [k[0] for k in keys])   # 要素名の昇順
        self.assertTrue(any(u"売上高" in l or u"現金及び預金" in l for l in lines))
        self.assertTrue(all(l.count(u" | ") == 4 for l in lines[2:]))

    def test_t_2_a_single_entity_filer_gets_its_non_consolidated_facts(self):
        seed, _m = GEN.seed_value(ROOT)
        r97 = [r for r in jload(GEN.REGRESS97_REL)[u"書類"]]
        found = None
        for r in r97:
            if r[u"標本"] in GEN.SAMPLE_DIR:
                zb = GEN.read_zip(r)
                from adapters.xbrl import instance as I
                inst = I.load_instance(zb)
                if I.consolidated_element_count(inst["facts"]) == 0:
                    found = zb
                    break
        self.assertIsNotNone(found, "単体だけの書類が 97 に無い")
        _t, used_on, total, _l = GEN.build_facts_table(found)
        p = Patch()
        try:
            p.set(GEN, "NONCONSOLIDATED_FALLBACK", False)
            _t2, used_off, _t3, _l2 = GEN.build_facts_table(found)
        finally:
            p.undo()
        self.assertTrue(GEN.NONCONSOLIDATED_FALLBACK)
        self.assertGreater(used_on, 5 * max(used_off, 1))                   # 旗が偽だと表がほぼ空になる(封に無い決定の根拠)


class ConstantsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_constants_agree_with_the_seal(self):
        self.assertEqual([], const_problems(self.seal))

    def test_a_2_a_changed_constant_or_seal_character_turns_it_red(self):
        p = Patch()
        try:
            for mod, name, val in ((GEN, "COST_CAP_USD", 51.0), (GEN, "PRICE_OUT", 24.0), (GEN, "MAX_TOKENS", 4001), (GEN, "MODELS", ("claude-sonnet-5-5",)),
                                    (GEN, "RETRY_WAITS", (2, 9)), (GEN, "SEAT2_N", 31), (TAL, "A4_BOUNDS", collections.OrderedDict([("F1", (55, 81)), ("F2", (40, 75)), ("F3", (25, 65)), ("F4", (45, 75))])),
                                    (TAL, "A6_PASS_MAX", 11), (TAL, "A1_MIN_BOOKS", 149), (TAL, "A9_P27_ORIG_MAX", 46.0), (TAL, "A11_RANGE", (30, 301))):
                p.set(mod, name, val)
                self.assertNotEqual([], const_problems(self.seal), name)
                p.undo()
        finally:
            p.undo()
        for old, new in ((u"**150 以上**", u"**149 以上**"), (u"**12 ポイント以下**", u"**13 ポイント以下**"), (u"上限 **50 USD**", u"上限 **40 USD**"), (u"最大 2 回", u"最大 3 回")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], const_problems(self.seal.replace(old, new, 1)), old)
        # 書き手の指示文に検証を知らせる語が混ざる / 形の字が欠ける
        p = Patch()
        try:
            p.set(GEN, "WRITER_COMMON", GEN.WRITER_COMMON.replace(u"レポートだけ", u"後で機械が検証するのでレポートだけ"))
            self.assertNotEqual([], const_problems(self.seal))
            p.undo()
            forms = collections.OrderedDict(GEN.WRITER_FORMS)
            forms["F3"] = forms["F3"].replace(u"5〜12 行", u"5〜13 行")
            p.set(GEN, "WRITER_FORMS", forms)
            self.assertNotEqual([], const_problems(self.seal))
            p.undo()
            p.set(RUN, "LABELLER_PROMPT", RUN.LABELLER_PROMPT.replace(u"判定不能", u"不明"))
            self.assertNotEqual([], const_problems(self.seal))
        finally:
            p.undo()

    def test_a_3_the_prompt_is_the_common_text_plus_the_form_plus_the_table(self):
        table = u"| a | b | c | d | e |\n|---|---|---|---|---|\n| x{FORM}y | z | 1 | JPY | 2025 時点 |"
        for f in GEN.FORMS:
            pr = GEN.render_prompt(f, table)
            self.assertEqual(1, pr.count(table))
            self.assertIn(GEN.WRITER_FORMS[f], pr)
            self.assertEqual(GEN.WRITER_COMMON.replace(u"{FACTS}", u"\0").replace(u"{FORM}", GEN.WRITER_FORMS[f]).replace(u"\0", table), pr)

    def test_a_4_seal_says_each_prediction_row_once(self):
        self.assertEqual([u"A-%d" % i for i in range(1, 13)], list(seal_pred_rows(self.seal)))


# ---------------------------------------------------------------- 使い捨ての小さい流れ(g)
@unittest.skipUnless(HAVE_CACHE, "cache の ZIP が無い")
class SmokeFlow(unittest.TestCase):
    u"""1 書類・1 model(4 本)で gen → judge → inject → labels → tally を偽の書き手・偽の席で通し、記録の検査が緑 → 変異で赤になる。"""

    R = None

    @classmethod
    def setUpClass(cls):
        cls.p = Patch()
        cls.tmp = tempfile.mkdtemp(prefix="aiforms_smoke_", dir=os.environ.get("TMPDIR"))
        seed, _m = GEN.seed_value(ROOT)
        chosen, counts = GEN.select_companies(ROOT, seed)
        cls.one, cls.doc = chosen[:1], chosen[0]["docID"]
        for g in gen_instances():
            cls.p.set(g, "select_companies", lambda root, seed=None: (cls.one, counts))
            cls.p.set(g, "MODELS", ("claude-sonnet-5-5",))
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
            facts = LAB.fact_names(d["facts"])
            el = sorted(facts)[0]
            labs = [{"id": c["id"], u"札": u"偽" if i % 6 == 5 else (u"判定不能" if i % 11 == 10 else u"真"), u"根拠": u"%s の当期の値と照合した。" % el,
                     u"誤りの型": u"計算の誤り" if i % 6 == 5 else None, u"確信": u"高"} for i, c in enumerate(d["claims"])]
            write_abs(os.path.join(ddir, b[u"札付けの束の鍵"] + ".seat1.json"), {u"札": labs})
            if b[u"name"] in claims[u"2 席目を立てる本"]:
                labs2 = [dict(x, 札=u"真", 誤りの型=None) if i % 3 == 0 else x for i, x in enumerate(labs)]
                write_abs(os.path.join(ddir, b[u"札付けの束の鍵"] + ".seat2.json"), {u"札": labs2})
        cls.labels_path = os.path.join(cls.tmp, "labels.json")
        LAB.run(root=ROOT, new_cache=cls.cache, claims_path=cls.claims_path, out=cls.labels_path, say=lambda *a: None)
        R = collections.OrderedDict([("gen", jload_abs(cls.gen_path)), ("claims", claims), ("labels", jload_abs(cls.labels_path)), ("inject", jload_abs(cls.inject_path))])
        T = TAL.build(R)
        J = TAL.judge(T)
        c = collections.Counter(v[u"判定"] for v in J.values())
        R["tally"] = collections.OrderedDict([(u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"この script の sha256", sha256_rel(SCRIPT_REL["tally"])),
                                              (u"入力の記録の sha256", {}), (u"集計", json.loads(json.dumps(T))), (u"予測の判定", json.loads(json.dumps(J))),
                                              (u"当たり", c.get(HIT, 0)), (u"外れ", c.get(MISS, 0)), (u"判定しない", c.get(NOJ, 0)), (u"key_leaks", [])])
        cls.R = R

    @classmethod
    def tearDownClass(cls):
        cls.p.undo()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def probs(self, R=None):
        return record_problems(copy.deepcopy(self.R) if R is None else R, full=False)

    def test_g_0_the_flow_is_green(self):
        self.assertEqual([], self.probs())
        gen = self.R["gen"]
        self.assertEqual(4, gen[u"累計"][u"成功"])
        self.assertTrue(self.R["claims"][u"本"])
        self.assertTrue(self.R["inject"][u"行"])

    def test_g_1_no_free_text_reaches_a_record(self):
        for k, rec in self.R.items():
            self.assertNotIn(u"の当期の値と照合した", json.dumps(rec, ensure_ascii=False), k)       # 偽の席が書いた根拠の自由文
        # 偽の書き手の文の字はどの記録にも無い
        n = 0
        for fn in os.listdir(os.path.join(self.cache, "texts")):
            for line in open(os.path.join(self.cache, "texts", fn), encoding="utf-8").read().split("\n"):
                if len(line) < 8:
                    continue
                n += 1
                for k, rec in self.R.items():
                    self.assertNotIn(line, json.dumps(rec, ensure_ascii=False), k)
        self.assertGreater(n, 10)

    def mutate(self, key, fn):
        R = copy.deepcopy(self.R)
        fn(R[key])
        return self.probs(R)

    def test_g_2_record_mutations_turn_it_red(self):
        def kl(r): r[u"key_leaks"] = ["x"]
        def forb(r): r[u"呼び出し"][0][u"文"] = "x"
        def docid(r): r[u"会社の選び"][u"docID"].append("S100ZZZZ")
        def cost(r): r[u"呼び出し"][0][u"cost_usd"] = r[u"呼び出し"][0][u"cost_usd"] + 1
        def total(r): r[u"累計"][u"成功"] = 99
        def cap(r): r[u"費用"][u"上限 USD"] = 51.0
        def cache(r): r[u"cache の前後"][u"変化なし"] = False
        def shas(r): r[u"呼び出し"][0][u"sha256"] = "z"
        def model(r): r[u"呼び出し"][0][u"model"] = "gpt"
        def retr(r): r[u"呼び出し"][0][u"retries"] = 3
        def scr(r): r[u"この script の sha256"] = "0" * 64
        def comp(r): r[u"会社の選び"][u"数え"][u"選んだ会社"] = 19
        for fn in (kl, forb, docid, cost, total, cap, cache, shas, model, retr, scr):
            self.assertTrue(self.mutate("gen", fn), fn.__name__)
        def c_state(r): r[u"本"][0][u"行"][0][-1] = ["X", None, [], True, None, None, None]
        def c_cnt(r): r[u"本"][0][u"数の claim の数(P27)"] += 1
        def c_dup(r): r[u"本"][0][u"行"].append(list(r[u"本"][0][u"行"][0]))
        def c_ptr(r): r[u"本"][0][u"行"][0][-1] = ["GROUNDED", None, ["a b@当期"], True, None, None, None]
        def c_sha(r): r[u"本"][0][u"文の sha256"] = "0" * 64
        def c_pair(r): r[u"本"][0][u"対応"] = False
        def c_miss(r): r[u"欠けた本"].append("x")
        def c_s2(r): r[u"2 席目を立てる本"] = r[u"2 席目を立てる本"][:-1]
        def c_forb(r): r.__setitem__(u"文", "x")
        def c_prompt(r): r[u"札付けの席の指示文の sha256"] = "0" * 64
        def c_lead(r): r[u"本"][0][u"行"][0][5] = "Z"
        def c_other(r): r[u"本"][0][u"行"][0][-1] = ["GROUNDED", None, [], True, [1, 2], None, None]
        for fn in (c_state, c_cnt, c_dup, c_ptr, c_sha, c_pair, c_miss, c_s2, c_forb, c_prompt, c_lead, c_other):
            self.assertTrue(self.mutate("claims", fn), fn.__name__)

    def test_g_3_label_mutations_turn_it_red(self):
        def l_word(r): r[u"本"][0][u"札"][0][1] = "良"
        def l_etype(r): r[u"本"][0][u"札"][0][2] = u"計算の誤り" if r[u"本"][0][u"札"][0][1] != u"偽" else None
        def l_id(r): r[u"本"][0][u"札"][0][0] = "N999"
        def l_el(r): r[u"本"][0][u"札"][0][4] = ["not a name"]
        def l_s2(r): r[u"本"][0].pop(u"2 席目", None) if u"2 席目" in r[u"本"][0] else r[u"本"][0].__setitem__(u"2 席目", [])
        def l_dist(r): r[u"集計"][u"札の分布"][u"全体"][u"数の claim"] += 1
        def l_agree(r): r[u"集計"][u"2 席目との一致"][u"一致"] += 1
        def l_forb(r): r[u"本"][0][u"根拠"] = "x"
        def l_conf(r): r[u"本"][0][u"札"][0][3] = "超"
        for fn in (l_word, l_etype, l_id, l_el, l_s2, l_dist, l_agree, l_forb, l_conf):
            self.assertTrue(self.mutate("labels", fn), fn.__name__)

    def test_g_4_inject_mutations_turn_it_red(self):
        def i_cell(r): r[u"行"][0]["P27"][u"結果"] = "通した?"
        def i_cap(r): r[u"行"] += [dict(r[u"行"][0], id=r[u"行"][0][u"id"] + "x%d" % i) for i in range(11)]
        def i_base(r): r[u"行"][0][u"基準の claim"] = "N999"
        def i_sum(r): r[u"集計"]["T1_VALUE"]["P27"][u"全体"][u"注入の行"] += 1
        def i_forb(r): r[u"行"][0][u"元の字"] = "x"
        def i_r(r): next(x for x in r[u"行"] if x[u"型"] == "T8_REL")["r"] = 0.5
        def i_dup(r): r[u"行"].append(dict(r[u"行"][0]))
        def i_book(r): r[u"行"][0][u"docID"] = "S100ZZZZ"
        def i_type(r): r[u"行"][0][u"型"] = "T2_UNIT"
        for fn in (i_cell, i_cap, i_base, i_sum, i_forb, i_r, i_dup, i_book, i_type):
            self.assertTrue(self.mutate("inject", fn), fn.__name__)
        # 土台が GROUNDED でなくなる(claims 側を壊す)
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        name = GEN.text_key(row[u"docID"], row[u"form"], row[u"model"])
        b = next(x for x in R["claims"][u"本"] if x[u"name"] == name)
        for raw in b[u"行"]:
            if raw[0] == row[u"基準の claim"]:
                raw[len(RUN.CLAIM_COLS)] = ["VALUE_MISMATCH", None, [], True, None, None, None]
        self.assertTrue(self.probs(R))

    def test_g_5_tally_mutations_turn_it_red(self):
        def t_sum(r): r[u"集計"][u"1 配線"][u"生成できた本"] += 1
        def t_judge(r): r[u"予測の判定"]["A-8"][u"判定"] = MISS if r[u"予測の判定"]["A-8"][u"判定"] != MISS else HIT
        def t_count(r): r[u"当たり"] += 1
        def t_forb(r): r[u"集計"][u"文"] = "x"
        for fn in (t_sum, t_judge, t_count, t_forb):
            self.assertTrue(self.mutate("tally", fn), fn.__name__)

    def test_g_6_judgments_move_with_the_records(self):
        base = TAL.judge(TAL.build(self.R))
        R = copy.deepcopy(self.R)
        for row in R["inject"][u"行"]:                       # 全部の注入を『通した』にすると A-9 が当たりのままではいられない
            for p in RUN.PROFILES:
                row[p] = {u"対応": True, u"結果": RUN.TUNE.LABEL_PASS, u"state": "GROUNDED", u"reason": None}
        j2 = TAL.judge(TAL.build(R))
        self.assertEqual(MISS, j2["A-9"][u"判定"])
        R = copy.deepcopy(self.R)
        for b in R["labels"][u"本"]:                          # 札を全部 偽 にすると A-3 は外れ
            for r in b[u"札"]:
                r[1], r[2] = u"偽", u"計算の誤り"
        self.assertEqual(MISS, TAL.judge(TAL.build(R))["A-3"][u"判定"])
        self.assertEqual(NOJ, base["A-12"][u"判定"])

    def a1_with_stop(self, why):
        u"""A-1 の他の条件(150 本以上・費用 3〜25)を満たす表に、gen の記録の止めた理由だけを替えて判定する。"""
        R = copy.deepcopy(self.R)
        R["gen"][u"止めた理由"] = why
        T = TAL.build(R)
        T[u"1 配線"][u"生成できて P27 の数の claim が %d 以上ある本" % TAL.A1_MIN_CLAIMS] = 160
        T[u"1 配線"][u"費用 USD(記録の cost_usd の合計)"] = 10.0
        return T, TAL.judge(T)["A-1"][u"判定"]

    def test_g_6a_a_cap_stop_makes_a1_a_miss(self):
        _T, base = self.a1_with_stop(None)
        self.assertEqual(HIT, base)
        for why in (CAP_STOP_RUNNING_EXAMPLE, CAP_STOP_ESTIMATE_EXAMPLE):
            T, j = self.a1_with_stop(why)
            self.assertEqual(MISS, j, why)
            self.assertTrue(T[u"1 配線"][u"上限で止まった"])
            self.assertIsNone(T[u"1 配線"][u"上限でない停止(字)"])

    def test_g_6b_a_non_cap_stop_does_not_make_a1_a_miss_and_is_shown(self):
        for why in (u"HTTP 401(鍵の問題)", u"x", u"HTTP 403(鍵の問題)"):
            T, j = self.a1_with_stop(why)
            self.assertEqual(HIT, j, why)
            self.assertFalse(T[u"1 配線"][u"上限で止まった"])
            self.assertEqual(why, T[u"1 配線"][u"上限でない停止(字)"])             # 表示欄に出す
        self.assertEqual(u"x", self.a1_with_stop(u"x")[0][u"1 配線"][u"止めた理由"])           # 記録の字そのものも残る

    def test_g_8_each_judgment_flips_at_the_seal_boundary(self):
        T0 = TAL.build(self.R)

        def judged(edit):
            T = copy.deepcopy(T0)
            edit(T)
            return TAL.judge(T)
        E = u"3 engine の判定(無改変)"
        w = lambda T: T[u"1 配線"]
        key_books = u"生成できて P27 の数の claim が %d 以上ある本" % TAL.A1_MIN_CLAIMS
        cost_key = u"費用 USD(記録の cost_usd の合計)"

        def a1(n, c, why=None):
            def e(T):
                w(T)[key_books], w(T)[cost_key], w(T)[u"止めた理由"] = n, c, why
            return judged(e)["A-1"][u"判定"]
        self.assertEqual((HIT, MISS, HIT, MISS, MISS, HIT, MISS),
                         (a1(150, 3.0), a1(149, 3.0), a1(150, 25.0), a1(150, 25.01), a1(150, 2.99), a1(160, 10.0), a1(160, 10.0, CAP_STOP_RUNNING_EXAMPLE)))

        def a2(f, x):
            def e(T):
                for ff in TAL.FORMS:
                    w(T)[u"形 × model"][ff][u"P27 の数の claim の数"] = {u"中央値": sum(TAL.A2_BOUNDS[ff]) / 2.0}
                w(T)[u"形 × model"][f][u"P27 の数の claim の数"] = {u"中央値": x}
            return judged(e)["A-2"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS), (a2("F3", 5), a2("F3", 35), a2("F3", 4.5), a2("F3", 35.5)))

        def a3(t, f, a):
            def e(T):
                L = T[u"2 札"]
                L[u"札の分布"][u"全体"][u"真"][u"率"], L[u"札の分布"][u"全体"][u"偽"][u"率"], L[u"2 席目との一致"][u"一致率"] = t, f, a
            return judged(e)["A-3"][u"判定"]
        self.assertEqual((HIT, MISS, MISS, HIT, MISS, MISS, HIT, MISS),
                         (a3(85.0, 1.0, 90.0), a3(84.9, 4.0, 95.0), a3(90.0, 0.9, 95.0), a3(90.0, 8.0, 95.0), a3(90.0, 8.1, 95.0), a3(90.0, 4.0, 89.9), a3(90.0, 4.0, 90.0), a3(None, 4.0, 90.0)))

        def a4(vals):
            def e(T):
                for f, v in zip(TAL.FORMS, vals):
                    T[E]["P28E"][f][u"札 真の行の GROUNDED 率"][u"率"] = v
            return judged(e)["A-4"][u"判定"]
        self.assertEqual((HIT, MISS, MISS, MISS), (a4((55, 40, 25, 45)), a4((55, 40, 40, 45)), a4((54.9, 40, 25, 45)), a4((55, 40, 24.9, 45))))

        def a5(f2, f3):
            def e(T):
                for f, share in (("F2", f2), ("F3", f3)):
                    T[E]["P28E"][f][u"札 真で止めた率"][u"件"] = 100
                    T[E]["P28E"][f][u"札 真で止めた行の reason/state の内訳"] = {u"no_subject/UNVERIFIABLE": share, u"(reason なし)/VALUE_MISMATCH": 100 - share}
            return judged(e)["A-5"][u"判定"]
        self.assertEqual((HIT, MISS, MISS), (a5(35, 35), a5(34, 35), a5(35, 34)))

        def a6(rate, passed):
            def e(T):
                T[E]["P28E"][u"全体"][u"札 偽の行で止めた率"][u"率"] = rate
                T[E]["P28E"][u"全体"][u"札 偽の行で通した数"] = passed
            return judged(e)["A-6"][u"判定"]
        self.assertEqual((HIT, MISS, MISS), (a6(85.0, 10), a6(84.9, 10), a6(90.0, 11)))

        O = u"O の効き(P27E → P28E で GROUNDED になった行)"

        def a7(total, f2, others):
            def e(T):
                T[u"4 profile の差"][O][u"全体"] = total
                for f in TAL.FORMS:
                    T[u"4 profile の差"][O][f] = f2 if f == "F2" else others
            return judged(e)["A-7"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, MISS), (a7(20, 5, 4), a7(200, 5, 4), a7(19, 5, 4), a7(201, 5, 4), a7(100, 5, 5)))
        Bk = u"B の効き(P27 → P27E で no_same_value → VALUE_MISMATCH)"

        def a8(x):
            def e(T):
                T[u"4 profile の差"][Bk][u"全体"] = x
            return judged(e)["A-8"][u"判定"]
        self.assertEqual((HIT, HIT, MISS), (a8(0), a8(60), a8(61)))

        def a9(p27, p28e, orig28, orig27):
            def e(T):
                for t in RUN.INJECT_TYPES:
                    T[u"5 注入"][t]["P27"][u"全体"][u"通した"][u"率"] = p27
                    T[u"5 注入"][t]["P28E"][u"全体"][u"通した"][u"率"] = p28e
                T[u"5 注入"]["T8_REL"]["P28E"][u"全体"][u"名指して原本の値を返した"][u"率"] = orig28
                T[u"5 注入"]["T8_REL"]["P27"][u"全体"][u"名指して原本の値を返した"][u"率"] = orig27
            return judged(e)["A-9"][u"判定"]
        self.assertEqual((HIT, MISS, MISS, MISS, MISS), (a9(3.0, 3.0, 60.0, 45.0), a9(3.1, 3.0, 60.0, 45.0), a9(3.0, 3.1, 60.0, 45.0), a9(3.0, 3.0, 59.9, 45.0), a9(3.0, 3.0, 60.0, 45.1)))

        def a10(w1, w2):
            def e(T):
                for f, a, b in zip(TAL.FORMS, w1, w2):
                    T[E]["P28E"][TAL.cell_key(f, "W1")][u"札 真の行の GROUNDED 率"][u"率"] = a
                    T[E]["P28E"][TAL.cell_key(f, "W2")][u"札 真の行の GROUNDED 率"][u"率"] = b
            return judged(e)["A-10"][u"判定"]
        self.assertEqual((HIT, MISS, MISS), (a10((50, 60, 70, 65), (50, 60, 62, 65)), a10((50, 60, 70, 65), (50, 60, 57.9, 65)), a10((50, 60, 54.9, 60), (50, 60, 54.9, 60))))
        Sk = u"「その他」の形の行(provenance)"

        def a11(n, d, rate):
            def e(T):
                c = T[u"4 profile の差"][Sk]["P28E"][u"全体"]
                c[u"「その他」の形の行"], c[u"決まった"][u"件"], c[u"決まった"][u"率"] = n, d, rate
            return judged(e)["A-11"][u"判定"]
        self.assertEqual((HIT, HIT, MISS, MISS, MISS, MISS, HIT, HIT), (a11(30, 10, 35.0), a11(300, 240, 80.0), a11(29, 10, 50.0), a11(301, 10, 50.0), a11(100, 10, 34.9), a11(100, 10, 80.1), a11(100, 50, 50.0), a11(100, 80, 80.0)))

    def test_g_7_the_table_in_the_result_document_follows_the_records(self):
        J = TAL.judge(TAL.build(self.R))
        table = TAL.render_table(J)
        doc = u"# 結果\n\n<!-- 門:start pred -->\n%s\n<!-- 門:end -->\n\n本文。\n" % table
        self.assertEqual([], doc_problems(doc, self.R))
        self.assertTrue(doc_problems(doc.replace(u"A-3", u"A-4", 1), self.R))
        self.assertTrue(doc_problems(doc.replace(u"当たり", u"外れ", 1), self.R))
        self.assertTrue(doc_problems(doc + u"\nS100ABCD\n", self.R))
        self.assertTrue(doc_problems(doc + u"\n精度が高い。\n", self.R))
        self.assertTrue(doc_problems(doc + u"\n本文に 1234 がある。\n", self.R))
        self.assertEqual([], doc_problems(doc + u"\n本文に 1234 がある。【門なし】\n", self.R))
        R = copy.deepcopy(self.R)
        R["gen"][u"呼び出し"][0][u"ok"] = True
        R["claims"][u"本"][0][u"数の claim の数(P27)"] = 0
        self.assertTrue(doc_problems(doc, R))                # 記録を 1 つ変えると表が変わる


def jload_abs(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def write_abs(p, obj):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


# ---------------------------------------------------------------- 順序(e)の変異(使い捨ての repo)
OTHERS = list(REC_REL.values()) + [DOC_REL] + list(GATE_FILES)
IMPLS = list(SCRIPT_REL.values())
SEALF = SEAL_REL


class OrderMutationTest(unittest.TestCase):
    def _good(self):
        r = PR.Repo()
        r.put(SEALF)
        s = r.commit(SEALF)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        for f in OTHERS:
            r.put(f)
        r.commit(*OTHERS)
        return r, s

    def probe(self, r, s):
        return PR.order_problems(r.d, PREFIX, SEALF, s[:7], IMPLS, OTHERS)

    def test_e_1_good_order_is_green(self):
        r, s = self._good()
        self.assertEqual([], self.probe(r, s))

    def test_e_2_uncommitted_before_seal_or_before_scripts_is_red(self):
        r = PR.Repo()
        r.put(SEALF)
        s = r.commit(SEALF)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(self.probe(r, s)))
        r2 = PR.Repo()
        r2.put(OTHERS[0])
        r2.commit(OTHERS[0])
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        for f in IMPLS:
            r2.put(f)
        r2.commit(*IMPLS)
        for f in OTHERS[1:]:
            r2.put(f)
        r2.commit(*OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], self.probe(r2, s2))
        r3 = PR.Repo()
        r3.put(SEALF)
        s3 = r3.commit(SEALF)
        r3.put(OTHERS[0])
        r3.commit(OTHERS[0])
        for f in IMPLS:
            r3.put(f)
        r3.commit(*IMPLS)
        for f in OTHERS[1:]:
            r3.put(f)
        r3.commit(*OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], self.probe(r3, s3))

    def test_e_3_a_seal_touching_the_engine_or_a_wrong_seal_is_red(self):
        r = PR.Repo()
        r.put("docs/before.md")
        r.commit("docs/before.md")
        r.put("adapters/xbrl/vocabulary.py")
        r.put(SEALF)
        s = r.commit(SEALF, "adapters/xbrl/vocabulary.py")
        self.assertIn("SEAL_TOUCHES_ENGINE", self.probe(r, s))
        r2, s2 = self._good()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r2.d, PREFIX, SEALF, "abcdef0", IMPLS, OTHERS))


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

    def test_e_1_order_is_seal_then_scripts_then_records(self):
        self.assertEqual([], order_of(REPO))


if __name__ == "__main__":
    unittest.main()
