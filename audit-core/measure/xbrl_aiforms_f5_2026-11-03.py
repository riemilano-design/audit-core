# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_F5_SEAL_2026-11-03.md §0-2 の 7 ― F5(標準ラベルを見せない書き手)の駆動 script。

前の便の script 4 本(``xbrl_aiforms_{gen,run,labels,tally}_2026-11-03.py``)は **1 byte も変えず**、この 1 本が importlib で読み込んで差し替える
(形の表・指示文の 1 行・表の作り・置き場所・記録の path・2 席目の本数・前の便の累計・封の名と commit)。差し替えた先は記録の ``差し替え`` の欄に名前と sha256 で書く。

    python3 measure/xbrl_aiforms_f5_2026-11-03.py gen --dry-run [--only DOC]       # 本数・見積り(USD)。鍵は読まない・通信しない
    ANTHROPIC_API_KEY=... python3 measure/xbrl_aiforms_f5_2026-11-03.py gen [--only DOC] [--resume]    # 有料。司令塔だけが走らせる(40 本)
    python3 measure/xbrl_aiforms_f5_2026-11-03.py judge  [--procs N] [--only DOC]  # 0 USD。4 profile の判定 → f5_claims_2026-11-03.json・札付けの束
    python3 measure/xbrl_aiforms_f5_2026-11-03.py inject [--procs N] [--only DOC]  # 0 USD。注入 → f5_inject_2026-11-03.json
    python3 measure/xbrl_aiforms_f5_2026-11-03.py labels                            # 0 USD。盲検の席の札 → f5_labels_2026-11-03.json
    python3 measure/xbrl_aiforms_f5_2026-11-03.py tally                             # 0 USD。集計と封 §2 の B-1〜B-9 の判定・§2-1 の推奨 → f5_tally_2026-11-03.json

守り(前の便と同じ。差し替えても落ちない):
  - 鍵は環境変数 ``ANTHROPIC_API_KEY`` だけから読む(``gen`` の有料の呼び出しのときだけ)。記録は書く前と書いた後に ``key_leaks`` を検査する。
  - 上限 50 USD は実験の全体。前の便の累計 ``PREV_TOTAL_USD``(29.46516。前の便の記録の ``累計.費用 USD 合計(記録の外を含む)``)を字で留め、
    走らせる前の止め(``plan_problem``)も呼ぶ前の止め(``cum + est > COST_CAP_USD``)も ``GEN.recorded_cost`` 経由でこの値を含む。
  - 会社の列は前の便の ``会社の選び.docID`` と一致しなければ止める。置き場は新しい folder(``NEW_CACHE``)。前の便の folder も既存の cache 3 folder と同じく前後を記録し、変われば止める。

engine(``core/``・``adapters/``)は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_f5")
RUN = load_module("xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_f5")
LAB = load_module("xbrl_aiforms_labels_2026-11-03.py", "aiforms_labels_for_f5")
TAL = load_module("xbrl_aiforms_tally_2026-11-03.py", "aiforms_tally_for_f5")

Stop = GEN.Stop
PREV_GEN_SCRIPT_REL = "measure/xbrl_aiforms_gen_2026-11-03.py"
PREV_GEN_REL = GEN.GEN_REL                                   # 差し替える前の値(前の便の記録)
PREV_TALLY_REL = TAL.TALLY_REL
SEAL_REL = "docs/XBRL_AI_FORMS_F5_SEAL_2026-11-03.md"
SEAL_COMMIT = "e564683"
F5_GEN_REL = GEN.REC_DIR_REL + "/f5_gen_2026-11-03.json"
F5_CLAIMS_REL = GEN.REC_DIR_REL + "/f5_claims_2026-11-03.json"
F5_LABELS_REL = GEN.REC_DIR_REL + "/f5_labels_2026-11-03.json"
F5_INJECT_REL = GEN.REC_DIR_REL + "/f5_inject_2026-11-03.json"
F5_TALLY_REL = GEN.REC_DIR_REL + "/f5_tally_2026-11-03.json"
F5_NEW_CACHE = os.path.join(GEN.CACHE_BASE, "aiforms-f5-2026-11-03")
PREV_CACHE_NAME = "aiforms-2026-11-03"                       # 前の便の folder(この便は 1 file も書かない。前後を記録して照らす)
PREV_CACHE = GEN.NEW_CACHE
assert os.path.basename(PREV_CACHE) == PREV_CACHE_NAME

# ---- 封 §0-2 の決めごと(字で留める)
PREV_TOTAL_USD = 29.46516                                    # 封 §0-2 の 4: 前の便の gen の記録の 累計.費用 USD 合計(記録の外を含む)
F5_SEAT2_N = 8                                               # 封 §0-2 の 5: 2 席目は種で引いた 8 本(20%)
F5_FORMS = ("F5",)
F5_N_BOOKS = 20 * 1 * 2

# ---- 差し替える前の値(門が照らす)
ORIG = {
    "WRITER_COMMON": GEN.WRITER_COMMON,
    "WRITER_FORMS": GEN.WRITER_FORMS,
    "F1_FORM_TEXT": GEN.WRITER_FORMS["F1"],
    "build_facts_table": GEN.build_facts_table,
    "select_companies": GEN.select_companies,
    "new_record": GEN.new_record,
    "key_leaks": GEN.key_leaks,
    "header": RUN.header,
}

# ---- 指示文(封 §0-2 の 2)。共通の指示文は 1 行の 1 文だけを置換し、形の指示は F1 と同じ字(同じ object)
COMMON_OLD = u"各行は、項目の要素名・標準ラベル(日本語名)・値・単位・期間です。"
COMMON_NEW = u"各行は、項目の要素名・値・単位・期間です。"
F5_HEADER = u"| 項目(要素名) | 値 | 単位 | 期間 |"
F5_RULE = u"|---|---|---|---|"
F1_FORM_TEXT = ORIG["F1_FORM_TEXT"]


def common_f5(common=None):
    u"""前の便の WRITER_COMMON から COMMON_OLD の 1 文だけを COMMON_NEW に替えた字。替える前後で 1 行だけが違うことをここで確かめる(違えば AssertionError)。"""
    common = ORIG["WRITER_COMMON"] if common is None else common
    if common.count(COMMON_OLD) != 1:
        raise AssertionError(u"前の便の WRITER_COMMON に置換の対象の文がちょうど 1 つでない")
    new = common.replace(COMMON_OLD, COMMON_NEW)
    a, b = common.split(u"\n"), new.split(u"\n")
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(a) != len(b) or len(diff) != 1 or a[diff[0]].replace(COMMON_OLD, COMMON_NEW) != b[diff[0]]:
        raise AssertionError(u"置換の前後で違う行がちょうど 1 行でない")
    return new


WRITER_COMMON_F5 = common_f5()
WRITER_FORMS_F5 = collections.OrderedDict([("F5", F1_FORM_TEXT)])


# ======================================================================================================
# fact の表: 前の便の関数を呼んで 5 欄の表から標準ラベルの列を落とす(行の集合・並び・値の書き方・期間の字は前の便と同じ)
def drop_label_column(table):
    u"""5 欄の表(``| 要素名 | 標準ラベル | 値 | 単位 | 期間 |``)から標準ラベルの列を落とした 4 欄の表。
    行は右から 3 つ(値・単位・期間)と左の要素名で切る(標準ラベルの中に ' | ' があっても崩れない)。"""
    lines = table.split(u"\n")
    out = [F5_HEADER, F5_RULE]
    for ln in lines[2:]:
        head, val, unit, period = ln.rsplit(u" | ", 3)
        name = head[2:].split(u" | ")[0]
        out.append(u"| %s | %s | %s | %s" % (name, val, unit, period))
    return u"\n".join(out)


def build_facts_table_f5(zb, label_map=None):
    u"""(表, 使った行数, 全 fact 数, 標準ラベルが付いた行数)。標準ラベルは見せないので 4 つ目は 0。"""
    table, used, total, _labelled = ORIG["build_facts_table"](zb, label_map)
    return drop_label_column(table), used, total, 0


# ======================================================================================================
# 鍵の検査: 封の path「docs/XBRL_AI_FORMS_F5_SEAL_2026-11-03.md」は英数字・_・- が 32 字続く(前の便の封は 29 字)ので、前の便の ``key_leaks`` の
# 「32 字以上の英数字の連なり」に当たってしまう。封の path そのものの字だけを検査の前に除く(ほかの字は前の便の検査のまま)。
def key_leaks_f5(text, key_value=None, long_alnum=True):
    return ORIG["key_leaks"](text.replace(SEAL_REL, u""), key_value, long_alnum)


# ======================================================================================================
# 費用: 前の便の累計を記録の外の欄として字で入れる
def outside_calls_f5():
    return [collections.OrderedDict([
        (u"番号", u"前の便の累計"),
        (u"確かめ", u"前の便(gen_2026-11-03.json)の 累計.費用 USD 合計(記録の外を含む)。実験の全体の上限 50 USD の計算に入れる"),
        (u"cost_usd", PREV_TOTAL_USD)])]


def outside_cost_f5():
    return round(sum(c[u"cost_usd"] for c in outside_calls_f5()), 6)


# ======================================================================================================
# 前の便の記録(読むだけ)
def prev_gen(root=ROOT):
    return GEN.jload(os.path.join(root, PREV_GEN_REL))


def prev_tally(root=ROOT):
    return GEN.jload(os.path.join(root, PREV_TALLY_REL))


def prev_problems(root=ROOT):
    u"""PREV_TOTAL_USD が前の便の gen の記録の累計と一致するか。問題の列。"""
    out = []
    g = prev_gen(root)
    if g[u"累計"][u"費用 USD 合計(記録の外を含む)"] != PREV_TOTAL_USD:
        out.append(u"PREV_TOTAL_USD が前の便の gen の記録の 累計.費用 USD 合計(記録の外を含む) と違う")
    return out


def select_companies_f5(root=ROOT, seed=None):
    u"""前の便と同じ選び(同じ種・同じ規則)。前の便の記録の 会社の選び.docID と列が一致しなければ止める。"""
    chosen, counts = ORIG["select_companies"](root, seed)
    want = prev_gen(root)[u"会社の選び"][u"docID"]
    if [r["docID"] for r in chosen] != want:
        raise Stop(u"**会社の列が前の便の gen の記録の 会社の選び.docID と違う。止める**")
    return chosen, counts


# ======================================================================================================
# 差し替え
STEP_FROM, STEP_TO = u"AI の形 4 × model 2", u"AI の形 F5(標準ラベルなし)× model 2"

#: (module 名, 属性, 差し替えた先)。記録の ``差し替え`` の欄の ``差し替えた名前`` は ``module.属性`` の字の列
SWAP_TABLE = (
    ("GEN", "FORMS", F5_FORMS), ("GEN", "WRITER_FORMS", WRITER_FORMS_F5), ("GEN", "WRITER_COMMON", WRITER_COMMON_F5),
    ("GEN", "build_facts_table", build_facts_table_f5), ("GEN", "NEW_CACHE", F5_NEW_CACHE), ("GEN", "GEN_REL", F5_GEN_REL),
    ("GEN", "SEAL_REL", SEAL_REL), ("GEN", "SEAL_COMMIT", SEAL_COMMIT), ("GEN", "SEAT2_N", F5_SEAT2_N), ("GEN", "key_leaks", key_leaks_f5),
    ("GEN", "outside_calls", outside_calls_f5), ("GEN", "outside_cost", outside_cost_f5), ("GEN", "select_companies", select_companies_f5),
    ("RUN", "CLAIMS_REL", F5_CLAIMS_REL), ("RUN", "INJECT_REL", F5_INJECT_REL), ("RUN", "SEAL_REL", SEAL_REL), ("RUN", "SEAL_COMMIT", SEAL_COMMIT),
    ("LAB", "LABELS_REL", F5_LABELS_REL),
    ("TAL", "TALLY_REL", F5_TALLY_REL), ("TAL", "FORMS", F5_FORMS),
)
MODS = {"GEN": GEN, "RUN": RUN, "LAB": LAB, "TAL": TAL}
#: 同じ GEN の instance を他の module に差し込む(別 instance に patch が届かない罠。``X.GEN is GEN`` を門が見る)
SHARE_TABLE = (("RUN", "GEN", GEN), ("RUN", "Stop", GEN.Stop), ("LAB", "GEN", GEN), ("LAB", "RUN", RUN), ("LAB", "Stop", GEN.Stop),
               ("TAL", "GEN", GEN), ("TAL", "RUN", RUN), ("TAL", "LAB", LAB), ("TAL", "Stop", GEN.Stop))
F5_REC_REL = collections.OrderedDict([("gen", F5_GEN_REL), ("claims", F5_CLAIMS_REL), ("labels", F5_LABELS_REL), ("inject", F5_INJECT_REL)])
EXTRA_KEY = u"F5 追加"


def swapped_names():
    return [u"%s.%s" % (m, a) for m, a, _v in SWAP_TABLE] + [u"%s.%s" % (m, a) for m, a, _v in SHARE_TABLE] + \
        [u"GEN.EXISTING_CACHES", u"GEN.new_record", u"RUN.header", u"TAL.REC_REL"]


def swap_shas():
    return collections.OrderedDict([
        (u"WRITER_COMMON_F5", GEN.sha256_text(WRITER_COMMON_F5)),
        (u"WRITER_FORMS", collections.OrderedDict((k, GEN.sha256_text(v)) for k, v in WRITER_FORMS_F5.items()))])


def swap_field():
    u"""記録の ``差し替え`` の欄。名前の一覧・差し替え後の指示文の sha256・前の便の gen script の sha256・この駆動 script の sha256・前の便の累計。"""
    return collections.OrderedDict([
        (u"差し替えた名前", swapped_names()), (u"指示文の sha256", swap_shas()),
        (u"前の便の gen script の sha256", GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_gen_2026-11-03.py"))),
        (u"駆動 script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"前の便の累計 USD", PREV_TOTAL_USD)])


def restep(step):
    if STEP_FROM not in step:
        raise AssertionError(u"step の字が前の便の形でない")
    return step.replace(STEP_FROM, STEP_TO)


def new_record_f5(*a, **k):
    rec = ORIG["new_record"](*a, **k)
    rec[u"step"] = restep(rec[u"step"])
    rec[u"差し替え"] = swap_field()
    return rec


def header_f5(*a, **k):
    h = ORIG["header"](*a, **k)
    h[u"step"] = restep(h[u"step"])
    h[u"差し替え"] = swap_field()
    return h


def install():
    u"""差し替えを入れる(import 時に 1 回)。同じ GEN の instance を RUN・LAB・TAL の ``GEN`` に差し込む。"""
    for m, a, v in SHARE_TABLE:
        setattr(MODS[m], a, v)
    for m, a, v in SWAP_TABLE:
        setattr(MODS[m], a, v)
    GEN.EXISTING_CACHES = collections.OrderedDict(list(GEN.EXISTING_CACHES.items()) + [(PREV_CACHE_NAME, PREV_CACHE)])
    GEN.new_record = new_record_f5
    RUN.header = header_f5
    TAL.REC_REL = collections.OrderedDict(F5_REC_REL)


#: gen 以外の command(judge・inject・labels・tally)は会社の選び直しをしないので、この差し替えは見ない(試験が選びを絞るために差し替えても通る)
NOT_NEEDED_AFTER_GEN = ("GEN.select_companies",)


def wiring_problems(skip=()):
    u"""差し替えが全部届いているか(使う側の実体に届かないと黙って効かない)。問題の列。skip = 見ない名前(``module.属性``)。"""
    out = []
    for m, a, v in SHARE_TABLE:
        if getattr(MODS[m], a) is not v:
            out.append(u"%s.%s が同じ instance でない" % (m, a))
    for m, a, v in SWAP_TABLE:
        cur = getattr(MODS[m], a)
        if u"%s.%s" % (m, a) in skip:
            continue
        if not (cur is v or (isinstance(v, (str, int, tuple, dict)) and cur == v)):
            out.append(u"%s.%s が差し替えた先でない" % (m, a))
    if list(GEN.EXISTING_CACHES)[-1] != PREV_CACHE_NAME or GEN.EXISTING_CACHES[PREV_CACHE_NAME] != PREV_CACHE:
        out.append(u"GEN.EXISTING_CACHES に前の便の folder が無い")
    if GEN.new_record is not new_record_f5:
        out.append(u"GEN.new_record が差し替えた先でない")
    if RUN.header is not header_f5:
        out.append(u"RUN.header が差し替えた先でない")
    if dict(TAL.REC_REL) != dict(F5_REC_REL):
        out.append(u"TAL.REC_REL が F5 の記録でない")
    if GEN.WRITER_FORMS.get("F5") is not F1_FORM_TEXT or list(GEN.WRITER_FORMS) != ["F5"]:
        out.append(u"形の指示が F1 と同じ字(同じ object)の F5 だけでない")
    return out


install()


# ======================================================================================================
# 封 §2 の B-1〜B-9(幅は字で留める。門が封の文書の字と照らす)
B1_BOOKS, B1_MIN_CLAIMS, B1_COST = F5_N_BOOKS, 10, (4.0, 10.0)
B2_RANGE, B2_RATIO = (20, 120), 2
B3_DECIDED, B3_RATE = (5, 60), (25.0, 70.0)
B5_FALSE, B5_TRUE_MIN = (3.5, 10.0), 80.0
B6_RANGE, B6_DIFF_MIN = (55.0, 75.0), 0.3
B7_MIN = 80.0
B8_PASS_MAX, B8_P28E_ORIG_MIN = 3.0, 60.0
#: 封 §2-1
R_KEEP_DECIDED_MIN = 5
KEEP, REVERT, ASK_HUMAN = u"据え置く", u"P27E に戻す", u"人間に判断を戻す"
PROV = u"「その他」の形の行(provenance)"
MOVES = u"P27E → P28E の state の動き(向き別)"
ALLOWED_MOVES = (u"POINTER_NOT_FOUND → GROUNDED", u"VALUE_MISMATCH → GROUNDED")
HIT, MISS, NOJ = TAL.HIT, TAL.MISS, TAL.NOJ


def pct(a, b):
    return TAL.pct(a, b)


def between(x, lo_hi):
    return TAL.between(x, lo_hi)


def sec_f5(rows):
    u"""B-7・B-9 のための追加の集計(O の形の行 = P28E の provenance の欄が在る claim。全 claim)。"""
    def oc(r):
        return r["P28E"][u"other_subject_2026_11_02"] if r["P28E"] is not None else None
    o_rows = [r for r in rows if oc(r) is not None]
    decided = [r for r in o_rows if oc(r)[2]]
    dl = [r for r in decided if r[u"label"] is not None]
    lab = collections.Counter(r[u"label"][0] for r in dl)
    cand = collections.Counter(str(oc(r)[1]) for r in o_rows)
    hold = [r for r in o_rows if oc(r)[1] >= 2 and not oc(r)[2]]
    hl = collections.Counter((r[u"label"][0] if r[u"label"] is not None else u"札なし") for r in hold)
    per_doc = collections.OrderedDict()
    for r in o_rows:
        d = per_doc.setdefault(r[u"docID"], collections.OrderedDict([(u"O の形の行", 0), (u"決まった", 0)]))
        d[u"O の形の行"] += 1
        d[u"決まった"] += 1 if oc(r)[2] else 0
    out = collections.OrderedDict()
    out[u"O の形の行"] = len(o_rows)
    out[u"決まった行"] = len(decided)
    out[u"決まった行のうち札のある行"] = len(dl)
    out[u"決まった行の札"] = collections.OrderedDict((w, lab.get(w, 0)) for w in RUN.LABEL_WORDS)
    out[u"決まった行のうち札 真の行"] = TAL.frac(lab.get(u"真", 0), len(dl))
    out[u"候補の数の分布"] = collections.OrderedDict(sorted(cand.items(), key=lambda kv: int(kv[0])))
    out[u"候補 2 以上で保留の行"] = collections.OrderedDict([
        (u"件", len(hold)), (u"札", collections.OrderedDict(sorted(hl.items()))),
        (u"P28E の state", collections.OrderedDict(sorted(collections.Counter(r["P28E"][u"state"] for r in hold).items())))])
    out[u"model 別"] = collections.OrderedDict(
        (w, collections.OrderedDict([(u"O の形の行", sum(1 for r in o_rows if r[u"writer"] == w)), (u"決まった", sum(1 for r in decided if r[u"writer"] == w))]))
        for w in TAL.WRITERS)
    out[u"会社ごと"] = per_doc
    return out


def build_f5(records):
    T = TAL.build(records)
    T[EXTRA_KEY] = sec_f5(TAL.claim_rows(records))
    return T


def judge_f5(T, prev=None):
    u"""{B-n: {判定, 値}}。値は判定の根拠にした数(門が結果の文書の表と照らす)。F1 の 9(B-2)と 2.5%(B-5)は前の便の tally の記録から読む。"""
    prev = prev_tally() if prev is None else prev
    pT = prev[u"集計"]
    f1_o = pT[u"4 profile の差"][PROV]["P28E"]["F1"][u"「その他」の形の行"]
    f1_false = pT[u"2 札"][u"札の分布"]["F1"][u"偽"][u"率"]
    J = collections.OrderedDict()
    w = T[u"1 配線"]
    made = w[u"生成できた本"]
    n_books = w[u"生成できて P27 の数の claim が %d 以上ある本" % B1_MIN_CLAIMS]
    cost = w[u"費用 USD(記録の cost_usd の合計)"]
    capped = TAL.is_cap_stop(w[u"止めた理由"])
    ok1 = made == B1_BOOKS and n_books == B1_BOOKS and between(cost, B1_COST) and not capped
    J["B-1"] = {u"判定": HIT if ok1 else MISS, u"値": collections.OrderedDict([
        (u"生成できた本", made), (u"数の claim が 10 以上の本", n_books), (u"費用 USD", cost), (u"上限で止まった", capped), (u"上限でない停止(字)", w[u"上限でない停止(字)"])])}
    S = T[u"4 profile の差"][PROV]["P28E"][u"全体"]
    n_o, n_dec, rate_dec = S[u"「その他」の形の行"], S[u"決まった"][u"件"], S[u"決まった"][u"率"]
    ok2 = between(n_o, B2_RANGE) and n_o >= B2_RATIO * f1_o
    J["B-2"] = {u"判定": HIT if ok2 else MISS, u"値": collections.OrderedDict([(u"O の形の行", n_o), (u"前の便の F1", f1_o)])}
    ok3 = between(n_dec, B3_DECIDED) and between(rate_dec, B3_RATE)
    J["B-3"] = {u"判定": HIT if ok3 else MISS, u"値": collections.OrderedDict([(u"決まった行", n_dec), (u"決まった率", rate_dec)])}
    mv = T[u"4 profile の差"][MOVES][u"全体"]
    other = sum(v for k, v in mv.items() if k not in ALLOWED_MOVES)
    lost = sum(v for k, v in mv.items() if k.startswith(u"GROUNDED → "))
    J["B-4"] = {u"判定": HIT if other == 0 and lost == 0 else MISS, u"値": collections.OrderedDict([
        (u"動いた行の向き別", collections.OrderedDict(sorted(mv.items()))), (u"許した向き以外の行", other), (u"GROUNDED でなくなった行", lost)])}
    L = T[u"2 札"][u"札の分布"][u"全体"]
    t_rate, f_rate = L[u"真"][u"率"], L[u"偽"][u"率"]
    ok5 = f_rate is not None and f_rate > f1_false and between(f_rate, B5_FALSE) and t_rate is not None and t_rate >= B5_TRUE_MIN
    J["B-5"] = {u"判定": HIT if ok5 else MISS, u"値": collections.OrderedDict([(u"偽の率", f_rate), (u"真の率", t_rate), (u"前の便の F1 の偽の率", f1_false)])}
    E = T[u"3 engine の判定(無改変)"]
    g28 = E["P28E"][u"全体"][u"札 真の行の GROUNDED 率"][u"率"]
    g27 = E["P27E"][u"全体"][u"札 真の行の GROUNDED 率"][u"率"]
    diff = round(g28 - g27, 1) if g28 is not None and g27 is not None else None
    ok6 = between(g28, B6_RANGE) and diff is not None and diff >= B6_DIFF_MIN
    J["B-6"] = {u"判定": HIT if ok6 else MISS, u"値": collections.OrderedDict([(u"P28E の札 真の行の GROUNDED 率", g28), (u"P27E", g27), (u"差(ポイント)", diff)])}
    X = T[EXTRA_KEY]
    r7 = X[u"決まった行のうち札 真の行"][u"率"]
    J["B-7"] = {u"判定": HIT if r7 is not None and r7 >= B7_MIN else MISS, u"値": collections.OrderedDict([
        (u"決まった行のうち札のある行", X[u"決まった行のうち札のある行"]), (u"札 真", X[u"決まった行のうち札 真の行"][u"件"]), (u"率", r7)])}
    I = T[u"5 注入"]
    passes = collections.OrderedDict()
    for t in RUN.INJECT_TYPES:
        for p in ("P27", "P28E"):
            passes[u"%s %s 通した率" % (t, p)] = I[t][p][u"全体"][u"通した"][u"率"]
    orig28 = I["T8_REL"]["P28E"][u"全体"][u"名指して原本の値を返した"][u"率"]
    ok8 = all(v is not None and v <= B8_PASS_MAX for v in passes.values()) and orig28 is not None and orig28 >= B8_P28E_ORIG_MIN
    J["B-8"] = {u"判定": HIT if ok8 else MISS, u"値": collections.OrderedDict(list(passes.items()) + [(u"T8_REL 名指して原本 P28E", orig28)])}
    docs_o = [d for d, v in X[u"会社ごと"].items() if v[u"O の形の行"] > 0]
    J["B-9"] = {u"判定": NOJ, u"値": collections.OrderedDict([
        (u"候補の数の分布", X[u"候補の数の分布"]), (u"候補 2 以上で保留の行", X[u"候補 2 以上で保留の行"][u"件"]),
        (u"O の形の行がある会社", len(docs_o)), (u"model 別", X[u"model 別"]),
        (u"札 判定不能", T[u"A-12 判定しない"][u"札 判定不能の中身"][u"件"])])}
    return J


def recommendation(J):
    u"""封 §2-1。``据え置く`` / ``P27E に戻す`` / ``人間に判断を戻す``。最後に決めるのは人間。
    重なる場合(決まった行 < 5 でも GROUNDED でなくなった行 ≥ 1 か B-7 < 80%)は、正しくない文を通した疑いを先にして人間に戻す(封に無い決め ― 報告に書く)。"""
    n_dec = J["B-3"][u"値"][u"決まった行"]
    lost = J["B-4"][u"値"][u"GROUNDED でなくなった行"]
    r7 = J["B-7"][u"値"][u"率"]
    if lost >= 1 or (r7 is not None and r7 < B7_MIN):
        return ASK_HUMAN
    if n_dec < R_KEEP_DECIDED_MIN:
        return REVERT
    if r7 is not None:
        return KEEP
    return ASK_HUMAN


def render_table(J):
    u"""結果の文書に貼る表(``<!-- 門:start pred -->`` の中。門が文書の表と一行も違わないことを見る)。"""
    return TAL.render_table(J)


def render_reco(J):
    u"""結果の文書の ``<!-- 門:start reco -->`` の中(任意)。§2-1 の決め方を機械で出した 1 行。"""
    return u"封 §2-1 の決め方による推奨: **%s**(決まった行 %d・GROUNDED でなくなった行 %d・B-7 %s%%)。最後に決めるのは人間。" % (
        recommendation(J), J["B-3"][u"値"][u"決まった行"], J["B-4"][u"値"][u"GROUNDED でなくなった行"], J["B-7"][u"値"][u"率"])


# ======================================================================================================
def restamp_json(path, key_value=None):
    u"""labels の script は step を持つ記録を自分で書くので、書いた後に step と 差し替え の 2 欄だけを F5 に直す(他の欄・並び・書式は変えない)。"""
    with io.open(path, encoding="utf-8") as fh:
        rec = json.load(fh, object_pairs_hook=collections.OrderedDict)
    rec[u"step"] = restep(rec[u"step"])
    rec[u"差し替え"] = swap_field()
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    if GEN.key_leaks(text, key_value, long_alnum=False):
        os.remove(path)
        raise Stop(u"**記録に鍵らしい字が在る。消して止める**")
    GEN.write_text(path, text)
    return rec


def run_gen(root=ROOT, **kw):
    bad = wiring_problems() + prev_problems(root)
    if bad:
        raise Stop(u"**差し替えか前の便の累計が合わない: %s。止める**" % u" / ".join(bad))
    return GEN.run(root=root, **kw)


def run_labels(root=ROOT, out=None, **kw):
    bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    out = out or os.path.join(root, LAB.LABELS_REL)
    LAB.run(root=root, out=out, **kw)
    return restamp_json(out, kw.get("key_value"))


def tally_record(records, input_sha, prev_sha, head, prev=None):
    u"""tally の記録(``f5_tally``)。records = gen・claims・labels・inject の 4 つ。input_sha・prev_sha = それぞれ記録の sha256 の欄(試験は {} を渡す)。"""
    T = build_f5(records)
    J = judge_f5(T, prev)
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT), (u"step", restep(u"AI の形 4 × model 2 ― 集計と封 §2 の B-1〜B-9 の判定(0 USD)")),
        (u"HEAD の commit", head), (u"この script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"差し替え", swap_field()),
        (u"入力の記録の sha256", input_sha), (u"前の便の記録の sha256", prev_sha),
        (u"集計", T), (u"予測の判定", J),
        (u"当たり", sum(1 for v in J.values() if v[u"判定"] == HIT)), (u"外れ", sum(1 for v in J.values() if v[u"判定"] == MISS)),
        (u"判定しない", sum(1 for v in J.values() if v[u"判定"] == NOJ)),
        (u"封 §2-1 の推奨", recommendation(J)), (u"key_leaks", [])])


def run_tally(root=ROOT, out=None, say=print):
    bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    out = out or os.path.join(root, TAL.TALLY_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    records = TAL.load_records(root)
    rec = tally_record(records, collections.OrderedDict((k, GEN.sha256_file(os.path.join(root, v))) for k, v in TAL.REC_REL.items()),
                       collections.OrderedDict([("gen", GEN.sha256_file(os.path.join(root, PREV_GEN_REL))), ("tally", GEN.sha256_file(os.path.join(root, PREV_TALLY_REL)))]),
                       GEN.git_head(os.path.dirname(root)), prev_tally(root))
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    if GEN.key_leaks(text, None, long_alnum=False):
        raise Stop(u"**記録に鍵らしい字が在る。書かずに止める**")
    GEN.write_text(out, text)
    J = rec[u"予測の判定"]
    say(render_table(J))
    say(render_reco(J))
    say(u"-> %s" % out)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("gen", "judge", "inject", "labels", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true", help="gen: 見積りと本数だけ(通信しない・鍵は読まない)")
    ap.add_argument("--only", default=None, help="gen・judge・inject: この docID の本だけ")
    ap.add_argument("--resume", action="store_true", help="gen: 既に在る文は飛ばして続ける")
    ap.add_argument("--procs", type=int, default=1, help="judge・inject の並列数")
    a = ap.parse_args(argv)
    if a.cmd == "gen":
        run_gen(root=a.root, dry_run=a.dry_run, only=a.only, resume=a.resume, out=a.out)
    elif a.cmd in ("judge", "inject"):
        bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
        if bad:
            raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
        (RUN.run_judge if a.cmd == "judge" else RUN.run_inject)(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "labels":
        run_labels(root=a.root, out=a.out)
    else:
        run_tally(root=a.root, out=a.out)


if __name__ == "__main__":
    main()
