# -*- coding: utf-8 -*-
u"""丸めの帯を片側にする P23 の段 1 の測定 ― 封 ``docs/XBRL_ROUNDING_SEAL_2026-10-21.md`` §2(R-1〜R-7。R-7 は段 2 なので判定しない)。

    cd audit-core
    python3 measure/xbrl_rounding_2026-10-21.py --stage all                  # 記録 fixtures/xbrl/rounding_2026-10-21.json を書く
    python3 measure/xbrl_rounding_2026-10-21.py --stage r3 --out <file> --docs S100YMFV   # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。
engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**(P23 は別に実装済み)。期を縛る P22 の測定
(``measure/xbrl_period_bind_2026-10-20.py``)の道具(穴 B の注入 ``inject_with_profile``・段 2 の材料 ``e4``)・儀式
(``measure/ritual_2026-10-20.py`` の ``build``)・穴 B の道具(``measure/xbrl_point_prior_2026-10-20.py``)は import して使う(書き直さない)。
比べる 2 つは **P22(対照。いまの既定)と P23(旗 2 つ)** で、どちらも明示して呼ぶ(既定が動いても同じ数が出る)。

  R-1  儀式(同梱の 1 書類 S100Z4Q1、注入 240 件)を P23 で。対照: P22 で回すと儀式の記録(``ritual_2026-10-20.json``)に 240 件全部一致。
  R-2  経営分析の文を持つ 67 書類の**無改変**を P22 と P23 で ``verify_document`` し、claim ごとに ``(state, pointers, reason, recomputed, form)`` を比べる。
       動いた行の一覧(向き・単位別・抜粋・生の値・文の値)、新 GROUNDED、書類ごとの丸め方の判定(R / T / 決めた丸め方)が P22 と P23 で変わるか。
  R-3  穴 B の 485 件(前期の値への置き換え)を P23 で再検証。対照: P22 の再計算が期を縛る P22 の記録(``period_bind_2026-10-20.json`` の E1)の 485 行に全部一致。
  R-4  R-2 の 67 書類で無改変の VALUE_MISMATCH の数(P22 / P23)。
  R-5  段 2 の材料(24 行 × 8 書類 = 192 行)の Core 自身を P22 と P23 で当て直す。対照: P22 の再計算が期を縛る P22 の記録の E4 に全行一致。
  R-6  engine の差分の行数(``git diff HEAD --numstat``)と、既存試験 ``tests/adapters/xbrl``(``--run-tests`` のとき pytest を走らせる)。
  R-7  段 2(既定の切り替え)。この実行では判定しない。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PB = _mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_for_rounding")
PP = PB.PP
RIT = PB.RIT
NF = PB.NF
OLD, NEW = "P22", "P23"
# period_bind の道具は module の OLD / NEW を呼ぶ時に読む。ここで P22(対照)/ P23 に差し替える(この script の中だけ)。
PB.OLD, PB.NEW = OLD, NEW

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import recipes as R          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/rounding_2026-10-21.json"
RITUAL_REL = "fixtures/xbrl/ritual_2026-10-20.json"                 # 記録の欄の名前(測った当時の字。P22(既定)で採り直した儀式の記録)
# 2026-10-23(P26 の段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で ritual_2026-10-20.json は P26(既定)で採り直したので、P22 のときの記録は同じバイト列(sha256 c89824f7…)の写し ritual_2026-10-20_p22.json を読む。記録の欄の名前(RITUAL_REL)は測った当時の字で変えない
RITUAL_P22_FILE = "fixtures/xbrl/ritual_2026-10-20_p22.json"
PERIOD_BIND_REL = "fixtures/xbrl/period_bind_2026-10-20.json"
S2_MATERIAL_REL = PB.S2_MATERIAL_REL
S2_REC_REL = PB.S2_REC_REL
RATE_UNITS = (u"％", u"%", u"ポイント")
KEY_NAMES = PB.KEY_NAMES
#: 封 §2 の R-6 は「登録の一覧の試験 4 か所に P23 を足す以外の既存試験は全部緑」と書いた。4 か所のほかに直した既存試験(実装席が見つけた)。
#: これが空でないとき R-6 は外れ。
EXTRA_EXISTING_FIXES = [
    u"tests/adapters/xbrl/test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag(率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P23 を足した。P23 は P18 の旗を積む)",
    u"tests/adapters/xbrl/test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on(period_bind を持つ profile の一覧を [P22] から [P22, P23] に。P23 は P22 から作る)",
    u"tests/adapters/xbrl/test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact(除外を P22 のみから P22・P23 に。P23 は period_bind を引き継ぐ)"]

pct, frac, sha_file, jload, git = PB.pct, PB.frac, PB.sha_file, PB.jload, PB.git
claim_key, view = PB.claim_key, PB.view


def kv(d):
    return dict(sorted(d.items()))


# ====================================================================================================
# R-1
def r1(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    old = RIT.build(zb, OLD, label_shas)
    new = RIT.build(zb, NEW, label_shas)
    rec = jload(RITUAL_P22_FILE)
    key = lambda x: (x[u"id"], x[u"型"])
    by_rec = dict((key(x), x[u"結果"]) for x in rec[u"注入の一覧"])
    by_old = dict((key(x), x[u"結果"]) for x in old[u"注入の一覧"])
    rows = []
    new_by = dict((key(x), x) for x in new[u"注入の一覧"])
    old_by = dict((key(x), x) for x in old[u"注入の一覧"])
    for k in sorted(set(new_by) | set(old_by)):
        n, o = new_by.get(k), old_by.get(k)
        base = n or o
        rows.append({u"id": k[0], u"型": k[1], u"元の字": base[u"元の字"], u"後の字": base.get(u"後の字"), u"元の値": base[u"元の値"],
                     u"単位": base[u"単位"], u"P22": (o[u"結果"] if o else None), u"P23": (n[u"結果"] if n else None)})
    passed_new = [x for x in new[u"通した の一覧"]]
    plain_old = VD.verify_document(zb, OLD, None)["claims"]
    plain_new = VD.verify_document(zb, NEW, None)["claims"]
    plain_moved = [{u"id": x["id"], u"span": x["span"], u"P22": view(x), u"P23": view(y)}
                   for x, y in zip(plain_old, plain_new) if claim_key(x) != claim_key(y)]
    return {u"行": rows,
            u"通した P23 の一覧": [{u"id": x[u"id"], u"型": x[u"型"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"], u"単位": x[u"単位"],
                               u"分類": x[u"分類"], u"値の差": x[u"値の差"], u"1 最小単位": x[u"1 最小単位"], u"文脈": x[u"文脈"]} for x in passed_new],
            u"通した P23": new[u"通した"], u"止めた P23": new[u"止めた"], u"その他 P23": new[u"止めた でも 通した でもない結果"],
            u"通した P22(対照)": old[u"通した"], u"止めた P22(対照)": old[u"止めた"],
            u"通した の分け方 P23": new[u"通した の分け方"], u"通した の分け方 P22(対照)": old[u"通した の分け方"],
            u"型別 P23": new[u"型別"], u"型別 P22(対照)": old[u"型別"],
            u"対照: P22 の再計算が儀式の記録と違った行": sum(1 for k in set(by_rec) | set(by_old) if by_rec.get(k) != by_old.get(k)),
            u"記録の行数": len(by_rec), u"P22 の行数": len(by_old), u"P23 の行数": len(new_by),
            u"N237・N277 の P23 の結果": dict((i, [x[u"P23"] for x in rows if x[u"id"] == i]) for i in ("N237", "N277")),
            u"素の書類 P23": new[u"素の書類"], u"素の書類 P22": old[u"素の書類"],
            u"素の書類で P22 → P23 で動いた claim": plain_moved,
            u"注入の対象 P23": new[u"注入"][u"注入の対象(GROUNDED の site)"], u"注入の対象 P22": old[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"所要秒": {u"P22": old[u"所要秒"][u"全体"], u"P23": new[u"所要秒"][u"全体"]}}


# ====================================================================================================
# R-2 / R-4
class _InfoTap(object):
    u"""``recipes.build_recipes`` を呼ぶ時に ``info`` を足して、書類の丸め方の判定(R / T / 決めた丸め方)を拾う。engine の file は変えない
    (module の属性を実行中だけ差し替える)。"""

    def __enter__(self):
        self.orig = R.build_recipes
        self.last = None
        tap = self

        def wrapped(zb, profile, info=None):
            d = {} if info is None else info
            out = tap.orig(zb, profile, d)
            tap.last = d
            return out
        R.build_recipes = wrapped
        return self

    def __exit__(self, *a):
        R.build_recipes = self.orig
        if R.build_recipes is not self.orig:
            raise SystemExit(u"**build_recipes を戻せていない。止める**")


def verify_with_info(zb, profile):
    with _InfoTap() as t:
        out = VD.verify_document(zb, profile)
        info = t.last
    return out, {u"丸め方": info.get("rounding"), u"R(round しか説明できない)": info.get("rounding_round_only"),
                 u"T(truncate しか説明できない)": info.get("rounding_truncate_only")}


def r2(doc_ids):
    per_doc, moved = [], []
    tot = collections.Counter()
    missing = []
    for d in doc_ids:
        p = ED.cache_path(d)
        if not os.path.exists(p):
            missing.append(d)
            continue
        with io.open(p, "rb") as fh:
            zb = fh.read()
        a, ia = verify_with_info(zb, OLD)
        b, ib = verify_with_info(zb, NEW)
        if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
            raise SystemExit(u"**claim の id の並びが P22 と P23 で違う: %s。止める**" % d)
        if [c["span"] for c in a["claims"]] != [c["span"] for c in b["claims"]]:
            raise SystemExit(u"**claim の span が P22 と P23 で違う: %s。止める**" % d)
        text = None
        try:
            text = PP.classify_doc(zb)[2]
        except Exception:  # noqa: BLE001
            text = None
        n_moved = 0
        for x, y in zip(a["claims"], b["claims"]):
            tot[u"claims"] += 1
            if x["state"] == "GROUNDED":
                tot[u"P22 の GROUNDED"] += 1
            if claim_key(x) == claim_key(y):
                continue
            n_moved += 1
            ctx = None
            if text and x["span"]:
                i = text.find(x["span"])
                if i >= 0:
                    ctx = text[max(0, i - 20):i + len(x["span"]) + 40]
            moved.append({u"doc": d, u"id": x["id"], u"subject": x["subject"], u"unit": x["unit"], u"value": x["value"], u"span": x["span"],
                          u"文脈": ctx, u"P22": view(x), u"P23": view(y), u"向き": u"%s → %s" % (x["state"], y["state"])})
        per_doc.append({u"doc": d, u"claims": len(a["claims"]), u"動いた": n_moved,
                        u"states P22": a["document"]["states"], u"states P23": b["document"]["states"],
                        u"丸めの判定 P22": ia, u"丸めの判定 P23": ib})
    return {u"書類": per_doc, u"動いた行": moved, u"キャッシュに無い書類": missing, u"総 claim": tot[u"claims"], u"P22 の GROUNDED": tot[u"P22 の GROUNDED"]}


def r2_summary(rec):
    u"""R-2 / R-4 の集計。**書類別と動いた行から数える純関数**(門が記録に同じ関数ではなく独立に当て直す)。"""
    mv = rec[u"動いた行"]
    g2n = [r for r in mv if r[u"P22"][u"state"] == "GROUNDED" and r[u"P23"][u"state"] != "GROUNDED"]
    n2g = [r for r in mv if r[u"P22"][u"state"] != "GROUNDED" and r[u"P23"][u"state"] == "GROUNDED"]
    g2g = [r for r in mv if r[u"P22"][u"state"] == "GROUNDED" and r[u"P23"][u"state"] == "GROUNDED"]
    rate = [r for r in g2n if r[u"unit"] in RATE_UNITS]
    money = [r for r in g2n if r[u"unit"] not in RATE_UNITS]
    docs = rec[u"書類"]
    changed = [d[u"doc"] for d in docs if d[u"丸めの判定 P22"] != d[u"丸めの判定 P23"]]
    changed_mode = [d[u"doc"] for d in docs if d[u"丸めの判定 P22"][u"丸め方"] != d[u"丸めの判定 P23"][u"丸め方"]]
    vm = lambda k: sum(d[k].get("VALUE_MISMATCH", 0) for d in docs)
    gr = lambda k: sum(d[k].get("GROUNDED", 0) for d in docs)
    return {u"動いた(全 state)": len(mv),
            u"GROUNDED → GROUNDED でない": len(g2n),
            u"GROUNDED でない → GROUNDED(新 GROUNDED)": len(n2g),
            u"GROUNDED → GROUNDED(参照先だけ動いた)": len(g2g),
            u"GROUNDED を離れた行の単位別": kv(collections.Counter(r[u"unit"] for r in g2n)),
            u"GROUNDED を離れた行のうち 率(％・%・ポイント)": len(rate),
            u"GROUNDED を離れた行のうち 金額ほか(率でない)": len(money),
            u"GROUNDED を離れた行の向き": kv(collections.Counter(r[u"向き"] for r in g2n)),
            u"GROUNDED を離れた行の書類数": len({r[u"doc"] for r in g2n}),
            u"向き(全部)": kv(collections.Counter(r[u"向き"] for r in mv)),
            u"書類数": len(docs),
            u"丸めの判定が変わった書類(丸め方・R・T のどれか)": changed,
            u"丸め方(round / truncate)が変わった書類": changed_mode,
            u"丸め方 P22(書類数)": kv(collections.Counter(str(d[u"丸めの判定 P22"][u"丸め方"]) for d in docs)),
            u"丸め方 P23(書類数)": kv(collections.Counter(str(d[u"丸めの判定 P23"][u"丸め方"]) for d in docs)),
            u"GROUNDED の合計 P22": gr(u"states P22"), u"GROUNDED の合計 P23": gr(u"states P23"),
            u"VALUE_MISMATCH の合計 P22": vm(u"states P22"), u"VALUE_MISMATCH の合計 P23": vm(u"states P23")}


def r2b(doc_ids):
    u"""R-2 の補助(『金額 0』が自分の欠陥でないことの確かめ): **新しい旗 truncate_abs_band だけ**を P22 に積んだ profile(in-process で登録、出るとき必ず消す)と
    P22 を 67 書類の無改変で比べる。あわせて、旗が効きうる場所の数 = 切り捨てと判定された書類で、負の fact に GROUNDED した金額の claim
    (``recomputed`` < 0、``unit_scale`` あり、札が切り捨て)の数を、P22 の生の claim(``build_raw_claims``)から数える。"""
    import dataclasses
    name = "P22_ABS_ONLY_FOR_MEASURE"
    V.PROFILES[name] = dataclasses.replace(V.PROFILES[OLD], name=name, truncate_abs_band=True)
    moved, opp, opp_docs, n_trunc_docs = [], collections.Counter(), set(), 0
    try:
        for d in doc_ids:
            p = ED.cache_path(d)
            if not os.path.exists(p):
                continue
            with io.open(p, "rb") as fh:
                zb = fh.read()
            a = VD.verify_document(zb, OLD)
            b = VD.verify_document(zb, name)
            for x, y in zip(a["claims"], b["claims"]):
                if claim_key(x) != claim_key(y):
                    moved.append({u"doc": d, u"id": x["id"], u"P22": view(x), u"P22+abs": view(y)})
            info = {}
            raw_num, _raw_text = R.build_raw_claims(zb, V.PROFILES[OLD], info)
            if info.get("rounding") != "truncate":
                continue
            n_trunc_docs += 1
            for c in raw_num:
                if c.get("unit_scale") is None or c.get("result") != "GROUNDED" or c.get("recomputed") is None or c.get("rounding") != "truncate":
                    continue
                if c["recomputed"] < 0:
                    opp[u"負の fact に GROUNDED(切り捨ての書類の金額)"] += 1
                    opp_docs.add(d)
                    opp[u"うち札 %s%s" % (c.get("match"), u"(CF 流量項目。札は abs を落とした梯子で付く)" if c.get("flow_convention") is not None else u"")] += 1
    finally:
        V.PROFILES.pop(name, None)
    if name in V.PROFILES:
        raise SystemExit(u"**登録を戻せていない。止める**")
    return {u"profile": u"P22 に truncate_abs_band だけを in-process で積んだもの(P23 から率の旗を除いたもの)",
            u"動いた行": moved, u"動いた行の数": len(moved), u"切り捨てと判定された書類": n_trunc_docs,
            u"旗が効きうる行(P22 の生の claim から数えた)": kv(opp), u"旗が効きうる行のある書類数": len(opp_docs)}


# ====================================================================================================
# R-3
def r3_doc(doc_id, zb, text0):
    sites, _diag, _b, _o, sentences, _base = PP.find_sites(zb, text0)
    for s in sites:
        s[u"書類"] = doc_id
    rows_old = PB.inject_with_profile(doc_id, zb, text0, sites, sentences, OLD)
    rows_new = PB.inject_with_profile(doc_id, zb, text0, sites, sentences, NEW)
    made = [s for s in sites if s[u"作れた"]]
    if len(rows_old) != len(made) or len(rows_new) != len(made):
        raise SystemExit(u"**注入の行の数が作れた site の数と違う(%s): %d / %d / %d。止める**" % (doc_id, len(rows_old), len(rows_new), len(made)))
    by_old = dict((r[u"id"], r) for r in rows_old)
    out = []
    for r in rows_new:
        o = by_old[r[u"id"]]
        out.append({u"書類": doc_id, u"id": r[u"id"], u"要素": r[u"要素"], u"単位": r[u"単位"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"],
                    u"当期の fact": r[u"当期の fact"], u"前期の fact": r[u"前期の fact"], u"文脈 60 字": r[u"文脈 60 字"],
                    u"P22": {u"結果": o[u"結果"], u"state": o[u"結果の細目"], u"reason": o.get(u"後の reason"), u"pointers": o.get(u"後の pointers")},
                    u"P23": {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers"),
                           u"注入後の文脈": r.get(u"_文")}})
    return out, len(sites), len(made)


def r3_summary(rows):
    u"""R-3 の集計。**行から数える純関数**。"""
    n = len(rows)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    new = collections.Counter(r[u"P23"][u"結果"] for r in rows)
    old = collections.Counter(r[u"P22"][u"結果"] for r in rows)
    p_new, p_old = sum(new[k] for k in passed_kinds), sum(old[k] for k in passed_kinds)
    return {u"注入": n,
            u"P23 の結果": kv(new), u"P22(対照)の結果": kv(old),
            u"P23 で通した(GROUNDED のまま)": frac(p_new, n), u"P22(対照)で通した": frac(p_old, n),
            u"P23 で止めた(VALUE_MISMATCH)": frac(new[PP.K_STOP], n),
            u"P23 でその他": frac(new[PP.K_ELSE], n),
            u"P22 → P23 の遷移": kv(collections.Counter(u"%s → %s" % (r[u"P22"][u"結果"], r[u"P23"][u"結果"]) for r in rows)),
            u"P23 で通した行": [{u"書類": r[u"書類"], u"id": r[u"id"], u"単位": r[u"単位"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"],
                             u"当期の fact": r[u"当期の fact"], u"前期の fact": r[u"前期の fact"]} for r in rows if r[u"P23"][u"結果"] in passed_kinds],
            u"P22 で通して P23 で止めた行": sum(1 for r in rows if r[u"P22"][u"結果"] in passed_kinds and r[u"P23"][u"結果"] not in passed_kinds),
            u"P22 で通さず P23 で通した行": sum(1 for r in rows if r[u"P22"][u"結果"] not in passed_kinds and r[u"P23"][u"結果"] in passed_kinds)}


def r3_vs_period_bind(rows):
    u"""対照の再現: 期を縛る P22 の記録の E1(485 行)の P22 の欄と、(書類, id) ごとに 結果・state・reason・pointers が一致するか。"""
    rec = jload(PERIOD_BIND_REL)[u"E1"][u"行"]
    want = dict(((r[u"書類"], r[u"id"]), r) for r in rec)
    diff = []
    for r in rows:
        w = want.get((r[u"書類"], r[u"id"]))
        o = r[u"P22"]
        if w is None:
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
            continue
        wp = w[u"P22"]
        if (wp[u"結果"], wp[u"state"], wp[u"reason"], wp[u"pointers"]) != (o[u"結果"], o[u"state"], o[u"reason"], o[u"pointers"]):
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
    return {u"記録の行": len(want), u"今回の行": len(rows), u"記録に無い行": sum(1 for r in rows if (r[u"書類"], r[u"id"]) not in want),
            u"違った行": len(diff), u"違った行の id": diff[:20]}


# ====================================================================================================
# R-5
def r5(work):
    rows = PB.e4(work)
    rec = dict(((r[u"doc"], r[u"id"]), r) for r in jload(PERIOD_BIND_REL)[u"E4"][u"行"])
    out = []
    for r in rows:
        w = rec[(r[u"doc"], r[u"id"])]
        out.append({u"doc": r[u"doc"], u"id": r[u"id"], u"注入か": r[u"注入か"], u"注入の型": r[u"注入の型"],
                    u"Core 自身 P22(今回)": r[u"Core 自身 P21(今回)"],       # PB.OLD = P22 なので PB の「P21(今回)」の欄は P22
                    u"Core 自身 P23": r[u"Core 自身 P22"],
                    u"Core 自身 P22(期を縛る P22 の記録)": w[u"Core 自身 P22"]})
    return out


def r5_summary(rows):
    u"""R-5 の集計(行から数える純関数)。"""
    moved = [r for r in rows if r[u"Core 自身 P22(今回)"] != r[u"Core 自身 P23"]]
    ctrl = [r for r in rows if r[u"Core 自身 P22(今回)"] != r[u"Core 自身 P22(期を縛る P22 の記録)"]]
    inj = [r for r in rows if r[u"注入か"]]
    return {u"行": len(rows), u"注入": len(inj),
            u"Core 自身が P22 → P23 で動いた行": len(moved),
            u"動いた行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in moved],
            u"対照: P22 の再計算が期を縛る P22 の記録と違った行": len(ctrl),
            u"全注入で Core 自身 P22 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P22(今回)"][u"state"] == "GROUNDED"), len(inj)),
            u"全注入で Core 自身 P23 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P23"][u"state"] == "GROUNDED"), len(inj)),
            u"T6_PRIOR の注入で Core 自身 P23 が GROUNDED": frac(sum(1 for r in inj if r[u"注入の型"] == "T6_PRIOR" and r[u"Core 自身 P23"][u"state"] == "GROUNDED"),
                                                       sum(1 for r in inj if r[u"注入の型"] == "T6_PRIOR"))}


# ====================================================================================================
# R-6
def numstat():
    out = {}
    for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py"):
        rc, o = git("diff", "--numstat", "HEAD", "--", f)
        p = o.split()
        out[f] = {u"挿入": int(p[0]), u"削除": int(p[1])} if len(p) >= 2 and p[0].isdigit() else {u"挿入": 0, u"削除": 0}
    rc, o = git("diff", "--numstat", "HEAD", "--", "core")
    rc2, st = git("status", "--porcelain", "--", "core")
    out[u"core/"] = {u"差の行数": sum(int(l.split("\t")[0]) + int(l.split("\t")[1]) for l in o.splitlines() if l.split("\t")[0].isdigit()),
                     u"status": st.strip()}
    return out


# ====================================================================================================
def env_block(label_shas):
    bundle, n_files = RIT.engine_bundle_sha256()
    return {u"封": SEAL, u"HEAD": RIT.git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順。変更後)": bundle,
            u"engine の file 数": n_files,
            u"vocabulary.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/vocabulary.py"))[:16],
            u"comparators.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/comparators.py"))[:16],
            u"recipes.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/recipes.py"))[:16],
            u"DEFAULT_PROFILE": V.DEFAULT_PROFILE, u"比べた profile": [OLD, NEW],
            u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
            u"名前が ANTHROPIC/OPENAI/GOOGLE/GEMINI で始まる環境変数の数(値は読まない)": sum(1 for k in os.environ if k.split("_")[0] in ("ANTHROPIC", "OPENAI", "GOOGLE", "GEMINI")),
            u"ラベル 2 file の sha256(起動時に照合)": label_shas,
            u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"費用": u"0 USD"}


def judge(rec):
    u"""封 §2 の R-1〜R-7 の機械的な判定。幅・外れ方は封の字のまま。"""
    J = {}
    if u"R1" in rec:
        e = rec[u"R1"]
        p = e[u"通した P23"]
        ids = [x[u"id"] for x in e[u"通した P23 の一覧"]]
        parts = {u"通した 2〜3": 2 <= p[u"件"] <= 3, u"止めた 237〜238": 237 <= e[u"止めた P23"][u"件"] <= 238,
                 u"N237・N277 は止まる(通した一覧に無い)": "N237" not in ids and "N277" not in ids}
        J[u"R-1"] = {u"実測": u"通した %d / %d(%s)・止めた %d / %d・その他 %d。N237・N277 の結果 %s。対照 P22 の通した %d / %d" % (
            p[u"件"], p[u"分母"], u"・".join(ids), e[u"止めた P23"][u"件"], e[u"止めた P23"][u"分母"], sum(e[u"その他 P23"].values()),
            json.dumps(e[u"N237・N277 の P23 の結果"], ensure_ascii=False), e[u"通した P22(対照)"][u"件"], e[u"通した P22(対照)"][u"分母"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"R2" in rec:
        s = rec[u"R2"][u"集計"]
        n = s[u"GROUNDED → GROUNDED でない"]
        parts = {u"GROUNDED を離れる行 6〜12": 6 <= n <= 12,
                 u"うち金額 0": s[u"GROUNDED を離れた行のうち 金額ほか(率でない)"] == 0,
                 u"全部 率(％・ポイント)": s[u"GROUNDED を離れた行のうち 率(％・%・ポイント)"] == n,
                 u"新 GROUNDED 0": s[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == 0,
                 u"書類ごとの丸め方の判定が 1 つも変わらない": not s[u"丸めの判定が変わった書類(丸め方・R・T のどれか)"]}
        J[u"R-2"] = {u"実測": u"67 書類(実数 %d)の無改変で動いた行 %d・GROUNDED を離れた %d(率 %d・金額 %d、単位別 %s)・新 GROUNDED %d・参照先だけ動いた %d・丸めの判定が変わった書類 %d(丸め方が変わった %d)" % (
            s[u"書類数"], s[u"動いた(全 state)"], n, s[u"GROUNDED を離れた行のうち 率(％・%・ポイント)"], s[u"GROUNDED を離れた行のうち 金額ほか(率でない)"],
            json.dumps(s[u"GROUNDED を離れた行の単位別"], ensure_ascii=False), s[u"GROUNDED でない → GROUNDED(新 GROUNDED)"],
            s[u"GROUNDED → GROUNDED(参照先だけ動いた)"], len(s[u"丸めの判定が変わった書類(丸め方・R・T のどれか)"]), len(s[u"丸め方(round / truncate)が変わった書類"])),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"R3" in rec:
        s = rec[u"R3"][u"集計"]
        p = s[u"P23 で通した(GROUNDED のまま)"]
        J[u"R-3"] = {u"実測": u"通した %d / %d・止めた %d・その他 %d。対照 P22 の通した %d" % (
            p[u"件"], p[u"分母"], s[u"P23 で止めた(VALUE_MISMATCH)"][u"件"], s[u"P23 でその他"][u"件"], s[u"P22(対照)で通した"][u"件"]),
            u"判定": u"当たり" if 0 <= p[u"件"] <= 2 else u"外れ"}
    if u"R2" in rec:
        s = rec[u"R2"][u"集計"]
        v22, v23 = s[u"VALUE_MISMATCH の合計 P22"], s[u"VALUE_MISMATCH の合計 P23"]
        J[u"R-4"] = {u"実測": u"無改変の VALUE_MISMATCH P22 %s → P23 %s(差 %d)" % (format(v22, ","), format(v23, ","), v23 - v22),
                   u"判定": u"当たり" if 1416 <= v23 <= 1422 else u"外れ"}
    if u"R5" in rec:
        s = rec[u"R5"][u"集計"]
        J[u"R-5"] = {u"実測": u"段 2 の材料 %d 行の Core 自身 P22 → P23 で動いた行 %d(対照: P22 の再計算が期を縛る P22 の記録と違った行 %d)" % (
            s[u"行"], s[u"Core 自身が P22 → P23 で動いた行"], s[u"対照: P22 の再計算が期を縛る P22 の記録と違った行"]),
            u"判定": u"当たり" if s[u"Core 自身が P22 → P23 で動いた行"] == 0 else u"外れ"}
    if u"R6" in rec:
        e = rec[u"R6"]
        r = e[u"engine の差分"]
        v, c, rc = (r["adapters/xbrl/vocabulary.py"], r["adapters/xbrl/comparators.py"], r["adapters/xbrl/recipes.py"])
        tests_ok = all(t[u"rc"] == 0 for t in e.get(u"既存試験", []))
        parts = {u"vocabulary.py 挿入 ≤ 20": v[u"挿入"] <= 20, u"comparators.py 挿入 ≤ 10": c[u"挿入"] <= 10, u"recipes.py 挿入 ≤ 10": rc[u"挿入"] <= 10,
                 u"core/ 0 行": r[u"core/"][u"差の行数"] == 0,
                 u"登録の一覧の試験 4 か所に P23 を足す以外の既存試験は全部緑(直した既存試験が 4 か所のほかに無い)": bool(e.get(u"既存試験")) and tests_ok and not e.get(u"封の 4 か所のほかに直した既存試験")}
        J[u"R-6"] = {u"実測": u"vocabulary.py 挿入 %d・削除 %d、comparators.py 挿入 %d・削除 %d、recipes.py 挿入 %d・削除 %d、core/ %d 行。既存試験 %s。4 か所のほかに直した既存試験 %d" % (
            v[u"挿入"], v[u"削除"], c[u"挿入"], c[u"削除"], rc[u"挿入"], rc[u"削除"], r[u"core/"][u"差の行数"],
            u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e.get(u"既存試験", [])) or u"(この実行では走らせていない)",
            len(e.get(u"封の 4 か所のほかに直した既存試験", []))),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    J[u"R-7"] = {u"実測": u"段 2(既定 P22 → P23。P24・P25 とまとめて)は人間の承認の後。この実行では何も変えていない(DEFAULT_PROFILE = %s)" % V.DEFAULT_PROFILE,
               u"判定": u"判定しない(段 2)"}
    return J


def inputs_block(doc_ids_67):
    d = {}
    for rel in (RITUAL_REL, PERIOD_BIND_REL, S2_MATERIAL_REL, S2_REC_REL):
        d[rel] = sha_file(os.path.join(ROOT, RITUAL_P22_FILE if rel == RITUAL_REL else rel))
    d[u"seat answers(hybrid_s2_answers)"] = dict((fn, sha_file(os.path.join(PB.HS2.ANS_DIR, fn))) for fn in sorted(os.listdir(PB.HS2.ANS_DIR)) if fn.endswith("_answer.json"))
    d[u"儀式の同梱書類"] = sha_file(os.path.join(ROOT, RIT.ZIP_REL))
    d[u"書類 67(経営分析の文を持つ)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_67 if os.path.exists(ED.cache_path(x)))
    return d


def run(stage, only_docs=None, run_tests=False, progress=None):
    t_all = time.time()
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        raise SystemExit(2)
    zips = PP.list_zips()
    if only_docs:
        zips = [(d, p) for d, p in zips if d in only_docs]
    texts = {}
    for doc_id, path in zips:
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts[doc_id] = (zb, text)
    ids67 = sorted(texts)
    rec = {u"step": u"**丸めの帯を片側にする P23 の段 1 の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"環境": env_block(label_shas), u"書類の数": {u"経営分析の文を持つ": len(ids67)}}
    secs = {}
    if stage in ("r1", "all"):
        t = time.time()
        rec[u"R1"] = r1(label_shas)
        secs[u"R1"] = round(time.time() - t, 1)
    if stage in ("r2", "all"):
        t = time.time()
        r = r2(ids67)
        rec[u"R2"] = dict(r, **{u"集計": r2_summary(r)})
        secs[u"R2"] = round(time.time() - t, 1)
    if stage in ("r2b", "all"):
        t = time.time()
        rec[u"R2b"] = r2b(ids67)
        secs[u"R2b"] = round(time.time() - t, 1)
    if stage in ("r3", "all"):
        t = time.time()
        rows, per = [], []
        for d in ids67:
            zb, text = texts[d]
            r, ns, nm = r3_doc(d, zb, text)
            rows.extend(r)
            per.append({u"書類": d, u"site": ns, u"作れた": nm})
            if progress:
                progress(u"R-3 %s site %d 作れた %d" % (d, ns, nm))
        rec[u"R3"] = {u"書類別": per, u"行": rows, u"集計": r3_summary(rows),
                      u"対照: P22 の再計算と期を縛る P22 の記録": (r3_vs_period_bind(rows) if not only_docs else None)}
        secs[u"R3"] = round(time.time() - t, 1)
    if stage in ("r5", "all"):
        t = time.time()
        work = tempfile.mkdtemp(prefix="rounding_r5_")
        try:
            rows = r5(work)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
        rec[u"R5"] = {u"行": rows, u"集計": r5_summary(rows)}
        secs[u"R5"] = round(time.time() - t, 1)
    if stage in ("r6", "all"):
        t = time.time()
        e6 = {u"engine の差分": numstat()}
        if run_tests:
            e6[u"既存試験"] = [PB.run_pytest("tests/adapters/xbrl")]
        e6[u"封の 4 か所のほかに直した既存試験"] = EXTRA_EXISTING_FIXES
        rec[u"R6"] = e6
        secs[u"R6"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"入力の sha256"] = inputs_block(ids67)
    rec[u"予測の判定"] = judge(rec)
    rec[u"limits"] = [
        u"手元の cache の 67 書類(経営分析の文を持つ)。無作為ではない。別の書類では動く行が増えうる。",
        u"R-2 の『動いた』は (state, pointers, reason, recomputed, form) の組が P22 と P23 で違った claim。正しさは人の読み(結果文書)。",
        u"R-1 の儀式は同梱 1 書類(S100Z4Q1)。注入は型 V1(最小の桁の 1 字を変える)・V2(値を ±1 最小単位)だけ。",
        u"R-3 の 485 件は『前期の値がそのまま書かれる』誤りだけ(穴 B の限界を引き継ぐ)。site は P21 の土台で選んだ。",
        u"率の帯(1 桁で ±0.06)は、提出者が表示の桁の金額から率を出した型を落とす(封 §3)。退化値(0 → 00)は帯では止まらない。",
        u"書類ごとの丸め方の判定(R / T)は build_recipes の info から拾った(engine の file は変えない)。",
        u"R-5 の Core 自身は cd8 の材料 script と同じ claim の対の付け方の再現(期を縛る P22 の測定の道具をそのまま使った)。α 型(verify_external)は profile を取らない経路なので測っていない。",
        u"R-6 の既存試験は tests/adapters/xbrl だけ(tests/measure は結果文書に別に書く)。",
        u"前々期の値への置き換えは P23 でも通る(P22 の限界のまま)。"]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"P23 の段 1 の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["r1", "r2", "r2b", "r3", "r5", "r6", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--run-tests", action="store_true", help=u"R-6 で tests/adapters/xbrl の pytest も走らせて記録する(約 20 分)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, run_tests=a.run_tests,
              progress=lambda m: print(m, file=sys.stderr))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 丸めの帯 P23 の段 1(%s → %s・手元の cache・鍵なし・0 USD)===" % (OLD, NEW))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
