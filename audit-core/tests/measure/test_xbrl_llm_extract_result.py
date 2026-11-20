# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md(198961e6・追記 a2ed6d0b・追記 2 07719813)の結果の文書 docs/XBRL_LLM_EXTRACT_RESULT_2026-11-19.md。

封の門 ``test_xbrl_llm_extract_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない・通信しない・鍵は読まない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・記録・封の門の sha256(字で留める)と、記録の script の sha256・封の commit の欄
 b 記録の数え直し: 行(止めた行は席の答えと member の欄から・語の表は便 SC・便 PA の記録の行から)と呼び出しの欄と札から、**script の関数を使わずに**、
   集計の欄・呼び出しの記録・予測の判定に要る数(参考を含む)を数え直して記録と同じことを見る
 c 結果の文書の数: 数字を含む行は全部(塊の外の表の行も)、記録から組んだ数の並びと同じ(どの行にも当たらない数字の行は赤)。文書が言う「全部が…」の類の主張も記録から数え直す
 d 予測 LX-1〜LX-11 の当たり外れを、封 §5 の字から取った境と記録の行から決め直し、文書の表の判定・件数・当たりの一覧・外れの一覧・あと何行で境をまたぐかと同じことを見る
 e 文書に禁止語・docID・要点の字・限界の節が在る
 f 封が commit から 1 字も変わっていない(履歴の 3 commit)・順序(未 commit は赤)・engine は封の commit から 0 行・記録の commit
この file は docID の字を持たない。
"""
import collections
import copy
import fractions
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SG = load_module("tests/measure/test_xbrl_llm_extract_seal.py", "llm_extract_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
MS = SG.MS
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_llm_extract_result.py"
DOC_REL = "docs/XBRL_LLM_EXTRACT_RESULT_2026-11-19.md"
SC_RECORD_REL = "fixtures/xbrl/scope_cond/stops_2026-11-19.json"
PA_RECORD_REL = SG.PA_RECORD_REL
RECORD_COMMIT_SHORT = "9f74c8e2"                              # 記録を足した commit(履歴から探した値と照らす)
SCRIPT_COMMIT_SHORT = "20be4c37"                              # 記録を書いた版の script の commit

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "0e625b4d4381dfd81f563dced5ebe13dc475394a339c97c64ac2825f49e30f01"),
    (SCRIPT_REL, "626c632760493649300b3ac8ee493f057309d69a33a40c3b805e4263d564fe1d"),
    (SEAL_GATE_REL, "098a1b5fb046e5809c5f6871e4213c8a1eb681d551db73fcb07dd221ab0b49bc")])

K_WIRE = u"配線の確認(封 §2-1。予測ではない。違えば止まる)"
K_TALLY = u"数えるもの(封 §2-5 の 1〜5。束 × 便。語の表の数を隣に)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_PRED = u"予測の判定に要る数(LX-1〜LX-11。当たり・外れは結果の文書で)"
REF_KEY = u"参考 文か見出しに元から 【 か 】 が在る行を除いた行だけの数(当たり・外れは全部の行で付ける。封 §8)"
ROW_COLUMNS = [u"便", u"本の #", u"文の種類か節", u"文の番号", u"位置", u"state", u"member が空", u"主の席の範囲", u"主の席の性質", u"副の席の範囲", u"副の席の性質",
               u"指示文の sha256", u"主の席の呼び出しの数", u"副の席の呼び出しの数", u"文に元から 【 か 】 が在る", u"見出しに元から 【 か 】 が在る"]
CALL_COLUMNS = [u"行の番号", u"席", u"答えの回", u"中断した呼び出し", u"HTTP の状態", u"HTTP の再試行の数", u"stop_reason", u"block の type の並び", u"入力 token", u"出力 token",
                u"返った usage の USD", u"見積りで数えた USD", u"返った text の字数", u"答えが読めた"]
NOANS = u"答えなし"
IN, OUT, DROP = u"内", u"外", u"除く"                          # 札の種別(便 AT の字)
BATCHES = (u"TSS", u"KAM", u"YS")
PART, PLAN = u"一部分", u"計画・予想"


# ======================================================================================================
# 道具
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel, root=ROOT):
    with io.open(os.path.join(root, rel), "rb") as fh:
        return fh.read()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def pct1(n, d):
    u"""小数 1 桁の %(四捨五入は整数の計算。門の側で独立に書く)。"""
    return u"%d.%d" % divmod((n * 2000 + d) // (2 * d), 10)


def point2(n1, d1, n2, d2):
    u"""(n1/d1 − n2/d2)× 100 を小数 2 桁(四捨五入)の字で。"""
    x = (fractions.Fraction(n1, d1) - fractions.Fraction(n2, d2)) * 100
    q = int(math.floor(x * 100 + fractions.Fraction(1, 2)))
    return u"%d.%02d" % divmod(q, 100)


def num(x):
    u"""数の字(整数は整数・小数は repr)。"""
    return u"%d" % x if float(x).is_integer() and not isinstance(x, float) else repr(x)


_REAL = {}


def real_labels():
    u"""札つきの行(読みの記録から。便 SC の読み出しを使う ― 入力の読みであって数えるのは門の側)。"""
    if "labs" not in _REAL:
        _REAL["labs"] = MS.SC.build_labels(MS.load_all_records(ROOT))
    return _REAL["labs"]


def real_stops():
    u"""便 SC・便 PA の記録の行 → 語の表の段 2 で止めたか。(S の辞書, P の辞書)。"""
    if "w" not in _REAL:
        sc = json.loads(read(SC_RECORD_REL))
        pa = json.loads(read(PA_RECORD_REL))
        _REAL["w"] = (dict((tuple(r[:5]), r[8] != u"") for r in sc[u"行"]), dict((tuple(r[:5]), r[7] != u"") for r in pa[u"行"]), len(pa[u"行"]))
    return _REAL["w"]


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)
        self.labs = copy.deepcopy(real_labels())
        self.ws, self.wp, self.pa_rows = real_stops()
        self.swap = None                                   # 変異: 束の取り違え


# ======================================================================================================
# a. sha256 と記録の来歴の欄
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


def header_problems(c):
    out = []
    r = c.rec
    if r.get(u"この script の sha256") != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が字で留めた値と違う")
    if (r.get(u"封の commit"), r.get(u"封の追記の commit"), r.get(u"封の追記 2 の commit")) != (SEAL_COMMIT_SHORT, SG.SEAL_ADDENDUM_SHORT, SG.SEAL_ADDENDUM2_SHORT):
        out.append(u"記録の封の commit・追記の commit が違う")
    if r.get(u"行の欄") != ROW_COLUMNS or r.get(u"呼び出しの欄") != CALL_COLUMNS or r.get(u"key_leaks") != [] or len(r.get(u"行", [])) != 421:
        out.append(u"記録の行の欄・呼び出しの欄・key_leaks・行の数が決めと違う")
    return out


# ======================================================================================================
# b. 数え直し(script の関数を使わない)
def is_range(l):
    return l[u"state"] == u"V" and l[u"種別"] == IN and l[u"先"] == u"範囲"


def is_plan(l):
    return l[u"state"] == u"V" and l[u"種別"] == OUT and l[u"先"] == u"見積り・計画"


def is_drop(l):
    return l[u"state"] == u"V" and l[u"種別"] == DROP


def is_other(l):
    return l[u"state"] == u"V" and not is_range(l) and not is_plan(l) and not is_drop(l)


def bucket_fns(swap=None):
    u"""束の述語。``swap`` は変異用(束の取り違え)。"""
    f = collections.OrderedDict([
        (u"range", is_range), (u"plan", is_plan), (u"other", is_other), (u"drop", is_drop),
        (u"ga", lambda l: l[u"state"] == u"G" and l[u"型"] == u"a"), (u"gb", lambda l: l[u"state"] == u"G" and l[u"型"] == u"b"),
        (u"gbr", lambda l: l[u"state"] == u"G" and l[u"型"] == u"b" and l[u"違うもの"] == u"範囲"), (u"gc", lambda l: l[u"state"] == u"G" and l[u"型"] == u"c")])
    if swap == u"range_other":
        f[u"range"], f[u"other"] = f[u"other"], f[u"range"]
    return f


def stops(a, empty):
    u"""席の答え((範囲, 性質) か None)と member が空か → (L-S, L-P, L-U)。"""
    if a is None:
        return (0, 0, 0)
    s = 1 if (a[0] == PART and empty) else 0
    p = 1 if a[1] == PLAN else 0
    return (s, p, 1 if (s or p) else 0)


def views(c):
    u"""記録の行 → 数える行。札・便 SC・便 PA の記録の行は鍵で引く(引けなければ例外)。"""
    lab = dict(((l[u"便"], l[u"#"], l[u"側"], l[u"si"], l[u"pos"]), l) for l in c.labs)
    out = []
    for r in c.rec[u"行"]:
        k = tuple(r[:5])
        l = lab[k]
        if l[u"state"] != r[5]:
            raise ValueError(u"札の state が行と違う")
        out.append({u"b": r[0], u"k": k, u"l": l, u"e": bool(r[6]), u"m": None if r[7] == NOANS else (r[7], r[8]), u"s": None if r[9] == NOANS else (r[9], r[10]),
                    u"ws": bool(c.ws[k]), u"wp": bool(c.wp[k]), u"sb": bool(r[14]), u"hb": bool(r[15]), u"sha": r[11]})
    return out


def cellv(vs):
    u"""行の集まり → 数(行, 主の L-S・L-P・L-U, 副の L-S・L-P・L-U, W-S・W-P・W-U)。"""
    ms = [stops(v[u"m"], v[u"e"]) for v in vs]
    ss = [stops(v[u"s"], v[u"e"]) for v in vs]
    d = {u"n": len(vs)}
    for i, t in enumerate(u"SPU"):
        d[u"m" + t] = sum(x[i] for x in ms)
        d[u"s" + t] = sum(x[i] for x in ss)
    d[u"WS"] = sum(1 for v in vs if v[u"ws"])
    d[u"WP"] = sum(1 for v in vs if v[u"wp"])
    d[u"WU"] = sum(1 for v in vs if v[u"ws"] or v[u"wp"])
    d[u"mnone"] = sum(1 for v in vs if v[u"m"] is None)
    d[u"snone"] = sum(1 for v in vs if v[u"s"] is None)
    return d


def overlap(vs, i, wkey):
    u"""(語の表も席も・語の表だけ・席だけ・どちらも)。主の席。"""
    a = collections.Counter()
    for v in vs:
        w = v[wkey] if wkey != u"WU" else (v[u"ws"] or v[u"wp"])
        a[(bool(w), bool(stops(v[u"m"], v[u"e"])[i]))] += 1
    return [a[(True, True)], a[(True, False)], a[(False, True)], a[(False, False)]]


def agree(vs):
    both = [v for v in vs if v[u"m"] is not None and v[u"s"] is not None]
    return {u"both": len(both), u"r": sum(1 for v in both if v[u"m"][0] == v[u"s"][0]), u"n": sum(1 for v in both if v[u"m"][1] == v[u"s"][1]),
            u"rn": sum(1 for v in both if v[u"m"] == v[u"s"])}


def calc(c):
    u"""全部の数(``D``)。束 × 便の cellv・予測の数・参考(2 つの束を除く)・重なり・席の一致・呼び出し。"""
    V = views(c)
    B = bucket_fns(c.swap)
    D = {u"V": V}
    D[u"cell"] = {}
    for name, f in B.items():
        sel = [v for v in V if f(v[u"l"])]
        D[u"cell"][name] = dict([(u"全体", cellv(sel))] + [(b, cellv([v for v in sel if v[u"b"] == b])) for b in BATCHES])
    for name, key in ((u"sb", u"sb"), (u"hb", u"hb")):
        sel = [v for v in V if v[key]]
        D[u"cell"][name] = dict([(u"全体", cellv(sel))] + [(b, cellv([v for v in sel if v[u"b"] == b])) for b in BATCHES])
    D[u"all"] = cellv(V)
    D[u"ov"] = dict((t, overlap(V, i, {u"S": u"ws", u"P": u"wp", u"U": u"WU"}[t])) for i, t in enumerate(u"SPU"))
    D[u"agree"] = agree(V)
    D[u"lx"] = lxnums(V, B)
    D[u"ref"] = lxnums([v for v in V if not (v[u"sb"] or v[u"hb"])], B)
    D[u"calls"] = call_numbers(c)
    return D


def lxnums(V, B):
    u"""LX-1〜LX-11 の数。(行, 主, 副, 語の表)の組などを辞書で。"""
    def sel(f, bs=None):
        return [v for v in V if f(v[u"l"]) and (bs is None or v[u"b"] in bs)]

    def p(vs, t):
        d = cellv(vs)
        return (d[u"n"], d[u"m" + t], d[u"s" + t], d[u"W" + t])
    rng, plan, oth, ga, gbr = sel(B[u"range"]), sel(B[u"plan"]), sel(B[u"other"]), sel(B[u"ga"]), sel(B[u"gbr"])
    both = rng + plan
    ag = agree(V)
    x = {}
    x[1] = p(rng, u"S")
    x[2] = p(sel(B[u"range"], (u"KAM", u"YS")), u"S")
    x[3] = p(ga, u"S")
    x[4] = p(plan, u"P")
    x[5] = p(sel(B[u"plan"], (u"YS",)), u"P")
    x[6] = p(ga, u"P")
    x[7] = p(gbr, u"S")
    x[8] = (p(both, u"U"), p(ga, u"U"))
    x[9] = (cellv(oth)[u"mU"], len(oth), cellv(both)[u"mU"], len(both))
    x[10] = ag
    x[11] = sum(1 for v in V if v[u"m"] is None)
    return x


def call_numbers(c):
    u"""呼び出しの欄と行から、席ごとの数。"""
    rows, calls = c.rec[u"行"], c.rec[u"呼び出し"]
    out = {}
    for tag, col_none in ((u"主", 7), (u"副", 9)):
        cs = [x for x in calls if x[1] == tag]
        real = [x for x in cs if not x[3]]
        usd_u = round(sum(x[10] for x in cs), 6)
        usd_e = round(sum(x[11] for x in cs), 6)
        out[tag] = {u"calls": len(real), u"first": sum(1 for x in real if x[2] == 1), u"redo": sum(1 for x in real if x[2] == 2), u"retries": sum(x[5] for x in real),
                    u"aborted": sum(1 for x in cs if x[3]), u"none": sum(1 for r in rows if r[col_none] == NOANS), u"tin": sum(x[8] or 0 for x in cs), u"tout": sum(x[9] or 0 for x in cs),
                    u"usd_u": usd_u, u"usd_e": usd_e, u"usd": round(usd_u + usd_e, 6),
                    u"blocks": [[k, v] for k, v in sorted(collections.Counter(x[7] for x in real if x[7] is not None).items())],
                    u"stop": [[k, v] for k, v in sorted(collections.Counter(str(x[6]) for x in real).items())],
                    u"http": [[k, v] for k, v in sorted(collections.Counter(str(x[4]) for x in real).items())]}
    out[u"total"] = round(out[u"主"][u"usd"] + out[u"副"][u"usd"], 6)
    return out


def tally_problems(c, D):
    u"""記録の集計の欄(束 × 便・重なり・席の一致)・呼び出しの記録・予測の判定に要る数(参考を含む)を、数え直した数と照らす。"""
    out = []
    T = c.rec[K_TALLY]
    names = collections.OrderedDict([
        (u"札つきの行の全部", None), (u"V 「範囲」の札", u"range"), (u"V 「見積り・計画」の札", u"plan"), (u"V 「それ以外」の札(分母から除く札は除く)", u"other"), (u"V 分母から除く札", u"drop"),
        (u"G 札 a", u"ga"), (u"G 札 b", u"gb"), (u"G 札 b のうち「違うもの」が範囲", u"gbr"), (u"G 札 c", u"gc"),
        (u"文に元から 【 か 】 が在る行(封 §8)", u"sb"), (u"見出しに元から 【 か 】 が在る行(封 §8)", u"hb")])
    for rname, key in names.items():
        for col in (u"全体",) + BATCHES:
            cell = T[rname][col]
            if key is None:
                mine = cellv([v for v in D[u"V"] if col == u"全体" or v[u"b"] == col])
            else:
                mine = D[u"cell"][key][col]
            got = {u"n": cell[u"行"], u"WS": cell[u"語の表で止めた行"][u"W-S(便 SC の段 2)"], u"WP": cell[u"語の表で止めた行"][u"W-P(便 PA の段 2)"], u"WU": cell[u"語の表で止めた行"][u"W-U(どちらか)"],
                   u"mnone": cell[u"主の席"][u"答えなしの行"], u"snone": cell[u"副の席"][u"答えなしの行"]}
            for t in u"SPU":
                got[u"m" + t] = cell[u"主の席"][u"止めた行"][u"L-" + t]
                got[u"s" + t] = cell[u"副の席"][u"止めた行"][u"L-" + t]
            if got != dict((k, mine[k]) for k in got):
                out.append(u"記録の集計が数え直しと違う: %s・%s" % (rname[:8], col))
    all_ = T[u"札つきの行の全部"][u"全体"]
    for t in u"SPU":
        if [all_[u"主の席"][u"語の表との重なり"][t][k] for k in (u"語の表も席も止めた", u"語の表だけが止めた", u"席だけが止めた", u"どちらも止めない")] != D[u"ov"][t]:
            out.append(u"記録の重なりが数え直しと違う: %s" % t)
    ag = all_[u"2 つの席の一致"]
    if (ag[u"両方の席に答えが在る行"], ag[u"範囲が同じ答えの行"], ag[u"性質が同じ答えの行"], ag[u"範囲と性質の両方が同じ答えの行"]) != (D[u"agree"][u"both"], D[u"agree"][u"r"], D[u"agree"][u"n"], D[u"agree"][u"rn"]):
        out.append(u"記録の席の一致が数え直しと違う")
    cl = c.rec[K_CALLS]
    for tag in (u"主", u"副"):
        m, g = D[u"calls"][tag], cl[tag]
        got = {u"calls": g[u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], u"first": g[u"うち 1 回目"], u"redo": g[u"答えのやり直し(封 §2-3)"], u"retries": g[u"HTTP の再試行(429・5xx)の合計"],
               u"aborted": g[u"中断した(次の走りで見つけた・上限で止めた)呼び出し"], u"none": g[u"答えなしの行"], u"tin": g[u"入力 token の合計"], u"tout": g[u"出力 token の合計"],
               u"usd_u": g[u"USD(返った usage で。§3 の単価)"], u"usd_e": g[u"USD(返らなかった呼び出しの見積りで数えた分)"], u"usd": g[u"USD 合計"], u"blocks": g[u"返った block の type の並びの種類"],
               u"stop": g[u"stop_reason の種類"], u"http": g[u"HTTP の状態の種類"]}
        if got != m:
            out.append(u"記録の呼び出しの記録が数え直しと違う: %s" % tag)
    if cl[u"USD の全部"] != D[u"calls"][u"total"] or c.rec[u"費用"][u"使った額 USD"] != D[u"calls"][u"total"]:
        out.append(u"記録の USD の全部・使った額が数え直しと違う")
    pr = c.rec[K_PRED]

    def pk(d, prefix):
        ks = [k for k in d if k.startswith(prefix)]
        if len(ks) != 1:
            raise ValueError(prefix)
        return d[ks[0]]

    def pair(d):
        return (d[u"行"], d[u"主の席"], d[u"副の席"], d[u"語の表"])
    for src, lx in ((pr, D[u"lx"]), (pr[REF_KEY], D[u"ref"])):
        for i in range(1, 8):
            if pair(pk(src, u"LX-%d " % i)) != lx[i]:
                out.append(u"記録の予測の判定に要る数が数え直しと違う: LX-%d%s" % (i, u"(参考)" if src is not pr else u""))
        l8 = pk(src, u"LX-8 ")
        if (pair(l8[u"V 「範囲」と「見積り・計画」の合わせ"]), pair(l8[u"G 札 a"])) != lx[8]:
            out.append(u"記録の LX-8 が数え直しと違う")
        l9 = pk(src, u"LX-9 ")
        if (l9[u"V 「それ以外」の札"][u"分子"], l9[u"V 「それ以外」の札"][u"分母"], l9[u"V 「範囲」と「見積り・計画」の合わせ"][u"分子"], l9[u"V 「範囲」と「見積り・計画」の合わせ"][u"分母"]) != lx[9]:
            out.append(u"記録の LX-9 が数え直しと違う")
        l10 = pk(src, u"LX-10 ")
        if (l10[u"範囲"][u"分子"], l10[u"範囲"][u"分母"], l10[u"性質"][u"分子"], l10[u"性質"][u"分母"]) != (lx[10][u"r"], lx[10][u"both"], lx[10][u"n"], lx[10][u"both"]):
            out.append(u"記録の LX-10 が数え直しと違う")
        if pk(src, u"LX-11 ") != lx[11]:
            out.append(u"記録の LX-11 が数え直しと違う")
    wire = c.rec[K_WIRE]
    if wire[u"member の欄が空の行"] != sum(1 for v in D[u"V"] if v[u"e"]) or wire[u"文に元から 【 か 】 が在る行(封 §8)"] != D[u"cell"][u"sb"][u"全体"][u"n"] or \
            wire[u"見出しに元から 【 か 】 が在る行(封 §8)"] != D[u"cell"][u"hb"][u"全体"][u"n"] or wire[u"送る行の数(札つきで同じ state で引けた行)"] != D[u"all"][u"n"]:
        out.append(u"記録の配線の確認の数が数え直しと違う")
    for b in BATCHES:
        for s in (u"V", u"G"):
            if wire[u"便ごとの送る行(V・G)"][b][s] != sum(1 for v in D[u"V"] if v[u"b"] == b and v[u"l"][u"state"] == s):
                out.append(u"記録の便ごとの送る行が数え直しと違う")
    return out


def recount_problems(c):
    try:
        D = calc(c)
    except (KeyError, ValueError) as e:
        return [u"数え直せない(%s)" % type(e).__name__]
    return tally_problems(c, D)


# ======================================================================================================
# d. 判定(封 §5 の字の境から決め直す)
def seal_bounds(seal):
    u"""封 §5 の表の予測の欄から境を取る。{1: (下, 上), 2: 下, 3: (下, 上), 4: 下, 5: 下, 6: 上, 7: 下, 8: (V の差の下, G の差の上), 9: ポイント, 10: %, 11: 上}。"""
    rows = {}
    for ln in seal.split(u"\n"):
        m = re.match(r"\| LX-(\d+) \| (.*?) \| (.*?) \|$", ln)
        if m:
            rows[int(m.group(1))] = m.group(2)
    g = lambda i, pat: re.search(pat, rows[i])
    b = {}
    m = g(1, r"(\d+) 行以上 (\d+) 行以下")
    b[1] = (int(m.group(1)), int(m.group(2)))
    b[2] = int(g(2, r"(\d+) 行以上を止める").group(1))
    m = g(3, r"(\d+) 行以上 (\d+) 行以下")
    b[3] = (int(m.group(1)), int(m.group(2)))
    b[4] = int(g(4, r"(\d+) 行以上を止める").group(1))
    b[5] = int(g(5, r"(\d+) 行以上を止める").group(1))
    b[6] = int(g(6, r"(\d+) 行以下").group(1))
    b[7] = int(g(7, r"(\d+) 行以上を止める").group(1))
    m = g(8, r"(\d+) 行以上多く止め.*?(\d+) 行多い数まで")
    b[8] = (int(m.group(1)), int(m.group(2)))
    b[9] = int(g(9, r"(\d+) ポイント以上低い").group(1))
    b[10] = int(g(10, r"(\d+)% 以上").group(1))
    b[11] = int(g(11, r"(\d+) 行以下").group(1))
    return b


def judge(c, D=None):
    u"""LX-1〜LX-11 の当たり(True)・外れ(False)と、あと何行で境をまたぐか(境に近い印。向きと行数)。封 §5 の境と数え直した数だけから。"""
    D = D or calc(c)
    b = seal_bounds(c.seal)
    x = D[u"lx"]
    j, near = {}, {}
    j[1] = b[1][0] <= x[1][1] <= b[1][1]
    j[2] = x[2][1] >= b[2]
    j[3] = b[3][0] <= x[3][1] <= b[3][1]
    j[4] = x[4][1] >= b[4]
    j[5] = x[5][1] >= b[5]
    j[6] = x[6][1] <= b[6]
    j[7] = x[7][1] >= b[7]
    (vn, vm, vs_, vw), (gn, gm, gs, gw) = x[8]
    j[8] = (vm - vw >= b[8][0]) and (gm - gw <= b[8][1])
    on, od_, bn, bd = x[9]
    j[9] = point2(bn, bd, on, od_) is not None and fractions.Fraction(bn, bd) * 100 - fractions.Fraction(on, od_) * 100 >= b[9]
    a = x[10]
    j[10] = fractions.Fraction(a[u"r"], a[u"both"]) * 100 >= b[10] and fractions.Fraction(a[u"n"], a[u"both"]) * 100 >= b[10]
    j[11] = x[11] <= b[11]
    near[3] = x[3][1] - b[3][1]                         # 上に何行(外れのとき)
    near[6] = (b[6] + 1) - x[6][1]                      # あと何行で外れ(当たりのとき)
    near[11] = (b[11] + 1) - x[11]
    near[8] = (gm - gw) - b[8][1]                       # 境を何行超えたか
    return j, near, b


def judge_problems(c):
    out = []
    try:
        D = calc(c)
        j, near, b = judge(c, D)
    except (KeyError, ValueError, ZeroDivisionError, AttributeError, TypeError) as e:
        return [u"判定を決め直せない(%s)" % type(e).__name__]
    hits = [i for i in range(1, 12) if j[i]]
    miss = [i for i in range(1, 12) if not j[i]]
    if miss != [3, 7, 8, 10] or len(hits) != 7:
        out.append(u"決め直した判定が字で留めた判定(当たり 7・外れ LX-3・LX-7・LX-8・LX-10)と違う: 外れ %s" % (miss,))
    # 文書の表の判定・件数・一覧
    doc = c.doc
    for i in range(1, 12):
        ln = [x for x in doc.split(u"\n") if x.startswith(u"| LX-%d |" % i)]
        if len(ln) != 1:
            out.append(u"文書の表に LX-%d の行が 1 つで無い" % i)
            continue
        cells = [x.strip() for x in ln[0].strip(u"|").split(u"|")]
        want = u"当たり" if j[i] else u"外れ"
        if len(cells) != 4 or not cells[3].startswith(want) or (j[i] and cells[3].startswith(u"外れ")):
            out.append(u"文書の LX-%d の判定が決め直した判定(%s)と違う" % (i, want))
    ids = lambda xs: u"・".join(u"LX-%d" % i for i in xs)
    if (u"当たり %d(%s)・外れ %d(%s)" % (len(hits), ids(hits), len(miss), ids(miss))) not in doc:
        out.append(u"文書の当たり・外れの一覧が決め直した判定と違う")
    if (u"判定した 11 本のうち当たり %d・外れ %d(%s)" % (len(hits), len(miss), ids(miss))) not in doc:
        out.append(u"文書の先頭の件数が決め直した判定と違う")
    if (u"あと %d 行で外れ" % near[6]) not in doc or (u"あと %d 行で外れ" % near[11]) not in doc:
        out.append(u"文書の「あと何行で外れ」が数え直しと違う")
    if (u"外れ(上に %d 行)" % near[3]) not in doc or (u"それを %d 行超えた" % near[8]) not in doc:
        out.append(u"文書の「上に何行」「何行超えた」が数え直しと違う")
    if j[1] is False or j[4] is False:
        out.append(u"LX-1・LX-4 が下に外れている(封 §5 の「先に自分の欠陥を疑う」が発火する)")
    # 記録の予測の判定に要る数の行から読み直した判定とも同じ(記録は判定を書かない)
    pr = c.rec[K_PRED]
    if [k[:5] for k in pr if k.startswith(u"LX-")][:2] != [u"LX-1 ", u"LX-2 "]:
        out.append(u"記録の予測の判定に要る数の並びが違う")
    return out


# ======================================================================================================
# c. 文書の数(数字を含む行は全部、記録から組んだ数の並びと同じ)
CLEAN = (r"`[^`]*`", r"\b[0-9a-f]{8}\b", r"§\d+(?:-\d+)?", r"2026-11-\d\d", r"LX-\d+", r"claude-[a-z]+-\d-\d", r"P33E", r"sha256")
TOK = re.compile(r"\d[\d,]*(?:\.\d+)?")


def tokens(line):
    for p in CLEAN:
        line = re.sub(p, u"", line)
    return TOK.findall(line)


def usd(x):
    return repr(x)


def expected_lines(c, D=None, J=None):
    u"""(行を見つける正規表現, 期待する数の並び)の一覧。記録・数え直し・判定・封の境から組む。構造の数(「2 つの席」など)は字で留める。"""
    D = D or calc(c)
    j, near, b = J or judge(c, D)
    x, ref, cl = D[u"lx"], D[u"ref"], D[u"calls"]
    cell, V = D[u"cell"], D[u"V"]
    hits = sum(1 for i in range(1, 12) if j[i])
    miss = 11 - hits
    s = lambda *a: [u"%d" % t for t in a]
    (vn, vm, vs_, vw), (gn, gm, gs, gw) = x[8]
    on, od_, bn, bd = x[9]
    a = x[10]
    ga, gaK, gaY = cell[u"ga"][u"全体"], cell[u"ga"][u"KAM"], cell[u"ga"][u"YS"]
    rg = cell[u"range"]
    wire = c.rec[K_WIRE]
    pa_n = c.pa_rows
    E = []
    add = lambda pat, toks: E.append((pat, toks))
    add(r"^# 結果", s(2))
    add(r"^封 `docs", s(2, 0) + [usd(cl[u"total"]), u"15", u"0"])
    add(r"^この文書の数は全部", s(1))
    add(r"^- 判定した", s(11, hits, miss))
    add(r"^- \*\*封 §5 の読み方", s(vn, vm - vw, vm, vw, gn, gm - gw, gm, gw, b[8][1], (gm - gw) - b[8][1]))
    add(r"^- 正しい結びを減らした分", s(ga[u"mU"], gaK[u"mU"], gaK[u"n"], gaY[u"mU"], gaY[u"n"]))
    add(r"^- 副の席\(", s(ga[u"sU"], ga[u"n"], 2, a[u"r"], a[u"both"]) + [pct1(a[u"r"], a[u"both"]), u"%d" % b[10]])
    add(r"^- 読みの札は AI の席", s(1, 1))
    add(r"^- `temperature` は送って", s(1))
    add(r"^- 材料に元から", s(cell[u"sb"][u"全体"][u"n"] + cell[u"hb"][u"全体"][u"n"], cell[u"sb"][u"全体"][u"n"], cell[u"hb"][u"全体"][u"n"], x[5][0], 2))
    add(r"^- 送ったのは札つきの", s(D[u"all"][u"n"], pa_n))
    add(r"^封 §5 の字の境", s(1))
    P = lambda i: s(x[i][0], 0, 0, 0)
    add(r"^\| LX-1 \|", s(x[1][0], b[1][0], b[1][1], x[1][1], x[1][0], x[1][2], x[1][3]))
    add(r"^\| LX-2 \|", s(x[2][0], b[2], x[2][1], x[2][0], x[2][2], x[2][3]))
    add(r"^\| LX-3 \|", s(x[3][0], b[3][0], b[3][1], x[3][1], x[3][0], x[3][2], x[3][3], near[3]))
    add(r"^\| LX-4 \|", s(x[4][0], b[4], x[4][1], x[4][0], x[4][2], x[4][3]))
    add(r"^\| LX-5 \|", s(x[5][0], b[5], x[5][1], x[5][0], x[5][2], x[5][3]))
    add(r"^\| LX-6 \|", s(x[6][0], b[6], x[6][1], x[6][0], x[6][2], x[6][3], near[6]))
    add(r"^\| LX-7 \|", s(x[7][0], b[7], x[7][1], x[7][0], x[7][2], x[7][3]))
    add(r"^\| LX-8 \|", s(vn, b[8][0], b[8][1], vm, vw, vm - vw, gm, gw, gm - gw))
    add(r"^\| LX-9 \|", s(b[9], on, od_) + [pct1(on, od_)] + s(bn, bd) + [pct1(bn, bd), point2(bn, bd, on, od_)])
    add(r"^\| LX-10 \|", s(2, b[10], a[u"r"], a[u"both"]) + [pct1(a[u"r"], a[u"both"])] + s(a[u"n"], a[u"both"]) + [pct1(a[u"n"], a[u"both"])])
    add(r"^\| LX-11 \|", s(b[11], x[11], near[11]))
    add(r"^- 当たり \d+\(", s(hits, miss))
    add(r"^- LX-3 の外れは", s(near[3], cell[u"ga"][u"KAM"][u"mS"], cell[u"ga"][u"YS"][u"mS"], x[7][0], x[7][1], x[7][0], cell[u"gbr"][u"全体"][u"mP"]))
    add(r"^- LX-4 は", s(x[4][1], x[4][0], x[5][0]))
    add(r"^- 送った行 \d+", s(D[u"all"][u"n"], wire[u"便ごとの送る行(V・G)"][u"TSS"][u"V"], wire[u"便ごとの送る行(V・G)"][u"KAM"][u"V"], wire[u"便ごとの送る行(V・G)"][u"KAM"][u"G"],
                          wire[u"便ごとの送る行(V・G)"][u"YS"][u"V"], wire[u"便ごとの送る行(V・G)"][u"YS"][u"G"], wire[u"封の行の数"], wire[u"送る行の鍵の重なり"],
                          wire[u"送る行の(鍵, state)が便 PA の記録の行に在る"][u"無い行"], wire[u"member の欄が空の行"], wire[u"見出しが無い行((なし))"]))
    add(r"^- 文か見出しに元から", s(wire[u"文か見出しに元から 【 か 】 が在る行(数えるだけ。字は変えない)"], wire[u"文に元から 【 か 】 が在る行(封 §8)"], wire[u"見出しに元から 【 か 】 が在る行(封 §8)"]))
    add(r"^- `--check`", s(0, 421))
    add(r"^\| 席 \| model", s(1))
    for tag, row in ((u"主", r"^\| 主 \| claude"), (u"副", r"^\| 副 \| claude")):
        m = cl[tag]
        add(row, s(m[u"calls"], m[u"first"], m[u"redo"], m[u"none"], m[u"aborted"], m[u"tin"], m[u"tout"]) + [usd(m[u"usd"])])
    st = dict((k, v) for k, v in cl[u"主"][u"stop"])
    add(r"^- 返った block は", s(st.get(u"end_turn", 0), st.get(u"max_tokens", 0), dict(cl[u"副"][u"stop"]).get(u"end_turn", 0), 200, cl[u"主"][u"none"], 2, 200))
    add(r"^- 中断した呼び出し", s(1, 1, 400) + [usd(cl[u"主"][u"usd_e"])])
    add(r"^- USD は返った usage", s(5, 25, 100))
    add(r"^- 封 §9 のとおり、司令塔", s(3) + [u"0.01"])
    add(r"^L-S・L-P・L-U は席", s(2))
    rows3 = ((u"range", r"^\| V 「範囲」の札 \| \d+ \|"), (u"plan", r"^\| V 「見積り・計画」の札 \| \d+ \|"), (u"other", r"^\| V 「それ以外」の札 \| \d+ \|"), (u"ga", r"^\| G 札 a \| \d+ \|"),
             (u"gb", r"^\| G 札 b \| \d+ \|"), (u"gc", r"^\| G 札 c \| \d+ \|"), (u"sb", r"^\| 文に元から【】の在る行 \| \d+ \|"), (u"hb", r"^\| 見出しに元から【】の在る行 \| \d+ \|"))
    for key, pat in rows3:
        d = cell[key][u"全体"]
        add(pat, s(d[u"n"], d[u"mS"], d[u"mP"], d[u"mU"], d[u"sU"], d[u"WS"], d[u"WP"], d[u"WU"]))
    rowsb = ((u"range", r"^\| V 「範囲」の札 \| \d+/\d+"), (u"plan", r"^\| V 「見積り・計画」の札 \| \d+/\d+"), (u"other", r"^\| V 「それ以外」の札 \| \d+/\d+"), (u"ga", r"^\| G 札 a \| \d+/\d+"))
    for key, pat in rowsb:
        t = []
        for bt in BATCHES:
            d = cell[key][bt]
            t += s(d[u"mU"], d[u"n"]) + (s(d[u"WU"]) if d[u"n"] else [])
        add(pat, t)
    add(r"^参考: 文か見出しに", s(cell[u"sb"][u"全体"][u"n"] + cell[u"hb"][u"全体"][u"n"], D[u"all"][u"n"] - cell[u"sb"][u"全体"][u"n"] - cell[u"hb"][u"全体"][u"n"]))
    r = ref
    ra = r[10]
    (rvn, rvm, _rvs, rvw), (rgn, rgm, _rgs, rgw) = r[8]
    ron, rod, rbn, rbd = r[9]
    add(r"^- LX-1 \d+/\d+\(語の表", s(r[1][1], r[1][0], r[1][3], r[2][1], r[2][0], r[2][3], r[3][1], r[3][0], r[3][3], r[4][1], r[4][0], r[4][3], r[5][0], r[6][1], r[6][0], r[6][3], r[7][0],
                                  rvm, rvn, rvw, rgm, rgn, rgw, ron, rod) + [pct1(ron, rod)] + s(rbn, rbd) + [pct1(rbn, rbd)] + s(ra[u"r"], ra[u"both"]) + [pct1(ra[u"r"], ra[u"both"])] +
        s(ra[u"n"], ra[u"both"]) + [pct1(ra[u"n"], ra[u"both"])] + s(r[11]))
    add(r"^- 除いた残りでも", s(rgm, rgw, b[8][1]))
    add(r"^## §4", s(421))
    for t, pat in ((u"S", r"^\| S \| \d+ \|"), (u"P", r"^\| P \| \d+ \|"), (u"U", r"^\| U \| \d+ \|")):
        add(pat, s(*D[u"ov"][t]))
    ovu = D[u"ov"][u"U"]
    add(r"^- 語の表で止めた", s(ovu[0] + ovu[1], ovu[0], ovu[2]))
    add(r"^- 言えること: 同じ行", s(1, 1, vm, vw, vn, x[4][1], x[5][3], x[5][1], x[5][0]))
    add(r"^- 言えること: 同時に", s(2, gm, gw, gn))
    add(r"^- 言えないこと", s(1))
    add(r"^- 人間に返すこと", s(cell[u"ga"][u"KAM"][u"mU"]))
    # 構造の数(限界の節。封・script の字から。字で留める)
    add(r"^- 答えを返した呼び出しは", s(2, 1, 400))
    add(r"^- 置き場の進捗の file", s(400))
    add(r"^- 400 の断りの文は", s(400, 300, 1))
    add(r"^- 門が走らせていない枝", s(401, 403, 200, 429, 5))
    add(r"^- 指示文の sha256 は", s(len(set(v[u"sha"] for v in V)), 421, 421 - len(set(v[u"sha"] for v in V))))
    add(r"^- 【 】の囲み方", s(1, 1))
    return E


def doc_problems(c):
    out = []
    try:
        D = calc(c)
        J = judge(c, D)
        E = expected_lines(c, D, J)
    except (KeyError, ValueError, ZeroDivisionError, AttributeError, TypeError, IndexError) as e:
        return [u"文書の期待を組めない(%s)" % type(e).__name__]
    lines = c.doc.split(u"\n")
    used = collections.Counter()
    for ln in lines:
        tk = tokens(ln)
        if not tk:
            continue
        hit = [i for i, (pat, _t) in enumerate(E) if re.search(pat, ln)]
        if len(hit) != 1:
            out.append(u"文書の数字を含む行がどの期待にも 1 つで当たらない: %s" % ln[:24])
            continue
        used[hit[0]] += 1
        if tk != E[hit[0]][1]:
            out.append(u"文書の数が記録から組んだ数と違う: %s ― 文書 %s・記録 %s" % (ln[:20], tk, E[hit[0]][1]))
    for i, (pat, _t) in enumerate(E):
        if used[i] != 1:
            out.append(u"期待の行が文書に 1 つで無い(%d): %s" % (used[i], pat[:24]))
    out.extend(claims_problems(c, D))
    return out


def claims_problems(c, D):
    u"""文書が言う、数字の字面に出ない主張(「全部が…」)を記録から数え直す。"""
    out = []
    V, cell = D[u"V"], D[u"cell"]
    if cell[u"sb"][u"KAM"][u"n"] != cell[u"sb"][u"全体"][u"n"] or cell[u"hb"][u"YS"][u"n"] != cell[u"hb"][u"全体"][u"n"]:
        out.append(u"「文の中 19 行は全部 KAM・見出し 150 行は全部 YS」が記録と違う")
    if any(v[u"hb"] is False for v in V if v[u"b"] == u"YS" and is_plan(v[u"l"])):
        out.append(u"「YS の見積り・計画の札の 7 行は全部が見出しに 【 の在る行」が記録と違う")
    if sum(1 for v in V if v[u"sb"] and v[u"hb"]) != 0:
        out.append(u"「重なりなし」が記録と違う")
    if any(v[u"b"] != u"YS" for v in V if bucket_fns()[u"gbr"](v[u"l"])):
        out.append(u"「札 b の違うものが範囲の 15 行は全部 YS」が記録と違う")
    if cell[u"ga"][u"TSS"][u"n"] != 0:
        out.append(u"「TSS の G に札が無い」が記録と違う")
    calls, rows = c.rec[u"呼び出し"], c.rec[u"行"]
    none_rows = [i for i, r in enumerate(rows) if r[7] == NOANS]
    for i in none_rows:
        cs = [x for x in calls if x[0] == i and x[1] == u"主" and not x[3]]
        if len(cs) != 2 or any(x[6] != u"max_tokens" for x in cs):
            out.append(u"「答えなしの行は 2 回とも max_tokens で止まった行」が記録と違う")
    ab = [x for x in calls if x[3]]
    if len(ab) != 1 or ab[0][4] != 400 or ab[0][11] != 0.007875 or ab[0][1] != u"主":
        out.append(u"「中断した呼び出し 1 は試しの 1 回目の HTTP 400(0.007875 USD)」が記録と違う")
    if len(set(v[u"sha"] for v in V)) != 418:
        out.append(u"「指示文の sha256 は 418 種類」が記録と違う")
    if D[u"calls"][u"主"][u"blocks"] != [[u"text", 424]] or D[u"calls"][u"副"][u"blocks"] != [[u"text", 421]]:
        out.append(u"「返った block はどの呼び出しも text だけ」が記録と違う")
    if D[u"calls"][u"主"][u"http"] != [[u"200", 424]] or D[u"calls"][u"副"][u"http"] != [[u"200", 421]]:
        out.append(u"「HTTP の状態は全部 200」が記録と違う")
    return out


# ======================================================================================================
# e. 文書の言葉・節・限界
FORBIDDEN = (u"全部当たった", u"人の" + u"目", u"勧める必要はない", u"証明した")
REQUIRED = (u"先に負けと限界を書く", u"席は語の表を上回らない", u"盲検でない", u"人は読んでいない", u"系統の癖の一致", u"繰り返しの幅は測っていない", u"止めた行の中身は誰も読んでいない",
            u"人間に返すこと", u"監査の所見で直していないもの", u"言えないこと", u"engine は 0 行", u"封も予測も、結果を見てから書き換えていない", u"有料: LLM の席(API)を呼んだ")
SECTIONS = (u"## §1 ", u"## §2 ", u"## §3 ", u"## §4 ", u"## §5 ", u"## §6 ")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")


def words_problems(c):
    out = [u"禁止語が文書に在る: %s" % w for w in FORBIDDEN if w in c.doc]
    out += [u"文書に要点の字が無い: %s" % w[:12] for w in REQUIRED if w not in c.doc]
    out += [u"文書の節が無い: %s" % s_ for s_ in SECTIONS if s_ not in c.doc]
    if DOCID_RE.search(c.doc):
        out.append(u"文書に docID の形の字が在る")
    if re.search(r"[〇一二三四五六七八九十百千]{3,}", c.doc):
        out.append(u"文書に 3 字以上の漢数字が在る(数の門を逃がす)")
    return out


def seal_problems(c):
    u"""封に文書が根にする字(境の字・追記)が在り、境が取れる。"""
    out = []
    for need in (u"## §5 ", u"| LX-1 |", u"| LX-11 |", u"## §8 追記", u"## §9 追記", u"上限の替え", u"読み方の決め"):
        if need not in c.seal:
            out.append(u"封に %s が無い" % need)
    try:
        b = seal_bounds(c.seal)
        if b != {1: (60, 94), 2: 15, 3: (4, 16), 4: 22, 5: 4, 6: 10, 7: 5, 8: (10, 5), 9: 30, 10: 85, 11: 5}:
            out.append(u"封 §5 から取った境が字で留めた境と違う: %s" % (b,))
    except (AttributeError, ValueError, KeyError, TypeError):
        out.append(u"封 §5 の境が取れない")
    return out


# ======================================================================================================
# f. 封・順序・engine・記録の commit
def frozen_problems(text, commit, rel, root=REPO):
    rc, _ = PR.git_in(root, "cat-file", "-e", commit + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (commit, PREFIX, rel)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    return [] if text.encode("utf-8").startswith(r.stdout.rstrip(b"\n")) else [u"封が %s のときの字から(頭が)変わっている" % commit]


def seal_frozen_problems(c):
    return frozen_problems(c.seal, SEAL_COMMIT_SHORT, SEAL_REL) + SG.seal_history_problems()


def order_problems_real(root=REPO):
    u"""封 ⊏ script・封の門 ⊑ 記録 ⊑ 結果の文書・この門(未 commit は赤)。"""
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL], [RECORD_REL, DOC_REL, GATE_REL])


def record_commit_problems(root=REPO):
    out = []
    c = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(c) != 1 or not c[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が履歴に 1 つで字で持つ hash と一致しない")
    rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + SCRIPT_REL)
    if not last.startswith(SCRIPT_COMMIT_SHORT):
        out.append(u"script の最後の commit が字で持つ hash(記録を書いた版)と違う")
    return out


def engine_problems(root=REPO):
    return list(SG.engine_zero_problems(root))


# ======================================================================================================
# 変異の表
CHECKS = collections.OrderedDict([
    (u"sha", lambda c: sha_problems(c.texts)),
    (u"header", header_problems),
    (u"recount", recount_problems),
    (u"doc", doc_problems),
    (u"judge", judge_problems),
    (u"words", words_problems),
    (u"seal", seal_problems),
    (u"frozen", seal_frozen_problems),
])
MUTATIONS = []


def M(label, check, fn):
    MUTATIONS.append((label, check, fn))


def doc_replace(old, new, every=False):
    def f(c):
        n = c.doc.count(old)
        assert n >= 1 and (every or n == 1), (old, n)
        c.doc = c.doc.replace(old, new)
    return f


def seal_replace(old, new):
    def f(c):
        assert c.seal.count(old) == 1, old
        c.seal = c.seal.replace(old, new)
    return f


def rec_edit(fn):
    def f(c):
        fn(c.rec)
    return f


def text_edit(rel, fn):
    def f(c):
        c.texts[rel] = fn(c.texts[rel])
    return f


def set_swap(c):
    c.swap = u"range_other"


# 予測(変異を走らせる前に書いた。どの検査が赤になるか): 記録の数を替える → recount(と、予測の判定に要る数)・文書の数を替える → doc・判定を替える → judge・境を替える → judge・束を取り違える → recount と doc
M(u"記録: 行の主の席の範囲を 1 つ替える(一部分 → 全体)", u"recount", rec_edit(lambda r: [r[u"行"][i].__setitem__(7, u"全体") for i in range(len(r[u"行"])) if r[u"行"][i][7] == PART][:1]))
M(u"記録: 呼び出しの欄の入力 token を 1 つ替える", u"recount", rec_edit(lambda r: r[u"呼び出し"][1].__setitem__(8, r[u"呼び出し"][1][8] + 1)))
M(u"記録: 予測の判定に要る数の 1 つを替える(LX-11)", u"recount", rec_edit(lambda r: r[K_PRED].__setitem__(u"LX-11 主の席の答えなしの行", 4)))
M(u"記録: 参考の LX-1 の行の数を替える", u"recount", rec_edit(lambda r: r[K_PRED][REF_KEY][u"LX-1 L-S の止めた行 / V 「範囲」の札"].__setitem__(u"主の席", 75)))
M(u"記録: 集計の欄の 1 つを替える", u"recount", rec_edit(lambda r: r[K_TALLY][u"G 札 a"][u"全体"].__setitem__(u"行", 213)))
M(u"記録: 行の「見出しに元から 【 が在る」の欄を 1 つ替える", u"recount", rec_edit(lambda r: r[u"行"][0].__setitem__(15, True)))
M(u"記録: 使った額を替える", u"recount", rec_edit(lambda r: r[u"費用"].__setitem__(u"使った額 USD", 2.7)))
M(u"記録: script の sha256 の欄を替える", u"header", rec_edit(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64)))
M(u"記録: 封の追記 2 の commit を替える", u"header", rec_edit(lambda r: r.__setitem__(u"封の追記 2 の commit", u"07719814")))
M(u"字: 記録の 1 byte を替える", u"sha", text_edit(RECORD_REL, lambda b: b + b" "))
M(u"字: script の 1 byte を替える", u"sha", text_edit(SCRIPT_REL, lambda b: b + b" "))
M(u"文書: §1 の表の数を 1 つ替える(LX-1 の 82)", u"doc", doc_replace(u"82/104(副 85・語の表 53)", u"81/104(副 85・語の表 53)"))
M(u"文書: §3 の表の数を 1 つ替える(G 札 a の行)", u"doc", doc_replace(u"| G 札 a | 214 | 29 | 7 | 36 | 94 | 9 | 6 | 15 |", u"| G 札 a | 214 | 29 | 7 | 37 | 94 | 9 | 6 | 15 |"))
M(u"文書: §3 の便ごとの表の数を 1 つ替える", u"doc", doc_replace(u"| 58/75(43) |", u"| 57/75(43) |"))
M(u"文書: §4 の表の数を 1 つ替える", u"doc", doc_replace(u"| S | 57 | 8 | 66 | 290 |", u"| S | 57 | 8 | 67 | 290 |"))
M(u"文書: 先頭の散文の数を 1 つ替える(36 対 15)", u"doc", doc_replace(u"(109 対 73)", u"(109 対 74)"))
M(u"文書: 呼び出しの表の USD を替える", u"doc", doc_replace(u"1.396095", u"1.396096"))
M(u"文書: 参考の行の数を替える", u"doc", doc_replace(u"LX-3 25/86(9)", u"LX-3 25/85(9)"))
M(u"文書: 限界の節の数を替える(418 種類)", u"doc", doc_replace(u"418 種類", u"417 種類"))
M(u"文書: 数字を含む行を 1 つ足す(記録に無い数)", u"doc", lambda c: setattr(c, u"doc", c.doc + u"\n- 席の答えは 123 行で変わった。\n"))
M(u"記録: 文の中に印が在る行を KAM から YS へ 1 行入れ替える(件数は同じ・文書の「全部 KAM」が崩れる)", u"doc", rec_edit(lambda r: (
    r[u"行"][[n for n, x in enumerate(r[u"行"]) if x[0] == u"KAM" and x[14]][0]].__setitem__(14, False),
    r[u"行"][[n for n, x in enumerate(r[u"行"]) if x[0] == u"YS" and not x[14] and not x[15]][0]].__setitem__(14, True))))
M(u"文書: 判定を 1 つ替える(LX-1 当たり → 外れ)", u"judge", doc_replace(u"| 82/104(副 85・語の表 53) | 当たり |", u"| 82/104(副 85・語の表 53) | 外れ |"))
M(u"文書: 判定を 1 つ替える(LX-8 外れ → 当たり)", u"judge", doc_replace(u"| 外れ(G の側) |", u"| 当たり |"))
M(u"文書: 当たりの一覧から 1 つ落とす", u"judge", doc_replace(u"当たり 7(LX-1・LX-2・", u"当たり 7(LX-2・"))
M(u"文書: 「あと 4 行で外れ」を替える", u"judge", doc_replace(u"あと 4 行で外れ", u"あと 5 行で外れ"))
M(u"文書: 外れの件数を替える", u"judge", doc_replace(u"外れ 4(LX-3・LX-7・LX-8・LX-10)。\n- **封", u"外れ 3(LX-3・LX-7・LX-8・LX-10)。\n- **封"))
M(u"封: LX-6 の境を替える(10 行以下 → 6 行以下)", u"judge", seal_replace(u"札 a の G の行は、214 行のうち 10 行以下", u"札 a の G の行は、214 行のうち 6 行以下"))
M(u"封: LX-1 の境を替える(60 行以上 → 90 行以上)", u"judge", seal_replace(u"のうち 60 行以上 94 行以下", u"のうち 90 行以上 94 行以下"))
M(u"封: LX-8 の境を替える(5 行多い → 40 行多い)", u"judge", seal_replace(u"W-U より 5 行多い数まで", u"W-U より 40 行多い数まで"))
M(u"封: LX-10 の境を替える(85% → 70%)", u"judge", seal_replace(u"の 85% 以上", u"の 70% 以上"))
M(u"封: LX-11 の境を替える(5 行以下 → 2 行以下)", u"judge", seal_replace(u"主の席の答えなしは 5 行以下", u"主の席の答えなしは 2 行以下"))
M(u"封: 境の字を替える(LX-3 の 16 → 12)", u"seal", seal_replace(u"4 行以上 16 行以下", u"4 行以上 12 行以下"))
M(u"数え直し: 「範囲」と「それ以外」の束を取り違える", u"recount", set_swap)
M(u"数え直し: 束を取り違える(判定も)", u"judge", set_swap)
M(u"数え直し: 束を取り違える(文書の数も)", u"doc", set_swap)
M(u"文書: 禁止語を足す", u"words", lambda c: setattr(c, u"doc", c.doc + u"\n全部当たった。\n"))
M(u"文書: docID の形を足す", u"words", lambda c: setattr(c, u"doc", c.doc + u"\nS100ABCD\n"))
M(u"文書: 限界の見出しを落とす", u"words", doc_replace(u"## §6 ", u"## 6 "))
M(u"封: 封の頭の字を替える(封の commit の字から変わる)", u"frozen", seal_replace(u"# 封: 便 LX", u"# 封: 便 LY"))


def check_problems(check, c):
    return guard(CHECKS[check], c)


class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_record_the_script_and_the_seal_gate_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))
        self.assertEqual([], header_problems(Ctx()))

    def test_b_1_the_record_equals_the_recount_from_its_rows_and_calls(self):
        self.assertEqual([], recount_problems(Ctx()))

    def test_b_2_the_recount_reads_the_real_label_and_word_table_records(self):
        c = Ctx()
        self.assertEqual(422, len(c.labs))
        D = calc(c)
        self.assertEqual(421, D[u"all"][u"n"])
        self.assertEqual((104, 27, 42, 6, 214, 27), (D[u"cell"][u"range"][u"全体"][u"n"], D[u"cell"][u"plan"][u"全体"][u"n"], D[u"cell"][u"other"][u"全体"][u"n"], D[u"cell"][u"gc"][u"全体"][u"n"],
                                                       D[u"cell"][u"ga"][u"全体"][u"n"], D[u"cell"][u"gb"][u"全体"][u"n"]))
        self.assertEqual(1, sum(1 for l in c.labs if is_drop(l)))

    def test_c_1_the_document_numbers_equal_the_numbers_built_from_the_record(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_every_line_with_a_digit_is_covered_exactly_once(self):
        c = Ctx()
        E = expected_lines(c)
        lines = [ln for ln in c.doc.split(u"\n") if tokens(ln)]
        self.assertEqual(len(E), len(lines))
        self.assertEqual(sorted(i for i, (pat, _t) in enumerate(E)), list(range(len(E))))

    def test_c_3_the_claims_behind_the_words_are_counted_from_the_record(self):
        c = Ctx()
        self.assertEqual([], claims_problems(c, calc(c)))

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record_rows(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_seven_hits_and_four_misses(self):
        c = Ctx()
        j, near, b = judge(c)
        self.assertEqual([3, 7, 8, 10], [i for i in range(1, 12) if not j[i]])
        self.assertEqual({1: (60, 94), 2: 15, 3: (4, 16), 4: 22, 5: 4, 6: 10, 7: 5, 8: (10, 5), 9: 30, 10: 85, 11: 5}, b)
        self.assertEqual((13, 4, 3, 16), (near[3], near[6], near[11], near[8]))

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        self.assertEqual([], seal_problems(Ctx()))

    def test_d_4_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"主の席の答えなしは 5 行以下", u"主の席の答えなしは 2 行以下")
        self.assertFalse(judge(c)[0][11])
        c = Ctx()
        c.seal = c.seal.replace(u"主の席の答えなしは 5 行以下", u"主の席の答えなしは 3 行以下")
        self.assertTrue(judge(c)[0][11])

    def test_d_5_the_judge_compares_exact_fractions_at_the_edges(self):
        c = Ctx()
        a = calc(c)[u"lx"][10]
        self.assertEqual((293, 418, 403, 418), (a[u"r"], a[u"both"], a[u"n"], a[u"both"]))
        self.assertTrue(fractions.Fraction(403, 418) * 100 >= 85 > fractions.Fraction(293, 418) * 100)
        self.assertEqual(u"66.54", point2(109, 131, 7, 42))

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_f_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx()))

    def test_f_2_the_real_history_has_the_seal_before_the_script_the_record_the_document_and_this_gate(self):
        u"""結果の文書・この門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        bad = order_problems_real()
        rc, st = PR.git_in(REPO, "status", "--porcelain", "--", PREFIX + DOC_REL, PREFIX + GATE_REL)
        dirty = set(x for x in (DOC_REL, GATE_REL) if x in st)
        self.assertEqual(sorted(u"UNCOMMITTED:" + x for x in dirty), sorted(bad))

    def test_f_4_the_order_check_names_exist(self):
        for rel in (SCRIPT_REL, SEAL_GATE_REL, RECORD_REL, DOC_REL, GATE_REL):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_f_5_engine_is_untouched_since_the_seal_commit(self):
        self.assertEqual([], engine_problems())

    def test_f_6_the_record_commit_is_the_one_in_the_history(self):
        self.assertEqual([], record_commit_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        others = ["fixtures/r.json", "docs/r.md", "tests/g.py"]
        for o in others:
            r.put(o)
        impls = ["measure/s.py"]
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        r2 = PR.Repo()
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put("docs/r.md")
        r2.commit("docs/r.md")
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], ["measure/s.py"], ["docs/r.md"]))


class MutationTest(unittest.TestCase):
    def test_m_1_every_check_is_green_on_the_real_records(self):
        c = Ctx()
        for name, fn in CHECKS.items():
            self.assertEqual([], guard(fn, c), name)

    def test_m_2_every_mutation_turns_its_check_red(self):
        silent = []
        for label, check, fn in MUTATIONS:
            c = Ctx()
            fn(c)
            if not check_problems(check, c):
                silent.append(label)
        self.assertEqual([], silent)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        before = tuple(hashlib.sha256(read_bytes(r)).hexdigest() for r in (RECORD_REL, DOC_REL, SEAL_REL, SCRIPT_REL))
        for label, check, fn in MUTATIONS:
            c = Ctx()
            fn(c)
        after = tuple(hashlib.sha256(read_bytes(r)).hexdigest() for r in (RECORD_REL, DOC_REL, SEAL_REL, SCRIPT_REL))
        self.assertEqual(before, after)
        self.assertEqual([], guard(CHECKS[u"doc"], Ctx()))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(m[1] for m in MUTATIONS))
        labels = u"\n".join(m[0] for m in MUTATIONS)
        for need in (u"記録の", u"文書: §1", u"判定を 1 つ替える", u"境を替える", u"束を取り違える"):
            self.assertIn(need, labels)


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src.replace(u"S100ABCD", u"")))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            self.assertNotIn(u"llm_extract", fh.read())

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))

    def test_n_4_this_gate_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(GATE_REL, "llm_extract_result_gate_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        del mod


if __name__ == "__main__":
    unittest.main()
