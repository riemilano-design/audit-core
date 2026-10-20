# -*- coding: utf-8 -*-
u"""穴 2 つ(単位語「ポイント」/ 前期の値を通す)の広さを測る ― 封 ``docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md``。

    python3 measure/xbrl_point_prior_2026-10-20.py --stage all          # 記録 fixtures/xbrl/point_prior_2026-10-20.json を書く
    python3 measure/xbrl_point_prior_2026-10-20.py --stage a --out <file>
    python3 measure/xbrl_point_prior_2026-10-20.py --stage b --out <file> --docs S100YMFV

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。
engine(``core/``・``adapters/``)と ``measure/false_pass_2026-10-14.py``・``measure/inject.py`` は 1 行も変えず、import して使う。

A(穴 A): cache の全 zip を 文あり(経営分析の文 ``select_mdna`` を持つ)/ 文なし / 読めない に分け、文ありの書類を既定 P21 の
  ``verify_document(zb, None, None)`` に掛けて、単位が「ポイント」の claim を全部集める。対照は単位が「％」「%」の claim の state 分布。
B(穴 B): 同じ文ありの書類で、GROUNDED の claim のうち pointers が 1 本で ``CurrentYear…`` の fact を指し、同じ要素・同じ枠の
  ``Prior1Year…`` の fact が 1 件在り(同じ単位・どちらも正・値が違う)= site。site の数の字を前期の値に(``inject.t6_sites`` と同じ条件:
  単位の倍率に戻して元の字の形で 1 字違わず書ける場合だけ作れる)置き換え、1 文 1 件・25 件 batch(``false_pass`` の ``run_doc`` と同じ型)で
  ``verify_document(zb, None, text)`` に掛け直し、注入 1 件ごとに 止めた / 通した(前期へ移った・当期の同じ参照先・当期の別要素ほか)/ その他 に分ける。
"""
from __future__ import print_function

import argparse
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
import unicodedata
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import instance as I  # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V  # noqa: E402
from lib import numbers as N  # noqa: E402  (inject.py と同じ描き方 ``render_value``)
from lib import scales as SC  # noqa: E402

SEAL = "docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md"
OUT_REL = "fixtures/xbrl/point_prior_2026-10-20.json"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
KEY_NAMES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY")
BATCH = 25
TOL = 1e-9
POINT_UNIT = u"ポイント"
PERCENT_UNITS = (u"％", u"%")
DIFF_WORDS = ("Change", "Increase", "Decrease", "Ratio")
PRINT_RX = re.compile(r"\d+(?:\.\d+)?ポイント")

K_MOVED = u"通した(参照先が前期へ移った)"
K_SAME = u"通した(参照先が当期の同じ参照先のまま)"
K_OTHER = u"通した(参照先が当期の別要素)"
K_ODD = u"通した(参照先がそのほか)"
K_STOP = u"止めた"
K_ELSE = u"その他"
PASSED_KINDS = (K_MOVED, K_SAME, K_OTHER, K_ODD)

CAT_TEXT, CAT_NOTEXT, CAT_BAD = u"文あり", u"文なし", u"読めない"


def _load_false_pass():
    sp = importlib.util.spec_from_file_location("false_pass_for_point_prior", os.path.join(HERE, "false_pass_2026-10-14.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _load_ritual():
    sp = importlib.util.spec_from_file_location("ritual_for_point_prior", os.path.join(HERE, "ritual_2026-10-20.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


FP = _load_false_pass()


def pct(a, b):
    return round(100.0 * a / b, 1)


def frac_text(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def git(*a):
    try:
        out = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True, timeout=30)
        return out.returncode, out.stdout
    except Exception:
        return 1, ""


# --------------------------------------------------------------------------------------------------
# 書類の区分
def kind_of(zb):
    u"""提出書類の種別(PublicDoc の .xbrl の file 名の ``jpcrp…-asr-`` の形)。取れなければ None。"""
    try:
        z = zipfile.ZipFile(io.BytesIO(zb))
        for n in z.namelist():
            b = os.path.basename(n)
            m = n.endswith(".xbrl") and "PublicDoc" in n and re.match(r"(jp[a-z]+)\d+-(\w+)-", b)
            if m:
                return m.group(1) + u"…-" + m.group(2) + u"-"
    except Exception:
        return None
    return None


def classify_doc(zb):
    u"""(区分, 理由, 経営分析の文 or None)。"""
    try:
        inst = I.load_instance(zb)
    except Exception as e:  # noqa: BLE001
        return CAT_BAD, u"load_instance: %s" % type(e).__name__, None
    try:
        name = I.select_mdna(inst["textblocks"])
    except Exception as e:  # noqa: BLE001
        return CAT_BAD, u"select_mdna: %s" % type(e).__name__, None
    if name is None:
        return CAT_NOTEXT, None, None
    try:
        text = unicodedata.normalize("NFKC", I.strip_html(inst["textblocks"][name]))
    except Exception as e:  # noqa: BLE001
        return CAT_BAD, u"mdna_text: %s" % type(e).__name__, None
    return CAT_TEXT, None, text


def list_zips():
    out = []
    if os.path.isdir(CACHE):
        for fn in sorted(os.listdir(CACHE)):
            if fn.endswith(".zip"):
                out.append((fn[:-4], os.path.join(CACHE, fn)))
    return out


# --------------------------------------------------------------------------------------------------
# A
def elem_of(pointer):
    u"""``xbrl:jpcrp_cor:Name@Ctx`` -> (``jpcrp_cor:Name``, ``Ctx``)。xbrl: でなければ (None, None)。"""
    if not pointer.startswith("xbrl:"):
        return None, None
    name, _, ctx = pointer[5:].partition("@")
    return name, ctx


def mark_pointers(pointers):
    elems = []
    for p in pointers:
        n, ctx = elem_of(p)
        if n:
            elems.append({u"要素": n, u"枠": ctx, u"要素名に差・比の語": any(w in n.split(":", 1)[-1] for w in DIFF_WORDS)})
    return {u"xbrl の参照先": elems,
            u"式の pointer": [p for p in pointers if not p.startswith("xbrl:")],
            u"要素名に Change/Increase/Decrease/Ratio の語が在る": any(e[u"要素名に差・比の語"] for e in elems),
            u"差の式(formula:a-b)を持つ": any(p.startswith("formula:a-b") for p in pointers)}


def doc_a(doc_id, zb, text0):
    u"""1 書類の A(単位ポイントの claim の行・対照・診断)。"""
    out = VD.verify_document(zb, None, None)
    profile = V.PROFILES[V.DEFAULT_PROFILE]
    sentences, sites = FP.number_sites(text0, profile)
    by_site = {s["id"]: s for s in sites}
    points, pct_states, pt_states = [], {}, {}
    span_has_point_other_unit = 0
    for c in out["claims"]:
        if c["unit"] == POINT_UNIT:
            s = by_site.get(c["id"])
            ctx = None
            if s is not None and c["value"] is not None and abs(s["value"] - c["value"]) <= 1e-6 * max(1.0, abs(s["value"])):
                ctx = sentences[s["si"]][max(0, s["a"] - 30):s["b"] + 30]
            row = {u"書類": doc_id, u"id": c["id"], u"値": c["value"], u"state": c["state"], u"reason": c["reason"],
                   u"pointers": c["pointers"], u"主語": c["subject"], u"形": c["form"], u"再計算": c["recomputed"],
                   u"span": c["span"], u"文脈 60 字": ctx}
            if c["state"] == "GROUNDED":
                row[u"参照先の印"] = mark_pointers(c["pointers"])
            points.append(row)
            pt_states[c["state"]] = pt_states.get(c["state"], 0) + 1
        elif c["unit"] in PERCENT_UNITS:
            pct_states[c["state"]] = pct_states.get(c["state"], 0) + 1
        elif c["span"] and u"ポイント" in (c["span"] or u""):
            span_has_point_other_unit += 1
    return {u"書類": doc_id, u"claim": out["document"]["claims"], u"state の分布": out["document"]["states"],
            u"印字(数字+ポイント)": len(PRINT_RX.findall(text0)),
            u"ポイントの claim": len(points), u"ポイントの state": dict(sorted(pt_states.items())),
            u"％の claim の state": dict(sorted(pct_states.items())),
            u"span に ポイント を含むが単位がポイントでない claim": span_has_point_other_unit}, points


def dist(rows, key=u"state"):
    d = {}
    for r in rows:
        k = r[key] if r[key] is not None else u"(なし)"
        d[k] = d.get(k, 0) + 1
    return dict(sorted(d.items()))


# --------------------------------------------------------------------------------------------------
# B
def factor_of(unit, cur_fact):
    u"""``engine の文の値`` -> fact の値 への倍率。金額は単位語(``円`` は 1。engine が先に 円 に直した値も 1)、
    率(%)は fact が pure で 1.5 以下なら 0.01、ほかは 1。"""
    f = SC.scale_of(unit)
    if f is not None:
        return float(f)
    if unit in PERCENT_UNITS and cur_fact["unit"] == "pure" and abs(cur_fact["value"]) <= 1.5:
        return 0.01
    return 1.0


class _Tok(object):
    def __init__(self, num):
        self.text = num
        self.has_frac = "." in num
        self.has_comma = "," in num


def render_prior(raw, unit, value, cur_fact, prior_fact):
    u"""前期の値を ``raw`` の字の形で書く。書けなければ (None, 理由, 倍率)。倍率 = 字の数字部分 -> fact の値。
    数字部分の倍率は engine が数えた文の値 ``value`` と字の数字から求める(``2百万円`` は value 2000000.0・``6,451百万円`` は 6451.0 と、
    engine は書き方によって単位を円に直したり直さなかったりする)。"""
    pre, num, post = FP._digits_part(raw)
    if not num:
        return None, u"数字部分が無い", None
    if not re.fullmatch(r"\d[\d,]*(?:\.\d+)?", num):
        return None, u"数字部分が単純な数でない(複合表記。例 13億51百万円)", None
    nf = float(num.replace(",", ""))
    if nf == 0:
        return None, u"数字が 0", None
    factor = factor_of(unit, cur_fact) * (abs(value) / nf)
    cand = prior_fact["value"] / factor
    rendered = N.render_value(cand, _Tok(num))
    try:
        back = float(rendered.replace(",", "")) * factor
    except ValueError:
        return None, u"書いた字が数でない", factor
    if abs(back - prior_fact["value"]) > max(TOL, abs(prior_fact["value"]) * 1e-9):
        return None, u"元の字の形では前期の値を 1 字違わず書けない", factor
    if rendered == num:
        return None, u"書いた字が元の字と同じ", factor
    return pre + rendered + post, None, factor


def find_sites(zb, text0):
    u"""(site の一覧, 絞り込みの各段の件数, 土台の state の分布)。site は作れた/作れないの別つき。"""
    profile = V.PROFILES[V.DEFAULT_PROFILE]
    inst = I.load_instance(zb)
    by_key = {}
    for f in inst["facts"]:
        by_key.setdefault((f["name"], f["context"]), []).append(f)
    base = VD.verify_document(zb, None, text0)
    orig = VD.verify_document(zb, None, None)
    sentences, sites = FP.number_sites(text0, profile)
    by_id = {c["id"]: c for c in base["claims"]}
    diag = {u"1 数の site": len(sites)}

    def bump(k):
        diag[k] = diag.get(k, 0) + 1

    out = []
    for s in sites:
        c = by_id.get(s["id"])
        if c is None or c.get("value") is None or abs(c["value"] - s["value"]) > 1e-6 * max(1.0, abs(s["value"])):
            bump(u"1b 土台の不一致(id と値が engine と合わない)")
            continue
        if c["state"] != "GROUNDED":
            continue
        bump(u"2 GROUNDED")
        if len(c["pointers"]) != 1:
            continue
        name, ctx = elem_of(c["pointers"][0])
        if name is None:
            continue
        bump(u"3 pointers が xbrl の 1 本")
        if not ctx.startswith("CurrentYear"):
            continue
        bump(u"4 参照先の枠が CurrentYear で始まる")
        pctx = "Prior1Year" + ctx[len("CurrentYear"):]
        curs = by_key.get((name, ctx), [])
        priors = by_key.get((name, pctx), [])
        if not curs or len(priors) != 1:
            continue
        bump(u"5 同じ要素・同じ枠の Prior1Year の fact が 1 件在る")
        cur, prior = curs[0], priors[0]
        if cur["unit"] != prior["unit"]:
            continue
        bump(u"6 単位が同じ")
        if not (cur["value"] > 0 and prior["value"] > 0 and s["value"] > 0 and abs(cur["value"] - prior["value"]) > TOL):
            continue
        bump(u"7 どちらも正で値が違う(site)")
        new_raw, why, factor = render_prior(s["raw"], s["unit"], s["value"], cur, prior)
        site = {u"書類": None, u"id": s["id"], u"要素": name, u"当期の枠": ctx, u"前期の枠": pctx, u"元の字": s["raw"],
                u"単位": s["unit"], u"文の値": s["value"], u"当期の fact": cur["value"], u"前期の fact": prior["value"],
                u"fact の単位": cur["unit"], u"倍率": factor, u"作れた": new_raw is not None, u"作れない理由": why,
                u"後の字": new_raw, u"文脈 60 字": sentences[s["si"]][max(0, s["a"] - 30):s["b"] + 30],
                u"_si": s["si"], u"_a": s["a"], u"_b": s["b"]}
        if new_raw is not None:
            bump(u"8 元の字の形で 1 字違わず書ける(作れた)")
        out.append(site)
    return out, diag, base["document"]["states"], orig["document"]["states"], sentences, base


def classify_after(site, c):
    u"""(区分, 後の state, reason, pointers)。"""
    if c is None:
        return K_ELSE, None, None, []
    st, ptr = c["state"], c["pointers"]
    if st == "VALUE_MISMATCH":
        return K_STOP, st, c["reason"], ptr
    if st != "GROUNDED":
        return K_ELSE, st, c["reason"], ptr
    xs = [elem_of(p) for p in ptr if p.startswith("xbrl:")]
    if xs and all(ctx.startswith("Prior1Year") for _n, ctx in xs):
        return K_MOVED, st, c["reason"], ptr
    if xs and all(n == site[u"要素"] and ctx == site[u"当期の枠"] for n, ctx in xs):
        return K_SAME, st, c["reason"], ptr
    if xs and any(n != site[u"要素"] and ctx.startswith("CurrentYear") for n, ctx in xs):
        return K_OTHER, st, c["reason"], ptr
    return K_ODD, st, c["reason"], ptr


def inject_doc(doc_id, zb, text0, sites, sentences):
    u"""作れた site を 1 文 1 件・25 件 batch で注入し、verify_document(zb, None, text) で再検証(``run_doc`` と同じ型)。"""
    pending = [s for s in sites if s[u"作れた"]]
    rows = []
    while pending:
        batch, used, rest = [], set(), []
        for s in pending:
            if len(batch) < BATCH and s[u"_si"] not in used:
                batch.append(s)
                used.add(s[u"_si"])
            else:
                rest.append(s)
        pending = rest
        new_sents = {}
        plan = []
        for s in batch:
            sent = sentences[s[u"_si"]]
            ns = sent[:s[u"_a"]] + s[u"後の字"] + sent[s[u"_b"]:]
            new_sents[s[u"_si"]] = ns
            vals = [v for (_a, _b, v, _u, _p) in FP.E.iter_numbers(s[u"後の字"])]
            plan.append((s, vals[0] if len(vals) == 1 else None))
        text = text0
        for (s, exp) in sorted(plan, key=lambda t: -text0.find(sentences[t[0][u"_si"]])):
            pos = text.find(sentences[s[u"_si"]])
            if pos < 0:
                rows.append(dict(_row(doc_id, s), **{u"結果": K_ELSE, u"結果の細目": u"sentence_not_found"}))
                continue
            text = text[:pos] + new_sents[s[u"_si"]] + text[pos + len(sentences[s[u"_si"]]):]
        got = {c["id"]: c for c in VD.verify_document(zb, None, text)["claims"]}
        for (s, exp) in plan:
            if any(r[u"id"] == s[u"id"] and r[u"結果の細目"] == u"sentence_not_found" for r in rows if r[u"書類"] == doc_id):
                continue
            c = got.get(s[u"id"])
            row = _row(doc_id, s)
            if c is None:
                row.update({u"結果": K_ELSE, u"結果の細目": u"missing"})
            elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
                row.update({u"結果": K_ELSE, u"結果の細目": u"id_shift"})
            else:
                kind, st, reason, ptr = classify_after(s, c)
                row.update({u"結果": kind, u"結果の細目": st, u"後の reason": reason, u"後の pointers": ptr})
            rows.append(row)
    return rows


def _row(doc_id, s):
    return {u"書類": doc_id, u"id": s[u"id"], u"要素": s[u"要素"], u"当期の枠": s[u"当期の枠"], u"前期の枠": s[u"前期の枠"],
            u"元の字": s[u"元の字"], u"後の字": s[u"後の字"], u"単位": s[u"単位"], u"文の値": s[u"文の値"],
            u"当期の fact": s[u"当期の fact"], u"前期の fact": s[u"前期の fact"], u"文脈 60 字": s[u"文脈 60 字"], u"結果の細目": None}


def doc_b(doc_id, zb, text0):
    sites, diag, base_states, orig_states, sentences, _base = find_sites(zb, text0)
    for s in sites:
        s[u"書類"] = doc_id
    rows = inject_doc(doc_id, zb, text0, sites, sentences)
    made = [s for s in sites if s[u"作れた"]]
    if len(rows) != len(made):
        raise SystemExit(u"**注入の行の数が作れた site の数と違う(%s): %d != %d。止める**" % (doc_id, len(rows), len(made)))
    unmade = [{k: v for k, v in s.items() if not k.startswith("_")} for s in sites if not s[u"作れた"]]
    summary = {u"書類": doc_id, u"site": len(sites), u"作れた": len(made), u"作れない": len(unmade),
               u"絞り込み": diag, u"土台の state が経営分析の文のままと同じ": base_states == orig_states,
               u"結果": dist(rows, u"結果")}
    return summary, rows, unmade


# --------------------------------------------------------------------------------------------------
# 集計と判定(純関数。門が記録から同じ関数ではなく独立に数え直す)
def median(xs):
    return float(statistics.median(xs)) if xs else None


def _pct_in_point_docs(docs_rows):
    d = {}
    for r in docs_rows:
        if r[u"ポイントの claim"] > 0:
            for k, v in r[u"％の claim の state"].items():
                d[k] = d.get(k, 0) + v
    return dict(sorted(d.items()))


def summarize_a(docs_rows, points):
    n = len(points)
    st = dist(points)
    ctrl = {}
    for d in docs_rows:
        for k, v in d[u"％の claim の state"].items():
            ctrl[k] = ctrl.get(k, 0) + v
    nctrl = sum(ctrl.values())
    g = st.get("GROUNDED", 0)
    gc = ctrl.get("GROUNDED", 0)
    return {u"ポイントの claim": n, u"ポイントの state": st,
            u"ポイントの GROUNDED": {u"件": g, u"分母": n, u"率": pct(g, n) if n else None},
            u"ポイントの POINTER_NOT_FOUND + UNVERIFIABLE": {u"件": st.get("POINTER_NOT_FOUND", 0) + st.get("UNVERIFIABLE", 0), u"分母": n,
                                                          u"率": pct(st.get("POINTER_NOT_FOUND", 0) + st.get("UNVERIFIABLE", 0), n) if n else None},
            u"ポイントの reason": dist([{u"r": p[u"reason"]} for p in points], u"r"),
            u"ポイントの claim がある書類": len({p[u"書類"] for p in points}),
            u"印字(数字+ポイント)の合計": sum(d[u"印字(数字+ポイント)"] for d in docs_rows),
            u"％の claim": nctrl, u"％の state": dict(sorted(ctrl.items())),
            u"％の GROUNDED": {u"件": gc, u"分母": nctrl, u"率": pct(gc, nctrl) if nctrl else None},
            u"％の state(ポイントの claim がある書類だけ)": _pct_in_point_docs(docs_rows),
            u"％ − ポイント の GROUNDED の差(pt)": round(pct(gc, nctrl) - pct(g, n), 1) if n and nctrl else None,
            u"GROUNDED のポイント行のうち 差の式 formula:a-b を持つ": sum(1 for p in points if p[u"state"] == "GROUNDED" and p[u"参照先の印"][u"差の式(formula:a-b)を持つ"]),
            u"GROUNDED のポイント行のうち 要素名に Change/Increase/Decrease/Ratio の語": sum(1 for p in points if p[u"state"] == "GROUNDED" and p[u"参照先の印"][u"要素名に Change/Increase/Decrease/Ratio の語が在る"]),
            u"span に ポイント を含むが単位がポイントでない claim の合計": sum(d[u"span に ポイント を含むが単位がポイントでない claim"] for d in docs_rows)}


def _by_unit(rows):
    d = {}
    for x in rows:
        d.setdefault(x[u"単位"], {})
        d[x[u"単位"]][x[u"結果"]] = d[x[u"単位"]].get(x[u"結果"], 0) + 1
    return {k: dict(sorted(v.items())) for k, v in sorted(d.items())}


def summarize_b(sums, rows, unmade):
    per_site = [s[u"site"] for s in sums]
    per_made = [s[u"作れた"] for s in sums]
    n = len(rows)
    r = dist(rows, u"結果")
    passed = sum(r.get(k, 0) for k in PASSED_KINDS)
    moved = r.get(K_MOVED, 0)
    return {u"書類の数(分母)": len(sums),
            u"site": {u"合計": sum(per_site), u"書類あたり中央値": median(per_site), u"書類あたり最大": max(per_site) if per_site else None,
                      u"site が 0 の書類": sum(1 for x in per_site if x == 0)},
            u"作れた注入": {u"合計": n, u"書類あたり中央値": median(per_made)},
            u"作れない site": {u"合計": len(unmade), u"理由": dist(unmade, u"作れない理由")},
            u"結果": r,
            u"通した(GROUNDED のまま)合計": {u"件": passed, u"分母": n, u"率": pct(passed, n) if n else None},
            u"前期へ移って通した": {u"件": moved, u"分母": n, u"率": pct(moved, n) if n else None},
            u"通した のうち参照先が Prior1Year でない": {u"件": passed - moved, u"分母": passed, u"率": pct(passed - moved, passed) if passed else None},
            u"単位別の結果": _by_unit(rows),
            u"前期へ移って通したうち 要素が同じ": sum(1 for x in rows if x[u"結果"] == K_MOVED and all(elem_of(p)[0] == x[u"要素"] for p in x[u"後の pointers"] if p.startswith("xbrl:")))}


def judge(rec):
    u"""予測 A-1〜A-4・B-1〜B-5 の機械的な判定(人の読みが要るものは 判定は文書で)。"""
    J = {}
    if u"A" in rec:
        a = rec[u"A"][u"集計"]
        n = a[u"ポイントの claim"]
        J[u"A-1"] = {u"実測": u"ポイントの claim %d 件" % n, u"判定": u"当たり" if 29 <= n <= 45 else u"外れ"}
        g, pn = a[u"ポイントの GROUNDED"][u"率"], a[u"ポイントの POINTER_NOT_FOUND + UNVERIFIABLE"][u"率"]
        ok = n > 0 and 10 <= g <= 25 and 65 <= pn <= 85
        J[u"A-2"] = {u"実測": u"GROUNDED %s%%・POINTER_NOT_FOUND + UNVERIFIABLE %s%%" % (g, pn), u"判定": u"当たり" if ok else u"外れ"}
        d = a[u"％ − ポイント の GROUNDED の差(pt)"]
        J[u"A-3"] = {u"実測": u"％の GROUNDED %s%% − ポイント %s%% = %s pt" % (a[u"％の GROUNDED"][u"率"], g, d),
                   u"判定": u"当たり" if (d is not None and d >= 20) else u"外れ"}
        J[u"A-4"] = {u"実測": u"機械的な印: GROUNDED のポイント %d 行のうち 差の式 %d・要素名に差/比の語 %d" % (
            a[u"ポイントの GROUNDED"][u"件"], a[u"GROUNDED のポイント行のうち 差の式 formula:a-b を持つ"],
            a[u"GROUNDED のポイント行のうち 要素名に Change/Increase/Decrease/Ratio の語"]), u"判定": u"判定は文書で(人の読み)"}
    if u"B" in rec:
        b = rec[u"B"][u"集計"]
        med, tot = b[u"site"][u"書類あたり中央値"], b[u"site"][u"合計"]
        J[u"B-1"] = {u"実測": u"site 合計 %d・書類あたり中央値 %s(作れた注入 %d・中央値 %s)" % (
            tot, med, b[u"作れた注入"][u"合計"], b[u"作れた注入"][u"書類あたり中央値"]),
            u"判定": u"当たり" if (med is not None and 3 <= med <= 15 and 200 <= tot <= 1000) else u"外れ"}
        m = b[u"前期へ移って通した"]
        J[u"B-2"] = {u"実測": u"前期へ移って通した %s" % (frac_text(m[u"件"], m[u"分母"]) if m[u"分母"] else u"分母 0"),
                   u"判定": u"当たり" if (m[u"分母"] and 30 <= m[u"率"] <= 70) else u"外れ"}
        o = b[u"通した のうち参照先が Prior1Year でない"]
        J[u"B-3"] = {u"実測": u"通した %d のうち参照先が Prior1Year でないもの %s(内訳 %s)" % (
            o[u"分母"], frac_text(o[u"件"], o[u"分母"]) if o[u"分母"] else u"分母 0",
            json.dumps({k: b[u"結果"].get(k, 0) for k in (K_MOVED, K_SAME, K_OTHER, K_ODD)}, ensure_ascii=False)),
            u"判定": (u"当たり" if o[u"率"] <= 2.0 else u"外れ") if o[u"分母"] else u"判定不能(通した 0)"}
    if u"所要秒" in rec and u"A" in rec and u"B" in rec:   # 全体の所要と engine の部分は --stage all のときだけ判定する
        s = rec[u"所要秒"]
        J[u"B-4"] = {u"実測": u"A %s 秒・B %s 秒・全体 %s 秒" % (s.get(u"A"), s.get(u"B"), s[u"全体"]), u"判定": u"当たり" if s[u"全体"] <= 1800 else u"外れ"}
        e = rec[u"環境"][u"engine と測定の道具の差(git diff HEAD)"]
        J[u"B-5"] = {u"実測": u"engine・false_pass・inject の git diff 行数 %d・未追跡 %d。既存 tests の赤 0 は 判定は文書で(pytest の結果)" % (e[u"差の行数"], len(e[u"未追跡・変更の file"])),
                   u"判定": u"engine の部分は 当たり(既存 tests の赤は文書で)" if (e[u"差の行数"] == 0 and not e[u"未追跡・変更の file"]) else u"外れ"}
    return J


# --------------------------------------------------------------------------------------------------
def env_block(ritual):
    bundle, n_files = ritual.engine_bundle_sha256()
    rc, dif = git("diff", "--numstat", "HEAD", "--", "core", "adapters", "measure/false_pass_2026-10-14.py", "measure/inject.py")
    rc2, stat = git("status", "--porcelain", "--", "core", "adapters", "measure/false_pass_2026-10-14.py", "measure/inject.py")
    lines = 0
    for ln in dif.splitlines():
        p = ln.split("\t")
        if len(p) >= 2 and p[0].isdigit() and p[1].isdigit():
            lines += int(p[0]) + int(p[1])
    return {u"封": SEAL, u"HEAD": ritual.git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)": bundle,
            u"engine の file 数": n_files,
            u"engine と測定の道具の差(git diff HEAD)": {u"対象": u"core・adapters・measure/false_pass_2026-10-14.py・measure/inject.py",
                                              u"差の行数": lines, u"未追跡・変更の file": [l.strip() for l in stat.splitlines()]},
            u"鍵の名前の有無(値は読まない)": {k: (k in os.environ) for k in KEY_NAMES},
            u"profile": V.DEFAULT_PROFILE, u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"費用": u"0 USD"}


def run(stage, only_docs=None, progress=None):
    ritual = _load_ritual()
    t_all = time.time()
    zips = list_zips()
    if only_docs:
        zips = [(d, p) for d, p in zips if d in only_docs]
    docs, texts = [], {}
    for doc_id, path in zips:
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, why, text = classify_doc(zb)
        docs.append({u"docID": doc_id, u"sha256": hashlib.sha256(zb).hexdigest(), u"bytes": len(zb), u"区分": cat, u"理由": why,
                     u"提出書類の種別": kind_of(zb)})
        if cat == CAT_TEXT:
            texts[doc_id] = (zb, text)
    rec = {u"step": u"**穴 2 つ(単位語「ポイント」/ 前期の値を通す)の広さ。0 USD・通信なし・engine 0 行**",
           u"環境": env_block(ritual), u"書類": docs,
           u"書類の数": {u"全部": len(docs), CAT_TEXT: sum(1 for d in docs if d[u"区分"] == CAT_TEXT),
                      CAT_NOTEXT: sum(1 for d in docs if d[u"区分"] == CAT_NOTEXT), CAT_BAD: sum(1 for d in docs if d[u"区分"] == CAT_BAD)}}
    secs = {}
    if stage in ("a", "all"):
        t = time.time()
        drows, points = [], []
        for doc_id in sorted(texts):
            zb, text = texts[doc_id]
            d, p = doc_a(doc_id, zb, text)
            drows.append(d)
            points.extend(p)
            if progress:
                progress(u"A %s" % doc_id)
        rec[u"A"] = {u"書類別": drows, u"行": points, u"集計": summarize_a(drows, points)}
        secs[u"A"] = round(time.time() - t, 1)
    if stage in ("b", "all"):
        t = time.time()
        sums, rows, unmade = [], [], []
        for doc_id in sorted(texts):
            zb, text = texts[doc_id]
            s, r, u = doc_b(doc_id, zb, text)
            sums.append(s)
            rows.extend(r)
            unmade.extend(u)
            if progress:
                progress(u"B %s site %d 作れた %d" % (doc_id, s[u"site"], s[u"作れた"]))
        rec[u"B"] = {u"書類別": sums, u"行": rows, u"作れない site": unmade, u"集計": summarize_b(sums, rows, unmade)}
        secs[u"B"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"予測の判定"] = judge(rec)
    rec[u"limits"] = [
        u"手元の cache の全 zip(無作為ではない)。経営分析の文を持つ書類だけが分母。",
        u"A-4 と「正しく結べたか」の読みは人の読みで、機械は参照先の要素名の印(差・比の語、差の式)を付けるだけ。判定は文書で。",
        u"B は「前期の値がそのまま書かれる」誤りだけ(前期の値 ±1 などは測らない)。",
        u"25 件 batch(封の字)。false_pass の docstring は --batch 1 が正としている(同じ束の数が書類の丸め方に入る)ので、batch 1 では通す数が変わりうる。",
        u"site は Core の GROUNDED の claim と pointers から作る(inject.t6_sites は参照先の一覧 refs から作る別の道。条件は同じ形だが同一の関数ではない)。"]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"穴 2 つの広さ(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["a", "b", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage a|b か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    ritual = _load_ritual()
    _shas, why = ritual.check_labels()
    if why:
        print(ritual.label_guidance(why), file=sys.stderr)
        return 2
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, progress=lambda m: print(m, file=sys.stderr))
    rec[u"環境"][u"ラベル 2 file の sha256(起動時に照合)"] = _shas
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    n = rec[u"書類の数"]
    print(u"=== 穴 2 つの広さ(%s・手元の cache・鍵なし・0 USD)===" % V.DEFAULT_PROFILE)
    print(u"書類 %d(文あり %d・文なし %d・読めない %d)" % (n[u"全部"], n[CAT_TEXT], n[CAT_NOTEXT], n[CAT_BAD]))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
