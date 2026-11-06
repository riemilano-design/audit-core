# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md §1・§5 ― T9 の第 2 便(注入後の claim を基準の claim の id で引く対応付け)の測定と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_pswap_idmap_2026-11-06.py inject [--procs N] [--only <docID>[,<docID>...]] [--out PATH]   # 切り替え 真 で T9 を注入(P29E・P30E)→ fixtures/xbrl/pswap/inject_idmap_2026-11-06.json
    python3 measure/xbrl_pswap_idmap_2026-11-06.py tally  [--root DIR]                                              # 記録から Q-1〜Q-10 と K-1〜K-4 の表を出す(file は書かない)

T9 の便の script ``xbrl_pswap_2026-11-06.py``(PS)は **1 byte も変えず**、importlib で読み込んで使う(JT・NS・RM・NF・RUN・GEN・TUNE・IJ・N・S・SC は PS の持つ同じ instance。
site の関数 ``t9_all_sites``・``build_t9`` と、行の欄の関数 ``engine_cue``・``has_prior_word``・``pointer_period``・``reached_of``・``shape_of_token`` もそのまま使う)。
site・並べ替え・cap・差し替え・本ごとの数え・集計は T9 のまま(同じ種・同じ cap なので行の id は T9 の記録と同じになるはず = Q-2)。**替えるのは注入後の claim の引き方だけ。**
``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 対応付け(封 §1-1): 注入後の文の claim のうち ``id == 基準の claim の id`` の claim c を引き、(ア) c が在る (イ) ``c["value"]`` が在り円に直した値が注入した値と ``TUNE.same_number``
  (target = ``SC.scaled_value(new_value, token.unit)``) (ウ) ``c["span"]`` に差し替えの字 rendered が在る、の 3 つ全部で対応が付く。欠けたら「対応が付かない」(行には残し、欠けた条件を欄に持つ)。
  「基準の claim の id」は profile ごとの土台の claim の id(P29E は P29E の土台の claim の id。P29E の土台に対応が付かない行は P29E の欄が対応なしで、条件の欄は なし、欠けた条件は 土台なし)。
- 旧の対応付け(封 §1-2): 同じ行に ``TUNE.claim_for_p27`` の結果(付いた / 同じ id)も持つ。判定には使わず、Q-4・Q-5 の照らしに使う。
- 「届いた」(封 §1-3): 元の字が基準の claim の span に在る かつ id で引いた claim(P30E)の span に rendered が在る。注入後の pointer の期も id で引いた claim(P30E)で決める
  ((イ)が欠けても(ウ)が真なら届いた。対応の有無とは別の欄)。claim が無い(ア)が偽の行は なし。
- Q-3 の「注入の前後で claim の数が同じ行」は P30E の claim の数(無改変の文と注入後の文)。Q-6 の 2 本目の分母は旧の対応付け(P30E)が付かない行(id で付かない行も分母に入る)。
  Q-10 の止めた行 = id で対応が付く行 - 通した行。分母 0 の率は None = 外れ。Q-5 は旧の対応(P30E)が付いた行について、P29E・P30E の 結果 と state が T9 の記録の同じ id の行と同じか。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。

engine(``core/``・``adapters/``)・``measure/inject.py``・``measure/lib``・前の便(T9・J・H・RB・N)の script と記録は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。``sys.modules`` にも登録する(``--procs`` 2 以上の fork で pickle に落ちないため)。"""
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


PS = load_module("xbrl_pswap_2026-11-06.py", "pswap_for_idmap")
JT = PS.JT
NS = PS.NS
RM, NF, RUN, GEN, TUNE, IJ = PS.RM, PS.NF, PS.RUN, PS.GEN, PS.TUNE, PS.IJ
N, S, SC = PS.N, PS.S, PS.SC
Stop = GEN.Stop

FLAG = PS.FLAG
SEAL_REL = "docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md"
SEAL_COMMIT = "ec00fa1"
DOC_REL = "docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md"
REC_DIR_REL = "fixtures/xbrl/pswap"
INJECT_REL = REC_DIR_REL + "/inject_idmap_2026-11-06.json"
REC_REL = collections.OrderedDict([("inject", INJECT_REL)])
SCRIPT_REL = "measure/xbrl_pswap_idmap_2026-11-06.py"
PS_SCRIPT_REL = "measure/xbrl_pswap_2026-11-06.py"
PS_RECORD_REL = PS.INJECT_REL                      # fixtures/xbrl/pswap/inject_2026-11-06.json(T9 の記録。読むだけ)
H_RECORD_REL = PS.H_RECORD_REL
RB_RECORD_REL = PS.RB_RECORD_REL
LIB_RELS = PS.LIB_RELS
UNTOUCHED_FOR_Q1 = ("measure/inject.py", "measure/lib/sites.py", PS_SCRIPT_REL)
SOURCES = PS.SOURCES
INJECT_PROFILES = PS.INJECT_PROFILES               # ("P29E", "P30E")
T9 = PS.T9
SHAPES = PS.SHAPES
LINK_KEY, COMPARE_KEY = PS.LINK_KEY, PS.COMPARE_KEY
LINKED, UNLINKED = PS.LINKED, PS.UNLINKED
HIT, MISS = RM.HIT, RM.MISS
BASE_WORD, SITE_WORD = PS.BASE_WORD, PS.SITE_WORD
BREAKDOWN_KEY, CUE_KEY, PERIOD_KEY = PS.BREAKDOWN_KEY, PS.CUE_KEY, PS.PERIOD_KEY
PERIODS = PS.PERIODS
Q_KEY = "Q の欄"
#: 対応の 3 つの条件(封 §1-1 の (ア)(イ)(ウ)。行の欄の名前)
COND_A = u"ア id の claim が在る"
COND_I = u"イ 値が注入した値"
COND_U = u"ウ span に差し替えの字"
CONDS = (COND_A, COND_I, COND_U)
NO_BASE = u"土台なし"
#: 欄の名前(行)
F_COND = u"%s の対応の条件"
F_MISS = u"%s の欠けた条件"
F_OLD = u"旧の対応(%s)"
F_SAMEN = u"注入の前後で claim の数が同じ(P30E)"
OLD_KEYS = (u"付いた", u"同じ id")
#: Q の欄の名前(記録の ``Q の欄`` と tally の判定が使う)
QCOL = collections.OrderedDict([
    ("Q-2", u"Q-2 行の数と id の集合(T9 の記録と比べる)"), ("Q-3", u"Q-3 id で対応が付く行と claim の数が同じ行"),
    ("Q-4", u"Q-4 旧の対応付けが付く行と同じ claim の行"), ("Q-5", u"Q-5 旧で付いた行の判定が T9 の記録と同じ行"),
    ("Q-6", u"Q-6 通した率(P30E)と旧で付かなかった行の通した率"), ("Q-7", u"Q-7 通した行の注入後の pointer の期と手がかり真の行の通した率"),
    ("Q-8", u"Q-8 P29E と P30E で判定が違う行(両方に対応が付く行)"), ("Q-9", u"Q-9"), ("Q-10", u"Q-10 止めた行の中で名指して原本の割合")])
#: 封 §6 の字に足す、この script の限界(数は変えない)
EXTRA_LIMITS = (
    "対応付けは profile ごとの土台の claim の id で引く(P29E は P29E の土台の claim の id)。P29E の土台に対応が付かない行の P29E の欄は対応なし(条件の欄は なし、欠けた条件は 土台なし)",
    "「届いた」と注入後の pointer の期は id で引いた claim(P30E)で決める。(イ)が欠けても(ウ)が真なら届いた。claim が無い行の期は なし",
    "Q-3 の「注入の前後で claim の数が同じ行」は P30E の claim の数。Q-6 の 2 本目の分母は旧の対応付け(P30E)が付かない行で、id で対応が付かない行も分母に入る。Q-10 の止めた行は 対応が付く行 − 通した行",
    "Q-5 は旧の対応付け(P30E)が付いた行について、P29E・P30E の 結果 と state が T9 の記録の同じ id の行と同じか。Q-8 は P29E・P30E の両方に対応が付き結果が違う行",
    "Q-2 の id の集合は T9 の記録と比べる(--only の走りでは一致しない)。engine の手がかり・round-trip・読み直し・pointer の期の分け方は T9 の script の関数をそのまま使う(T9 と同じ限界)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def norm(x):
    return json.loads(json.dumps(x))


yen_scan_on = NS.yen_scan_on
within = RM.within
fmt = RM.fmt
LABEL_PASS, LABEL_NAMED_ORIGINAL = TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL


# ======================================================================================================
# 配線・鍵の検査
def wiring_problems():
    return NS.wiring_problems()


def inject_wiring_problems():
    return NS.inject_wiring_problems()


def key_leaks_pi(text, key_value=None, long_alnum=True):
    u"""この便の封の path と T9 の封の path(32 字に近い英数字・_・- の連なり)を除いて、T9 の便の検査に渡す。"""
    return PS.key_leaks_ps(text.replace(SEAL_REL, u""), key_value, long_alnum)


@contextlib.contextmanager
def key_check_pi():
    u"""``GEN.key_leaks`` を with の中だけこの便の封の path を除く版にする(NS の配線の検査は with の外で走らせる)。"""
    old = GEN.key_leaks
    GEN.key_leaks = key_leaks_pi
    try:
        yield
    finally:
        GEN.key_leaks = old


def assert_clean_pi(rec, key_value=None):
    with key_check_pi():
        RUN.assert_clean(rec, key_value)


# ======================================================================================================
# 対応付け(封 §1-1・§1-2。行の欄の部品。対応付けの試験が欠けた claim の列で固定する)
def id_claim(claims, base_id):
    u"""``id == 基準の claim の id`` の claim(最初の 1 件。無ければ None)。"""
    if base_id is None:
        return None
    for c in claims:
        if c.get("id") == base_id:
            return c
    return None


def id_conditions(c, target, rendered):
    u"""(ア)(イ)(ウ)の真偽(OrderedDict)。(ア)が偽なら(イ)(ウ)も偽。"""
    a = c is not None
    i = bool(a and c.get("value") is not None and TUNE.same_number(TUNE.claim_scaled(c), target))
    u = bool(a and rendered in (c.get("span") or ""))
    return collections.OrderedDict([(COND_A, a), (COND_I, i), (COND_U, u)])


def id_map(claims, base_id, target, rendered):
    u"""(対応した claim か None, 条件の真偽, 欠けた条件の列, 引いた claim か None)。3 つ全部が真のときだけ対応が付く。"""
    c = id_claim(claims, base_id)
    conds = id_conditions(c, target, rendered)
    miss = [k for k in CONDS if not conds[k]]
    return (c if not miss else None), conds, miss, c


def old_map(claims, inj, unit, base_id):
    u"""旧の対応付け(``TUNE.claim_for_p27``)の結果: {付いた, 同じ id}。判定には使わない。"""
    old = TUNE.claim_for_p27(claims, inj, unit)
    return collections.OrderedDict([(OLD_KEYS[0], old is not None), (OLD_KEYS[1], bool(old is not None and base_id is not None and old.get("id") == base_id))])


# ======================================================================================================
# 1 本の注入
def inject_text_pi(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""T9 の 1 本の注入(site・並べ替え・cap・差し替え・行の欄は PS のまま)。注入後の claim を基準の claim の id で引く。(行, 数え)。"""
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([("注入しない", "文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or PS.VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    stages, sites = PS.t9_all_sites(text, refs, seed, key)
    ok, pop = [], collections.Counter()
    for s in sites:
        st, bc = RM.base_status_rb(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
        if bc is not None:
            ok.append((s, bc))
    counts = collections.OrderedDict([
        ("段", stages), ("作れる site", PS.shape_counter(sites)), ("作れる site の手がかり", PS.cue_counter(text, sites)),
        ("作れる site の状態", collections.OrderedDict(sorted(pop.items()))),
        ("土台 P30E が GROUNDED の site", len(ok)), ("cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
    taken = collections.Counter()
    rows = []
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        tok = s["token"]
        inj = PS.build_t9(s, "%s-T9-%02d" % (key, n))
        target = SC.scaled_value(inj["new_value"], tok.unit)
        taken[LINKED if bc["ids"][profiles[0]] is not None else UNLINKED] += 1
        tampered, placements = IJ.apply_edits(text, [inj])
        rt = IJ.revert(tampered, [inj], placements, text) == text
        orig_digits = text[tok.start:tok.end]
        row = collections.OrderedDict([
            ("id", inj["id"]), ("型", T9), ("形", PS.shape_of_token(tok)), ("単位", tok.unit),
            ("基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None),
            ("round-trip", bool(rt)), ("読み直し", bool(JT.reread_j(tampered, tok, inj["new_value"], tok.unit))),
            ("先頭の位が減った", bool(tok.groups is not None and NS.groups_in(inj["replacement"]) < len(tok.groups))),
            ("engine の手がかり", PS.engine_cue(text, tok)), ("文に前期の語", PS.has_prior_word(text, tok)),
            ("基準の pointer の期", PS.pointer_period(bc.get("pointers")))])
        conds, miss, old, found = {}, {}, {}, {}
        same_n = False
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)
                conds[p], miss[p], found[p] = None, [NO_BASE], None
                old[p] = collections.OrderedDict([(OLD_KEYS[0], False), (OLD_KEYS[1], False)])
                continue
            claims = verify(zb, p, tampered)["claims"]
            res, conds[p], miss[p], found[p] = id_map(claims, bc["ids"][p], target, inj["replacement"])
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
            old[p] = old_map(claims, inj, tok.unit, bc["ids"][p])
            if p == profiles[1]:
                same_n = len(claims) == len(base_claims[p])
        c30 = found[profiles[1]]
        row["注入後の pointer の期"] = PS.pointer_period(c30.get("pointers")) if c30 is not None else "なし"
        row["届いた"] = PS.reached_of(orig_digits, bc.get("span"), c30, inj["replacement"])
        for p in profiles:
            row[F_COND % p] = conds[p]
        for p in profiles:
            row[F_MISS % p] = miss[p]
        for p in profiles:
            row[F_OLD % p] = old[p]
        row[F_SAMEN] = bool(same_n)
        rows.append(row)
    counts["採った"] = n
    counts["採った の状態"] = collections.OrderedDict(sorted(taken.items()))
    return rows, counts


def inject_job_pi(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(N, FLAG):
        raise Stop("**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_pi(zb, text, refs, seed, name)
    base = collections.OrderedDict([("docID", item["docID"]), ("form", item["form"]), ("model", item["model"]), ("writer", item["writer"])])
    out = []
    for r in rows:
        d = collections.OrderedDict(base)
        d.update(r)
        out.append(d)
    return name, out, counts


# ======================================================================================================
# 集計(門が記録の行と本ごとの数えから作り直して照らす)。集計・形別・手がかり別・期の内訳は T9 の関数をそのまま使う
inject_summaries = PS.inject_summaries
unlinked_counts = PS.unlinked_counts
breakdown = PS.breakdown
cue_breakdown = PS.cue_breakdown
period_breakdown = PS.period_breakdown
pass_rate = PS.pass_rate


def t9_rows_by_id(t9_rows):
    return dict((r["id"], r) for r in t9_rows)


def same_verdict(a, b):
    u"""2 つの行の P29E・P30E の 結果 と state が同じか。"""
    return all(a[p]["結果"] == b[p]["結果"] and a[p]["state"] == b[p]["state"] for p in INJECT_PROFILES)


def q_columns(rows, t9_rows):
    u"""Q-2〜Q-10 の欄を ``行`` と T9 の記録の ``行`` から数える(記録の ``Q の欄`` と tally の判定が使う)。"""
    t9 = t9_rows_by_id(t9_rows)
    ids, t9ids = set(r["id"] for r in rows), set(t9)
    q2 = collections.OrderedDict([("行の数", len(rows)), ("T9 の記録の行の数", len(t9_rows)), ("id の集合が T9 の記録と同じ", ids == t9ids),
                                  ("T9 の記録にだけ在る id", len(t9ids - ids)), ("この記録にだけ在る id", len(ids - t9ids))])
    m30 = [r for r in rows if r["P30E"]["対応"]]
    m29 = [r for r in rows if r["P29E"]["対応"]]
    q3 = collections.OrderedDict([("P30E で対応が付く行", len(m30)), ("P29E で対応が付く行", len(m29)),
                                  ("注入の前後で claim の数が同じ行", sum(1 for r in rows if r[F_SAMEN]))])
    old = [r for r in rows if r[F_OLD % "P30E"][OLD_KEYS[0]]]
    q4 = collections.OrderedDict([("旧の対応付けが付く行(P30E)", len(old)), ("うち id で引いた claim と同じ claim の行", sum(1 for r in old if r[F_OLD % "P30E"][OLD_KEYS[1]]))])
    same = [r for r in old if r["id"] in t9 and same_verdict(r, t9[r["id"]])]
    q5 = collections.OrderedDict([("旧の対応付けが付いた行(P30E)", len(old)), ("P29E・P30E の結果と state が T9 の記録と同じ行", len(same))])
    passed = [r for r in rows if r["P30E"]["結果"] == LABEL_PASS]
    notold = [r for r in rows if not r[F_OLD % "P30E"][OLD_KEYS[0]]]
    notold_pass = [r for r in notold if r["P30E"]["結果"] == LABEL_PASS]
    q6 = collections.OrderedDict([("通した率(P30E)", pct(len(passed), len(m30))), ("通した行", len(passed)), ("id で対応が付く行", len(m30)),
                                  ("旧で付かなかった行の通した率", pct(len(notold_pass), len(notold))), ("旧で付かなかった行の通した行", len(notold_pass)), ("旧で付かなかった行", len(notold))])
    cur = sum(1 for r in passed if r["注入後の pointer の期"] == "CurrentYear")
    cue = [r for r in m30 if r["engine の手がかり"]]
    q7 = collections.OrderedDict([("通した行", len(passed)), ("うち注入後の pointer の期が CurrentYear", cur), ("割合", pct(cur, len(passed))),
                                  ("手がかり真の行の通した率", pass_rate(cue)), ("対応が付く行のうち手がかり真", len(cue))])
    both = [r for r in rows if r["P29E"]["対応"] and r["P30E"]["対応"]]
    q8 = collections.OrderedDict([("違う行", sum(1 for r in both if r["P29E"]["結果"] != r["P30E"]["結果"])), ("両方に対応が付く行", len(both))])
    q9 = collections.OrderedDict([("round-trip 不一致", sum(1 for r in rows if not r["round-trip"])), ("読み直し不一致", sum(1 for r in rows if not r["読み直し"])),
                                  ("先頭の位が減った行", sum(1 for r in rows if r["先頭の位が減った"])), ("届いた行", sum(1 for r in rows if r["届いた"]))])
    stopped = [r for r in m30 if r["P30E"]["結果"] != LABEL_PASS]
    named = [r for r in stopped if r["P30E"]["結果"] == LABEL_NAMED_ORIGINAL]
    q10 = collections.OrderedDict([("対応が付く行", len(m30)), ("止めた行", len(stopped)), ("うち名指して原本", len(named)), ("割合", pct(len(named), len(stopped)))])
    ref = collections.OrderedDict([("文に前期の語がある行", sum(1 for r in rows if r["文に前期の語"])), ("手がかり真の行(全部)", sum(1 for r in rows if r["engine の手がかり"])),
                                   ("P30E の欠けた条件(ア)", sum(1 for r in rows if COND_A in r[F_MISS % "P30E"])), ("P30E の欠けた条件(イ)", sum(1 for r in rows if COND_I in r[F_MISS % "P30E"])),
                                   ("P30E の欠けた条件(ウ)", sum(1 for r in rows if COND_U in r[F_MISS % "P30E"])), ("P29E の欠けた条件がある行", sum(1 for r in rows if r[F_MISS % "P29E"]))])
    return collections.OrderedDict([(QCOL["Q-2"], q2), (QCOL["Q-3"], q3), (QCOL["Q-4"], q4), (QCOL["Q-5"], q5), (QCOL["Q-6"], q6), (QCOL["Q-7"], q7),
                                    (QCOL["Q-8"], q8), (QCOL["Q-9"], q9), (QCOL["Q-10"], q10), (u"参考", ref)])


# ======================================================================================================
# 記録の書き方
caches_all = PS.caches_all


def header_pi(root, step, seed_meta, before, after, profiles):
    u"""T9 の頭(PS.header_ps)を使い、封・封の commit・この script の sha256 を替え、T9 の script と記録の sha256 を足す。"""
    h = PS.header_ps(root, step, seed_meta, before, after, profiles)
    h["seal"] = SEAL_REL
    h["封の commit"] = SEAL_COMMIT
    h["この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h["T9 の script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_pswap_2026-11-06.py"))
    h["T9 の記録の sha256"] = GEN.sha256_file(os.path.join(root, PS_RECORD_REL))
    return h


def scope_word(only):
    return "全 200 本" if only is None else "**--only(本番の記録ではない)**"


load_books = PS.load_books


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_limits(seal):
    return NS.seal_limits(seal)


def write_json(out, rec, key_value=None):
    text = RUN.dumps_inject(rec)
    with key_check_pi():
        RUN.write_record(out, text, rec, key_value)


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None):
    if out is None:
        if only is not None:
            raise Stop("**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop("**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if getattr(N, FLAG):
        raise Stop("**切り替えが真のまま inject を始めた。止める**")
    RM.install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop("**差し替えが届いていない: %s。止める**" % " / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="pswap_idmap_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say("注入 %d 本 × 2 profile(P29E・P30E)。切り替え 真・T9_PRIOR_TO_CURRENT・id で引く対応付け ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with yen_scan_on():
        if not getattr(N, FLAG) or wiring_problems():
            raise Stop("**切り替えを真にできない・配線が崩れた。止める**")
        results = NF.map_pool(inject_job_pi, jobs_, procs)
    if getattr(N, FLAG):
        raise Stop("**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop("**cache の件数か名前が変わった。記録を書かずに止める**")
    t9_rec = GEN.jload(os.path.join(root, PS_RECORD_REL))
    rec = header_pi(root, "T9 の第 2 便(注入後の claim を基準の claim の id で引く)― 切り替え 真・T9_PRIOR_TO_CURRENT の注入(P29E・P30E。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec["範囲"] = scope_word(only)
    rec["切り替え"] = collections.OrderedDict([("名前", FLAG), ("inject の中の値", True), ("出たあとの値", bool(getattr(N, FLAG))), ("配線の問題", wiring_problems())])
    rec["種"] = {"file": RUN.SEED_REL_STR, "種の確認": seed_meta}
    rec["型"] = collections.OrderedDict([
        (T9, "T9 の便と同じ site・並べ替え・cap・差し替え(S.identified_sites の (token, ref) のうち ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件の数に、その当期の値を元の字の形で入れる)。"
             "注入後の claim は 基準の claim と同じ id の claim を引く"),
        ("上限", "1 本あたり %d" % RUN.INJECT_CAP),
        ("site", SITE_WORD),
        ("土台", BASE_WORD),
        ("土台の結び方", "P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        ("対応付け", "注入後の文の claim のうち id が基準の claim の id の claim c が、(ア)在る (イ)値が注入した値(円に直して TUNE.same_number) (ウ)span に差し替えの字が在る、の 3 つ全部のときだけ対応が付く。欠けた条件は行に持つ"),
        ("旧の対応付け", "TUNE.claim_for_p27 の結果(付いた / 同じ id)を行に持つ。判定には使わない(Q-4・Q-5 の照らし)"),
        ("届いた", "元の字が基準の claim の span に在る かつ id で引いた claim(P30E)の span に差し替えの字が在る"),
        ("engine の手がかり", "recipes._prior_cue(注入前の文, token.start, token.end) の真偽。読むだけで site の選びには使わない"),
        ("pointer の期", "基準の claim と id で引いた claim(P30E)の pointers の先頭の context の先頭: CurrentYear / Prior1Year / 他 / なし。要素名は持たない"),
        ("集計の2本", "集計 = 全部の site での P29E・P30E の率。" + COMPARE_KEY + " = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率"),
        ("inject の docID の引数", "本の名前(<docID>_<形>_<model>)")])
    rec["本ごとの数え"] = per
    rec["注入の行の数"] = len(rows)
    rec["集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[BREAKDOWN_KEY] = breakdown(rows)
    rec[CUE_KEY] = cue_breakdown(rows)
    rec[PERIOD_KEY] = period_breakdown(rows)
    rec["P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[Q_KEY] = q_columns(rows, t9_rec["行"])
    rec["限界"] = seal_limits(seal_text(root)) + list(EXTRA_LIMITS)
    rec["行"] = rows
    write_json(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の Q-1〜Q-10・§4 の K-1〜K-4)を読み、記録から判定する
def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {Q-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (Q-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else "")
    return out


def seal_k_rows(seal):
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    return collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^- (K-\d): (.*)$", sec4, re.M))


NUM = r"[\d,]+(?:\.\d+)?"
RANGE = r"(%s)〜(%s)" % (NUM, NUM)


def _rng(m, i):
    return (NF.num(m.group(i)), NF.num(m.group(i + 1)))


def seal_bounds(seal):
    u"""封の字から予測の幅と採用の基準の閾値を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    K = seal_k_rows(seal)
    b = collections.OrderedDict()
    b["Q-1"] = P["Q-1"][1].strip()
    m = re.match(r"^(\d+)・同じ$", P["Q-2"][1].strip())
    b["Q-2"] = int(m.group(1))
    m = re.match(r"^(\d+) / (\d+)・(\d+)$", P["Q-3"][1].strip())
    b["Q-3"] = collections.OrderedDict([("P30E で対応が付く行", int(m.group(1))), ("P29E で対応が付く行", int(m.group(2))), ("注入の前後で claim の数が同じ行", int(m.group(3)))])
    m = re.match(r"^(\d+)・(\d+)$", P["Q-4"][1].strip())
    b["Q-4"] = collections.OrderedDict([("旧の対応付けが付く行(P30E)", int(m.group(1))), ("うち id で引いた claim と同じ claim の行", int(m.group(2)))])
    m = re.match(r"^(\d+) / (\d+)$", P["Q-5"][1].strip())
    b["Q-5"] = collections.OrderedDict([("P29E・P30E の結果と state が T9 の記録と同じ行", int(m.group(1))), ("旧の対応付けが付いた行(P30E)", int(m.group(2)))])
    m = re.match(r"^%s%%、%s%%$" % (RANGE, RANGE), P["Q-6"][1].strip())
    b["Q-6"] = collections.OrderedDict([("通した率(P30E)", _rng(m, 1)), ("旧で付かなかった行の通した率", _rng(m, 3))])
    m = re.match(r"^%s%%、%s%%$" % (RANGE, RANGE), P["Q-7"][1].strip())
    b["Q-7"] = collections.OrderedDict([("割合", _rng(m, 1)), ("手がかり真の行の通した率", _rng(m, 3))])
    m = re.match(r"^(\d+)〜(\d+)$", P["Q-8"][1].strip())
    b["Q-8"] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^(\d+) / (\d+) / (\d+) / (\d+)$", P["Q-9"][1].strip())
    b["Q-9"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2))), ("先頭の位が減った行", int(m.group(3))), ("届いた行", int(m.group(4)))])
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["Q-10"][1].strip())
    b["Q-10"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    b["K-1"] = re.search(r"Q-1 が (一致)", K["K-1"]).group(1)
    m = re.search(r"Q-9 の round-trip 不一致 (\d+)・読み直し不一致 (\d+)", K["K-2"])
    b["K-2"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2)))])
    b["K-3"] = NF.num(re.search(r"id で対応が付く行\(P30E\)≥ (%s)" % NUM, K["K-3"]).group(1))
    m = re.search(r"Q-5 が (\d+) / (\d+)", K["K-4"])
    b["K-4"] = collections.OrderedDict([("P29E・P30E の結果と state が T9 の記録と同じ行", int(m.group(1))), ("旧の対応付けが付いた行(P30E)", int(m.group(2)))])
    return b


def git_numstat_since_seal(root=ROOT):
    u"""``git diff --numstat <封の commit> -- measure/inject.py measure/lib/sites.py <T9 の script>`` の行(空なら 0 行)。git が読めなければ None。"""
    p = subprocess.run(["git", "diff", "--numstat", SEAL_COMMIT, "--"] + list(UNTOUCHED_FOR_Q1), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return None
    return [ln for ln in p.stdout.decode("utf-8").splitlines() if ln]


def q1_value(rec, h_rec, rb_rec, numstat):
    u"""Q-1 の 3 つ: lib の指紋が H の記録と、engine の指紋(sha256 の 2 欄。git_commit は比べない)が RB の記録と一致・inject.py・sites.py・T9 の script が封の commit から変わった file の数。"""
    fp, rfp = rec.get("engine の指紋") or {}, rb_rec.get("engine の指紋") or {}
    eng = all(fp.get(k) is not None and fp.get(k) == rfp.get(k) for k in ("adapter_xbrl_py_sha256", "core_py_sha256"))
    lib = rec.get("lib の指紋") is not None and norm(rec.get("lib の指紋")) == norm(h_rec.get("lib の指紋"))
    return collections.OrderedDict([("lib の指紋が H の記録と一致", bool(lib)), ("engine の指紋が RB の記録と一致", bool(eng)),
                                    ("inject.py・sites.py・T9 の script が封の commit から変わった file", None if numstat is None else len(numstat))])


NOT_GIVEN = object()


def build_Q(R_, seal, numstat=NOT_GIVEN):
    u"""{Q, K, 採用, 欄}。R_ = {"inject", "h", "rb", "t9"}(記録の JSON)。欄は inject の記録の 行 と T9 の記録の 行 から数え直す(記録の ``Q の欄`` は使わない)。
    numstat 省略時は git に聞く。None を渡したら『読めなかった』= Q-1 は外れ(省略とは別。読めないのに作業木の答えで代えない)。"""
    inj = R_["inject"]
    if numstat is NOT_GIVEN:
        numstat = git_numstat_since_seal()
    return judge_from(q1_value(inj, R_["h"], R_["rb"], numstat), q_columns(inj["行"], R_["t9"]["行"]), seal)


def judge_from(q1, cols, seal):
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    Q = collections.OrderedDict()

    def put(k, ok, val):
        Q[k] = {"判定": HIT if ok else MISS, "値": val}
    put("Q-1", q1["lib の指紋が H の記録と一致"] and q1["engine の指紋が RB の記録と一致"] and q1["inject.py・sites.py・T9 の script が封の commit から変わった file"] == 0, q1)
    c2 = cols[QCOL["Q-2"]]
    put("Q-2", c2["行の数"] == B["Q-2"] and c2["id の集合が T9 の記録と同じ"] is True, c2)
    c3 = cols[QCOL["Q-3"]]
    put("Q-3", all(c3[k] == B["Q-3"][k] for k in B["Q-3"]), c3)
    c4 = cols[QCOL["Q-4"]]
    put("Q-4", all(c4[k] == B["Q-4"][k] for k in B["Q-4"]), c4)
    c5 = cols[QCOL["Q-5"]]
    put("Q-5", all(c5[k] == B["Q-5"][k] for k in B["Q-5"]), c5)
    c6 = cols[QCOL["Q-6"]]
    put("Q-6", all(within(c6[k], B["Q-6"][k]) for k in B["Q-6"]), c6)
    c7 = cols[QCOL["Q-7"]]
    put("Q-7", all(within(c7[k], B["Q-7"][k]) for k in B["Q-7"]), c7)
    c8 = cols[QCOL["Q-8"]]
    put("Q-8", within(c8["違う行"], B["Q-8"]), c8)
    c9 = cols[QCOL["Q-9"]]
    put("Q-9", all(c9[k] == B["Q-9"][k] for k in B["Q-9"]), c9)
    c10 = cols[QCOL["Q-10"]]
    put("Q-10", within(c10["割合"], B["Q-10"]), c10)
    K = collections.OrderedDict()
    K["K-1"] = {"判定": Q["Q-1"]["判定"], "値": collections.OrderedDict([("Q-1", Q["Q-1"]["判定"])])}
    k2 = all(c9[k] == B["K-2"][k] for k in B["K-2"])
    K["K-2"] = {"判定": HIT if k2 else MISS, "値": collections.OrderedDict([("round-trip 不一致", c9["round-trip 不一致"]), ("読み直し不一致", c9["読み直し不一致"])])}
    K["K-3"] = {"判定": HIT if c3["P30E で対応が付く行"] >= B["K-3"] else MISS, "値": collections.OrderedDict([("id で対応が付く行(P30E)", c3["P30E で対応が付く行"])])}
    k4 = all(c5[k] == B["K-4"][k] for k in B["K-4"])
    K["K-4"] = {"判定": HIT if k4 else MISS, "値": collections.OrderedDict((k, c5[k]) for k in B["K-4"])}
    adopt = all(K[k]["判定"] == HIT for k in K)
    return collections.OrderedDict([("Q", Q), ("K", K), ("採用", adopt), ("欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = ["| # | 欄 | 予測 | 測った値 | 判定 |", "|---|---|---|---|---|"]
    for k, v in J["Q"].items():
        lines.append("| %s | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], fmt(v["値"]), v["判定"]))
    return "\n".join(lines)


def k_cell(text):
    u"""封の K の本文の最初の一文(「。」の前まで)。表を短くする。決め方は固定。"""
    return text.split("。")[0].strip()


def render_judge(J, seal=None):
    seal = seal if seal is not None else read_seal()
    names = seal_k_rows(seal)
    lines = ["| # | 基準 | 測った値 | 判定 |", "|---|---|---|---|"]
    for k, v in J["K"].items():
        lines.append("| %s | %s | %s | %s |" % (k, k_cell(names[k]), fmt(v["値"]), v["判定"]))
    lines.append("")
    lines.append("採用の判定(K-1〜K-4 を全部満たす): **%s**。最後に決めるのは人間。" % ("採用" if J["採用"] else "見送り"))
    return "\n".join(lines)


def load_records(root=ROOT):
    return collections.OrderedDict([("inject", GEN.jload(os.path.join(root, INJECT_REL))), ("h", GEN.jload(os.path.join(root, H_RECORD_REL))),
                                    ("rb", GEN.jload(os.path.join(root, RB_RECORD_REL))), ("t9", GEN.jload(os.path.join(root, PS_RECORD_REL)))])


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_Q(load_records(root), seal, git_numstat_since_seal(root))
    say(render_pred(J, seal))
    say("")
    say(render_judge(J, seal))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="inject: この docID の本だけ(コンマで分けて複数。--out が要る)")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
