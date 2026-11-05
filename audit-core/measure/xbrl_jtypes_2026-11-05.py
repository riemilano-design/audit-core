# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INJECT_TYPES_SEAL_2026-11-05.md §1・§5 ― J(AI の文 200 本に注入の型を広げる: T2_UNIT・T6_PRIOR・T7_ROUND)の測定と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_jtypes_2026-11-05.py inject [--procs N] [--only <docID>[,<docID>...]] [--out PATH]   # 切り替え 真 で T2・T6・T7 を注入(P29E・P30E)→ fixtures/xbrl/jtypes/inject_2026-11-05.json
    python3 measure/xbrl_jtypes_2026-11-05.py tally  [--root DIR]                                              # 記録から J-1〜J-10 と K-1〜K-4 の表を出す(file は書かない)

H の便の script ``xbrl_nscan_2026-11-05.py``(NS)は **1 byte も変えず**、importlib で読み込んで使う(RM・NF・RUN・GEN・TUNE・IJ・N・S・SC は NS の持つ同じ instance)。
``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- T2: ``S.t2_sites`` を with の中だけ「``groups`` が 2 つ以上の token を除く」版に差し替えて ``IJ.select(types=["T2_UNIT"])`` を呼ぶ(cap は採用に掛ける = 基準で絞る前)。
  差し替えで site にしなかった複合の数は本ごとの数えに持つ。注入後の claim は ``TUNE.claim_for_p27(claims, inj, 後の単位)``。読み直しは同じ start・後の単位・同じ値。
- T6: ``IJ.t6_sites`` を ``S.identified_sites`` を「複合を除く」版に差し替えた with の中で呼ぶ(既存・万だけ)+ 複合の写し(描いた字 + 単位を ``N.scan`` して値に戻し、前期の値と一致を見る)。
  2 つを token の start の順に並べてから ``random.Random("<seed>|<本の名前>|T6_PRIOR")`` で並べ替え、土台が P30E GROUNDED の site だけを先頭から cap 件。
- T7: ``IJ.t7_sites(text, refs, rng)`` を ``S.data_bearing_sites`` を「複合を除く」版に差し替えた with の中で呼ぶ + 複合の写し(符号は ``random.Random("<seed>|<本の名前>|T7_ROUND|複合")`` で [1, -1] を並べ替えて先に選び、作れなければ逆側)。
  仕掛けの乱数 ``random.Random("<seed>|<本の名前>|T7_ROUND")`` は ``IJ.select`` の erng と同じく t7_sites に渡したあと同じ乱数で並べ替えにも使う。複合の写しの乱数は仕掛けの乱数と混ぜない。
- J-3 の「採った」: 封 §1 の 2・3 は「土台 GROUNDED の site を先頭から cap 件」、J-3 は「採った / うち土台 P30E が GROUNDED の行」(採った ⊇ うち)。T6・T7 は後者に合わせ、
  「採った」= **cap だけを基準で絞る前に掛けた数**(= 型ごと 1 本 min(cap, 作れる site))、「うち土台 P30E が GROUNDED の行」= 実際に注入した行(土台 GROUNDED の site を先頭から cap 件)とした。
  T2 は IJ.select の cap が採用に掛かる(基準で絞る前)ので「採った」はその数。どちらも本ごとの数えに持つ。
- 「届いた」= 元の字(``text[t.start:t.end]``)が基準の claim の span に在る かつ 注入後の claim(P30E。対応が付いたとき)の span に差し替えの字が在る。
  T2 は差し替えの字が単位なので、注入後の文の ``t.start`` から差し替えの終わりまで(元の数の字 + 後の単位。区切りの空白は元のまま)が注入後の claim の span に在るか、で見る。
- J-4 の率の分母は H と同じ ``RUN.inject_cell``(P30E の claim に対応が付いた行)。J-6 の T7 は分母 = 対応が付く − 通した。
- 記録は文・span・value・会社名を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。

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


NS = load_module("xbrl_nscan_2026-11-05.py", "nscan_for_jtypes")
RM, NF, RUN, GEN, TUNE, IJ = NS.RM, NS.NF, NS.RUN, NS.GEN, NS.TUNE, NS.IJ
N, S, SC = NS.N, NS.S, NS.SC
Stop = GEN.Stop

from adapters.xbrl import verify_document as VD      # noqa: E402

FLAG = NS.FLAG
SEAL_REL = "docs/XBRL_INJECT_TYPES_SEAL_2026-11-05.md"
SEAL_COMMIT = "edad5cd"
DOC_REL = "docs/XBRL_INJECT_TYPES_RESULT_2026-11-05.md"
REC_DIR_REL = "fixtures/xbrl/jtypes"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-05.json"
REC_REL = collections.OrderedDict([("inject", INJECT_REL)])
SCRIPT_REL = "measure/xbrl_jtypes_2026-11-05.py"
NS_SCRIPT_REL = "measure/xbrl_nscan_2026-11-05.py"
H_RECORD_REL = NS.INJECT_REL                       # fixtures/xbrl/nscan/inject_2026-11-05.json(読むだけ)
RB_RECORD_REL = NS.RB_INJECT_REL                   # fixtures/xbrl/rmix/inject_2026-11-04.json(読むだけ)
LIB_RELS = NS.LIB_RELS
UNTOUCHED_FOR_J1 = ("measure/inject.py", "measure/lib/sites.py")
SOURCES = NS.SOURCES
INJECT_PROFILES = NS.INJECT_PROFILES               # ("P29E", "P30E")
J_TYPES = ("T2_UNIT", "T6_PRIOR", "T7_ROUND")
TYPE_SHORT = collections.OrderedDict([("T2_UNIT", "T2"), ("T6_PRIOR", "T6"), ("T7_ROUND", "T7")])
SHAPES = ("既存", "万だけ", "複合")
LINK_KEY, COMPARE_KEY = RM.LINK_KEY, RM.COMPARE_KEY
LINKED, UNLINKED = RM.LINKED, RM.UNLINKED
HIT, MISS = RM.HIT, RM.MISS
STATUS_NO_BASE, STATUS_NOT_G = NS.STATUS_NO_BASE, NS.STATUS_NOT_G
BASE_WORD = RM.BASE_WORD
SITE_WORD = "T2 は複合を除く・T6 と T7 は仕掛けの経路(既存・万だけ)+ 複合の写し"
BREAKDOWN_KEY = "型 × 形の内訳(P30E)"
J_KEY = "J の欄"
#: 乱数の種の字(封 §1 の 2・3 の字と同じ)。仕掛けの乱数と複合の写しの乱数は混ぜない
SEED_T6 = "%s|%s|T6_PRIOR"
SEED_T7 = "%s|%s|T7_ROUND"
SEED_T7_COMPOUND = "%s|%s|T7_ROUND|複合"
#: 封 §6 の字に足す、この script の限界(数は変えない)
EXTRA_LIMITS = (
    "round-trip 不一致は止めずに数える(K-2 の欄)。封 §3 の J-9 は 0 を予測し、判定は K-2 に出る",
    "T6・T7 の J-3 の「採った」は cap を基準で絞る前に掛けた数、「うち土台 P30E が GROUNDED の行」が実際に注入した行(封 §1 の 2・3 と J-3 の読みの間で後者に合わせた)",
    "T2 の「届いた」は元の数の字 + 後の単位が注入後の claim の span に在るか(区切りの空白は元のまま)で見る",
    "J-4 の率の分母は H と同じく P30E の claim に対応が付いた行(封 §3 の J-4 の『分母 = P30E が GROUNDED の site』と同じ集まり)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def norm(x):
    return json.loads(json.dumps(x))


def shape_of_token(t):
    u"""形: 既存(groups が None。空白入りの「5 万円」も)/ 万だけ(groups が 1 つ)/ 複合(groups が 2 つ以上)。"""
    if t.groups is None:
        return "既存"
    return "万だけ" if len(t.groups) == 1 else "複合"


def is_compound(t):
    return t.groups is not None and len(t.groups) >= 2


def kind4(t):
    u"""token の種類 4 つ(groups と unit 万円 で): 既存・万円(空白入り)・万だけ・複合。"""
    if t.groups is None:
        return "万円(空白入り)" if t.unit == "万円" else "既存"
    return "万だけ" if len(t.groups) == 1 else "複合"


KIND4 = ("既存", "万円(空白入り)", "万だけ", "複合")


# ======================================================================================================
# 切り替え・差し替え
yen_scan_on = NS.yen_scan_on


@contextlib.contextmanager
def yen_scan_off():
    u"""切り替えを with の中だけ偽にする(T5 の偽の数を同じ process で数えるため)。出るときは必ず元の値に戻す。"""
    old = getattr(N, FLAG)
    setattr(N, FLAG, False)
    try:
        yield
    finally:
        setattr(N, FLAG, old)


def _token_of(name, item):
    return item[0] if name in ("identified_sites", "data_bearing_sites") else item["token"]


@contextlib.contextmanager
def without_compound(name):
    u"""``S.<name>``(t2_sites・identified_sites・data_bearing_sites)を『groups が 2 つ以上の token を除く』版に with の中だけ差し替える(出るときは必ず戻す)。"""
    orig = getattr(S, name)

    def fn(text, refs):
        return [x for x in orig(text, refs) if not is_compound(_token_of(name, x))]
    setattr(S, name, fn)
    try:
        yield orig
    finally:
        setattr(S, name, orig)


# ======================================================================================================
# 配線
def wiring_problems():
    return NS.wiring_problems()


def inject_wiring_problems():
    return NS.inject_wiring_problems()


def key_leaks_j(text, key_value=None, long_alnum=True):
    u"""この便の封の path(32 字を超えて英数字・_・- が続く)の字を除いて、H の便の検査に渡す。"""
    return NS.key_leaks_h(text.replace(SEAL_REL, u""), key_value, long_alnum)


@contextlib.contextmanager
def key_check_j():
    u"""``GEN.key_leaks`` を with の中だけこの便の封の path を除く版にする(NS の配線の検査は with の外で走らせる)。"""
    old = GEN.key_leaks
    GEN.key_leaks = key_leaks_j
    try:
        yield
    finally:
        GEN.key_leaks = old


def assert_clean_j(rec, key_value=None):
    with key_check_j():
        RUN.assert_clean(rec, key_value)


# ======================================================================================================
# 複合の写し(T6・T7。仕掛けの経路は複合で落ちる・先頭の位が落ちた形だけが site になるため)
def rendered_back(rendered, unit):
    u"""描いた字 + 単位を ``N.scan`` して、1 つの token が全体を覆うときだけ値(円。単位の倍率を掛けたもの)を返す。違えば None。"""
    s = rendered + unit
    toks = N.scan(s)
    if len(toks) != 1:
        return None
    t = toks[0]
    if t.start != 0 or t.unit_end != len(s) or t.unit != unit:
        return None
    return t.value * (SC.scale_of(unit) or 1)


def t6_compound_sites(text, refs):
    u"""``IJ.t6_sites`` と同じ条件を複合 token に当てる写し。site の形は ``IJ.t6_sites`` と同じ。"""
    by_key = {}
    for r in refs:
        by_key.setdefault(r["key"], []).append(r)
    out = []
    for t, ref in S.identified_sites(text, refs):
        if not is_compound(t):
            continue
        elem, _, ctx = ref["key"].partition("@")
        if not ctx.startswith("CurrentYear"):
            continue
        pk = "%s@%s" % (elem, "Prior1Year" + ctx[len("CurrentYear"):])
        cands = by_key.get(pk, [])
        if len(cands) != 1:
            continue
        prior = cands[0]
        if prior.get("unit") != ref.get("unit"):
            continue
        if not (prior["value"] > 0 and ref["value"] > 0 and abs(prior["value"] - ref["value"]) > IJ.TOL):
            continue
        factor = SC.scale_of(t.unit) or 1
        cand = prior["value"] / float(factor)
        rendered = N.render_value(cand, t)
        back = rendered_back(rendered, t.unit)
        if back is None or abs(back - prior["value"]) > max(IJ.TOL, abs(prior["value"]) * 1e-9) or rendered == t.text:
            continue
        out.append({"type": "T6_PRIOR", "token": t, "ref": ref, "prior": prior, "prior_key": pk,
                    "element": elem, "new_value": cand, "rendered": rendered})
    return out


def t7_compound_sites(text, refs, rng):
    u"""複合 token の T7: 符号を ``rng`` で [1, -1] を並べ替えて先に選び、作れなければ逆側。値 ± 1(like の単位の最小の位)を ``N.render_value`` で描き、位の数が減らない・元の字と違う・refs のどの値とも一致しない、を要る。"""
    vindex = S._value_index(refs)
    out = []
    for t, cands in S.data_bearing_sites(text, refs):
        if not is_compound(t) or t.value == 0:
            continue
        order = [1, -1]
        rng.shuffle(order)
        for delta in order:
            new = t.value + delta
            if new <= 0:
                continue
            rendered = N.render_value(new, t)
            if NS.groups_in(rendered) != len(t.groups) or rendered == t.text:
                continue
            if S._matches(new, t.unit, vindex):
                continue
            out.append({"type": "T7_ROUND", "token": t, "candidates": cands, "delta": delta,
                        "new_value": new, "rendered": rendered, "new_value_present_in_refs": False})
            break
    return out


def t6_all_sites(text, refs, seed, key):
    u"""T6 の site 全部(並べ替え済み)。仕掛けの経路(複合を除く)+ 複合の写しを token の start の順に並べてから ``<seed>|<key>|T6_PRIOR`` で並べ替える。"""
    with without_compound("identified_sites"):
        sites = IJ.t6_sites(text, refs)
    sites = sites + t6_compound_sites(text, refs)
    sites.sort(key=lambda s: s["token"].start)
    random.Random(SEED_T6 % (seed, key)).shuffle(sites)
    return sites


def t7_all_sites(text, refs, seed, key):
    u"""T7 の site 全部(並べ替え済み)。仕掛けの経路(複合を除く。乱数は ``<seed>|<key>|T7_ROUND``)+ 複合の写し(乱数は ``...|T7_ROUND|複合``)。並べ替えは仕掛けの乱数の続き。"""
    erng = random.Random(SEED_T7 % (seed, key))
    with without_compound("data_bearing_sites"):
        sites = IJ.t7_sites(text, refs, erng)
    sites = sites + t7_compound_sites(text, refs, random.Random(SEED_T7_COMPOUND % (seed, key)))
    sites.sort(key=lambda s: s["token"].start)
    erng.shuffle(sites)
    return sites


# ======================================================================================================
# 数え
def token_kinds(text):
    u"""本ごとの token の種類別の数(全部と is_quantity 真)。"""
    toks = N.scan(text)
    a = collections.Counter(kind4(t) for t in toks)
    q = collections.Counter(kind4(t) for t in toks if N.is_quantity(text, t))
    return collections.OrderedDict([
        ("全部", collections.OrderedDict((k, a.get(k, 0)) for k in KIND4)),
        ("うち is_quantity 真", collections.OrderedDict((k, q.get(k, 0)) for k in KIND4))])


def unit_class(u):
    return "None" if u is None else ("円" if u == "円" else "その他")


def t5_counts(text, refs):
    u"""T5 の site(注入しない)。偽 = 切り替え 偽 の site の数、真 = 切り替え 真 の site の数と、真の相手(``others``)の参照の単位の内訳。"""
    with yen_scan_off():
        off = len(S.t5_sites(text, refs))
    sites = S.t5_sites(text, refs)
    only_none_yen = sum(1 for s in sites if all(unit_class(o.get("unit")) != "その他" for o in s["others"]))
    entries = collections.Counter(unit_class(o.get("unit")) for s in sites for o in s["others"])
    return collections.OrderedDict([
        ("偽", off), ("真", len(sites)),
        ("真の相手の単位", collections.OrderedDict([("全部 None か 円", only_none_yen), ("その他を含む", len(sites) - only_none_yen)])),
        ("others の単位の内訳", collections.OrderedDict((k, entries.get(k, 0)) for k in ("None", "円", "その他")))])


def reread_j(tampered, tok, new_value, unit):
    u"""注入後の文を ``N.scan`` して、同じ start・指定の単位・意図した値の token が在る(groups の有無は問わない)。"""
    return any(t2.start == tok.start and t2.unit == unit and abs(t2.value - new_value) < 1e-9 for t2 in N.scan(tampered))


def shape_counter(sites):
    c = collections.Counter(shape_of_token(s["token"]) for s in sites)
    return collections.OrderedDict((k, c.get(k, 0)) for k in SHAPES)


def status_counter(sites, base_claims, base_by_id, text):
    c = collections.Counter(RM.base_status_rb(base_claims, base_by_id, s["token"], text)[0] for s in sites)
    return collections.OrderedDict(sorted(c.items()))


# ======================================================================================================
# 1 本の注入
def inject_text_j(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""T2・T6・T7 の 1 本の注入(1 回に 1 件・round-trip は止めずに数える)。site は『T2: 複合を除く』『T6・T7: 仕掛けの経路 + 複合の写し』。(行, 数え)。"""
    kinds = token_kinds(text)
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([("token の数え", kinds), ("注入しない", "文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    toks = dict(((t.start, t.end), t) for t in N.scan(text))
    unit_toks = dict(((N.unit_start_of(t), t.unit_end), t) for t in N.scan(text) if t.unit is not None)
    counts = collections.OrderedDict([("token の数え", kinds), ("T5_COINCIDENT", t5_counts(text, refs))])
    work = []                                                       # (inj, tok, bc, 後の単位, 符号)

    # ---- T2
    skipped = sum(1 for s in S.t2_sites(text, refs) if is_compound(s["token"]))
    with without_compound("t2_sites"):
        chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T2_UNIT"])
        sites2 = S.t2_sites(text, refs)
    c2 = collections.OrderedDict([
        ("作れる site", collections.OrderedDict((k, v) for k, v in shape_counter(sites2).items() if k != "複合")),
        ("site にしなかった複合", skipped), ("作れる site の状態", status_counter(sites2, base_claims, base_by_id, text))])
    taken = collections.Counter()
    for inj in chosen:
        tok = unit_toks[tuple(inj["span"])]
        st, bc = RM.base_status_rb(base_claims, base_by_id, tok, text)
        taken[st] += 1
        work.append((inj, tok, bc, inj["detail"]["unit_after"], None))
    c2["採った"] = len(chosen)
    c2["cap を基準で絞る前に掛けた数"] = len(chosen)
    c2["採った の状態"] = collections.OrderedDict(sorted(taken.items()))
    c2["select の作れる site"] = cat["T2_UNIT"]
    counts["T2_UNIT"] = c2

    # ---- T6・T7(土台 GROUNDED の site だけを先頭から cap 件)
    for typ, sites_fn, builder in (("T6_PRIOR", t6_all_sites, IJ.build_t6), ("T7_ROUND", t7_all_sites, IJ.build_t7)):
        sites = sites_fn(text, refs, seed, key)
        ok, pop = [], collections.Counter()
        for s in sites:
            st, bc = RM.base_status_rb(base_claims, base_by_id, s["token"], text)
            pop[st] += 1
            if bc is not None:
                ok.append((s, bc))
        c = collections.OrderedDict([
            ("作れる site", shape_counter(sites)), ("作れる site の状態", collections.OrderedDict(sorted(pop.items()))),
            ("土台 P30E が GROUNDED の site", len(ok)), ("cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
        taken = collections.Counter()
        n = 0
        for s, bc in ok[:cap]:
            n += 1
            inj = builder(s, refs, None)
            inj["type"] = typ
            inj["id"] = "%s-%s-%02d" % (key, typ.split("_")[0], n)
            taken[LINKED if bc["ids"][profiles[0]] is not None else UNLINKED] += 1
            work.append((inj, s["token"], bc, None, s.get("delta")))
        c["採った"] = n
        c["採った の状態"] = collections.OrderedDict(sorted(taken.items()))
        counts[typ] = c

    rows = []
    for inj, tok, bc, unit_after, sign in work:
        tampered, placements = IJ.apply_edits(text, [inj])
        rt = IJ.revert(tampered, [inj], placements, text) == text
        if bc is None:
            continue
        unit_q = unit_after if inj["type"] == "T2_UNIT" else tok.unit
        value_q = tok.value if inj["type"] == "T2_UNIT" else inj["new_value"]
        want_tail = tampered[tok.start:placements[inj["id"]][1]] if inj["type"] == "T2_UNIT" else inj["replacement"]
        orig_in_base = text[tok.start:tok.end] in (bc.get("span") or "")
        row = collections.OrderedDict([
            ("id", inj["id"]), ("型", inj["type"]), ("形", shape_of_token(tok)), ("単位", tok.unit), ("単位の後", unit_after), ("符号", sign),
            ("基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None),
            ("round-trip", bool(rt)), ("読み直し", bool(reread_j(tampered, tok, value_q, unit_q))),
            ("先頭の位が減った", bool(inj["type"] != "T2_UNIT" and tok.groups is not None and NS.groups_in(inj["replacement"]) < len(tok.groups)))])
        reached = False
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)
                continue
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, unit_q)
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
            if p == profiles[1]:
                reached = bool(res is not None and orig_in_base and want_tail in (res.get("span") or ""))
        row["届いた"] = reached
        rows.append(row)
    return rows, counts


def inject_job_j(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(N, FLAG):
        raise Stop("**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_j(zb, text, refs, seed, name)
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
def j_types_in_run():
    u"""``RUN.INJECT_TYPES`` を with の中だけ J の 3 型にする(``RM.inject_summaries`` が型の並びをここから読むため)。出るときは必ず戻す。"""
    old_t, old_p = RUN.INJECT_TYPES, RUN.PROFILES
    RUN.INJECT_TYPES, RUN.PROFILES = J_TYPES, INJECT_PROFILES
    try:
        yield
    finally:
        RUN.INJECT_TYPES, RUN.PROFILES = old_t, old_p


def inject_summaries(rows):
    with j_types_in_run():
        return RM.inject_summaries(rows)


def unlinked_counts(rows):
    out = collections.OrderedDict([("全体", sum(1 for r in rows if not r[LINK_KEY]))])
    for t in J_TYPES:
        out[t] = sum(1 for r in rows if r["型"] == t and not r[LINK_KEY])
    return out


def breakdown(rows):
    u"""型 × 形(既存 / 万だけ / 複合)の P30E の率。"""
    out = collections.OrderedDict()
    for t in J_TYPES:
        sel = [r for r in rows if r["型"] == t]
        out[t] = collections.OrderedDict((k, RUN.inject_cell([r for r in sel if r["形"] == k], "P30E")) for k in SHAPES)
    return out


def rate(sel, p, label):
    return RUN.inject_cell(sel, p)[label]["率"]


def j_columns(per, rows):
    u"""J-2〜J-10 の欄を ``本ごとの数え`` と ``行`` から数える(記録の ``J の欄`` と tally の判定が使う)。"""
    sc = NS.sum_counts
    by = dict((t, [r for r in rows if r["型"] == t]) for t in J_TYPES)
    j2 = collections.OrderedDict()
    for t in J_TYPES:
        o = collections.OrderedDict((k, sc(per, (t, "作れる site", k))) for k in SHAPES if not (t == "T2_UNIT" and k == "複合"))
        if t == "T2_UNIT":
            o["site にしない複合"] = sc(per, (t, "site にしなかった複合"))
        j2[t] = o
    j3 = collections.OrderedDict((t, collections.OrderedDict([("採った", sc(per, (t, "cap を基準で絞る前に掛けた数"))), ("うち土台 P30E が GROUNDED の行", len(by[t]))])) for t in J_TYPES)
    j4 = collections.OrderedDict((t, rate(by[t], "P30E", TUNE.LABEL_PASS)) for t in J_TYPES)
    linked7 = [r for r in by["T7_ROUND"] if r[LINK_KEY]]
    p29, p30 = rate(linked7, "P29E", TUNE.LABEL_PASS), rate(linked7, "P30E", TUNE.LABEL_PASS)
    j5 = collections.OrderedDict([("P29E", p29), ("P30E", p30), ("差(pt)", round(p30 - p29, 1) if p29 is not None and p30 is not None else None), ("行", len(linked7))])
    j6 = collections.OrderedDict()
    for t in J_TYPES:
        if t == "T7_ROUND":
            mapped = [r for r in by[t] if r["P30E"]["対応"]]
            stopped = [r for r in mapped if r["P30E"]["結果"] != TUNE.LABEL_PASS]
            named = [r for r in stopped if r["P30E"]["結果"] == TUNE.LABEL_NAMED_ORIGINAL]
            j6[t] = pct(len(named), len(stopped))
        else:
            j6[t] = rate(by[t], "P30E", TUNE.LABEL_NAMED_ORIGINAL)
    differ = [r for r in rows if r[LINK_KEY] and r["P29E"]["結果"] != r["P30E"]["結果"]]
    d7 = sum(1 for r in differ if r["型"] == "T7_ROUND")
    j7 = collections.OrderedDict([("違う行", len(differ)), ("うち T7", d7), ("T7 の割合", pct(d7, len(differ)))])
    t2_pass = [r for r in by["T2_UNIT"] if r["P30E"]["結果"] == TUNE.LABEL_PASS]
    j8 = collections.OrderedDict([("通した行", len(t2_pass)), ("うち届いた", sum(1 for r in t2_pass if r["届いた"]))])
    j9 = collections.OrderedDict([("round-trip 不一致", sum(1 for r in rows if not r["round-trip"])), ("読み直し不一致", sum(1 for r in rows if not r["読み直し"])),
                                  ("先頭の位が減った行", sum(1 for r in rows if r["先頭の位が減った"]))])
    j10 = collections.OrderedDict([("偽", sc(per, ("T5_COINCIDENT", "偽"))), ("真", sc(per, ("T5_COINCIDENT", "真"))),
                                   ("真のうち相手の参照の単位が None か 円 でない site", sc(per, ("T5_COINCIDENT", "真の相手の単位", "その他を含む")))])
    ref = collections.OrderedDict((t, sum(1 for r in by[t] if r["届いた"])) for t in J_TYPES)
    return collections.OrderedDict([
        ("J-2 作れる site(種類別)", j2), ("J-3 採った / うち土台 P30E が GROUNDED の行", j3), ("J-4 通した率(P30E)", j4),
        ("J-5 T7_ROUND の通した率(P29E にも対応が付く行だけ)", j5), ("J-6 名指して原本の率(P30E。T7 は止めた行の中で)", j6),
        ("J-7 P29E と P30E で判定が違う行(P29E に対応が付く行)", j7), ("J-8 T2_UNIT で通した行(P30E)", j8), ("J-9", j9), ("J-10 T5 の site(注入しない)", j10),
        ("届いた行(型別。参考)", ref)])


# ======================================================================================================
# 記録の書き方
def caches_all():
    return RM.caches_all()


def header_j(root, step, seed_meta, before, after, profiles):
    h = RUN.header(root, step, os.path.join(root, SOURCES["aiforms"]["gen"]), seed_meta, before, after)
    h["seal"] = SEAL_REL
    h["封の commit"] = SEAL_COMMIT
    h["この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h["nscan script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_nscan_2026-11-05.py"))
    h["rmix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_rmix_2026-11-04.py"))
    h["numfix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_numfix_2026-11-04.py"))
    h["前の便の run script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_run_2026-11-03.py"))
    h["生成の記録の sha256"] = collections.OrderedDict((src, GEN.sha256_file(os.path.join(root, p["gen"]))) for src, p in SOURCES.items())
    h["H の記録の sha256"] = GEN.sha256_file(os.path.join(root, H_RECORD_REL))
    h["RB の記録の sha256"] = GEN.sha256_file(os.path.join(root, RB_RECORD_REL))
    h["lib の指紋"] = collections.OrderedDict((rel, GEN.sha256_file(os.path.join(root, rel))) for rel in LIB_RELS)
    h["profile"] = list(profiles)
    return h


def scope_word(only):
    return "全 200 本" if only is None else "**--only(本番の記録ではない)**"


def load_books(root=ROOT, only=None):
    u"""200 本の (source, name, item, row, prior)。``only`` は docID(コンマで分けて複数)。"""
    if only is None:
        return NF.load_books(root, None)
    ids = [x for x in only.split(",") if x]
    books = [b for b in NF.load_books(root, None) if b[2]["docID"] in ids]
    if not books or not set(ids) <= set(b[2]["docID"] for b in books):
        raise Stop("**--only の docID が 200 本に無い。止める**")
    return books


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_limits(seal):
    return NS.seal_limits(seal)


def write_json(out, rec, key_value=None):
    text = RUN.dumps_inject(rec)
    with key_check_j():
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
    work_root = work_root or tempfile.mkdtemp(prefix="jtypes_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say("注入 %d 本 × 2 profile(P29E・P30E)。切り替え 真・T2_UNIT・T6_PRIOR・T7_ROUND ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with yen_scan_on():
        if not getattr(N, FLAG) or wiring_problems():
            raise Stop("**切り替えを真にできない・配線が崩れた。止める**")
        results = NF.map_pool(inject_job_j, jobs_, procs)
    if getattr(N, FLAG):
        raise Stop("**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop("**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_j(root, "J(注入の型を広げる)― 切り替え 真・T2_UNIT・T6_PRIOR・T7_ROUND の注入(P29E・P30E。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec["範囲"] = scope_word(only)
    rec["切り替え"] = collections.OrderedDict([("名前", FLAG), ("inject の中の値", True), ("出たあとの値", bool(getattr(N, FLAG))), ("配線の問題", wiring_problems())])
    rec["種"] = {"file": RUN.SEED_REL_STR, "種の確認": seed_meta}
    rec["型"] = collections.OrderedDict([
        ("T2_UNIT", "inject.select(types=[T2_UNIT]) のまま。S.t2_sites を『groups が 2 つ以上の token を除く』版に with の中だけ差し替えた。cap は採用に掛ける(基準で絞る前)。注入後の claim は後の単位で引く"),
        ("T6_PRIOR", "IJ.t6_sites(S.identified_sites を複合を除く版に差し替えた with の中。既存・万だけ)+ 複合の写し。token の start の順に並べてから <seed>|<本の名前>|T6_PRIOR で並べ替え、土台 P30E GROUNDED の site を先頭から cap 件"),
        ("T7_ROUND", "IJ.t7_sites(S.data_bearing_sites を複合を除く版に差し替えた with の中。既存・万だけ)+ 複合の写し(符号は <seed>|<本の名前>|T7_ROUND|複合)。並べ替えと cap は T6 と同じ(種の字は T7_ROUND)"),
        ("T5_COINCIDENT・T3_ABSENT", "注入しない。T5 の site は切り替え 偽と真の数と、真の相手の参照の単位の内訳だけを本ごとの数えに持つ"),
        ("上限", "型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        ("site", SITE_WORD),
        ("土台", BASE_WORD),
        ("土台の結び方", "P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        ("届いた", "元の字が基準の claim の span に在る かつ 注入後の claim(P30E。対応が付いたとき)の span に差し替えの字が在る。T2 は元の数の字 + 後の単位"),
        ("集計の2本", "集計 = 全部の site での P29E・P30E の率。" + COMPARE_KEY + " = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率"),
        ("inject.select の docID の引数", "本の名前(<docID>_<形>_<model>)")])
    rec["本ごとの数え"] = per
    rec["注入の行の数"] = len(rows)
    rec["集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[BREAKDOWN_KEY] = breakdown(rows)
    rec["P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[J_KEY] = j_columns(per, rows)
    rec["限界"] = seal_limits(seal_text(root)) + list(EXTRA_LIMITS)
    rec["行"] = rows
    write_json(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の J-1〜J-10・§4 の K-1〜K-4)を読み、記録から判定する
def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {J-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (J-\d+) \| (.*) \|$", line)
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
    b["J-1"] = P["J-1"][1].strip()
    b["J-2"] = collections.OrderedDict()
    for t, names in (("T2", ("既存", "万だけ", "site にしない複合")), ("T6", ("既存", "万だけ", "複合")), ("T7", ("既存", "万だけ", "複合"))):
        m = re.search(r"%s %s / %s / %s" % ((t,) + (RANGE,) * 3), P["J-2"][1])
        b["J-2"][t] = collections.OrderedDict((n, _rng(m, 1 + 2 * i)) for i, n in enumerate(names))
    b["J-3"] = collections.OrderedDict()
    for t in ("T2", "T6", "T7"):
        m = re.search(r"%s %s / %s" % ((t,) + (RANGE,) * 2), P["J-3"][1])
        b["J-3"][t] = collections.OrderedDict([("採った", _rng(m, 1)), ("うち土台 P30E が GROUNDED の行", _rng(m, 3))])
    b["J-4"] = collections.OrderedDict()
    for t in J_TYPES:
        m = re.search(r"%s (%s)〜(%s)%%" % (t, NUM, NUM), P["J-4"][1])
        b["J-4"][t] = (float(m.group(1)), float(m.group(2)))
    b["J-5"] = float(re.search(r"差 (%s) pt 以上" % NUM, P["J-5"][1]).group(1))
    b["J-6"] = collections.OrderedDict()
    for t, pat in (("T2_UNIT", r"T2 %s%%"), ("T6_PRIOR", r"T6 %s%%"), ("T7_ROUND", r"T7\(止めた行の中で\)%s%%")):
        m = re.search(pat % RANGE, P["J-6"][1])
        b["J-6"][t] = (float(m.group(1)), float(m.group(2)))
    m = re.search(r"%s 行・T7 が (%s)%% 以上" % (RANGE, NUM), P["J-7"][1])
    b["J-7"] = collections.OrderedDict([("違う行", _rng(m, 1)), ("T7 の割合", float(m.group(3)))])
    b["J-8"] = int(re.match(r"(\d+)$", P["J-8"][1].strip()).group(1))
    m = re.match(r"(\d+) / (\d+) / (\d+)〜(\d+)$", P["J-9"][1].strip())
    b["J-9"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2))), ("先頭の位が減った行", (int(m.group(3)), int(m.group(4))))])
    m = re.match(r"(\d+) / %s / (\d+)$" % RANGE, P["J-10"][1].strip())
    b["J-10"] = collections.OrderedDict([("偽", int(m.group(1))), ("真", _rng(m, 2)), ("その他を含む", int(m.group(4)))])
    b["K-1"] = re.search(r"J-1 が (一致)", K["K-1"]).group(1)
    m = re.search(r"J-9 の round-trip 不一致 (\d+)・読み直し不一致 (\d+)", K["K-2"])
    b["K-2"] = collections.OrderedDict([("round-trip 不一致", int(m.group(1))), ("読み直し不一致", int(m.group(2)))])
    b["K-3"] = NF.num(re.search(r"和 ≥ (%s)" % NUM, K["K-3"]).group(1))
    b["K-4"] = int(re.search(r"J-8 が (\d+)", K["K-4"]).group(1))
    return b


within = RM.within


def git_numstat_since_seal(root=ROOT):
    u"""``git diff --numstat <封の commit> -- measure/inject.py measure/lib/sites.py`` の行(空なら 0 行)。git が読めなければ None。"""
    p = subprocess.run(["git", "diff", "--numstat", SEAL_COMMIT, "--"] + list(UNTOUCHED_FOR_J1), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return None
    return [ln for ln in p.stdout.decode("utf-8").splitlines() if ln]


def j1_value(rec, h_rec, rb_rec, numstat):
    u"""J-1 の 3 つ: lib の指紋が H の記録と、engine の指紋(sha256 の 2 欄。git_commit は比べない)が RB の記録と一致・inject.py と sites.py が封の commit から変わった file の数。"""
    fp, rfp = rec.get("engine の指紋") or {}, rb_rec.get("engine の指紋") or {}
    eng = all(fp.get(k) is not None and fp.get(k) == rfp.get(k) for k in ("adapter_xbrl_py_sha256", "core_py_sha256"))
    lib = rec.get("lib の指紋") is not None and norm(rec.get("lib の指紋")) == norm(h_rec.get("lib の指紋"))
    return collections.OrderedDict([("lib の指紋が H の記録と一致", bool(lib)), ("engine の指紋が RB の記録と一致", bool(eng)),
                                    ("inject.py・sites.py が封の commit から変わった file", None if numstat is None else len(numstat))])


NOT_GIVEN = object()


def build_J(R_, seal, numstat=NOT_GIVEN):
    u"""{J, K, 採用, 欄}。R_ = {"inject", "h", "rb"}(記録の JSON)。欄は inject の記録の 本ごとの数え と 行 から数え直す(記録の ``J の欄`` は使わない)。
    numstat 省略時は git に聞く。None を渡したら『読めなかった』= J-1 は外れ(省略とは別。読めないのに作業木の答えで代えない)。"""
    inj = R_["inject"]
    if numstat is NOT_GIVEN:
        numstat = git_numstat_since_seal()
    return judge_from(j1_value(inj, R_["h"], R_["rb"], numstat), j_columns(inj["本ごとの数え"], inj["行"]), seal)


def judge_from(j1, cols, seal):
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    J = collections.OrderedDict()

    def put(k, ok, val):
        J[k] = {"判定": HIT if ok else MISS, "値": val}
    put("J-1", j1["lib の指紋が H の記録と一致"] and j1["engine の指紋が RB の記録と一致"] and j1["inject.py・sites.py が封の commit から変わった file"] == 0, j1)
    c2 = cols["J-2 作れる site(種類別)"]
    ok2 = all(within(c2[t][k], B["J-2"][TYPE_SHORT[t]][k]) for t in J_TYPES for k in c2[t])
    put("J-2", ok2 and all(set(c2[t]) == set(B["J-2"][TYPE_SHORT[t]]) for t in J_TYPES), collections.OrderedDict((TYPE_SHORT[t], c2[t]) for t in J_TYPES))
    c3 = cols["J-3 採った / うち土台 P30E が GROUNDED の行"]
    put("J-3", all(within(c3[t][k], B["J-3"][TYPE_SHORT[t]][k]) for t in J_TYPES for k in c3[t]), collections.OrderedDict((TYPE_SHORT[t], c3[t]) for t in J_TYPES))
    c4 = cols["J-4 通した率(P30E)"]
    put("J-4", all(within(c4[t], B["J-4"][t]) for t in J_TYPES), collections.OrderedDict((t + " 通した率 P30E", c4[t]) for t in J_TYPES))
    c5 = cols["J-5 T7_ROUND の通した率(P29E にも対応が付く行だけ)"]
    put("J-5", c5["差(pt)"] is not None and c5["差(pt)"] >= B["J-5"], c5)
    c6 = cols["J-6 名指して原本の率(P30E。T7 は止めた行の中で)"]
    put("J-6", all(within(c6[t], B["J-6"][t]) for t in J_TYPES), collections.OrderedDict((t + " 名指して原本 P30E", c6[t]) for t in J_TYPES))
    c7 = cols["J-7 P29E と P30E で判定が違う行(P29E に対応が付く行)"]
    put("J-7", within(c7["違う行"], B["J-7"]["違う行"]) and c7["T7 の割合"] is not None and c7["T7 の割合"] >= B["J-7"]["T7 の割合"], c7)
    c8 = cols["J-8 T2_UNIT で通した行(P30E)"]
    put("J-8", c8["うち届いた"] == B["J-8"], c8)
    c9 = cols["J-9"]
    put("J-9", c9["round-trip 不一致"] == B["J-9"]["round-trip 不一致"] and c9["読み直し不一致"] == B["J-9"]["読み直し不一致"] and within(c9["先頭の位が減った行"], B["J-9"]["先頭の位が減った行"]), c9)
    c10 = cols["J-10 T5 の site(注入しない)"]
    other = c10["真のうち相手の参照の単位が None か 円 でない site"]
    put("J-10", c10["偽"] == B["J-10"]["偽"] and within(c10["真"], B["J-10"]["真"]) and other == B["J-10"]["その他を含む"], c10)
    K = collections.OrderedDict()
    K["K-1"] = {"判定": J["J-1"]["判定"], "値": collections.OrderedDict([("J-1", J["J-1"]["判定"])])}
    k2 = c9["round-trip 不一致"] == B["K-2"]["round-trip 不一致"] and c9["読み直し不一致"] == B["K-2"]["読み直し不一致"]
    K["K-2"] = {"判定": HIT if k2 else MISS, "値": collections.OrderedDict([("round-trip 不一致", c9["round-trip 不一致"]), ("読み直し不一致", c9["読み直し不一致"])])}
    total = sum(c3[t]["うち土台 P30E が GROUNDED の行"] for t in J_TYPES)
    K["K-3"] = {"判定": HIT if total >= B["K-3"] else MISS, "値": collections.OrderedDict([("3 型の土台 P30E が GROUNDED の行の和", total)])}
    K["K-4"] = {"判定": HIT if c8["うち届いた"] == B["K-4"] else MISS, "値": collections.OrderedDict([("T2 で通した行のうち届いた", c8["うち届いた"])])}
    adopt = all(K[k]["判定"] == HIT for k in K)
    return collections.OrderedDict([("J", J), ("K", K), ("採用", adopt), ("欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


fmt = RM.fmt


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = ["| # | 欄 | 予測 | 測った値 | 判定 |", "|---|---|---|---|---|"]
    for k, v in J["J"].items():
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
    J = build_J(load_records(root), seal, git_numstat_since_seal(root))
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
