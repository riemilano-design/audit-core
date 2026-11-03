# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_SEAL_2026-11-03.md §1・§2 ― 記録 4 つ(gen・claims・labels・inject)から §1 の全部を 形 × model × profile で集計し、§2 の A-1〜A-12 の判定を機械で出す。**0 USD・通信なし。**

    python3 measure/xbrl_aiforms_tally_2026-11-03.py [--out fixtures/xbrl/aiforms/tally_2026-11-03.json]

判定は記録だけから求める(``build(records)`` → ``judge(T)``)。結果の文書の表(``render_table``)と封の予測の字は、門 ``tests/measure/test_xbrl_aiforms_result.py`` が照らす。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 「形」= F1〜F4、「model」= W1(claude-sonnet-5-5)・W2(claude-haiku-5-5)。率は ``{件, 分母, 率(小数 1 桁の %)}``。
- 「数の claim」= kind が num の claim。札(真 / 偽 / 判定不能)は 1 席目の札。「札 真の行」= 札付けされた数の claim で札が 真。
- 「止めた」= P28E(など、見ている profile)の state が GROUNDED でない。「通した」= GROUNDED。
- A-1: 生成できた本(gen の呼び出しが ok)で P27 の数の claim が 10 以上ある本が 150 以上、かつ費用の合計(記録の cost_usd。API の返した usage に保守的な単価を当てた値)が 3〜25 USD、かつ上限で止まっていない。
- A-2: 形ごと(両 model の本をまとめた)の P27 の数の claim の数の中央値(生成できた本。claim 0 の本も入れる)が、F1 30〜80・F2 20〜60・F3 5〜35・F4 15〜50 の全部に入る。
- A-3: 札 真の率 85% 以上・偽の率 1〜8%(分母は札付けされた数の claim の全部)・2 席目との一致率 90% 以上、の全部。
- A-4: P28E の 札 真の行の GROUNDED 率が F1 55〜80・F2 40〜75・F3 25〜65・F4 45〜75 の全部に入り、F3 が 4 形で最も低い(同率は最も低いに数えない)。
- A-5: P28E で札 真の行を止めた行のうち reason が ``no_subject`` の率が、F2 と F3 のそれぞれで 35% 以上。
- A-6: 札 偽の行(全体)を P28E が止める率が 85% 以上、かつ通した偽の行が全体で 10 以下。
- A-7: P27E → P28E で GROUNDED でなかった行が GROUNDED になった行(全 claim)が全体で 20〜200、かつ 4 形のうち F2 が最多(同数は最多に数えない)。
- A-8: P27 で POINTER_NOT_FOUND かつ reason が ``no_same_value`` の行が P27E で VALUE_MISMATCH になった行(全 claim)が全体で 0〜60。
- A-9: 注入。T1_VALUE・T8_REL のそれぞれで、P27・P28E の通した率(分母は対応が付いた注入)が 3% 以下、かつ T8_REL の名指して原本の値を返した率が P28E 60% 以上・P27 45% 以下。
- A-10: P28E の 札 真の行の GROUNDED 率について、各形で |W1 − W2| の最大が 12 ポイント以下、かつ各 model で形の間の幅(最大 − 最小)が 15 ポイント以上(2 model の両方)。
- A-11: 「その他」の形の行(P28E の other_subject_2026_11_02 が在る claim。全 claim)が 30〜300、そのうち 決まった の率が 35〜80%。
- A-12: 判定しない(会社ごとの内訳・要素名の分布・打ち切り・札 判定不能の中身を記録する)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import statistics
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


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_tally")
RUN = load_module("xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_tally")
LAB = load_module("xbrl_aiforms_labels_2026-11-03.py", "aiforms_labels_for_tally")

Stop = GEN.Stop
TALLY_REL = GEN.REC_DIR_REL + "/tally_2026-11-03.json"
REC_REL = collections.OrderedDict([("gen", GEN.GEN_REL), ("claims", RUN.CLAIMS_REL), ("labels", LAB.LABELS_REL), ("inject", RUN.INJECT_REL)])
PROFILES = RUN.PROFILES
STATES = RUN.STATES
FORMS = GEN.FORMS
WRITERS = tuple(GEN.MODEL_TAG[m] for m in GEN.MODELS)
HIT, MISS, NOJ = u"当たり", u"外れ", u"判定しない"
# 封 §2 の幅(字で留める。門が封の文書の字と照らす)
A2_BOUNDS = collections.OrderedDict([("F1", (30, 80)), ("F2", (20, 60)), ("F3", (5, 35)), ("F4", (15, 50))])
A4_BOUNDS = collections.OrderedDict([("F1", (55, 80)), ("F2", (40, 75)), ("F3", (25, 65)), ("F4", (45, 75))])
A1_MIN_BOOKS, A1_MIN_CLAIMS, A1_COST = 150, 10, (3.0, 25.0)
A3_TRUE_MIN, A3_FALSE = 85.0, (1.0, 8.0)
A3_AGREE_MIN = 90.0
A5_MIN = 35.0
A6_STOP_MIN, A6_PASS_MAX = 85.0, 10
A7_RANGE = (20, 200)
A8_RANGE = (0, 60)
A9_PASS_MAX, A9_P28E_ORIG_MIN, A9_P27_ORIG_MAX = 3.0, 60.0, 45.0
A10_PAIR_MAX, A10_SPREAD_MIN = 12.0, 15.0
A11_RANGE, A11_DECIDED = (30, 300), (35.0, 80.0)


def jload(rel_or_path, root=ROOT):
    p = rel_or_path if os.path.isabs(rel_or_path) else os.path.join(root, rel_or_path)
    return GEN.jload(p)


def load_records(root=ROOT):
    return collections.OrderedDict((k, jload(v, root)) for k, v in REC_REL.items())


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def frac(a, b):
    return collections.OrderedDict([(u"件", a), (u"分母", b), (u"率", pct(a, b))])


def writer_of(model):
    return GEN.MODEL_TAG[model]


def cell_key(form, writer):
    return u"%s×%s" % (form, writer)


# ======================================================================================================
# 行の組み立て(記録 → 1 claim = 1 行)
def claim_rows(records):
    u"""claims の記録 → [{name, docID, form, writer, id, kind, lead, multi, P27..P28E: 欄の辞書, label: (札, 誤りの型, 確信, 要素名) or None}]。"""
    lab = {}
    for b in records["labels"][u"本"]:
        for r in b[u"札"]:
            lab[(b[u"name"], r[0])] = (r[1], r[2], r[3], r[4])
    rows = []
    for b in records["claims"][u"本"]:
        if b.get(u"欠け"):
            continue
        for raw in b[u"行"]:
            d = RUN.decode_row(raw)
            d.update({u"name": b[u"name"], u"docID": b[u"docID"], u"form": b[u"form"], u"writer": b[u"writer"]})
            d[u"label"] = lab.get((b[u"name"], d[u"id"]))
            rows.append(d)
    return rows


def groups(rows):
    u"""全体 / 形別 / model 別 / 形 × model の row の組。"""
    g = collections.OrderedDict()
    g[u"全体"] = rows
    for f in FORMS:
        g[f] = [r for r in rows if r[u"form"] == f]
    for w in WRITERS:
        g[w] = [r for r in rows if r[u"writer"] == w]
    for f in FORMS:
        for w in WRITERS:
            g[cell_key(f, w)] = [r for r in rows if r[u"form"] == f and r[u"writer"] == w]
    return g


# ======================================================================================================
# §1 の集計
def sec_wiring(records):
    gen, claims = records["gen"], records["claims"]
    ok = dict((c[u"name"], c) for c in gen[u"呼び出し"] if c[u"ok"])
    books = [b for b in claims[u"本"] if not b.get(u"欠け")]
    out = collections.OrderedDict()
    out[u"本数(予定)"] = len(GEN.FORMS) * len(GEN.MODELS) * len(gen[u"会社の選び"][u"docID"])
    out[u"生成できた本"] = len(ok)
    out[u"生成できて P27 の数の claim が %d 以上ある本" % A1_MIN_CLAIMS] = sum(1 for b in books if b[u"数の claim の数(P27)"] >= A1_MIN_CLAIMS)
    out[u"費用 USD(記録の cost_usd の合計)"] = round(sum(c[u"cost_usd"] for c in gen[u"呼び出し"]), 4)
    out[u"呼び出しの数"] = len(gen[u"呼び出し"])
    out[u"失敗した呼び出し"] = sum(1 for c in gen[u"呼び出し"] if not c[u"ok"])
    out[u"再試行の合計"] = sum(c[u"retries"] for c in gen[u"呼び出し"])
    out[u"止めた理由"] = gen.get(u"止めた理由")
    out[u"max_tokens で打ち切られた本"] = sum(1 for c in ok.values() if c[u"stop_reason"] == "max_tokens")

    def dist(vals):
        if not vals:
            return None
        return collections.OrderedDict([(u"本", len(vals)), (u"最小", min(vals)), (u"中央値", statistics.median(vals)), (u"最大", max(vals))])
    per = collections.OrderedDict()
    for key, sel in groups_books(books).items():
        names = [b[u"name"] for b in sel]
        per[key] = collections.OrderedDict([
            (u"本", len(sel)), (u"P27 の数の claim の数", dist([b[u"数の claim の数(P27)"] for b in sel])),
            (u"文の字数", dist([ok[n][u"chars"] for n in names if n in ok])), (u"費用 USD", round(sum(ok[n][u"cost_usd"] for n in names if n in ok), 4))])
    out[u"形 × model"] = per
    return out


def groups_books(books):
    g = collections.OrderedDict()
    g[u"全体"] = books
    for f in FORMS:
        g[f] = [b for b in books if b[u"form"] == f]
    for w in WRITERS:
        g[w] = [b for b in books if b[u"writer"] == w]
    for f in FORMS:
        for w in WRITERS:
            g[cell_key(f, w)] = [b for b in books if b[u"form"] == f and b[u"writer"] == w]
    return g


def labelled(rows):
    return [r for r in rows if r[u"label"] is not None]


def sec_labels(records, rows):
    out = collections.OrderedDict()
    cells = collections.OrderedDict()
    for k, sel in groups(rows).items():
        lr = labelled(sel)
        c = collections.Counter(r[u"label"][0] for r in lr)
        cells[k] = collections.OrderedDict([(u"数の claim", len(lr))] + [(w, frac(c.get(w, 0), len(lr))) for w in RUN.LABEL_WORDS])
    out[u"札の分布"] = cells
    out[u"2 席目との一致"] = records["labels"][u"集計"][u"2 席目との一致"]
    return out


def sec_engine(rows):
    u"""4 state の分布(全 claim)と、札 真・札 偽の行の扱い(数の claim)。形 × model × profile。"""
    out = collections.OrderedDict()
    for p in PROFILES:
        pcell = collections.OrderedDict()
        for k, sel in groups(rows).items():
            states = collections.Counter(r[p][u"state"] for r in sel if r[p] is not None)
            lr = labelled(sel)
            true_rows = [r for r in lr if r[u"label"][0] == u"真"]
            false_rows = [r for r in lr if r[u"label"][0] == u"偽"]
            t_stop = [r for r in true_rows if r[p][u"state"] != "GROUNDED"]
            f_stop = [r for r in false_rows if r[p][u"state"] != "GROUNDED"]
            reasons = collections.Counter((r[p][u"reason"] or u"(reason なし)") + u"/" + r[p][u"state"] for r in t_stop)
            pcell[k] = collections.OrderedDict([
                (u"claim", len(sel)), (u"4 state", collections.OrderedDict((s, states.get(s, 0)) for s in STATES)),
                (u"札 真の行の GROUNDED 率", frac(len(true_rows) - len(t_stop), len(true_rows))),
                (u"札 真で止めた率", frac(len(t_stop), len(true_rows))),
                (u"札 真で止めた行の reason/state の内訳", collections.OrderedDict(sorted(reasons.items()))),
                (u"札 偽の行で止めた率", frac(len(f_stop), len(false_rows))),
                (u"札 偽の行で通した数", len(false_rows) - len(f_stop))])
        out[p] = pcell
    return out


def sec_diff(rows):
    u"""profile の差(全 claim)。向き別。「その他」の形の行(P28・P28E の provenance)。O の効き・B の効き。"""
    out = collections.OrderedDict()

    def moves(pa, pb, sel):
        c = collections.Counter()
        for r in sel:
            if r[pa] is None or r[pb] is None:
                continue
            if r[pa][u"state"] != r[pb][u"state"]:
                c[u"%s → %s" % (r[pa][u"state"], r[pb][u"state"])] += 1
        return collections.OrderedDict(sorted(c.items()))
    for (pa, pb) in (("P27", "P28E"), ("P27E", "P28E"), ("P27", "P27E")):
        cell = collections.OrderedDict()
        for k, sel in groups(rows).items():
            cell[k] = moves(pa, pb, sel)
        out[u"%s → %s の state の動き(向き別)" % (pa, pb)] = cell
    shape = collections.OrderedDict()
    for p in ("P28", "P28E"):
        cell = collections.OrderedDict()
        for k, sel in groups(rows).items():
            sr = [r for r in sel if r[p] is not None and r[p][u"other_subject_2026_11_02"] is not None]
            decided = [r for r in sr if r[p][u"other_subject_2026_11_02"][2]]
            cell[k] = collections.OrderedDict([(u"「その他」の形の行", len(sr)), (u"決まった", frac(len(decided), len(sr)))])
        shape[p] = cell
    out[u"「その他」の形の行(provenance)"] = shape
    o_eff = collections.OrderedDict()
    b_eff = collections.OrderedDict()
    for k, sel in groups(rows).items():
        o_eff[k] = sum(1 for r in sel if r["P27E"][u"state"] != "GROUNDED" and r["P28E"][u"state"] == "GROUNDED")
        b_eff[k] = sum(1 for r in sel if r["P27"][u"state"] == "POINTER_NOT_FOUND" and r["P27"][u"reason"] == "no_same_value" and r["P27E"][u"state"] == "VALUE_MISMATCH")
    out[u"O の効き(P27E → P28E で GROUNDED になった行)"] = o_eff
    out[u"B の効き(P27 → P27E で no_same_value → VALUE_MISMATCH)"] = b_eff
    return out


def sec_shape(rows):
    u"""形の性質(数の claim)。複数の数の行・主語が取れた率(P28E の subject)・行頭が記号の文の率。"""
    out = collections.OrderedDict()
    for k, sel in groups([r for r in rows if r[u"kind"] == "num"]).items():
        n = len(sel)
        known = [r for r in sel if r[u"multi_number_line"] is not None]
        leads = [r for r in sel if r[u"lead"] is not None]
        out[k] = collections.OrderedDict([
            (u"数の claim", n), (u"1 行に数が 2 つ以上", frac(sum(1 for r in known if r[u"multi_number_line"]), len(known))),
            (u"主語が取れた(P28E)", frac(sum(1 for r in sel if r["P28E"][u"subject"]), n)),
            (u"行頭が記号(・|QA)", frac(sum(1 for r in leads if r[u"lead"] in RUN.LEADS), len(leads))),
            (u"行頭の内訳", collections.OrderedDict(sorted(collections.Counter(r[u"lead"] for r in leads).items())))])
    return out


def sec_a12(records, rows):
    u"""判定しない: 会社ごと・要素名の分布・打ち切り・札 判定不能の中身。"""
    out = collections.OrderedDict()
    comp = collections.OrderedDict()
    for d in records["gen"][u"会社の選び"][u"docID"]:
        sel = [r for r in rows if r[u"docID"] == d]
        lr = labelled(sel)
        true_rows = [r for r in lr if r[u"label"][0] == u"真"]
        comp[d] = collections.OrderedDict([(u"本", len(set(r[u"name"] for r in sel))), (u"claim", len(sel)), (u"数の claim", len(lr)),
                                            (u"札 偽", sum(1 for r in lr if r[u"label"][0] == u"偽")), (u"札 判定不能", sum(1 for r in lr if r[u"label"][0] == u"判定不能")),
                                            (u"札 真の行の GROUNDED 率(P28E)", frac(sum(1 for r in true_rows if r["P28E"][u"state"] == "GROUNDED"), len(true_rows)))])
    out[u"会社ごと"] = comp
    elems = collections.Counter()
    for r in rows:
        for pt in (r["P28E"][u"pointers"] if r["P28E"] else []):
            if r["P28E"][u"state"] == "GROUNDED":
                elems[pt.split("@")[0]] += 1
    out[u"要素名の分布(P28E で GROUNDED の行の pointers。上位 30)"] = collections.OrderedDict(elems.most_common(30))
    ok = [c for c in records["gen"][u"呼び出し"] if c[u"ok"]]
    out[u"max_tokens で打ち切られた本"] = sum(1 for c in ok if c[u"stop_reason"] == "max_tokens")
    nj = [r for r in labelled(rows) if r[u"label"][0] == u"判定不能"]
    out[u"札 判定不能の中身"] = collections.OrderedDict([
        (u"件", len(nj)), (u"確信の内訳", collections.OrderedDict(sorted(collections.Counter(r[u"label"][2] for r in nj).items()))),
        (u"形別", collections.OrderedDict((f, sum(1 for r in nj if r[u"form"] == f)) for f in FORMS)),
        (u"P28E の state", collections.OrderedDict(sorted(collections.Counter(r["P28E"][u"state"] for r in nj).items()))),
        (u"根拠の要素名 上位 20", collections.OrderedDict(collections.Counter(e for r in nj for e in r[u"label"][3]).most_common(20)))])
    return out


def build(records):
    rows = claim_rows(records)
    T = collections.OrderedDict()
    T[u"1 配線"] = sec_wiring(records)
    T[u"2 札"] = sec_labels(records, rows)
    T[u"3 engine の判定(無改変)"] = sec_engine(rows)
    T[u"4 profile の差"] = sec_diff(rows)
    T[u"5 注入"] = RUN.inject_summary(records["inject"][u"行"])
    T[u"6 形の性質"] = sec_shape(rows)
    T[u"A-12 判定しない"] = sec_a12(records, rows)
    return T


# ======================================================================================================
# §2 の判定
def between(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


def judge(T):
    u"""{A-n: {判定, 値}}。値は判定の根拠にした数(門が結果の文書の表と照らす)。"""
    J = collections.OrderedDict()
    w = T[u"1 配線"]
    n_books = w[u"生成できて P27 の数の claim が %d 以上ある本" % A1_MIN_CLAIMS]
    cost = w[u"費用 USD(記録の cost_usd の合計)"]
    ok1 = n_books >= A1_MIN_BOOKS and between(cost, A1_COST) and not w[u"止めた理由"]
    J["A-1"] = {u"判定": HIT if ok1 else MISS, u"値": collections.OrderedDict([(u"数の claim が 10 以上の本", n_books), (u"生成できた本", w[u"生成できた本"]), (u"費用 USD", cost), (u"止めた理由", w[u"止めた理由"])])}
    med = collections.OrderedDict((f, (w[u"形 × model"][f][u"P27 の数の claim の数"] or {}).get(u"中央値")) for f in FORMS)
    J["A-2"] = {u"判定": HIT if all(between(med[f], A2_BOUNDS[f]) for f in FORMS) else MISS, u"値": med}
    L = T[u"2 札"]
    allc = L[u"札の分布"][u"全体"]
    t_rate, f_rate = allc[u"真"][u"率"], allc[u"偽"][u"率"]
    agree = L[u"2 席目との一致"][u"一致率"]
    ok3 = t_rate is not None and t_rate >= A3_TRUE_MIN and between(f_rate, A3_FALSE) and agree is not None and agree >= A3_AGREE_MIN
    J["A-3"] = {u"判定": HIT if ok3 else MISS, u"値": collections.OrderedDict([(u"真の率", t_rate), (u"偽の率", f_rate), (u"2 席目との一致率", agree)])}
    E = T[u"3 engine の判定(無改変)"]["P28E"]
    g = collections.OrderedDict((f, E[f][u"札 真の行の GROUNDED 率"][u"率"]) for f in FORMS)
    f3_lowest = g["F3"] is not None and all(g[f] is not None and g["F3"] < g[f] for f in FORMS if f != "F3")
    J["A-4"] = {u"判定": HIT if all(between(g[f], A4_BOUNDS[f]) for f in FORMS) and f3_lowest else MISS, u"値": collections.OrderedDict(list(g.items()) + [(u"F3 が最も低い", f3_lowest)])}
    ns = collections.OrderedDict()
    for f in ("F2", "F3"):
        ns[f] = pct(sum(v for k, v in E[f][u"札 真で止めた行の reason/state の内訳"].items() if k.startswith(u"no_subject/")), E[f][u"札 真で止めた率"][u"件"])
    J["A-5"] = {u"判定": HIT if all(v is not None and v >= A5_MIN for v in ns.values()) else MISS, u"値": ns}
    fa = E[u"全体"]
    stop_rate = fa[u"札 偽の行で止めた率"][u"率"]
    passed = fa[u"札 偽の行で通した数"]
    J["A-6"] = {u"判定": HIT if stop_rate is not None and stop_rate >= A6_STOP_MIN and passed <= A6_PASS_MAX else MISS,
                u"値": collections.OrderedDict([(u"止める率", stop_rate), (u"通した偽の行", passed)])}
    O = T[u"4 profile の差"][u"O の効き(P27E → P28E で GROUNDED になった行)"]
    o_all = O[u"全体"]
    o_forms = collections.OrderedDict((f, O[f]) for f in FORMS)
    f2_max = all(o_forms["F2"] > o_forms[f] for f in FORMS if f != "F2")
    J["A-7"] = {u"判定": HIT if between(o_all, A7_RANGE) and f2_max else MISS, u"値": collections.OrderedDict([(u"全体", o_all)] + list(o_forms.items()) + [(u"F2 が最多", f2_max)])}
    B = T[u"4 profile の差"][u"B の効き(P27 → P27E で no_same_value → VALUE_MISMATCH)"][u"全体"]
    J["A-8"] = {u"判定": HIT if between(B, A8_RANGE) else MISS, u"値": collections.OrderedDict([(u"全体", B)])}
    I = T[u"5 注入"]
    passes = collections.OrderedDict()
    for t in RUN.INJECT_TYPES:
        for p in ("P27", "P28E"):
            passes[u"%s %s 通した率" % (t, p)] = I[t][p][u"全体"][u"通した"][u"率"]
    orig28 = I["T8_REL"]["P28E"][u"全体"][u"名指して原本の値を返した"][u"率"]
    orig27 = I["T8_REL"]["P27"][u"全体"][u"名指して原本の値を返した"][u"率"]
    ok9 = (all(v is not None and v <= A9_PASS_MAX for v in passes.values()) and orig28 is not None and orig28 >= A9_P28E_ORIG_MIN
           and orig27 is not None and orig27 <= A9_P27_ORIG_MAX)
    J["A-9"] = {u"判定": HIT if ok9 else MISS, u"値": collections.OrderedDict(list(passes.items()) + [(u"T8_REL 名指して原本 P28E", orig28), (u"T8_REL 名指して原本 P27", orig27)])}
    gw = collections.OrderedDict()
    for f in FORMS:
        for wr in WRITERS:
            gw[(f, wr)] = E[cell_key(f, wr)][u"札 真の行の GROUNDED 率"][u"率"]
    pair = collections.OrderedDict((f, (abs(gw[(f, "W1")] - gw[(f, "W2")]) if gw[(f, "W1")] is not None and gw[(f, "W2")] is not None else None)) for f in FORMS)
    spread = collections.OrderedDict()
    for wr in WRITERS:
        vals = [gw[(f, wr)] for f in FORMS]
        spread[wr] = (max(vals) - min(vals)) if all(v is not None for v in vals) else None
    pair_max = max(pair.values()) if all(v is not None for v in pair.values()) else None
    ok10 = (pair_max is not None and pair_max <= A10_PAIR_MAX and all(v is not None and v >= A10_SPREAD_MIN for v in spread.values()))
    J["A-10"] = {u"判定": HIT if ok10 else MISS,
                 u"値": collections.OrderedDict([(u"形ごとの W1 と W2 の差の絶対値", collections.OrderedDict((f, round(v, 1) if v is not None else None) for f, v in pair.items())),
                                               (u"model ごとの形の幅", collections.OrderedDict((k, round(v, 1) if v is not None else None) for k, v in spread.items()))])}
    S = T[u"4 profile の差"][u"「その他」の形の行(provenance)"]["P28E"][u"全体"]
    ok11 = between(S[u"「その他」の形の行"], A11_RANGE) and between(S[u"決まった"][u"率"], A11_DECIDED)
    J["A-11"] = {u"判定": HIT if ok11 else MISS, u"値": collections.OrderedDict([(u"「その他」の形の行", S[u"「その他」の形の行"]), (u"決まった", S[u"決まった"][u"件"]), (u"決まった率", S[u"決まった"][u"率"])])}
    J["A-12"] = {u"判定": NOJ, u"値": collections.OrderedDict([(u"打ち切り", T[u"A-12 判定しない"][u"max_tokens で打ち切られた本"]), (u"札 判定不能", T[u"A-12 判定しない"][u"札 判定不能の中身"][u"件"])])}
    return J


def render_table(J):
    u"""結果の文書に貼る表(門が文書の表と一行も違わないことを見る)。"""
    lines = [u"| # | 判定 | 値 |", u"|---|---|---|"]
    for k, v in J.items():
        vals = u"、".join(u"%s=%s" % (kk, json.dumps(vv, ensure_ascii=False)) for kk, vv in v[u"値"].items())
        lines.append(u"| %s | %s | %s |" % (k, v[u"判定"], vals))
    c = collections.Counter(v[u"判定"] for v in J.values())
    lines.append(u"| 計 | 当たり %d・外れ %d・判定しない %d | |" % (c.get(HIT, 0), c.get(MISS, 0), c.get(NOJ, 0)))
    return u"\n".join(lines)


def run(root=ROOT, out=None, say=print):
    out = out or os.path.join(root, TALLY_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    records = load_records(root)
    T = build(records)
    J = judge(T)
    rec = collections.OrderedDict([
        (u"seal", GEN.SEAL_REL), (u"封の commit", GEN.SEAL_COMMIT), (u"step", u"AI の形 4 × model 2 ― 集計と §2 の判定(0 USD)"),
        (u"HEAD の commit", GEN.git_head(os.path.dirname(root))), (u"この script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"入力の記録の sha256", collections.OrderedDict((k, GEN.sha256_file(os.path.join(root, v))) for k, v in REC_REL.items())),
        (u"集計", T), (u"予測の判定", J),
        (u"当たり", sum(1 for v in J.values() if v[u"判定"] == HIT)), (u"外れ", sum(1 for v in J.values() if v[u"判定"] == MISS)),
        (u"判定しない", sum(1 for v in J.values() if v[u"判定"] == NOJ)), (u"key_leaks", [])])
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    if GEN.key_leaks(text, None, long_alnum=False):
        raise Stop(u"**記録に鍵らしい字が在る。書かずに止める**")
    GEN.write_text(out, text)
    say(render_table(J))
    say(u"-> %s" % out)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    run(root=a.root, out=a.out)


if __name__ == "__main__":
    main()
