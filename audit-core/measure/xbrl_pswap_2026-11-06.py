# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md §1・§5 ― T9(前期の fact に結ばれた数に当期の値を入れる注入 T9_PRIOR_TO_CURRENT)の測定と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_pswap_2026-11-06.py inject [--procs N] [--only <docID>[,<docID>...]] [--out PATH]   # 切り替え 真 で T9 を注入(P29E・P30E)→ fixtures/xbrl/pswap/inject_2026-11-06.json
    python3 measure/xbrl_pswap_2026-11-06.py tally  [--root DIR]                                              # 記録から PS-1〜PS-10 と K-1〜K-4 の表を出す(file は書かない)

J の便の script ``xbrl_jtypes_2026-11-05.py``(JT)は **1 byte も変えず**、importlib で読み込んで使う(NS・RM・NF・RUN・GEN・TUNE・IJ・N・S・SC は JT の持つ同じ instance)。
``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- site: ``S.identified_sites``(切り替え 真)の (token, ref) のうち、ref の context が ``Prior1Year`` で始まり、同じ要素・context の ``Prior1Year`` を ``CurrentYear`` に替えた key の fact がちょうど 1 件、
  単位が同じ・両方正・値が違う(``IJ.TOL``)、当期の値を元の字の形で描いて(``N.render_value``)``N.scan(rendered + 単位)`` で読み直すと token が 1 つで値 × factor が当期の値に一致、``rendered != token.text``。
  形は 既存 / 万だけ / 複合 の全部(T9 は仕掛けに無い型なので、複合を除く差し替えはしない = 仕掛けの site 関数は使わない)。
- 並べ替えと cap: token の start の順に並べ、``random.Random("<seed>|<本の名前>|T9_PRIOR_TO_CURRENT")`` で shuffle、土台が P30E GROUNDED の site だけを先頭から cap 件(型 1 本 10)。
  「採った」= cap を基準で絞る前に掛けた数 Σ min(cap, 作れる site)(J の T6 と同じ読み)。
- engine の手がかり: ``recipes._prior_cue(text, token.start, token.end)``(注入前の文・注入前の token)を**読むだけ**。site の選びには使わない。
- 注入: 1 回に 1 件(``IJ.apply_edits``・``IJ.revert``)。差し替えは ``[token.start, token.end]`` を rendered に(単位の字は触らない)。round-trip は止めずに数える。
- 「届いた」= 元の字(``text[t.start:t.end]``)が基準の claim の span に在る かつ 注入後の claim(P30E。対応が付いたとき)の span に rendered が在る。
- pointer の期の欄は基準の claim(P30E)と注入後の claim(P30E)の ``pointers[0]`` の context の先頭で CurrentYear / Prior1Year / 他 / なし に分けた語だけを持つ(要素名は持たない)。
- PS-10 の「止めた行」= 対応が付く行 − 通した行。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。

engine(``core/``・``adapters/``)・``measure/inject.py``・``measure/lib``・前の便の script と記録は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import importlib.util
import io
import json
import os
import random
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


JT = load_module("xbrl_jtypes_2026-11-05.py", "jtypes_for_pswap")
NS = JT.NS
RM, NF, RUN, GEN, TUNE, IJ = JT.RM, JT.NF, JT.RUN, JT.GEN, JT.TUNE, JT.IJ
N, S, SC = JT.N, JT.S, JT.SC
Stop = GEN.Stop

from adapters.xbrl import verify_document as VD      # noqa: E402
from adapters.xbrl import recipes as R                # noqa: E402

FLAG = NS.FLAG
SEAL_REL = "docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md"
SEAL_COMMIT = "3a6aefa"
DOC_REL = "docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md"
REC_DIR_REL = "fixtures/xbrl/pswap"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-06.json"
REC_REL = collections.OrderedDict([("inject", INJECT_REL)])
SCRIPT_REL = "measure/xbrl_pswap_2026-11-06.py"
JT_SCRIPT_REL = "measure/xbrl_jtypes_2026-11-05.py"
JT_RECORD_REL = JT.INJECT_REL                      # fixtures/xbrl/jtypes/inject_2026-11-05.json(読むだけ)
NS_SCRIPT_REL = JT.NS_SCRIPT_REL
H_RECORD_REL = JT.H_RECORD_REL                     # fixtures/xbrl/nscan/inject_2026-11-05.json(読むだけ)
RB_RECORD_REL = JT.RB_RECORD_REL                   # fixtures/xbrl/rmix/inject_2026-11-04.json(読むだけ)
LIB_RELS = JT.LIB_RELS
UNTOUCHED_FOR_PS1 = ("measure/inject.py", "measure/lib/sites.py")
SOURCES = JT.SOURCES
INJECT_PROFILES = JT.INJECT_PROFILES               # ("P29E", "P30E")
T9 = "T9_PRIOR_TO_CURRENT"
SHAPES = JT.SHAPES                                 # (既存, 万だけ, 複合)
LINK_KEY, COMPARE_KEY = RM.LINK_KEY, RM.COMPARE_KEY
LINKED, UNLINKED = RM.LINKED, RM.UNLINKED
HIT, MISS = RM.HIT, RM.MISS
STATUS_NO_BASE, STATUS_NOT_G = NS.STATUS_NO_BASE, NS.STATUS_NOT_G
BASE_WORD = RM.BASE_WORD
SITE_WORD = "ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件・単位が同じ・両方正・値が違い、当期の値を元の字の形で描ける数(既存・万だけ・複合の全部)"
BREAKDOWN_KEY = "形別の内訳(P30E)"
CUE_KEY = "engine の手がかり別の内訳(P30E)"
PERIOD_KEY = "通した行の注入後の pointer の期の内訳"
PS_KEY = "PS の欄"
#: 乱数の種の字(封 §1 の 2 の字と同じ)
SEED_T9 = "%s|%s|T9_PRIOR_TO_CURRENT"
#: 前期の語(封 §0-1 の 2 の 6 語。site の文に同じ行で在るか)
PRIOR_WORDS = ("前期", "前年", "前連結会計年度", "前事業年度", "前年同期", "前年度")
#: pointer の期の分け方(語は 4 つ)
PERIODS = ("CurrentYear", "Prior1Year", "他", "なし")
STAGE_KEYS = ("参照先が Prior1Year", "同じ要素の CurrentYear が 1 件", "単位が同じ・両方正・値が違う", "site")
#: 封 §6 の字に足す、この script の限界(数は変えない)
EXTRA_LIMITS = (
    "round-trip 不一致は止めずに数える(K-2 の欄)。封 §3 の PS-9 は 0 を予測し、判定は K-2 に出る",
    "PS-3 の「採った」は cap を基準で絞る前に掛けた数 Σ min(cap, 作れる site)、「うち土台 P30E が GROUNDED の行」が実際に注入した行(J の T6 と同じ読み)",
    "「届いた」は元の数の字が基準の claim の span に在り、かつ注入後の claim(P30E)の span に差し替えの字が在るか(T9 は単位の字を替えない)",
    "pointer の期は基準の claim と注入後の claim(どちらも P30E)の pointers の先頭の context の先頭で分けた語(claim が無い行は なし)。要素名は記録に持たない",
    "engine の手がかりは注入前の文と注入前の token で recipes._prior_cue を呼んだ真偽(site の選びには使わない)。PS-10 の止めた行は 対応が付く行 − 通した行",
    "PS-8 の「判定が違う行」は P29E と P30E の両方で注入後の claim に対応が付き、結果の語が違う行(片方の profile だけ対応が付かない行は判定が無いので数えない)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def norm(x):
    return json.loads(json.dumps(x))


shape_of_token = JT.shape_of_token
yen_scan_on = NS.yen_scan_on


# ======================================================================================================
# 配線・鍵の検査
def wiring_problems():
    return NS.wiring_problems()


def inject_wiring_problems():
    return NS.inject_wiring_problems()


def key_leaks_ps(text, key_value=None, long_alnum=True):
    u"""この便の封の path(32 字に近い英数字・_・- の連なり)を除いて、J の便の検査に渡す。"""
    return JT.key_leaks_j(text.replace(SEAL_REL, u""), key_value, long_alnum)


@contextlib.contextmanager
def key_check_ps():
    u"""``GEN.key_leaks`` を with の中だけこの便の封の path を除く版にする(NS の配線の検査は with の外で走らせる)。"""
    old = GEN.key_leaks
    GEN.key_leaks = key_leaks_ps
    try:
        yield
    finally:
        GEN.key_leaks = old


def assert_clean_ps(rec, key_value=None):
    with key_check_ps():
        RUN.assert_clean(rec, key_value)


# ======================================================================================================
# 期の分け方・手がかり・届いた(行の欄の部品。行の欄の試験が壊した例で固定する)
def pointer_period(pointers):
    u"""claim の pointers の先頭の context の先頭で 4 つの語に分ける。無ければ なし、xbrl の fact でなければ 他。要素名は返さない。"""
    ptrs = list(pointers or [])
    if not ptrs:
        return "なし"
    p = ptrs[0]
    if not isinstance(p, str) or not p.startswith("xbrl:") or "@" not in p:
        return "他"
    ctx = p.rpartition("@")[2]
    if ctx.startswith("CurrentYear"):
        return "CurrentYear"
    if ctx.startswith("Prior1Year"):
        return "Prior1Year"
    return "他"


def engine_cue(text, tok):
    u"""engine 自身の手がかりの判定(``recipes._prior_cue``)の真偽。読むだけ。"""
    return bool(R._prior_cue(text, tok.start, tok.end))


def line_of(text, tok):
    s0 = text.rfind("\n", 0, tok.start) + 1
    e0 = text.find("\n", tok.end)
    return text[s0:(len(text) if e0 < 0 else e0)]


def has_prior_word(text, tok):
    u"""site の文(token と同じ行)に前期の語(6 語)のどれかが在る。"""
    line = line_of(text, tok)
    return any(w in line for w in PRIOR_WORDS)


def reached_of(orig_digits, base_span, res, rendered):
    u"""届いた = 元の字が基準の claim の span に在る かつ 注入後の claim の span に差し替えの字が在る。"""
    return bool(res is not None and orig_digits in (base_span or "") and rendered in (res.get("span") or ""))


def read_back(rendered, unit):
    u"""描いた字 + 単位を ``N.scan`` して token が 1 つのとき、値 × 単位の倍率(円)。違えば None。"""
    toks = N.scan(rendered + (unit or ""))
    if len(toks) != 1:
        return None
    return toks[0].value * (SC.scale_of(unit) or 1)


# ======================================================================================================
# site
def t9_stages_and_sites(text, refs):
    u"""(段の数え, site の列)。site は ``S.identified_sites`` の (token, ref) から封 §1 の 1 のとおり作る。"""
    by_key = {}
    for r in refs:
        by_key.setdefault(r["key"], []).append(r)
    stages = collections.OrderedDict((k, 0) for k in STAGE_KEYS)
    out = []
    for t, ref in S.identified_sites(text, refs):
        elem, _, ctx = ref["key"].partition("@")
        if not ctx.startswith("Prior1Year"):
            continue
        stages["参照先が Prior1Year"] += 1
        ck = "%s@%s" % (elem, "CurrentYear" + ctx[len("Prior1Year"):])
        cands = by_key.get(ck, [])
        if len(cands) != 1:
            continue
        cur = cands[0]
        stages["同じ要素の CurrentYear が 1 件"] += 1
        if cur.get("unit") != ref.get("unit"):
            continue
        if not (cur["value"] > 0 and ref["value"] > 0 and abs(cur["value"] - ref["value"]) > IJ.TOL):
            continue
        stages["単位が同じ・両方正・値が違う"] += 1
        factor = SC.scale_of(t.unit) or 1
        cand = cur["value"] / float(factor)
        rendered = N.render_value(cand, t)
        back = read_back(rendered, t.unit)
        if back is None or abs(back - cur["value"]) > max(IJ.TOL, abs(cur["value"]) * 1e-9) or rendered == t.text:
            continue
        stages["site"] += 1
        out.append({"type": T9, "token": t, "ref": ref, "current": cur, "current_key": ck,
                    "element": elem, "new_value": cand, "rendered": rendered})
    return stages, out


def t9_sites(text, refs):
    return t9_stages_and_sites(text, refs)[1]


def t9_all_sites(text, refs, seed, key):
    u"""(段の数え, site 全部(並べ替え済み))。token の start の順に並べてから ``<seed>|<key>|T9_PRIOR_TO_CURRENT`` で並べ替える。"""
    stages, sites = t9_stages_and_sites(text, refs)
    sites.sort(key=lambda s: s["token"].start)
    random.Random(SEED_T9 % (seed, key)).shuffle(sites)
    return stages, sites


def build_t9(site, inj_id):
    u"""注入 1 件(``IJ.apply_edits`` が読む欄と ``TUNE.claim_for_p27`` が読む欄)。差し替えは [token.start, token.end] を rendered に(単位の字は触らない)。"""
    t = site["token"]
    return {"type": T9, "id": inj_id, "new_value": site["new_value"], "replacement": site["rendered"], "span": [t.start, t.end],
            "detail": {"original_value": t.value, "current_value_in_reference_units": site["current"]["value"],
                       "true_ref_key": site["ref"]["key"], "current_ref_key": site["current_key"]}}


# ======================================================================================================
# 数え
def status_counter(sites, base_claims, base_by_id, text):
    c = collections.Counter(RM.base_status_rb(base_claims, base_by_id, s["token"], text)[0] for s in sites)
    return collections.OrderedDict(sorted(c.items()))


def shape_counter(sites):
    c = collections.Counter(shape_of_token(s["token"]) for s in sites)
    return collections.OrderedDict((k, c.get(k, 0)) for k in SHAPES)


def cue_counter(text, sites):
    c = collections.Counter(engine_cue(text, s["token"]) for s in sites)
    return collections.OrderedDict([("真", c.get(True, 0)), ("偽", c.get(False, 0))])


# ======================================================================================================
# 1 本の注入
def inject_text_ps(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""T9 の 1 本の注入(1 回に 1 件・round-trip は止めずに数える)。site は ``t9_all_sites``。(行, 数え)。"""
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([("注入しない", "文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    stages, sites = t9_all_sites(text, refs, seed, key)
    ok, pop = [], collections.Counter()
    for s in sites:
        st, bc = RM.base_status_rb(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
        if bc is not None:
            ok.append((s, bc))
    counts = collections.OrderedDict([
        ("段", stages), ("作れる site", shape_counter(sites)), ("作れる site の手がかり", cue_counter(text, sites)),
        ("作れる site の状態", collections.OrderedDict(sorted(pop.items()))),
        ("土台 P30E が GROUNDED の site", len(ok)), ("cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
    taken = collections.Counter()
    rows = []
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        tok = s["token"]
        inj = build_t9(s, "%s-T9-%02d" % (key, n))
        taken[LINKED if bc["ids"][profiles[0]] is not None else UNLINKED] += 1
        tampered, placements = IJ.apply_edits(text, [inj])
        rt = IJ.revert(tampered, [inj], placements, text) == text
        orig_digits = text[tok.start:tok.end]
        row = collections.OrderedDict([
            ("id", inj["id"]), ("型", T9), ("形", shape_of_token(tok)), ("単位", tok.unit),
            ("基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None),
            ("round-trip", bool(rt)), ("読み直し", bool(JT.reread_j(tampered, tok, inj["new_value"], tok.unit))),
            ("先頭の位が減った", bool(tok.groups is not None and NS.groups_in(inj["replacement"]) < len(tok.groups))),
            ("engine の手がかり", engine_cue(text, tok)), ("文に前期の語", has_prior_word(text, tok)),
            ("基準の pointer の期", pointer_period(bc.get("pointers")))])
        reached, post_period = False, "なし"
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)
                continue
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
            if p == profiles[1]:
                reached = reached_of(orig_digits, bc.get("span"), res, inj["replacement"])
                post_period = pointer_period(res.get("pointers")) if res is not None else "なし"
        row["注入後の pointer の期"] = post_period
        row["届いた"] = reached
        rows.append(row)
    counts["採った"] = n
    counts["採った の状態"] = collections.OrderedDict(sorted(taken.items()))
    return rows, counts


def inject_job_ps(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(N, FLAG):
        raise Stop("**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_ps(zb, text, refs, seed, name)
    base = collections.OrderedDict([("docID", item["docID"]), ("form", item["form"]), ("model", item["model"]), ("writer", item["writer"])])
    out = []
    for r in rows:
        d = collections.OrderedDict(base)
        d.update(r)
        out.append(d)
    return name, out, counts


# ======================================================================================================
# 集計(門が記録の行と本ごとの数えから作り直して照らす)
@contextlib.contextmanager
def ps_types_in_run():
    u"""``RUN.INJECT_TYPES`` を with の中だけ T9 の 1 型にする(``RM.inject_summaries`` が型の並びをここから読むため)。出るときは必ず戻す。"""
    old_t, old_p = RUN.INJECT_TYPES, RUN.PROFILES
    RUN.INJECT_TYPES, RUN.PROFILES = (T9,), INJECT_PROFILES
    try:
        yield
    finally:
        RUN.INJECT_TYPES, RUN.PROFILES = old_t, old_p


def inject_summaries(rows):
    with ps_types_in_run():
        return RM.inject_summaries(rows)


def unlinked_counts(rows):
    return collections.OrderedDict([("全体", sum(1 for r in rows if not r[LINK_KEY])), (T9, sum(1 for r in rows if r["型"] == T9 and not r[LINK_KEY]))])


def breakdown(rows):
    u"""形(既存 / 万だけ / 複合)別の P30E の率。"""
    return collections.OrderedDict((k, RUN.inject_cell([r for r in rows if r["形"] == k], "P30E")) for k in SHAPES)


def cue_breakdown(rows):
    u"""engine の手がかり(真 / 偽)別の P30E の率。"""
    return collections.OrderedDict((k, RUN.inject_cell([r for r in rows if r["engine の手がかり"] is (k == "真")], "P30E")) for k in ("真", "偽"))


def period_breakdown(rows):
    u"""通した行(P30E)の注入後の pointer の期の内訳。"""
    passed = [r for r in rows if r["P30E"]["結果"] == TUNE.LABEL_PASS]
    c = collections.Counter(r["注入後の pointer の期"] for r in passed)
    return collections.OrderedDict([("通した行", len(passed))] + [(k, c.get(k, 0)) for k in PERIODS])


def pass_rate(sel):
    return RUN.inject_cell(sel, "P30E")[TUNE.LABEL_PASS]["率"]


def ps_columns(per, rows):
    u"""PS-2〜PS-10 の欄を ``本ごとの数え`` と ``行`` から数える(記録の ``PS の欄`` と tally の判定が使う)。"""
    sc = NS.sum_counts
    shapes = collections.OrderedDict((k, sc(per, ("作れる site", k))) for k in SHAPES)
    ps2 = collections.OrderedDict([("計", sum(shapes.values()))] + list(shapes.items()) + [("手がかり真", sc(per, ("作れる site の手がかり", "真")))])
    prior = sum(1 for r in rows if r["基準の pointer の期"] == "Prior1Year")
    ps3 = collections.OrderedDict([("採った", sc(per, ("cap を基準で絞る前に掛けた数",))), ("うち土台 P30E が GROUNDED の行", len(rows)),
                                   ("うち基準の pointer の期が Prior1Year の行", prior), ("割合", pct(prior, len(rows)))])
    ps4 = RUN.inject_cell(rows, "P30E")[TUNE.LABEL_PASS]
    ps4 = collections.OrderedDict([("通した率(P30E)", ps4["率"]), ("通した行", ps4["件"]), ("対応が付く行", ps4["分母"])])
    passed = [r for r in rows if r["P30E"]["結果"] == TUNE.LABEL_PASS]
    cur = sum(1 for r in passed if r["注入後の pointer の期"] == "CurrentYear")
    ps5 = collections.OrderedDict([("通した行", len(passed)), ("うち注入後の pointer の期が CurrentYear", cur), ("割合", pct(cur, len(passed)))])
    mapped = [r for r in rows if r["P30E"]["対応"]]
    cue = [r for r in mapped if r["engine の手がかり"]]
    ps6 = collections.OrderedDict([("対応が付く行", len(mapped)), ("うち手がかり真", len(cue)), ("手がかり真の割合", pct(len(cue), len(mapped))),
                                   ("手がかり真の行の通した率", pass_rate(cue))])
    ps7 = collections.OrderedDict([("通した行", len(passed)), ("うち届かない行", sum(1 for r in passed if not r["届いた"]))])
    both = [r for r in rows if r[LINK_KEY] and r["P29E"]["対応"] and r["P30E"]["対応"]]
    differ = [r for r in both if r["P29E"]["結果"] != r["P30E"]["結果"]]
    ps8 = collections.OrderedDict([("違う行", len(differ)), ("両方に対応が付く行", len(both))])
    ps9 = collections.OrderedDict([("round-trip 不一致", sum(1 for r in rows if not r["round-trip"])), ("読み直し不一致", sum(1 for r in rows if not r["読み直し"])),
                                   ("先頭の位が減った行", sum(1 for r in rows if r["先頭の位が減った"]))])
    stopped = [r for r in mapped if r["P30E"]["結果"] != TUNE.LABEL_PASS]
    named = [r for r in stopped if r["P30E"]["結果"] == TUNE.LABEL_NAMED_ORIGINAL]
    ps10 = collections.OrderedDict([("対応が付く行", len(mapped)), ("止めた行", len(stopped)), ("うち名指して原本", len(named)), ("割合", pct(len(named), len(stopped)))])
    ref = collections.OrderedDict([("届いた行", sum(1 for r in rows if r["届いた"])), ("文に前期の語がある行", sum(1 for r in rows if r["文に前期の語"])),
                                   ("手がかり真の行(全部)", sum(1 for r in rows if r["engine の手がかり"]))])
    return collections.OrderedDict([
        ("PS-2 作れる site(種類別)と engine の手がかり真", ps2), ("PS-3 採った / うち土台 P30E が GROUNDED の行 / 基準の pointer の期", ps3),
        ("PS-4 通した率(P30E)", ps4), ("PS-5 通した行の注入後の pointer の期", ps5), ("PS-6 engine の手がかり", ps6),
        ("PS-7 通した行のうち届かない行", ps7), ("PS-8 P29E と P30E で判定が違う行(両方に対応が付く行)", ps8), ("PS-9", ps9),
        ("PS-10 止めた行の中で名指して原本の割合", ps10), ("参考", ref)])


# ======================================================================================================
# 記録の書き方
def caches_all():
    return RM.caches_all()


def header_ps(root, step, seed_meta, before, after, profiles):
    h = RUN.header(root, step, os.path.join(root, SOURCES["aiforms"]["gen"]), seed_meta, before, after)
    h["seal"] = SEAL_REL
    h["封の commit"] = SEAL_COMMIT
    h["この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h["J の script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_jtypes_2026-11-05.py"))
    h["nscan script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_nscan_2026-11-05.py"))
    h["rmix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_rmix_2026-11-04.py"))
    h["numfix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_numfix_2026-11-04.py"))
    h["前の便の run script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_run_2026-11-03.py"))
    h["生成の記録の sha256"] = collections.OrderedDict((src, GEN.sha256_file(os.path.join(root, p["gen"]))) for src, p in SOURCES.items())
    h["J の記録の sha256"] = GEN.sha256_file(os.path.join(root, JT_RECORD_REL))
    h["H の記録の sha256"] = GEN.sha256_file(os.path.join(root, H_RECORD_REL))
    h["RB の記録の sha256"] = GEN.sha256_file(os.path.join(root, RB_RECORD_REL))
    h["lib の指紋"] = collections.OrderedDict((rel, GEN.sha256_file(os.path.join(root, rel))) for rel in LIB_RELS)
    h["profile"] = list(profiles)
    return h


def scope_word(only):
    return "全 200 本" if only is None else "**--only(本番の記録ではない)**"


load_books = JT.load_books


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_limits(seal):
    return NS.seal_limits(seal)


def write_json(out, rec, key_value=None):
    text = RUN.dumps_inject(rec)
    with key_check_ps():
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
    work_root = work_root or tempfile.mkdtemp(prefix="pswap_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say("注入 %d 本 × 2 profile(P29E・P30E)。切り替え 真・T9_PRIOR_TO_CURRENT ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with yen_scan_on():
        if not getattr(N, FLAG) or wiring_problems():
            raise Stop("**切り替えを真にできない・配線が崩れた。止める**")
        results = NF.map_pool(inject_job_ps, jobs_, procs)
    if getattr(N, FLAG):
        raise Stop("**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop("**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_ps(root, "T9(前期の fact に結ばれた数に当期の値を入れる)― 切り替え 真・T9_PRIOR_TO_CURRENT の注入(P29E・P30E。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec["範囲"] = scope_word(only)
    rec["切り替え"] = collections.OrderedDict([("名前", FLAG), ("inject の中の値", True), ("出たあとの値", bool(getattr(N, FLAG))), ("配線の問題", wiring_problems())])
    rec["種"] = {"file": RUN.SEED_REL_STR, "種の確認": seed_meta}
    rec["型"] = collections.OrderedDict([
        (T9, "S.identified_sites の (token, ref) のうち ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件の数に、その当期の値を元の字の形で入れる(単位の字は触らない)。"
             "token の start の順に並べてから <seed>|<本の名前>|T9_PRIOR_TO_CURRENT で並べ替え、土台 P30E GROUNDED の site を先頭から cap 件"),
        ("上限", "1 本あたり %d" % RUN.INJECT_CAP),
        ("site", SITE_WORD),
        ("土台", BASE_WORD),
        ("土台の結び方", "P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        ("届いた", "元の字が基準の claim の span に在る かつ 注入後の claim(P30E。対応が付いたとき)の span に差し替えの字が在る"),
        ("engine の手がかり", "recipes._prior_cue(注入前の文, token.start, token.end) の真偽。読むだけで site の選びには使わない"),
        ("pointer の期", "基準の claim と注入後の claim(P30E)の pointers の先頭の context の先頭: CurrentYear / Prior1Year / 他 / なし。要素名は持たない"),
        ("集計の2本", "集計 = 全部の site での P29E・P30E の率。" + COMPARE_KEY + " = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率"),
        ("inject の docID の引数", "本の名前(<docID>_<形>_<model>)")])
    rec["本ごとの数え"] = per
    rec["注入の行の数"] = len(rows)
    rec["集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[BREAKDOWN_KEY] = breakdown(rows)
    rec[CUE_KEY] = cue_breakdown(rows)
    rec[PERIOD_KEY] = period_breakdown(rows)
    rec["P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[PS_KEY] = ps_columns(per, rows)
    rec["限界"] = seal_limits(seal_text(root)) + list(EXTRA_LIMITS)
    rec["行"] = rows
    write_json(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の PS-1〜PS-10・§4 の K-1〜K-4)を読み、記録から判定する
def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {PS-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (PS-\d+) \| (.*) \|$", line)
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
    b["PS-1"] = P["PS-1"][1].strip()
    m = re.match(r"^%s / %s / %s / %s、手がかり真 %s$" % ((RANGE,) * 5), P["PS-2"][1].strip())
    b["PS-2"] = collections.OrderedDict([("計", _rng(m, 1)), ("既存", _rng(m, 3)), ("万だけ", _rng(m, 5)), ("複合", _rng(m, 7)), ("手がかり真", _rng(m, 9))])
    m = re.match(r"^%s / %s / (%s)〜(%s)%%$" % (RANGE, RANGE, NUM, NUM), P["PS-3"][1].strip())
    b["PS-3"] = collections.OrderedDict([("採った", _rng(m, 1)), ("うち土台 P30E が GROUNDED の行", _rng(m, 3)), ("割合", _rng(m, 5))])
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["PS-4"][1].strip())
    b["PS-4"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["PS-5"][1].strip())
    b["PS-5"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    m = re.match(r"^%s%%、%s%%$" % (RANGE, RANGE), P["PS-6"][1].strip())
    b["PS-6"] = collections.OrderedDict([("手がかり真の割合", _rng(m, 1)), ("手がかり真の行の通した率", _rng(m, 3))])
    b["PS-7"] = int(re.match(r"(\d+)$", P["PS-7"][1].strip()).group(1))
    m = re.match(r"^(\d+)〜(\d+)$", P["PS-8"][1].strip())
    b["PS-8"] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"(\d+) / (\d+) / (\d+)〜(\d+)$", P["PS-9"][1].strip())
    b["PS-9"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2))), ("先頭の位が減った行", (int(m.group(3)), int(m.group(4))))])
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["PS-10"][1].strip())
    b["PS-10"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    b["K-1"] = re.search(r"PS-1 が (一致)", K["K-1"]).group(1)
    m = re.search(r"PS-9 の round-trip 不一致 (\d+)・読み直し不一致 (\d+)", K["K-2"])
    b["K-2"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2)))])
    b["K-3"] = NF.num(re.search(r"対応が付く行 ≥ (%s)" % NUM, K["K-3"]).group(1))
    b["K-4"] = int(re.search(r"PS-7 が (\d+)", K["K-4"]).group(1))
    return b


within = RM.within


def git_numstat_since_seal(root=ROOT):
    u"""``git diff --numstat <封の commit> -- measure/inject.py measure/lib/sites.py`` の行(空なら 0 行)。git が読めなければ None。"""
    p = subprocess.run(["git", "diff", "--numstat", SEAL_COMMIT, "--"] + list(UNTOUCHED_FOR_PS1), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return None
    return [ln for ln in p.stdout.decode("utf-8").splitlines() if ln]


def ps1_value(rec, h_rec, rb_rec, numstat):
    u"""PS-1 の 3 つ: lib の指紋が H の記録と、engine の指紋(sha256 の 2 欄。git_commit は比べない)が RB の記録と一致・inject.py と sites.py が封の commit から変わった file の数。"""
    fp, rfp = rec.get("engine の指紋") or {}, rb_rec.get("engine の指紋") or {}
    eng = all(fp.get(k) is not None and fp.get(k) == rfp.get(k) for k in ("adapter_xbrl_py_sha256", "core_py_sha256"))
    lib = rec.get("lib の指紋") is not None and norm(rec.get("lib の指紋")) == norm(h_rec.get("lib の指紋"))
    return collections.OrderedDict([("lib の指紋が H の記録と一致", bool(lib)), ("engine の指紋が RB の記録と一致", bool(eng)),
                                    ("inject.py・sites.py が封の commit から変わった file", None if numstat is None else len(numstat))])


NOT_GIVEN = object()


def build_PS(R_, seal, numstat=NOT_GIVEN):
    u"""{PS, K, 採用, 欄}。R_ = {"inject", "h", "rb"}(記録の JSON)。欄は inject の記録の 本ごとの数え と 行 から数え直す(記録の ``PS の欄`` は使わない)。
    numstat 省略時は git に聞く。None を渡したら『読めなかった』= PS-1 は外れ(省略とは別。読めないのに作業木の答えで代えない)。"""
    inj = R_["inject"]
    if numstat is NOT_GIVEN:
        numstat = git_numstat_since_seal()
    return judge_from(ps1_value(inj, R_["h"], R_["rb"], numstat), ps_columns(inj["本ごとの数え"], inj["行"]), seal)


def judge_from(ps1, cols, seal):
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    PS = collections.OrderedDict()

    def put(k, ok, val):
        PS[k] = {"判定": HIT if ok else MISS, "値": val}
    put("PS-1", ps1["lib の指紋が H の記録と一致"] and ps1["engine の指紋が RB の記録と一致"] and ps1["inject.py・sites.py が封の commit から変わった file"] == 0, ps1)
    c2 = cols["PS-2 作れる site(種類別)と engine の手がかり真"]
    put("PS-2", all(within(c2[k], B["PS-2"][k]) for k in B["PS-2"]), c2)
    c3 = cols["PS-3 採った / うち土台 P30E が GROUNDED の行 / 基準の pointer の期"]
    put("PS-3", within(c3["採った"], B["PS-3"]["採った"]) and within(c3["うち土台 P30E が GROUNDED の行"], B["PS-3"]["うち土台 P30E が GROUNDED の行"])
        and within(c3["割合"], B["PS-3"]["割合"]), c3)
    c4 = cols["PS-4 通した率(P30E)"]
    put("PS-4", within(c4["通した率(P30E)"], B["PS-4"]), c4)
    c5 = cols["PS-5 通した行の注入後の pointer の期"]
    put("PS-5", within(c5["割合"], B["PS-5"]), c5)
    c6 = cols["PS-6 engine の手がかり"]
    put("PS-6", within(c6["手がかり真の割合"], B["PS-6"]["手がかり真の割合"]) and within(c6["手がかり真の行の通した率"], B["PS-6"]["手がかり真の行の通した率"]), c6)
    c7 = cols["PS-7 通した行のうち届かない行"]
    put("PS-7", c7["うち届かない行"] == B["PS-7"], c7)
    c8 = cols["PS-8 P29E と P30E で判定が違う行(両方に対応が付く行)"]
    put("PS-8", within(c8["違う行"], B["PS-8"]), c8)
    c9 = cols["PS-9"]
    put("PS-9", c9["round-trip 不一致"] == B["PS-9"]["round-trip 不一致"] and c9["読み直し不一致"] == B["PS-9"]["読み直し不一致"]
        and within(c9["先頭の位が減った行"], B["PS-9"]["先頭の位が減った行"]), c9)
    c10 = cols["PS-10 止めた行の中で名指して原本の割合"]
    put("PS-10", within(c10["割合"], B["PS-10"]), c10)
    K = collections.OrderedDict()
    K["K-1"] = {"判定": PS["PS-1"]["判定"], "値": collections.OrderedDict([("PS-1", PS["PS-1"]["判定"])])}
    k2 = c9["round-trip 不一致"] == B["K-2"]["round-trip 不一致"] and c9["読み直し不一致"] == B["K-2"]["読み直し不一致"]
    K["K-2"] = {"判定": HIT if k2 else MISS, "値": collections.OrderedDict([("round-trip 不一致", c9["round-trip 不一致"]), ("読み直し不一致", c9["読み直し不一致"])])}
    K["K-3"] = {"判定": HIT if c6["対応が付く行"] >= B["K-3"] else MISS, "値": collections.OrderedDict([("対応が付く行", c6["対応が付く行"])])}
    K["K-4"] = {"判定": HIT if c7["うち届かない行"] == B["K-4"] else MISS, "値": collections.OrderedDict([("通した行のうち届かない行", c7["うち届かない行"])])}
    adopt = all(K[k]["判定"] == HIT for k in K)
    return collections.OrderedDict([("PS", PS), ("K", K), ("採用", adopt), ("欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


fmt = RM.fmt


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = ["| # | 欄 | 予測 | 測った値 | 判定 |", "|---|---|---|---|---|"]
    for k, v in J["PS"].items():
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
    return collections.OrderedDict([("inject", GEN.jload(os.path.join(root, INJECT_REL))), ("h", GEN.jload(os.path.join(root, H_RECORD_REL))), ("rb", GEN.jload(os.path.join(root, RB_RECORD_REL)))])


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_PS(load_records(root), seal, git_numstat_since_seal(root))
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
