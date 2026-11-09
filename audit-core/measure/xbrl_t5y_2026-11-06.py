# -*- coding: utf-8 -*-
u"""封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §1・§5 ― T5Y(注入の仕掛けの T5 = 値が偶然一致して参照先が違う を円族の数に作れるようにする切り替え)の測定と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_t5y_2026-11-06.py inject [--procs N] [--only <docID>[,<docID>...]] [--out PATH]   # 切り替え 2 つ 真 で T5_COINCIDENT を注入(P29E・P30E)→ fixtures/xbrl/t5y/inject_2026-11-06.json
    python3 measure/xbrl_t5y_2026-11-06.py tally  [--root DIR]                                              # 記録から Y-1〜Y-10 と K-1〜K-4 の表を出す(file は書かない)

T9 の第 2 便の script ``xbrl_pswap_idmap_2026-11-06.py``(PI)は **1 byte も変えず**、importlib で読み込んで使う(PS・JT・NS・RM・NF・RUN・GEN・TUNE・IJ・N・S・SC は PI の持つ同じ instance。
注入後の claim を基準の claim の id で引く対応付けの関数 ``id_map``・``id_claim``・``id_conditions`` と、行の欄の関数 ``PS.reached_of``・``PS.pointer_period``・``PS.shape_of_token`` もそのまま使う)。
切り替えは 2 つ: H の ``yen_scan_2026_11_05``(``NS.yen_scan_on``)と T5Y の ``t5_yen_2026_11_06``(``S.t5_yen_on``)。どちらも with の中だけ真。
``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- site: ``S.t5_sites(text, refs)``(2 つの切り替え 真)。並べ替えは token の start の順 → ``random.Random("<seed>|<本の名前>|T5_COINCIDENT")`` で shuffle → 土台 P30E GROUNDED の site を先頭から cap 件。
  差し替えは ``IJ.build_t5(site, refs, rng)``。rng は並べ替えに使った同じ Random の続き(``IJ.select`` と同じ作り。取った site の順に 1 回ずつ引く = 封に無い決め)。
- 数え: 「作れる site」= 切り替え 真の ``t5_sites`` の数(形別)。「読み直せる site」= 篩だけの site(``S.t5_sites_yen(text, refs, False)``)のうち、相手の単位の優先を掛けた pool の先頭 3 件が全部読み直せる site(封 §0-1 の 2 の下調べと同じ定義)。
  偽の site 数 = T5 の切り替え 偽で ``t5_sites`` を、H の切り替え 偽(J の記録の「偽」)と 真(J の記録の「真」)の 2 通りで数えた数。
  T1_VALUE・T8_REL の作れる site は H の便と同じ関数(``NS.t1_sites_only_new``・``NS.t8_candidates_new``)で T5 の切り替え 偽のまま数えて H の記録と照らす(Y-1)。
- 対応付け: 注入後の文の claim のうち ``id == 基準の claim の id`` の claim を引き、T9 の第 2 便と同じ 3 条件((ア)(イ)(ウ))で対応を決める。
- 相手の fact の期 = ``coincident_ref_key`` の context の先頭(CurrentYear / Prior1Year / 他)。相手と同じ要素か = 相手の key と本当の参照の key の要素名(@ の前)が同じか(要素名は記録に持たず真偽だけ)。
  注入後の pointer が相手の fact と同じか = id で引いた claim(P30E)の pointers の先頭(名前空間の接頭辞を除いた ``<要素>@<context>``)が相手の key か(真偽だけ)。
- Y-10 の試験: ``measure/tests/test_inject.py``(偽のまま)・``measure/tests/test_t5_yen.py``(足した試験)を unittest で 1 回ずつ走らせ、封 §3 の Y-10 が名指す変異 5 つ(lib・inject の属性の差し替え。with の中だけ)で足した試験が赤になるか。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。

engine(``core/``・``adapters/``)・``measure/lib/numbers.py``・``scales.py``・前の便の script と記録は 1 行も変えない。
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
import unittest

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


PI = load_module("xbrl_pswap_idmap_2026-11-06.py", "pswap_idmap_for_t5y")
PS = PI.PS
JT = PI.JT
NS = PI.NS
RM, NF, RUN, GEN, TUNE, IJ = PI.RM, PI.NF, PI.RUN, PI.GEN, PI.TUNE, PI.IJ
N, S, SC = PI.N, PI.S, PI.SC
Stop = GEN.Stop

FLAG = PI.FLAG                                     # H の切り替え yen_scan_2026_11_05
FLAG2 = "t5_yen_2026_11_06"                        # T5Y の切り替え(measure/lib/sites.py)
SEAL_REL = "docs/XBRL_T5_YEN_SEAL_2026-11-06.md"
SEAL_COMMIT = "79d05cd"
DOC_REL = "docs/XBRL_T5_YEN_RESULT_2026-11-06.md"
REC_DIR_REL = "fixtures/xbrl/t5y"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-06.json"
REC_REL = collections.OrderedDict([("inject", INJECT_REL)])
SCRIPT_REL = "measure/xbrl_t5y_2026-11-06.py"
PI_SCRIPT_REL = "measure/xbrl_pswap_idmap_2026-11-06.py"
PI_RECORD_REL = PI.INJECT_REL                      # fixtures/xbrl/pswap/inject_idmap_2026-11-06.json(T9 の第 2 便の記録。読むだけ)
J_RECORD_REL = PS.JT_RECORD_REL                    # fixtures/xbrl/jtypes/inject_2026-11-05.json(Y-1 の照らし先。読むだけ)
H_RECORD_REL = PI.H_RECORD_REL
RB_RECORD_REL = PI.RB_RECORD_REL
LIB_RELS = PI.LIB_RELS
DEVICE_RELS = ("measure/lib/sites.py", "measure/inject.py")
TEST_INJECT_REL = "measure/tests/test_inject.py"
TEST_T5_REL = "measure/tests/test_t5_yen.py"
SOURCES = PI.SOURCES
INJECT_PROFILES = PI.INJECT_PROFILES               # ("P29E", "P30E")
T5 = "T5_COINCIDENT"
SEED_T5 = "%s|%s|T5_COINCIDENT"
SHAPES = PI.SHAPES                                 # (既存, 万だけ, 複合)
LINK_KEY, COMPARE_KEY = PI.LINK_KEY, PI.COMPARE_KEY
LINKED, UNLINKED = PI.LINKED, PI.UNLINKED
HIT, MISS = PI.HIT, PI.MISS
BASE_WORD = PI.BASE_WORD
BREAKDOWN_KEY = "形別の内訳(P30E)"
PARTNER_PERIOD_KEY = "相手の fact の期別の内訳(P30E)"
SAME_ELEMENT_KEY = "相手と同じ要素か別の内訳(P30E)"
PERIOD_KEY = "通した行の注入後の pointer の期の内訳"
SAME_POINTER_KEY = "通した行の注入後の pointer と相手の fact の内訳"
Y_KEY = "Y の欄"
#: 相手の fact の期の語(3 つ)
PARTNER_PERIODS = ("CurrentYear", "Prior1Year", "他")
#: 欄の名前(行)
F_COND = PI.F_COND
F_MISS = PI.F_MISS
YCOL = collections.OrderedDict([
    ("Y-2", u"Y-2 作れる site(形別)と読み直せる site"), ("Y-3", u"Y-3 採った と 注入の行"), ("Y-4", u"Y-4 id で対応が付く行の割合(P30E)"),
    ("Y-5", u"Y-5 通した率(P30E)と止めた行の中で名指して原本の割合"), ("Y-6", u"Y-6 通した行のうち注入後の pointer が相手の fact と同じ行の割合"),
    ("Y-7", u"Y-7 round-trip 不一致・読み直し不一致・届かない行"), ("Y-8", u"Y-8 P29E と P30E で判定が違う行(両方に対応が付く行)"),
    ("Y-9", u"Y-9 相手の fact の期別の通した率")])
#: 封 §6 の字に足す、この script の限界(数は変えない)
EXTRA_LIMITS = (
    "作れる site は T5 の切り替え 真の t5_sites の数(相手ごとの読み直しの篩を通った相手が 1 つ以上在る site)。読み直せる site は篩だけの site のうち、相手の単位の優先を掛けた pool の先頭 3 件が全部読み直せる site(封 §0-1 の 2 の下調べと同じ定義)",
    "差し替えの相手は IJ.build_t5 が決める(相手の単位の優先 → 並べ替えに使った同じ Random の続きで 1 回引く)。引く順は取った site の順で、封に無い決め",
    "対応付けは基準の claim の id で引く(T9 の第 2 便と同じ 3 条件)。「届いた」と注入後の pointer の期・相手の fact と同じ pointer は id で引いた claim(P30E)で決める。claim が無い行の期は なし、同じ pointer は偽",
    "Y-1 の T1_VALUE・T8_REL の作れる site は T5 の切り替え 偽のまま H の便と同じ関数で数えた値を H の記録と照らす。Y-10 の試験は measure/tests の test_inject.py・test_t5_yen.py を unittest で走らせた結果",
    "round-trip 不一致は止めずに数える(K-2 の欄)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def norm(x):
    return json.loads(json.dumps(x))


yen_scan_on = NS.yen_scan_on
t5_yen_on = S.t5_yen_on
within = RM.within
fmt = RM.fmt
LABEL_PASS, LABEL_NAMED_ORIGINAL = TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL


@contextlib.contextmanager
def t5_yen_off():
    u"""T5 の切り替えを with の中だけ偽にする(偽の site の数・T1/T8 の数を同じ process で数えるため)。出るときは必ず元の値に戻す。"""
    old = getattr(S, FLAG2)
    setattr(S, FLAG2, False)
    try:
        yield
    finally:
        setattr(S, FLAG2, old)


# ======================================================================================================
# 配線・鍵の検査
def wiring_problems():
    out = list(NS.wiring_problems())
    if getattr(IJ, "S", None) is not S:
        out.append(u"IJ が引く S(lib.sites)がこの script の S と同じ instance でない")
    if not hasattr(S, FLAG2):
        out.append(u"S に T5 の切り替えが無い")
    return out


def inject_wiring_problems():
    return list(NS.inject_wiring_problems()) + [p for p in wiring_problems() if p not in NS.wiring_problems()]


def key_leaks_ty(text, key_value=None, long_alnum=True):
    u"""この便の封の path と T9 の第 2 便の封の path(32 字に近い英数字・_・- の連なり)を除いて、T9 の第 2 便の検査に渡す。"""
    return PI.key_leaks_pi(text.replace(SEAL_REL, u""), key_value, long_alnum)


@contextlib.contextmanager
def key_check_ty():
    u"""``GEN.key_leaks`` を with の中だけこの便の封の path を除く版にする(NS の配線の検査は with の外で走らせる)。"""
    old = GEN.key_leaks
    GEN.key_leaks = key_leaks_ty
    try:
        yield
    finally:
        GEN.key_leaks = old


def assert_clean_ty(rec, key_value=None):
    with key_check_ty():
        RUN.assert_clean(rec, key_value)


# ======================================================================================================
# 行の欄の部品(行の欄の試験が壊した例で固定する)
def partner_period(coincident_key):
    u"""相手の fact の期: key の context(@ の後)の先頭で CurrentYear / Prior1Year / 他。"""
    ctx = str(coincident_key).partition("@")[2]
    if ctx.startswith("CurrentYear"):
        return "CurrentYear"
    if ctx.startswith("Prior1Year"):
        return "Prior1Year"
    return "他"


def element_of(key):
    return str(key).partition("@")[0]


def same_element(true_key, coincident_key):
    u"""相手と同じ要素か(要素名は記録に持たず真偽だけ)。"""
    return element_of(true_key) == element_of(coincident_key)


def pointer_key(pointer):
    u"""claim の pointer(``xbrl:<名前空間>:<要素>@<context>``)を参照の key(``<要素>@<context>``)の形にする。xbrl の fact の pointer でなければ None。"""
    if not isinstance(pointer, str) or not pointer.startswith("xbrl:") or "@" not in pointer:
        return None
    elem, _, ctx = pointer[len("xbrl:"):].partition("@")
    return "%s@%s" % (elem.rpartition(":")[2], ctx)


def pointer_is_partner(pointers, coincident_key):
    u"""id で引いた claim の pointers の先頭が相手の key(の fact)か。pointers が無ければ偽。"""
    ptrs = list(pointers or [])
    return bool(ptrs) and pointer_key(ptrs[0]) == str(coincident_key)


def head3_readable(site):
    u"""篩だけの site の『読み直せる』(封 §0-1 の 2 の下調べの定義): 相手の単位の優先を掛けた pool の先頭 3 件が全部読み直せる。"""
    ref = site["ref"]
    pool = [o for o in site["others"] if o.get("unit") == ref.get("unit")] or site["others"]
    return all(S.t5_readable(site["token"], o["value"]) for o in pool[:3])


# ======================================================================================================
# site
def t5_all_sites(text, refs, seed, key):
    u"""(site 全部(並べ替え済み), 並べ替えに使った Random)。token の start の順に並べてから ``<seed>|<key>|T5_COINCIDENT`` で並べ替える。"""
    sites = list(S.t5_sites(text, refs))
    sites.sort(key=lambda s: s["token"].start)
    rng = random.Random(SEED_T5 % (seed, key))
    rng.shuffle(sites)
    return sites, rng


def shape_counter(sites):
    c = collections.Counter(PS.shape_of_token(s["token"]) for s in sites)
    return collections.OrderedDict((k, c.get(k, 0)) for k in SHAPES)


def site_counts(text, refs):
    u"""T5 の site の数え(偽 2 通り・篩だけ・読み直しの篩つき・読み直せる・相手の候補の和)。切り替え 2 つ 真の中で呼ぶ。"""
    with t5_yen_off():
        with JT.yen_scan_off():
            off0 = len(S.t5_sites(text, refs))
        off1 = len(S.t5_sites(text, refs))
    screen = S.t5_sites_yen(text, refs, False)
    sites = S.t5_sites(text, refs)
    return collections.OrderedDict([
        ("偽", collections.OrderedDict([("H の切り替え 偽", off0), ("H の切り替え 真", off1)])),
        ("篩だけの site", collections.OrderedDict([("計", len(screen))] + list(shape_counter(screen).items()))),
        ("作れる site", collections.OrderedDict([("計", len(sites))] + list(shape_counter(sites).items()))),
        ("読み直せる site", sum(1 for s in screen if head3_readable(s))),
        ("相手の候補の和", sum(len(s["others"]) for s in screen))])


# ======================================================================================================
# 1 本の注入
def h_counts(text, refs, base_claims, base_by_id, seed, key, cap):
    u"""T1_VALUE・T8_REL の作れる site と採った数(H の便と同じ関数。T5 の切り替え 偽のまま)。"""
    with t5_yen_off():
        with NS.t1_sites_only_new():
            chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T1_VALUE"])
        _t8, c8 = NS.t8_candidates_new(text, refs, base_claims, base_by_id, seed, key, cap)
    return collections.OrderedDict([
        ("T1_VALUE", collections.OrderedDict([("作れる site", cat["T1_VALUE"]), ("採った", len(chosen))])),
        ("T8_REL", collections.OrderedDict([("作れる site", c8["作れる site"]), ("採った", c8["採った"])]))])


def inject_text_ty(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""T5 の 1 本の注入(1 回に 1 件・round-trip は止めずに数える)。site は ``S.t5_sites``(切り替え 2 つ 真)。(行, 数え)。"""
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([("注入しない", "文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or PS.VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    counts = collections.OrderedDict([("T5 の site", site_counts(text, refs))])
    counts.update(h_counts(text, refs, base_claims, base_by_id, seed, key, cap))
    sites, rng = t5_all_sites(text, refs, seed, key)
    ok, pop = [], collections.Counter()
    for s in sites:
        st, bc = RM.base_status_rb(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
        if bc is not None:
            ok.append((s, bc))
    counts["作れる site の状態"] = collections.OrderedDict(sorted(pop.items()))
    counts["土台 P30E が GROUNDED の site"] = len(ok)
    counts["cap を基準で絞る前に掛けた数"] = min(cap, len(sites))
    taken = collections.Counter()
    rows = []
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        tok = s["token"]
        inj = IJ.build_t5(s, refs, rng)
        inj["type"] = T5
        inj["id"] = "%s-T5-%02d" % (key, n)
        target = SC.scaled_value(inj["new_value"], tok.unit)
        taken[LINKED if bc["ids"][profiles[0]] is not None else UNLINKED] += 1
        tampered, placements = IJ.apply_edits(text, [inj])
        rt = IJ.revert(tampered, [inj], placements, text) == text
        orig_digits = text[tok.start:tok.end]
        ckey = inj["detail"]["coincident_ref_key"]
        row = collections.OrderedDict([
            ("id", inj["id"]), ("型", T5), ("形", PS.shape_of_token(tok)), ("単位", tok.unit),
            ("基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None),
            ("round-trip", bool(rt)), ("読み直し", bool(JT.reread_j(tampered, tok, inj["new_value"], tok.unit))),
            ("先頭の位が減った", bool(tok.groups is not None and NS.groups_in(inj["replacement"]) < len(tok.groups))),
            ("相手の fact の期", partner_period(ckey)), ("相手と同じ要素か", bool(same_element(inj["detail"]["true_ref_key"], ckey))),
            ("基準の pointer の期", PS.pointer_period(bc.get("pointers")))])
        conds, miss, found = {}, {}, {}
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)
                conds[p], miss[p], found[p] = None, [PI.NO_BASE], None
                continue
            claims = verify(zb, p, tampered)["claims"]
            res, conds[p], miss[p], found[p] = PI.id_map(claims, bc["ids"][p], target, inj["replacement"])
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
        c30 = found[profiles[1]]
        row["注入後の pointer の期"] = PS.pointer_period(c30.get("pointers")) if c30 is not None else "なし"
        row["注入後の pointer が相手の fact と同じか"] = bool(c30 is not None and pointer_is_partner(c30.get("pointers"), ckey))
        row["届いた"] = PS.reached_of(orig_digits, bc.get("span"), c30, inj["replacement"])
        for p in profiles:
            row[F_COND % p] = conds[p]
        for p in profiles:
            row[F_MISS % p] = miss[p]
        rows.append(row)
    counts["採った"] = n
    counts["採った の状態"] = collections.OrderedDict(sorted(taken.items()))
    return rows, counts


def inject_job_ty(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(N, FLAG) or not getattr(S, FLAG2):
        raise Stop("**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_ty(zb, text, refs, seed, name)
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
def t5_types_in_run():
    u"""``RUN.INJECT_TYPES`` を with の中だけ T5 の 1 型にする(``RM.inject_summaries`` が型の並びをここから読むため)。出るときは必ず戻す。"""
    old_t, old_p = RUN.INJECT_TYPES, RUN.PROFILES
    RUN.INJECT_TYPES, RUN.PROFILES = (T5,), INJECT_PROFILES
    try:
        yield
    finally:
        RUN.INJECT_TYPES, RUN.PROFILES = old_t, old_p


def inject_summaries(rows):
    with t5_types_in_run():
        return RM.inject_summaries(rows)


def unlinked_counts(rows):
    return collections.OrderedDict([("全体", sum(1 for r in rows if not r[LINK_KEY])), (T5, sum(1 for r in rows if r["型"] == T5 and not r[LINK_KEY]))])


def breakdown(rows):
    u"""形(既存 / 万だけ / 複合)別の P30E の率。"""
    return collections.OrderedDict((k, RUN.inject_cell([r for r in rows if r["形"] == k], "P30E")) for k in SHAPES)


def partner_period_breakdown(rows):
    u"""相手の fact の期(CurrentYear / Prior1Year / 他)別の P30E の率。"""
    return collections.OrderedDict((k, RUN.inject_cell([r for r in rows if r["相手の fact の期"] == k], "P30E")) for k in PARTNER_PERIODS)


def same_element_breakdown(rows):
    u"""相手と同じ要素か(同じ要素 / 別の要素)別の P30E の率。"""
    return collections.OrderedDict((k, RUN.inject_cell([r for r in rows if r["相手と同じ要素か"] is (k == "同じ要素")], "P30E")) for k in ("同じ要素", "別の要素"))


def period_breakdown(rows):
    return PS.period_breakdown(rows)


def same_pointer_breakdown(rows):
    u"""通した行(P30E)のうち、注入後の pointer が相手の fact と同じ行・違う行。"""
    passed = [r for r in rows if r["P30E"]["結果"] == LABEL_PASS]
    same = sum(1 for r in passed if r["注入後の pointer が相手の fact と同じか"])
    return collections.OrderedDict([("通した行", len(passed)), ("相手の fact と同じ", same), ("違う", len(passed) - same)])


def pass_rate(sel):
    return RUN.inject_cell(sel, "P30E")[LABEL_PASS]["率"]


def y_columns(per, rows):
    u"""Y-2〜Y-9 の欄を ``本ごとの数え`` と ``行`` から数える(記録の ``Y の欄`` と tally の判定が使う)。"""
    sc = NS.sum_counts
    made = collections.OrderedDict((k, sc(per, ("T5 の site", "作れる site", k))) for k in ("計",) + SHAPES)
    y2 = collections.OrderedDict([("計", made["計"]), ("複合", made["複合"]), ("万だけ", made["万だけ"]), ("既存", made["既存"]),
                                  ("読み直せる site", sc(per, ("T5 の site", "読み直せる site"))),
                                  ("篩だけの site", sc(per, ("T5 の site", "篩だけの site", "計"))), ("相手の候補の和", sc(per, ("T5 の site", "相手の候補の和")))])
    y3 = collections.OrderedDict([("採った", sc(per, ("cap を基準で絞る前に掛けた数",))), ("うち土台 P30E が GROUNDED の行", len(rows)),
                                  ("作れる site のうち土台 P30E が GROUNDED の site", sc(per, ("土台 P30E が GROUNDED の site",)))])
    mapped = [r for r in rows if r["P30E"]["対応"]]
    y4 = collections.OrderedDict([("注入の行", len(rows)), ("id で対応が付く行(P30E)", len(mapped)), ("割合", pct(len(mapped), len(rows)))])
    passed = [r for r in rows if r["P30E"]["結果"] == LABEL_PASS]
    stopped = [r for r in mapped if r["P30E"]["結果"] != LABEL_PASS]
    named = [r for r in stopped if r["P30E"]["結果"] == LABEL_NAMED_ORIGINAL]
    y5 = collections.OrderedDict([("通した率(P30E)", pct(len(passed), len(mapped))), ("通した行", len(passed)), ("対応が付く行", len(mapped)),
                                  ("止めた行", len(stopped)), ("うち名指して原本", len(named)), ("割合", pct(len(named), len(stopped)))])
    same = sum(1 for r in passed if r["注入後の pointer が相手の fact と同じか"])
    y6 = collections.OrderedDict([("通した行", len(passed)), ("うち注入後の pointer が相手の fact と同じ", same), ("割合", pct(same, len(passed)))])
    y7 = collections.OrderedDict([("round-trip 不一致", sum(1 for r in rows if not r["round-trip"])), ("読み直し不一致", sum(1 for r in rows if not r["読み直し"])),
                                  ("届かない行(対応が付く行の中)", sum(1 for r in mapped if not r["届いた"]))])
    both = [r for r in rows if r["P29E"]["対応"] and r["P30E"]["対応"]]
    y8 = collections.OrderedDict([("違う行", sum(1 for r in both if r["P29E"]["結果"] != r["P30E"]["結果"])), ("両方に対応が付く行", len(both))])
    cur = [r for r in mapped if r["相手の fact の期"] == "CurrentYear"]
    pri = [r for r in mapped if r["相手の fact の期"] == "Prior1Year"]
    y9 = collections.OrderedDict([("相手の期が CurrentYear の行の通した率", pass_rate(cur)), ("相手の期が Prior1Year の行の通した率", pass_rate(pri)),
                                  ("対応が付く行(CurrentYear)", len(cur)), ("対応が付く行(Prior1Year)", len(pri))])
    ref = collections.OrderedDict([("届いた行", sum(1 for r in rows if r["届いた"])), ("先頭の位が減った行", sum(1 for r in rows if r["先頭の位が減った"])),
                                   ("相手と同じ要素の行", sum(1 for r in rows if r["相手と同じ要素か"])), ("P30E の欠けた条件(ア)", sum(1 for r in rows if PI.COND_A in r[F_MISS % "P30E"])),
                                   ("P30E の欠けた条件(イ)", sum(1 for r in rows if PI.COND_I in r[F_MISS % "P30E"])), ("P30E の欠けた条件(ウ)", sum(1 for r in rows if PI.COND_U in r[F_MISS % "P30E"])),
                                   ("P29E の欠けた条件がある行", sum(1 for r in rows if r[F_MISS % "P29E"]))])
    return collections.OrderedDict([(YCOL["Y-2"], y2), (YCOL["Y-3"], y3), (YCOL["Y-4"], y4), (YCOL["Y-5"], y5), (YCOL["Y-6"], y6), (YCOL["Y-7"], y7),
                                    (YCOL["Y-8"], y8), (YCOL["Y-9"], y9), (u"参考", ref)])


# ======================================================================================================
# Y-10 の試験(measure/tests の結果の欄)
def sha256_rel(rel, root=ROOT):
    return GEN.sha256_file(os.path.join(root, rel))


def run_unittests(rel, mod_name, root=ROOT):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(root, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    stream = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()):                 # test_inject の試験が標準出力に書く行を捨てる
        res = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    return collections.OrderedDict([(u"path", rel), (u"sha256", sha256_rel(rel, root)), (u"試験", res.testsRun), (u"失敗", len(res.failures)), (u"エラー", len(res.errors)), (u"skip", len(res.skipped))])


@contextlib.contextmanager
def _patched(obj, names_values):
    saved = [(n, getattr(obj, n)) for n, _v in names_values]
    try:
        for n, v in names_values:
            setattr(obj, n, v)
        yield
    finally:
        for n, v in saved:
            setattr(obj, n, v)


def _sites_old(text, refs):
    u"""変異用: 規則 T5Y の前の ``t5_sites`` の写し(書かれた単位の値で比べ、相手ごとの読み直しの篩が無い)。"""
    out = []
    for t, r in S.identified_sites(text, refs):
        lo, hi = t.value / S.MAGNITUDE_RATIO, t.value * S.MAGNITUDE_RATIO
        others = [o for o in refs if o["key"] != r["key"] and str(o.get("label")) != str(r.get("label")) and abs(o["value"] - t.value) > S.TOL
                  and o["value"] > 0 and lo <= o["value"] <= hi and S._unit_compatible(t.unit, o.get("unit"))]
        if others:
            out.append({"type": "T5_COINCIDENT", "token": t, "ref": r, "others": others})
    return out


def _build_old(site, other):
    u"""変異用: 規則 T5Y の前の ``build_t5`` の描きの写し(倍率で割らない)。"""
    t = site["token"]
    cand = other["value"]
    return {"new_value": cand, "replacement": N.render_value(cand, t), "span": [t.start, t.end],
            "detail": {"true_ref_key": site["ref"]["key"], "true_ref_label": site["ref"].get("label"), "true_value": t.value, "replacement_value": cand,
                       "coincident_ref_key": other["key"], "coincident_ref_label": other.get("label"), "replacement_absent_from_reference_numbers": False},
            "expected": ""}


def _sites_written(text, refs, readback=True):
    u"""変異用: 篩を書かれた値に戻した ``t5_sites_yen``。"""
    out = []
    for t, r in S.identified_sites(text, refs):
        v = t.value
        lo, hi = v / S.MAGNITUDE_RATIO, v * S.MAGNITUDE_RATIO
        others = [o for o in refs if o["key"] != r["key"] and str(o.get("label")) != str(r.get("label")) and abs(o["value"] - v) > S.TOL
                  and o["value"] > 0 and lo <= o["value"] <= hi and S._unit_compatible(t.unit, o.get("unit"))]
        if readback:
            others = [o for o in others if S.t5_readable(t, o["value"])]
        if others:
            out.append({"type": "T5_COINCIDENT", "token": t, "ref": r, "others": others})
    return out


def _readback_unscaled(t, other_value):
    u"""変異用: 描きを倍率で割らない ``t5_readback``。"""
    rendered = N.render_value(other_value, t)
    toks = N.scan(rendered + (t.unit or ""))
    if len(toks) != 1:
        return rendered, None
    return rendered, S._scaled(toks[0].value, toks[0].unit)


def _build_t5_no_pool(site, refs, rng):
    u"""変異用: 相手の単位の優先を外した ``build_t5``(真のとき)。"""
    others = site["others"]
    other = others[rng.randrange(len(others))]
    return IJ._build_t5_yen(site, other)


@contextlib.contextmanager
def mutation_switch_off():
    u"""切り替えを外す: 真でも偽のときと同じ出力にする(篩と描きを前の写しに差し替える)。"""
    with _patched(S, [("t5_sites_yen", lambda text, refs, readback=True: _sites_old(text, refs))]):
        with _patched(IJ, [("_build_t5_yen", lambda site, other: _build_old(site, other))]):
            yield


@contextlib.contextmanager
def mutation_screen_written():
    with _patched(S, [("t5_sites_yen", _sites_written)]):
        yield


@contextlib.contextmanager
def mutation_no_scale():
    with _patched(S, [("t5_readback", _readback_unscaled)]):
        yield


@contextlib.contextmanager
def mutation_no_readback():
    with _patched(S, [("t5_readable", lambda t, v: True)]):
        yield


@contextlib.contextmanager
def mutation_no_unit_priority():
    orig = IJ.build_t5

    def mutated(site, refs, rng):
        if getattr(S, FLAG2):
            return _build_t5_no_pool(site, refs, rng)
        return orig(site, refs, rng)
    with _patched(IJ, [("build_t5", mutated)]):
        yield


#: 封 §3 の Y-10 が名指す変異の名前 → 入れ方(名前は封の字と一字一句同じ)
MUTATIONS = collections.OrderedDict([
    (u"切り替えを外す", mutation_switch_off), (u"篩を書かれた値に戻す", mutation_screen_written), (u"描きを倍率で割らない", mutation_no_scale),
    (u"読み直しを外す", mutation_no_readback), (u"相手の単位の優先を外す", mutation_no_unit_priority)])


def lib_state():
    u"""変異が戻ったことを見るための、差し替え対象の属性の同一性と切り替えの値。"""
    names = ("t5_sites_yen", "t5_readback", "t5_readable", "t5_sites", "t5_precision")
    return (tuple(id(getattr(S, n)) for n in names), id(IJ.build_t5), id(IJ._build_t5_yen), getattr(S, FLAG2), getattr(N, FLAG))


def seal_mutation_names(seal):
    u"""封 §3 の Y-10 の欄が名指す変異の名前(括弧の中を ・ で分けたもの)。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    m = re.search(r"^\| Y-10 \|.*?変異\(([^)]*)\)で赤", sec, re.M)
    if not m:
        raise Stop(u"**封 §3 の Y-10 から変異の名前を読めない。止める**")
    return [x.strip() for x in m.group(1).split(u"・")]


def y10_tests(root=ROOT, names=None):
    u"""Y-10 の記録: 既存の試験(偽のまま)・足した試験・変異ごとの赤の本数・戻したか。"""
    names = list(names) if names is not None else seal_mutation_names(seal_text(root))
    if getattr(N, FLAG) or getattr(S, FLAG2):
        raise Stop(u"**切り替えが真のまま Y-10 の試験を走らせた。止める**")
    before = lib_state()
    rec = collections.OrderedDict()
    rec[u"既存の試験(偽のまま)"] = run_unittests(TEST_INJECT_REL, "test_inject_for_t5y", root)
    rec[u"足した試験"] = run_unittests(TEST_T5_REL, "test_t5_yen_for_t5y", root)
    muts = []
    for n in names:
        if n not in MUTATIONS:
            raise Stop(u"**封の Y-10 の変異の名前を script が知らない: %s。止める**" % n)
        with MUTATIONS[n]():
            r = run_unittests(TEST_T5_REL, "test_t5_yen_mut_for_t5y", root)
        muts.append(collections.OrderedDict([(u"名前", n), (u"試験", r[u"試験"]), (u"赤", r[u"失敗"] + r[u"エラー"]), (u"戻した", lib_state() == before)]))
    rec[u"変異"] = muts
    rec[u"変異のあと lib が元に戻った"] = lib_state() == before
    return rec


# ======================================================================================================
# 記録の書き方
caches_all = PS.caches_all


def header_ty(root, step, seed_meta, before, after, profiles):
    u"""T9 の第 2 便の頭(PI.header_pi)を使い、封・封の commit・この script の sha256 を替え、T9 の第 2 便の script と記録・仕掛けの指紋を足す。"""
    h = PI.header_pi(root, step, seed_meta, before, after, profiles)
    h["seal"] = SEAL_REL
    h["封の commit"] = SEAL_COMMIT
    h["この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h["T9 の第 2 便の script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_pswap_idmap_2026-11-06.py"))
    h["T9 の第 2 便の記録の sha256"] = GEN.sha256_file(os.path.join(root, PI_RECORD_REL))
    h["仕掛けの指紋"] = collections.OrderedDict((rel, GEN.sha256_file(os.path.join(root, rel))) for rel in DEVICE_RELS)
    return h


def scope_word(only):
    return "全 200 本" if only is None else "**--only(本番の記録ではない)**"


load_books = PI.load_books


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_limits(seal):
    return NS.seal_limits(seal)


def write_json(out, rec, key_value=None):
    text = RUN.dumps_inject(rec)
    with key_check_ty():
        RUN.write_record(out, text, rec, key_value)


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None, run_tests=True):
    if out is None:
        if only is not None:
            raise Stop("**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop("**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if getattr(N, FLAG) or getattr(S, FLAG2):
        raise Stop("**切り替えが真のまま inject を始めた。止める**")
    RM.install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop("**差し替えが届いていない: %s。止める**" % " / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="t5y_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say("注入 %d 本 × 2 profile(P29E・P30E)。切り替え 2 つ 真・T5_COINCIDENT・id で引く対応付け ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with yen_scan_on():
        with t5_yen_on():
            if not getattr(N, FLAG) or not getattr(S, FLAG2) or wiring_problems():
                raise Stop("**切り替えを真にできない・配線が崩れた。止める**")
            results = NF.map_pool(inject_job_ty, jobs_, procs)
    if getattr(N, FLAG) or getattr(S, FLAG2):
        raise Stop("**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    tests = y10_tests(root) if run_tests else None
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop("**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_ty(root, "T5Y(注入の仕掛けの T5 を円族の数に作れるようにする)― 切り替え 2 つ 真・T5_COINCIDENT の注入(P29E・P30E。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec["範囲"] = scope_word(only)
    rec["切り替え"] = collections.OrderedDict([
        ("名前", FLAG), ("inject の中の値", True), ("出たあとの値", bool(getattr(N, FLAG))),
        ("T5 の切り替えの名前", FLAG2), ("T5 の切り替え inject の中の値", True), ("T5 の切り替え 出たあとの値", bool(getattr(S, FLAG2))), ("配線の問題", wiring_problems())])
    rec["種"] = {"file": RUN.SEED_REL_STR, "種の確認": seed_meta}
    rec["型"] = collections.OrderedDict([
        (T5, "S.t5_sites(切り替え 2 つ 真)の site。篩と値の違いを円に直して比べ、相手ごとに倍率で割って token の形で描き、読み直した円の値が相手の値と書かれた桁の半分以内・描いた字が元の字と違い・読み直した値が元の値から桁の半分より離れる相手だけを残す。"
             "token の start の順に並べてから <seed>|<本の名前>|T5_COINCIDENT で並べ替え、土台 P30E GROUNDED の site を先頭から cap 件。差し替えは IJ.build_t5(相手の単位の優先 → 同じ Random の続きで 1 回)"),
        ("上限", "1 本あたり %d" % RUN.INJECT_CAP),
        ("土台", BASE_WORD),
        ("土台の結び方", "P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        ("対応付け", "注入後の文の claim のうち id が基準の claim の id の claim c が、(ア)在る (イ)値が注入した値(円に直して TUNE.same_number) (ウ)span に差し替えの字が在る、の 3 つ全部のときだけ対応が付く。欠けた条件は行に持つ"),
        ("届いた", "元の字が基準の claim の span に在る かつ id で引いた claim(P30E)の span に差し替えの字が在る"),
        ("相手の fact の期", "coincident_ref_key の context の先頭: CurrentYear / Prior1Year / 他"),
        ("相手と同じ要素か", "相手の key と本当の参照の key の要素名(@ の前)が同じか。要素名は持たず真偽だけ"),
        ("pointer の期", "基準の claim と id で引いた claim(P30E)の pointers の先頭の context の先頭: CurrentYear / Prior1Year / 他 / なし。要素名は持たない"),
        ("注入後の pointer が相手の fact と同じか", "id で引いた claim(P30E)の pointers の先頭(名前空間の接頭辞を除いた <要素>@<context>)が相手の key か(真偽だけ)"),
        ("集計の2本", "集計 = 全部の site での P29E・P30E の率。" + COMPARE_KEY + " = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率"),
        ("inject の docID の引数", "本の名前(<docID>_<形>_<model>)")])
    rec["本ごとの数え"] = per
    rec["注入の行の数"] = len(rows)
    rec["集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[BREAKDOWN_KEY] = breakdown(rows)
    rec[PARTNER_PERIOD_KEY] = partner_period_breakdown(rows)
    rec[SAME_ELEMENT_KEY] = same_element_breakdown(rows)
    rec[PERIOD_KEY] = period_breakdown(rows)
    rec[SAME_POINTER_KEY] = same_pointer_breakdown(rows)
    rec["P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[Y_KEY] = y_columns(per, rows)
    if tests is not None:
        rec["試験"] = tests
    rec["限界"] = seal_limits(seal_text(root)) + list(EXTRA_LIMITS)
    rec["行"] = rows
    write_json(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の Y-1〜Y-10・§4 の K-1〜K-4)を読み、記録から判定する
def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {Y-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (Y-\d+) \| (.*) \|$", line)
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
    m = re.match(r"^(\d+)・一致$", P["Y-1"][1].strip())
    b["Y-1"] = int(m.group(1))
    m = re.match(r"^%s / %s / %s / %s、読み直せる %s$" % ((RANGE,) * 5), P["Y-2"][1].strip())
    b["Y-2"] = collections.OrderedDict([("計", _rng(m, 1)), ("複合", _rng(m, 3)), ("万だけ", _rng(m, 5)), ("既存", _rng(m, 7)), ("読み直せる site", _rng(m, 9))])
    m = re.match(r"^%s / %s$" % (RANGE, RANGE), P["Y-3"][1].strip())
    b["Y-3"] = collections.OrderedDict([("採った", _rng(m, 1)), ("うち土台 P30E が GROUNDED の行", _rng(m, 3))])
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["Y-4"][1].strip())
    b["Y-4"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    m = re.match(r"^%s%%、%s%%$" % (RANGE, RANGE), P["Y-5"][1].strip())
    b["Y-5"] = collections.OrderedDict([("通した率(P30E)", _rng(m, 1)), ("割合", _rng(m, 3))])
    m = re.match(r"^(%s)〜(%s)%%$" % (NUM, NUM), P["Y-6"][1].strip())
    b["Y-6"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    m = re.match(r"^(\d+) / (\d+) / (\d+)$", P["Y-7"][1].strip())
    b["Y-7"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2))), ("届かない行(対応が付く行の中)", int(m.group(3)))])
    m = re.match(r"^(\d+)〜(\d+)$", P["Y-8"][1].strip())
    b["Y-8"] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^両方 (%s)〜(%s)%%$" % (NUM, NUM), P["Y-9"][1].strip())
    b["Y-9"] = (NF.num(m.group(1)), NF.num(m.group(2)))
    m = re.match(r"^失敗 (\d+)・赤 (\d+) / (\d+)$", P["Y-10"][1].strip())
    b["Y-10"] = collections.OrderedDict([("失敗", int(m.group(1))), ("赤", int(m.group(2))), ("変異", int(m.group(3)))])
    b["K-1"] = re.search(r"Y-1 が(一致)", K["K-1"]).group(1)
    m = re.search(r"Y-7 の round-trip 不一致 (\d+)・読み直し不一致 (\d+)", K["K-2"])
    b["K-2"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2)))])
    b["K-3"] = NF.num(re.search(r"注入の行 ≥ (%s)" % NUM, K["K-3"]).group(1))
    m = re.search(r"Y-10 が 失敗 (\d+)・赤 (\d+) / (\d+)", K["K-4"])
    b["K-4"] = collections.OrderedDict([("失敗", int(m.group(1))), ("赤", int(m.group(2))), ("変異", int(m.group(3)))])
    return b


def y1_value(per, j_rec, h_rec, rec=None):
    u"""Y-1 の値: 偽の site の数(2 通り)を J の記録の 偽・真 と、T1_VALUE・T8_REL の作れる site を H の記録と本ごとに照らす。lib の指紋は H の記録と照らす。"""
    jper, hper = j_rec["本ごとの数え"], h_rec["本ごとの数え"]
    off0 = off1 = j0 = j1 = 0
    bad_j = bad_t1 = bad_t8 = 0
    for name, c in per.items():
        if "T5 の site" not in c:
            continue
        o = c["T5 の site"]["偽"]
        off0 += o["H の切り替え 偽"]
        off1 += o["H の切り替え 真"]
        jc = (jper.get(name) or {}).get("T5_COINCIDENT") or {}
        j0 += jc.get("偽", 0)
        j1 += jc.get("真", 0)
        if (o["H の切り替え 偽"], o["H の切り替え 真"]) != (jc.get("偽"), jc.get("真")):
            bad_j += 1
        hc = hper.get(name) or {}
        if c["T1_VALUE"]["作れる site"] != (hc.get("T1_VALUE") or {}).get("作れる site"):
            bad_t1 += 1
        if c["T8_REL"]["作れる site"] != (hc.get("T8_REL") or {}).get("作れる site"):
            bad_t8 += 1
    lib = None
    if rec is not None:
        lib = rec.get("lib の指紋") is not None and norm(rec.get("lib の指紋")) == norm(h_rec.get("lib の指紋"))
    return collections.OrderedDict([
        ("T5 の site(H の切り替え 偽)", off0), ("J の記録の 偽", j0), ("T5 の site(H の切り替え 真)", off1), ("J の記録の 真", j1),
        ("J の記録と違う本", bad_j), ("T1_VALUE の作れる site が H の記録と違う本", bad_t1), ("T8_REL の作れる site が H の記録と違う本", bad_t8),
        ("lib の指紋が H の記録と一致", lib), ("本", sum(1 for c in per.values() if "T5 の site" in c))])


def build_Y(R_, seal):
    u"""{Y, K, 採用, 欄}。R_ = {"inject", "j", "h"}(記録の JSON)。欄は inject の記録の 本ごとの数え と 行 から数え直す(記録の ``Y の欄`` は使わない)。"""
    inj = R_["inject"]
    return judge_from(y1_value(inj["本ごとの数え"], R_["j"], R_["h"], inj), y_columns(inj["本ごとの数え"], inj["行"]), y10_value(inj.get("試験")), seal)


def y10_value(tests):
    u"""Y-10 の値: 失敗 = 既存の試験と足した試験の失敗・エラーの和、赤 = 足した試験が赤になった変異の数、変異 = 変異の数。試験の欄が無ければ None。"""
    if not tests:
        return None
    muts = tests.get(u"変異") or []
    fails = sum(tests[k][u"失敗"] + tests[k][u"エラー"] for k in (u"既存の試験(偽のまま)", u"足した試験"))
    return collections.OrderedDict([("失敗", fails), ("赤", sum(1 for m in muts if m[u"赤"] >= 1)), ("変異", len(muts)),
                                    ("戻した", bool(tests.get(u"変異のあと lib が元に戻った")))])


def judge_from(y1, cols, y10, seal):
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    Y = collections.OrderedDict()

    def put(k, ok, val):
        Y[k] = {"判定": HIT if ok else MISS, "値": val}
    put("Y-1", y1["T5 の site(H の切り替え 偽)"] == y1["J の記録の 偽"] and y1["T5 の site(H の切り替え 真)"] == y1["J の記録の 真"] == B["Y-1"]
        and y1["J の記録と違う本"] == 0 and y1["T1_VALUE の作れる site が H の記録と違う本"] == 0 and y1["T8_REL の作れる site が H の記録と違う本"] == 0
        and y1["lib の指紋が H の記録と一致"] is True and y1["本"] > 0, y1)
    c2 = cols[YCOL["Y-2"]]
    put("Y-2", all(within(c2[k], B["Y-2"][k]) for k in B["Y-2"]), c2)
    c3 = cols[YCOL["Y-3"]]
    put("Y-3", all(within(c3[k], B["Y-3"][k]) for k in B["Y-3"]), c3)
    c4 = cols[YCOL["Y-4"]]
    put("Y-4", within(c4["割合"], B["Y-4"]), c4)
    c5 = cols[YCOL["Y-5"]]
    put("Y-5", all(within(c5[k], B["Y-5"][k]) for k in B["Y-5"]), c5)
    c6 = cols[YCOL["Y-6"]]
    put("Y-6", within(c6["割合"], B["Y-6"]), c6)
    c7 = cols[YCOL["Y-7"]]
    put("Y-7", all(c7[k] == B["Y-7"][k] for k in B["Y-7"]), c7)
    c8 = cols[YCOL["Y-8"]]
    put("Y-8", within(c8["違う行"], B["Y-8"]), c8)
    c9 = cols[YCOL["Y-9"]]
    put("Y-9", within(c9["相手の期が CurrentYear の行の通した率"], B["Y-9"]) and within(c9["相手の期が Prior1Year の行の通した率"], B["Y-9"]), c9)
    put("Y-10", y10 is not None and y10["失敗"] == B["Y-10"]["失敗"] and y10["赤"] == B["Y-10"]["赤"] and y10["変異"] == B["Y-10"]["変異"] and y10["戻した"] is True,
        y10 if y10 is not None else "なし")
    K = collections.OrderedDict()
    K["K-1"] = {"判定": Y["Y-1"]["判定"], "値": collections.OrderedDict([("Y-1", Y["Y-1"]["判定"])])}
    k2 = all(c7[k] == B["K-2"][k] for k in B["K-2"])
    K["K-2"] = {"判定": HIT if k2 else MISS, "値": collections.OrderedDict([("round-trip 不一致", c7["round-trip 不一致"]), ("読み直し不一致", c7["読み直し不一致"])])}
    K["K-3"] = {"判定": HIT if c4["注入の行"] >= B["K-3"] else MISS, "値": collections.OrderedDict([("注入の行", c4["注入の行"])])}
    k4 = y10 is not None and y10["失敗"] == B["K-4"]["失敗"] and y10["赤"] == B["K-4"]["赤"] and y10["変異"] == B["K-4"]["変異"] and y10["戻した"] is True
    K["K-4"] = {"判定": HIT if k4 else MISS, "値": y10 if y10 is not None else "なし"}
    adopt = all(K[k]["判定"] == HIT for k in K)
    return collections.OrderedDict([("Y", Y), ("K", K), ("採用", adopt), ("欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = ["| # | 欄 | 予測 | 測った値 | 判定 |", "|---|---|---|---|---|"]
    for k, v in J["Y"].items():
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
    return collections.OrderedDict([("inject", GEN.jload(os.path.join(root, INJECT_REL))), ("j", GEN.jload(os.path.join(root, J_RECORD_REL))), ("h", GEN.jload(os.path.join(root, H_RECORD_REL)))])


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_Y(load_records(root), seal)
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
