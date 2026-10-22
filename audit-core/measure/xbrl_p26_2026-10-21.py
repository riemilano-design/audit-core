# -*- coding: utf-8 -*-
u"""「違う」に出る正しい文の主因を減らす P26 の段 1 の測定 ― 封 ``docs/XBRL_P26_SEAL_2026-10-21.md`` §2(Q-1〜Q-8。Q-8 は段 2 なので判定しない)。

    cd audit-core
    python3 measure/xbrl_p26_2026-10-21.py --stage all --readings <読みの file> --mutations <変異の表> --out fixtures/xbrl/p26_2026-10-21.json
    python3 measure/xbrl_p26_2026-10-21.py --stage q1 --out <file> --docs S100YYK8              # 軽い走らせ直し(--out 必須)
    python3 measure/xbrl_p26_2026-10-21.py --stage dossier --out <file>                         # 人が読むための材料(Q-2 の行)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。
engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**。穴 B の道具・儀式・段 2 の材料は P25 の測定(``measure/xbrl_lastbranch_2026-10-21.py``)
経由で import して使う(書き直さない)。比べる 2 つは **P25(対照)と P26** で、どちらも明示して呼ぶ(既定が動いても同じ数が出る)。
旗ごとの効きは、この script の中で ``dataclasses.replace`` した profile を ``vocabulary.PROFILES`` に**実行中だけ**足して測る(engine には登録しない)。

  Q-1  経営分析の文を持つ 67 書類の無改変を P25 と P26 で ``verify_document`` し、claim ごとに ``(state, pointers, reason, recomputed, form)`` と値・span・単位を比べる。
       VALUE_MISMATCH の合計・新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED)・GROUNDED から外れた行・動いた行の向き。
  Q-2  「違う」(VALUE_MISMATCH)から外れた行の全部の人(エージェント)の読み(正しい文 / 文が本当に違う / 分からない)。
  Q-3  穴 B の 485 件・儀式(同梱の 1 書類)・段 2 の材料(24 行 × 8 書類)。数の読み取りで儀式の表から消える円銭の注入は手で当てる。
  Q-4  動いた全行の文の数を 1 回に 1 件だけ変える注入(末尾の桁 ±3・10 倍)で P26 が GROUNDED にする数。
  Q-5  P25 で GROUNDED の差の主張(pointer に ``formula:a-b``)の文の数を末尾の桁 ±1 に 1 回に 1 件だけ変え、P25 が止めて P26 が GROUNDED にした行(新しい GROUNDED)。
  Q-6  engine の差分の行数(``git diff HEAD --numstat``)と、既存試験で赤になった試験の種類。
  Q-7  報告形(``report_customer``)で P26 明示の 67 書類の「違う」の節と、3 つの理由の節、登録簿の理由の網羅。
  Q-8  段 2。この実行では判定しない。段 2 に見せる数は記録に置く。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import dataclasses
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import platform
import re
import sys
import tempfile
import time
import unicodedata

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


LB = _mod("measure/xbrl_lastbranch_2026-10-21.py", "lastbranch_for_p26")
PB, PP, RIT, FP = LB.PB, LB.PP, LB.RIT, LB.FP
OLD, NEW = "P25", "P26"
# LB・PB の道具は module の OLD / NEW を呼ぶ時に読む。ここで P25(対照)/ P26 に差し替える(この script の中だけ)。
LB.OLD, LB.NEW = OLD, NEW
PB.OLD, PB.NEW = OLD, NEW

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import instance as I          # noqa: E402
from adapters.xbrl import recipes as R           # noqa: E402
from adapters.xbrl import registry_setup as RS   # noqa: E402
from adapters.xbrl import report_customer as RC  # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_P26_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/p26_2026-10-21.json"
LASTBRANCH_REL = "fixtures/xbrl/lastbranch_2026-10-21.json"       # 対照の P25 の記録
REPORT_FIX_MEASURE_REL = "measure/xbrl_customer_report_fix_2026-10-21.py"
KEY_NAMES = PB.KEY_NAMES
pct, frac, sha_file, jload, git = PB.pct, PB.frac, PB.sha_file, PB.jload, PB.git
claim_key, view = PB.claim_key, PB.view

READ_OK, READ_WRONG, READ_UNSURE = LB.READ_OK, LB.READ_WRONG, LB.READ_UNSURE
READ_WORDS = LB.READ_WORDS
#: 読みの語。Q-2(「違う」から外れた行): 正しい文(道具が出した「違う」が偽 ― 名指した fact が文の参照先でない、または参照先と文が帯で合う)/
#: 文が本当に違う(名指した fact が文の参照先で、値が帯の外 ― 「違う」が正しかった = 弱めた代価)/ 分からない。
#: Q-2b(GROUNDED から外れた行): 偶然の一致(向きの語が主語でなく要因の項目にかかる文を、主語の増減と照合して合っていた)/
#: 正しい結びを失った(文の主張が正しく検証されていたのに外れた = 代価)/ 分からない。
READ_COINCIDENCE, READ_LOST = u"偶然の一致", u"正しい結びを失った"
READ_WORDS_2B = (READ_COINCIDENCE, READ_LOST, READ_UNSURE)
WORDS_OF = {u"Q2": READ_WORDS, u"Q2b": READ_WORDS_2B}
REASONS = ("other_concept", "direction_on_cause_item", "rounded_diff_within_double_band")
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py",
                "adapters/xbrl/registry_setup.py", "adapters/xbrl/report_customer.py")
FLAG_NAMES = ("concept_gate", "last_branch_digit_needs_size", "rounded_diff_hold", "cause_item_direction", "numbers_2026_10_21")
FLAG_PROFILES = (("G1", "P26_only_concept_gate"), ("G2", "P26_only_last_branch_digit_needs_size"), ("G3", "P26_only_rounded_diff_hold"),
                 ("G4", "P26_only_cause_item_direction"), ("G5", "P26_only_numbers_2026_10_21"))

_REL = {"P24": "P25", "P25": "P26"}


def relabel_key(k):
    u"""LB の道具は profile 名を P24(対照)・P25 と字で持つ。ここでは対照が P25、比べる側が P26 なので、キーだけ 1 回で読み替える(同時置換)。"""
    return re.sub(r"P2[45]", lambda m: _REL[m.group(0)], k) if isinstance(k, str) else k


def relabel(x):
    if isinstance(x, dict):
        return dict((relabel_key(k), relabel(v)) for k, v in x.items())
    if isinstance(x, list):
        return [relabel(v) for v in x]
    return x


def kv(d):
    return dict(sorted(d.items()))


def register_flag_profiles():
    u"""旗 1 つずつの profile を、この process の ``V.PROFILES`` に足す(engine の file には 1 字も書かない)。"""
    base = V.PROFILES[OLD]
    p26 = V.PROFILES[NEW]
    for (g, name), flag in zip(FLAG_PROFILES, FLAG_NAMES):
        V.PROFILES[name] = dataclasses.replace(base, name=name, **{flag: getattr(p26, flag)})


def unregister_flag_profiles():
    for _g, name in FLAG_PROFILES:
        V.PROFILES.pop(name, None)


# ====================================================================================================
# 道具: raw claim を拾う
class _Tap(LB._RawTap):
    pass


EXTRA_KEYS = ("reason", "cause_item", "other_concept", "concept_gate", "rounded_diff_hold", "last_branch_digit_floor", "last_branch_evidence",
              "no_same_value", "subject_from", "match", "claim_scale", "unit_scale", "rounding", "sentence", "pos")


def _dossier(inst, r, x, y, sent):
    if y["value"] is None or y["unit"] not in V.UNIT_SCALE:
        return {}
    try:
        return LB.dossier(inst, dict(r, pointer=(y["pointers"] or x["pointers"] or [None])[0],
                                     recomputed=y["recomputed"] if y["recomputed"] is not None else x["recomputed"]), sent, y["value"], y["unit"])
    except Exception as e:      # 読むための材料だけ。判定には使わない
        return {u"dossier の失敗": repr(e)}


def plain_doc(doc_id, zb):
    u"""1 書類の無改変を P25(対照)と P26 で。claim の id の並びが同じなら、値・span・単位が変わった行(数の読み取り G5)も止めずに数える。"""
    inst = I.load_instance(zb)
    with LB._RawTap() as tap:
        a, ra, _sa = LB.verify_raw(tap, zb, OLD)
        b, rb, sb = LB.verify_raw(tap, zb, NEW)
    if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
        raise SystemExit(u"**claim の id の並びが %s と %s で違う: %s。止める**" % (OLD, NEW, doc_id))
    moved, reread = [], []
    for x, y in zip(a["claims"], b["claims"]):
        r = rb.get(y["id"], {})
        ro = ra.get(x["id"], {})
        si = r.get("sentence")
        sent = sb[si] if (si is not None and si < len(sb)) else u""
        read_changed = (x["value"], x["span"], x["unit"]) != (y["value"], y["span"], y["unit"])
        if read_changed:
            reread.append({u"doc": doc_id, u"id": x["id"],
                           u"P25": {u"value": x["value"], u"unit": x["unit"], u"span": x["span"], u"state": x["state"]},
                           u"P26": {u"value": y["value"], u"unit": y["unit"], u"span": y["span"], u"state": y["state"]}})
        if claim_key(x) == claim_key(y) and x["subject"] == y["subject"] and not read_changed:
            continue
        direction = (u"非G→G" if (x["state"] != "GROUNDED" and y["state"] == "GROUNDED") else
                     u"G→非G" if (x["state"] == "GROUNDED" and y["state"] != "GROUNDED") else
                     u"G→G" if x["state"] == "GROUNDED" else u"非G→非G")
        moved.append({u"doc": doc_id, u"id": x["id"], u"kind": y["kind"], u"subject": y["subject"], u"unit": y["unit"], u"value": y["value"],
                      u"word": y["word"], u"span": y["span"], u"向き": direction, u"P25": view(x), u"P26": view(y), u"読みが変わった": read_changed,
                      u"P25 の値": x["value"], u"P25 の単位": x["unit"],
                      u"raw P26": dict((k, r.get(k)) for k in EXTRA_KEYS if r.get(k) is not None),
                      u"raw P25": dict((k, ro.get(k)) for k in EXTRA_KEYS if ro.get(k) is not None),
                      u"sentence": r.get("sentence"), u"pos": r.get("pos"), u"文": sent[:400],
                      u"dossier": _dossier(inst, r, x, y, sent)})
    per = {u"doc": doc_id, u"claims": len(a["claims"]), u"動いた": len(moved), u"読みが変わった": len(reread),
           u"states P25": a["document"]["states"], u"states P26": b["document"]["states"]}
    return per, moved, reread


def flag_doc(doc_id, zb):
    u"""旗 1 つずつ(P25 + その旗だけ)の state の分布と P25 から動いた行の数・向き。"""
    base = VD.verify_document(zb, OLD, None)
    out = {}
    for g, name in FLAG_PROFILES:
        o = VD.verify_document(zb, name, None)
        if [c["id"] for c in o["claims"]] != [c["id"] for c in base["claims"]]:
            raise SystemExit(u"**claim の id の並びが違う(旗 %s): %s。止める**" % (g, doc_id))
        mv = collections.Counter()
        for x, y in zip(base["claims"], o["claims"]):
            if claim_key(x) != claim_key(y) or (x["value"], x["span"], x["unit"]) != (y["value"], y["span"], y["unit"]):
                mv[u"%s(%s) → %s(%s)" % (x["state"], x["reason"], y["state"], y["reason"])] += 1
        out[g] = {u"states": o["document"]["states"], u"動いた向き": dict(mv)}
    return {u"doc": doc_id, u"states P25": base["document"]["states"], u"旗": out}


def plain_summary(rec):
    u"""Q-1 の集計。**書類別と行から数える純関数**(門が記録に独立に当て直す)。"""
    mv = rec[u"動いた行"]
    docs = rec[u"書類"]
    st = lambda k, s: sum(d[k].get(s, 0) for d in docs)
    new_g = [r for r in mv if r[u"P25"][u"state"] != "GROUNDED" and r[u"P26"][u"state"] == "GROUNDED"]
    out_g = [r for r in mv if r[u"P25"][u"state"] == "GROUNDED" and r[u"P26"][u"state"] != "GROUNDED"]
    return {u"書類数": len(docs), u"総 claim": sum(d[u"claims"] for d in docs), u"動いた(全 state)": len(mv),
            u"向き(全部)": kv(collections.Counter(u"%s(%s) → %s(%s)" % (r[u"P25"][u"state"], r[u"P25"][u"reason"], r[u"P26"][u"state"], r[u"P26"][u"reason"]) for r in mv)),
            u"GROUNDED の合計 P25": st(u"states P25", "GROUNDED"), u"GROUNDED の合計 P26": st(u"states P26", "GROUNDED"),
            u"VALUE_MISMATCH の合計 P25": st(u"states P25", "VALUE_MISMATCH"), u"VALUE_MISMATCH の合計 P26": st(u"states P26", "VALUE_MISMATCH"),
            u"UNVERIFIABLE の合計 P25": st(u"states P25", "UNVERIFIABLE"), u"UNVERIFIABLE の合計 P26": st(u"states P26", "UNVERIFIABLE"),
            u"POINTER_NOT_FOUND の合計 P25": st(u"states P25", "POINTER_NOT_FOUND"), u"POINTER_NOT_FOUND の合計 P26": st(u"states P26", "POINTER_NOT_FOUND"),
            u"新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED)": len(new_g),
            u"GROUNDED から外れた行(P25 が GROUNDED で P26 が GROUNDED でない)": len(out_g),
            u"「違う」から外れた行(P25 が VALUE_MISMATCH で P26 が違う)": sum(1 for r in mv if r[u"P25"][u"state"] == "VALUE_MISMATCH" and r[u"P26"][u"state"] != "VALUE_MISMATCH"),
            u"読みだけ変わった行(G5)": sum(1 for r in mv if r[u"読みが変わった"] and r[u"P25"] == r[u"P26"]),
            u"読みが変わった行(全部)": sum(d[u"読みが変わった"] for d in docs)}


def q2_rows(moved):
    u"""Q-2 の行 = P25 が VALUE_MISMATCH で P26 が VALUE_MISMATCH でない行。Q-2b = P25 が GROUNDED で P26 が GROUNDED でない行(読む)。"""
    q2 = [r for r in moved if r[u"P25"][u"state"] == "VALUE_MISMATCH" and r[u"P26"][u"state"] != "VALUE_MISMATCH"]
    q2b = [r for r in moved if r[u"P25"][u"state"] == "GROUNDED" and r[u"P26"][u"state"] != "GROUNDED"]
    return q2, q2b


def attach_readings(rec, readings):
    u"""``readings`` = {"Q2": {"doc:id": {"読み","根拠"}}, "Q2b": {...}} を行に写す。**行と読みは 1 対 1**(足りない・余る・語が違うは止める)。"""
    for part in (u"Q2", u"Q2b"):
        rows = rec[part][u"行"]
        want = set(u"%s:%s" % (r[u"doc"], r[u"id"]) for r in rows)
        got = set(readings.get(part, {}))
        if want != got or len(want) != len(rows):
            raise SystemExit(u"**読みと行が 1 対 1 でない(%s): 行 %d に読み %d(足りない %d・余り %d)。止める**" % (
                part, len(want), len(got), len(want - got), len(got - want)))
        for r in rows:
            x = readings[part][u"%s:%s" % (r[u"doc"], r[u"id"])]
            if x[u"読み"] not in WORDS_OF[part] or not x.get(u"根拠"):
                raise SystemExit(u"**読みの語か根拠が無い: %s %s**" % (r[u"doc"], r[u"id"]))
            r[u"読み"], r[u"根拠"] = x[u"読み"], x[u"根拠"]


def reading_summary(rows):
    c = collections.Counter(r.get(u"読み") for r in rows)
    n = len(rows)
    return {u"行": n, READ_OK: c.get(READ_OK, 0), READ_WRONG: c.get(READ_WRONG, 0), READ_UNSURE: c.get(READ_UNSURE, 0), u"未読": c.get(None, 0),
            READ_COINCIDENCE: c.get(READ_COINCIDENCE, 0), READ_LOST: c.get(READ_LOST, 0),
            u"文が本当に違う の率": frac(c.get(READ_WRONG, 0), n)}


# ====================================================================================================
# Q-3
def hole_b_summary(rows):
    n = len(rows)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    new = collections.Counter(r[u"P26"][u"結果"] for r in rows)
    old = collections.Counter(r[u"P25"][u"結果"] for r in rows)
    stop2conf = [r for r in rows if r[u"P25"][u"結果"] == PP.K_STOP and r[u"P26"][u"state"] == "POINTER_NOT_FOUND"]
    stop2unv = [r for r in rows if r[u"P25"][u"結果"] == PP.K_STOP and r[u"P26"][u"state"] == "UNVERIFIABLE"]
    return {u"注入": n, u"P26 の結果": kv(new), u"P25(対照)の結果": kv(old),
            u"P26 で通した(GROUNDED のまま)": frac(sum(new[k] for k in passed_kinds), n),
            u"P25(対照)で通した": frac(sum(old[k] for k in passed_kinds), n),
            u"P25 の止め": frac(old[PP.K_STOP], n), u"P26 で止めた(VALUE_MISMATCH)": frac(new[PP.K_STOP], n),
            u"止め(P25 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移る": frac(len(stop2conf) + len(stop2unv), old[PP.K_STOP]),
            u"要確認に移る行": [{u"書類": r[u"書類"], u"id": r[u"id"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"], u"文脈 60 字": r[u"文脈 60 字"],
                          u"P26 の state": r[u"P26"][u"state"], u"P26 の reason": r[u"P26"][u"reason"]} for r in stop2conf + stop2unv],
            u"P25 と P26 で(結果, state, reason, pointers)のどれかが違う行": sum(1 for r in rows if r[u"P25"] != r[u"P26"])}


def hole_b_vs_lastbranch(rows):
    u"""対照の再現: P25 の記録(lastbranch_2026-10-21.json の L4)の 485 行の P25 の欄と、今回の P25(対照)が一致するか。"""
    want = dict(((r[u"書類"], r[u"id"]), r[u"P25"]) for r in jload(LASTBRANCH_REL)[u"L4"][u"行"])
    diff = []
    for r in rows:
        w = want.get((r[u"書類"], r[u"id"]))
        o = r[u"P25"]
        if w is None or (w[u"結果"], w[u"state"], w[u"reason"], w[u"pointers"]) != (o[u"結果"], o[u"state"], o[u"reason"], o[u"pointers"]):
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
    return {u"記録の行": len(want), u"今回の行": len(rows), u"記録に無い行": sum(1 for r in rows if (r[u"書類"], r[u"id"]) not in want),
            u"違った行": len(diff), u"違った行の id": diff[:20]}


def ritual(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    old = RIT.build(zb, OLD, label_shas)
    new = RIT.build(zb, NEW, label_shas)
    rec = jload(LASTBRANCH_REL)[u"L5"]
    key = lambda x: (x[u"id"], x[u"型"])
    by_rec = dict((key(x), x[u"P25"]) for x in rec[u"行"])
    by_old = dict((key(x), x[u"結果"]) for x in old[u"注入の一覧"])
    by_new = dict((key(x), x[u"結果"]) for x in new[u"注入の一覧"])
    rows = [{u"id": k[0], u"型": k[1], u"P25": by_old.get(k), u"P26": by_new.get(k)} for k in sorted(set(by_old) | set(by_new))]
    gone = [r for r in rows if r[u"P26"] is None]
    return {u"行": rows,
            u"通した P26 の一覧": [{u"id": x[u"id"], u"型": x[u"型"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"], u"単位": x[u"単位"],
                               u"分類": x[u"分類"], u"値の差": x[u"値の差"], u"1 最小単位": x[u"1 最小単位"], u"文脈": x[u"文脈"]} for x in new[u"通した の一覧"]],
            u"通した P26": new[u"通した"], u"止めた P26": new[u"止めた"], u"その他 P26": new[u"止めた でも 通した でもない結果"],
            u"通した P25(対照)": old[u"通した"], u"止めた P25(対照)": old[u"止めた"],
            u"対照: P25 の再計算が P25 の記録の L5 と違った行": sum(1 for k in set(by_rec) | set(by_old) if by_rec.get(k) != by_old.get(k)),
            u"記録の行数": len(by_rec), u"P25 の行数": len(by_old), u"P26 の行数": len(by_new),
            u"素の書類 P26": new[u"素の書類"], u"素の書類 P25": old[u"素の書類"],
            u"手で当てた(P26 の表から消えた行)": ritual_by_hand(zb, gone, old),
            u"所要秒": {u"P25": old[u"所要秒"][u"全体"], u"P26": new[u"所要秒"][u"全体"]}}


def ritual_by_hand(zb, gone, old_build):
    u"""数の読み取り(G5)で P26 の儀式の表から消えた注入(P25 の表には在る)を、P25 の表の「元の字 → 後の字」のまま P26 で当てる。"""
    text0 = FP.mdna_text(zb)
    sentences, sites = FP.number_sites(text0, V.PROFILES[OLD])
    by_site = dict((s["id"], s) for s in sites)
    old_rows = dict(((x[u"id"], x[u"型"]), x) for x in old_build[u"注入の一覧"])
    out = []
    for g in gone:
        x = old_rows[(g[u"id"], g[u"型"])]
        s = by_site[g[u"id"]]
        row = {u"id": g[u"id"], u"型": g[u"型"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"], u"P25 の結果": x[u"結果"]}
        sent = sentences[s["si"]]
        new_sent = sent[:s["a"]] + x[u"後の字"] + sent[s["b"]:]
        pos = text0.find(sent)
        text = text0[:pos] + new_sent + text0[pos + len(sent):]
        plain = VD.verify_document(zb, NEW, text0)
        p0 = dict((c["id"], c) for c in plain["claims"])[g[u"id"]]
        o = VD.verify_document(zb, NEW, text)
        c = dict((cc["id"], cc) for cc in o["claims"]).get(g[u"id"])
        row[u"素の書類の P26"] = {u"state": p0["state"], u"value": p0["value"], u"span": p0["span"]}
        row[u"当てた後の P26"] = None if c is None else {u"state": c["state"], u"reason": c["reason"], u"value": c["value"], u"span": c["span"]}
        row[u"結果"] = (u"主張が見つからない" if c is None else u"PASSED" if c["state"] == "GROUNDED" else u"detected:%s" % c["state"])
        out.append(row)
    return out


def ritual_summary(rec):
    both = [r for r in rec[u"行"] if r[u"P25"] is not None and r[u"P26"] is not None]
    stop2conf = [r for r in both if r[u"P25"] == "detected:VALUE_MISMATCH" and r[u"P26"] in ("detected:POINTER_NOT_FOUND", "detected:UNVERIFIABLE")]
    passed = [r for r in rec[u"行"] if r[u"P26"] == "PASSED"]
    hand = rec[u"手で当てた(P26 の表から消えた行)"]
    return {u"P26 の行": sum(1 for r in rec[u"行"] if r[u"P26"] is not None), u"P25 の行": sum(1 for r in rec[u"行"] if r[u"P25"] is not None),
            u"共通の行": len(both), u"P26 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P25"] is None),
            u"P25 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P26"] is None),
            u"P26 の PASSED": len(passed), u"注入の止めが要確認に移った(共通の行)": len(stop2conf),
            u"移った行の型": kv(collections.Counter(r[u"型"] for r in stop2conf)),
            u"移った行の id": [u"%s %s" % (r[u"id"], r[u"型"]) for r in stop2conf],
            u"共通の行で結果が違う行": sum(1 for r in both if r[u"P25"] != r[u"P26"]),
            u"遷移(共通の行)": kv(collections.Counter(u"%s → %s" % (r[u"P25"], r[u"P26"]) for r in both if r[u"P25"] != r[u"P26"])),
            u"手で当てた行": len(hand), u"手で当てて通した": sum(1 for r in hand if r[u"結果"] == "PASSED"),
            u"手で当てた結果": kv(collections.Counter(r[u"結果"] for r in hand))}


def s2(work):
    return relabel(LB.s2(work))


def s2_summary(rows):
    moved = [r for r in rows if r[u"Core 自身 P25"] != r[u"Core 自身 P26"]]
    inj = [r for r in rows if r[u"注入か"]]
    stop2conf = [r for r in inj if r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH" and r[u"Core 自身 P26"][u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE")]
    return {u"行": len(rows), u"注入": len(inj), u"無改変": len(rows) - len(inj),
            u"Core 自身が P25 → P26 で動いた行": len(moved), u"動いた行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in moved],
            u"動いた行の遷移": kv(collections.Counter(u"%s(%s) → %s" % (r[u"Core 自身 P25"][u"state"], u"注入" if r[u"注入か"] else u"無改変", r[u"Core 自身 P26"][u"state"]) for r in moved)),
            u"全注入で Core 自身 P25 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "GROUNDED"), len(inj)),
            u"全注入で Core 自身 P26 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P26"][u"state"] == "GROUNDED"), len(inj)),
            u"注入の P25 の止め(VALUE_MISMATCH)": sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH"),
            u"注入の止めのうち要確認に移る": len(stop2conf), u"要確認に移る注入の型": kv(collections.Counter(str(r[u"注入の型"]) for r in stop2conf)),
            u"要確認に移る行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in stop2conf],
            u"無改変で P25 の VALUE_MISMATCH": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH"),
            u"無改変で P26 の VALUE_MISMATCH": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P26"][u"state"] == "VALUE_MISMATCH")}


def s2_vs_lastbranch(rows):
    rec = jload(LASTBRANCH_REL)[u"L6"][u"行"]
    want = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P25"]) for r in rec)
    diff = [r for r in rows if want.get((r[u"doc"], r[u"id"])) != r[u"Core 自身 P25"]]
    return {u"記録の行": len(want), u"今回の行": len(rows), u"違った行": len(diff)}


# ====================================================================================================
# Q-4(動いた全行への注入)
def injection_summary(rows, n_target):
    done = [x for x in rows if x.get(u"変え方")]
    st = lambda x, prof: x[prof].get(u"state") or x[prof].get(u"結果")
    valid = [x for x in done if x[OLD].get(u"state") is not None and x[NEW].get(u"state") is not None]
    tally = lambda prof, xs: kv(collections.Counter(u"%s:%s" % (x[u"変え方"], st(x, prof)) for x in xs))
    cnt = lambda prof, s, xs: sum(1 for x in xs if st(x, prof) == s)
    return {u"対象の行(P25 → P26 に動いた行)": n_target, u"注入の数": len(done), u"作れなかった": len(rows) - len(done), u"有効な注入": len(valid),
            u"有効でない注入(主張が見つからない・値がずれた)": len(done) - len(valid),
            u"P26 で GROUNDED(全部の注入)": cnt(NEW, "GROUNDED", done), u"P26 で GROUNDED(有効な注入)": cnt(NEW, "GROUNDED", valid),
            u"P25(対照)で GROUNDED(全部の注入)": cnt(OLD, "GROUNDED", done), u"P25(対照)で GROUNDED(有効な注入)": cnt(OLD, "GROUNDED", valid),
            u"有効な注入の P26": kv(collections.Counter(st(x, NEW) for x in valid)), u"有効な注入の P25": kv(collections.Counter(st(x, OLD) for x in valid)),
            u"集計 P26(有効)": tally(NEW, valid), u"集計 P25(有効)": tally(OLD, valid),
            u"P25 で VALUE_MISMATCH(違う)が P26 で要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移った有効な注入":
                sum(1 for x in valid if st(x, OLD) == "VALUE_MISMATCH" and st(x, NEW) in ("POINTER_NOT_FOUND", "UNVERIFIABLE")),
            u"P26 で GROUNDED の行": [dict((k, x[k]) for k in (u"doc", u"id", u"変え方", u"元の字", u"後の字", u"文")) for x in done if st(x, NEW) == "GROUNDED"]}


def injections_relabel(rows):
    return rows


# ====================================================================================================
# Q-5(P25 で GROUNDED の差の主張への末尾の桁 ±1)
def bump(tok, delta):
    for i in range(len(tok) - 1, -1, -1):
        if tok[i] in "0123456789":
            nd = int(tok[i]) + delta
            if nd < 0 or nd > 9:
                return None
            return tok[:i] + str(nd) + tok[i + 1:]
    return None


def diff_pm1_doc(doc_id, zb, text):
    u"""P25 で GROUNDED の差の主張(pointer に ``formula:a-b``)の文の数を、末尾の桁 +1 / −1 に 1 回に 1 件だけ変え、P25 と P26 で再検証する。
    同じ字の数が書類に 2 回以上ある行は、変えた方を取り違えうるので「重複」と付ける。"""
    base = VD.verify_document(zb, OLD, text)
    out = []
    for c in base["claims"]:
        if c["state"] != "GROUNDED" or c["kind"] != "num" or "formula:a-b" not in (c["pointers"] or []):
            continue
        span = c["span"]
        cand = [x for x in FP.E.iter_numbers(span) if abs(abs(x[2]) - abs(c["value"])) <= 1e-9 * max(1.0, abs(c["value"])) and x[3] == c["unit"]]
        if not cand:
            out.append({u"doc": doc_id, u"id": c["id"], u"結果": u"数の字が見つからない"})
            continue
        tok = span[cand[0][0]:cand[0][1]]
        dup = text.count(span) != 1
        pos = text.find(span)
        if pos < 0:
            out.append({u"doc": doc_id, u"id": c["id"], u"結果": u"span が見つからない"})
            continue
        for delta in (1, -1):
            nt = bump(tok, delta)
            if nt is None:
                continue
            t2 = text[:pos] + span.replace(tok, nt, 1) + text[pos + len(span):]
            row = {u"doc": doc_id, u"id": c["id"], u"変え方": u"%+d" % delta, u"元の字": tok, u"後の字": nt, u"重複": dup, u"span": span}
            for prof in (OLD, NEW):
                o = VD.verify_document(zb, prof, t2)
                g = [x for x in o["claims"] if x["id"] == c["id"]]
                if not g or g[0]["span"] == span:
                    row[prof] = {u"結果": u"主張が見つからない"}
                    continue
                row[prof] = {u"state": g[0]["state"], u"reason": g[0]["reason"], u"value": g[0]["value"], u"recomputed": g[0]["recomputed"]}
            out.append(row)
    return out


def diff_pm1_summary(rows):
    made = [r for r in rows if r.get(u"変え方")]
    valid = [r for r in made if r[OLD].get(u"state") and r[NEW].get(u"state")]
    cnt = collections.Counter((u"重複" if r[u"重複"] else u"単独", r[u"変え方"], r[OLD][u"state"], r[NEW][u"state"]) for r in valid)
    new_g = [r for r in valid if r[OLD][u"state"] != "GROUNDED" and r[NEW][u"state"] == "GROUNDED"]
    both_g = [r for r in valid if r[OLD][u"state"] == "GROUNDED" and r[NEW][u"state"] == "GROUNDED"]
    stopped_p25 = [r for r in valid if r[OLD][u"state"] != "GROUNDED"]
    to_conf = [r for r in valid if r[OLD][u"state"] == "VALUE_MISMATCH" and r[NEW][u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE")]
    return {u"対象の行(P25 で GROUNDED の差の主張)": len(set((r[u"doc"], r[u"id"]) for r in rows)), u"注入": len(made), u"有効": len(valid),
            u"集計(重複・変え方・P25・P26)": kv(dict((u" / ".join(k), v) for k, v in cnt.items())),
            u"P25 が止めた注入": len(stopped_p25),
            u"新しい GROUNDED(P25 が止めて P26 が GROUNDED にした)": len(new_g),
            u"P25 も P26 も GROUNDED にした注入(数えない)": len(both_g),
            u"P25 の止め(VALUE_MISMATCH)が P26 で要確認に移った注入": len(to_conf),
            u"新しい GROUNDED の行": [dict((k, r[k]) for k in (u"doc", u"id", u"変え方", u"元の字", u"後の字", u"重複", u"span")) for r in new_g]}


# ====================================================================================================
# Q-6
def numstat():
    out = {}
    for f in ENGINE_FILES + ("adapters/xbrl/comparators.py", "adapters/xbrl/report.py", "adapters/xbrl/verify_document.py"):
        rc, o = git("diff", "--numstat", "HEAD", "--", f)
        p = o.split()
        out[f] = {u"挿入": int(p[0]), u"削除": int(p[1])} if len(p) >= 2 and p[0].isdigit() else {u"挿入": 0, u"削除": 0}
    rc, o = git("diff", "--numstat", "HEAD", "--", "core")
    rc2, st = git("status", "--porcelain", "--", "core")
    out[u"core/"] = {u"差の行数": sum(int(l.split("\t")[0]) + int(l.split("\t")[1]) for l in o.splitlines() if l.split("\t")[0].isdigit()),
                     u"status": st.strip()}
    return out


def provenance_doc(doc_id, zb):
    n = collections.Counter()
    for rc in R.build_recipes(zb, V.PROFILES[NEW]):
        if rc.not_found_reason == "other_concept":
            n[u"other_concept の Recipe"] += 1
            if rc.claim.provenance.get("other_concept", {}).get("named"):
                n[u"provenance に名指しあり"] += 1
            if list(rc.pointers):
                n[u"pointer あり(0 のはず)"] += 1
        for r in ("direction_on_cause_item", "rounded_diff_within_double_band"):
            if rc.unverifiable_reason == r:
                n[u"%s の Recipe" % r] += 1
                key = "cause_item" if r.startswith("direction") else "rounded_diff_hold"
                if rc.claim.provenance.get(key):
                    n[u"%s の provenance あり" % r] += 1
                if list(rc.pointers):
                    n[u"pointer あり(0 のはず)"] += 1
    return dict(n)


# ====================================================================================================
# Q-7(報告形)
def report_block(ids67):
    RF = _mod(REPORT_FIX_MEASURE_REL, "report_fix_for_p26")
    std_dir = RF.labels_dir()
    std_labels, std_meta = RC.load_labels_with_meta(std_dir, None)
    per = []
    sect_of_reason = collections.Counter()
    reason_rows = 0
    total_vm = total_md_vm = 0
    for d in ids67:
        zp = ED.cache_path(d)
        with io.open(zp, "rb") as fh:
            zb = fh.read()
        labels, _meta = RF.compose(std_labels, std_meta, zp)
        out = VD.verify_document(zb, NEW, None)
        dei = RC.dei_from_zip(zp, (out.get("input") or {}).get("instance_source"))
        md = RC.render_markdown(out, labels, True, dei)
        heads = RF.heading_counts(md)
        by_sec = RF.ids_by_section(md)
        sec_of = dict((cid, s) for s, ids in by_sec.items() for cid in ids)
        states = collections.Counter(c["state"] for c in out["claims"])
        for c in out["claims"]:
            if c["reason"] in REASONS:
                reason_rows += 1
                sect_of_reason[sec_of.get(c["id"], u"(節に無い)")] += 1
        per.append({u"doc": d, u"違う(節の件数)": heads[u"違う"], u"VALUE_MISMATCH(state)": states.get("VALUE_MISMATCH", 0),
                    u"要確認(節の件数)": heads[u"要確認"], u"一致(節の件数)": heads[u"一致"], u"対象外": heads[u"対象外"], u"判断しない": heads[u"判断しない"],
                    u"claims": len(out["claims"])})
        total_vm += states.get("VALUE_MISMATCH", 0)
        total_md_vm += heads[u"違う"] or 0
    reasons_reg = sorted(set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS))
    return {u"書類別": per, u"違う(節)の合計": total_md_vm, u"VALUE_MISMATCH(state)の合計": total_vm,
            u"3 つの理由の行": reason_rows, u"3 つの理由の行が入った節": kv(sect_of_reason),
            u"登録簿の理由": {u"POINTER_NOT_FOUND": len(RS._POINTER_NOT_FOUND_REASONS), u"UNVERIFIABLE": len(RS._UNVERIFIABLE_REASONS),
                        u"合計": len(reasons_reg), u"表 REASON_JA にある": sum(1 for r in reasons_reg if r in RC.REASON_JA),
                        u"表に無い": [r for r in reasons_reg if r not in RC.REASON_JA],
                        u"3 つの理由が登録簿にある": [r for r in REASONS if r in reasons_reg]}}


# ====================================================================================================
def env_block(label_shas):
    bundle, n_files = RIT.engine_bundle_sha256()
    return {u"封": SEAL, u"HEAD": RIT.git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順。変更後)": bundle,
            u"engine の file 数": n_files,
            u"engine の sha16": dict((f, sha_file(os.path.join(ROOT, f))[:16]) for f in sorted(ENGINE_FILES + ("adapters/xbrl/comparators.py",))),
            u"DEFAULT_PROFILE": V.DEFAULT_PROFILE, u"比べた profile": [OLD, NEW],
            u"P26 の旗": dict((f, getattr(V.PROFILES[NEW], f)) for f in FLAG_NAMES),
            u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
            u"名前が ANTHROPIC/OPENAI/GOOGLE/GEMINI で始まる環境変数の数(値は読まない)": sum(1 for k in os.environ if k.split("_")[0] in ("ANTHROPIC", "OPENAI", "GOOGLE", "GEMINI")),
            u"ラベル 2 file の sha256(起動時に照合)": label_shas,
            u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"並列": u"multiprocessing(fork)の子プロセスで、書類ごと・段ごとに走らせる(結果は書類・id の順に並べ直す)",
            u"費用": u"0 USD"}


def inputs_block(doc_ids_67, doc_ids_out, readings_path, mutations_path=None):
    d = {}
    for rel in (LASTBRANCH_REL, PB.S2_MATERIAL_REL, PB.S2_REC_REL):
        d[rel] = sha_file(os.path.join(ROOT, rel))
    d[u"儀式の同梱書類"] = sha_file(os.path.join(ROOT, RIT.ZIP_REL))
    d[u"書類 67(経営分析の文を持つ)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_67 if os.path.exists(ED.cache_path(x)))
    d[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] = hashlib.sha256(
        u"\n".join(u"%s\t%s" % (x, sha_file(ED.cache_path(x))) for x in sorted(doc_ids_out)).encode("utf-8")).hexdigest()
    d[u"人の読みの入力 file の sha256(``--readings``。内容は記録の行に写した)"] = sha_file(readings_path) if readings_path else None
    d[u"engine の変異の表の入力 file の sha256(``--mutations``。手で走らせた表の写し)"] = sha_file(mutations_path) if mutations_path else None
    return d


# ====================================================================================================
def judge(rec, bounds):
    u"""封 §2 の Q-1〜Q-8 の機械的な判定。幅は封の字から取った ``bounds`` のまま。"""
    J = {}
    if u"Q1" in rec:
        s = rec[u"Q1"][u"集計"]
        lo, hi = bounds["Q1_vm"]
        glo, ghi = bounds["Q1_g_out"]
        parts = {u"VALUE_MISMATCH %d〜%d" % (lo, hi): lo <= s[u"VALUE_MISMATCH の合計 P26"] <= hi,
                 u"新しい GROUNDED 0": s[u"新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED)"] == 0,
                 u"GROUNDED → 非 GROUNDED %d〜%d" % (glo, ghi): glo <= s[u"GROUNDED から外れた行(P25 が GROUNDED で P26 が GROUNDED でない)"] <= ghi}
        J[u"Q-1"] = {u"実測": u"67 書類(実数 %d)・claim %s: VALUE_MISMATCH P25 %s → P26 %s、新しい GROUNDED %d、GROUNDED から外れた行 %d(GROUNDED %s → %s)、動いた %d 行" % (
            s[u"書類数"], format(s[u"総 claim"], ","), format(s[u"VALUE_MISMATCH の合計 P25"], ","), format(s[u"VALUE_MISMATCH の合計 P26"], ","),
            s[u"新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED)"], s[u"GROUNDED から外れた行(P25 が GROUNDED で P26 が GROUNDED でない)"],
            format(s[u"GROUNDED の合計 P25"], ","), format(s[u"GROUNDED の合計 P26"], ","), s[u"動いた(全 state)"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"Q2" in rec:
        rs = reading_summary(rec[u"Q2"][u"行"])
        lo, hi = bounds["Q2_wrong"]
        if rs[u"未読"] == 0:
            parts = {u"文が本当に違う %d〜%d" % (lo, hi): lo <= rs[READ_WRONG] <= hi}
            word = u"当たり" if all(parts.values()) else u"外れ"
        else:
            parts, word = {}, u"読み待ち"
        J[u"Q-2"] = {u"実測": u"「違う」から外れた %d 行の読み(実装席のエージェント): 正しい文 %d・文が本当に違う %d・分からない %d・未読 %d" % (
            rs[u"行"], rs[READ_OK], rs[READ_WRONG], rs[READ_UNSURE], rs[u"未読"]), u"部分の判定": parts, u"判定": word}
    if u"Q3" in rec:
        h = rec[u"Q3"][u"穴 B"][u"集計"][u"P26 で通した(GROUNDED のまま)"]
        r = rec[u"Q3"][u"儀式"]
        rs_ = r[u"集計"]
        s = rec[u"Q3"][u"段 2"][u"集計"][u"全注入で Core 自身 P26 が GROUNDED"]
        lo, hi = bounds["Q3_rit"]
        parts = {u"穴 B 通した 0 / 485": (h[u"件"], h[u"分母"]) == (0, 485), u"儀式 通した %d〜%d" % (lo, hi): lo <= r[u"通した P26"][u"件"] <= hi,
                 u"段 2 の注入 GROUNDED 0 / 64": (s[u"件"], s[u"分母"]) == (0, 64)}
        J[u"Q-3"] = {u"実測": u"穴 B 通した %d / %d・儀式 通した %d / %d(%s)・段 2 の注入 GROUNDED %d / %d。穴 B の止め → 要確認 %d、儀式の止め → 要確認 %d(手で当てた円銭 %d 行で通した %d)、段 2 の止め → 要確認 %d" % (
            h[u"件"], h[u"分母"], r[u"通した P26"][u"件"], r[u"通した P26"][u"分母"], u"・".join(x[u"id"] for x in r[u"通した P26 の一覧"]), s[u"件"], s[u"分母"],
            rec[u"Q3"][u"穴 B"][u"集計"][u"止め(P25 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移る"][u"件"],
            rs_[u"注入の止めが要確認に移った(共通の行)"], rs_[u"手で当てた行"], rs_[u"手で当てて通した"],
            rec[u"Q3"][u"段 2"][u"集計"][u"注入の止めのうち要確認に移る"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"Q4" in rec:
        s = rec[u"Q4"][u"集計"]
        parts = {u"P26 が GROUNDED にする 0 回": s[u"P26 で GROUNDED(全部の注入)"] == 0}
        J[u"Q-4"] = {u"実測": u"動いた %d 行・注入 %d 回(作れなかった %d・有効 %d)で P26 が GROUNDED %d(P25 の対照は %d)" % (
            s[u"対象の行(P25 → P26 に動いた行)"], s[u"注入の数"], s[u"作れなかった"], s[u"有効な注入"], s[u"P26 で GROUNDED(全部の注入)"], s[u"P25(対照)で GROUNDED(全部の注入)"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"Q5" in rec:
        s = rec[u"Q5"][u"集計"]
        parts = {u"新しい GROUNDED 0": s[u"新しい GROUNDED(P25 が止めて P26 が GROUNDED にした)"] == 0}
        J[u"Q-5"] = {u"実測": u"P25 で GROUNDED の差の主張 %d 行に末尾の桁 ±1 の注入 %d 回(有効 %d): P25 が止めて P26 が GROUNDED にした(新しい GROUNDED)%d・P25 も P26 も GROUNDED にした %d(数えない)・P25 の止めが P26 で要確認に移った %d" % (
            s[u"対象の行(P25 で GROUNDED の差の主張)"], s[u"注入"], s[u"有効"], s[u"新しい GROUNDED(P25 が止めて P26 が GROUNDED にした)"],
            s[u"P25 も P26 も GROUNDED にした注入(数えない)"], s[u"P25 の止め(VALUE_MISMATCH)が P26 で要確認に移った注入"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"Q6" in rec:
        e = rec[u"Q6"]
        d = e[u"engine の差分"]
        rc, ex, vc, rg, cp = d["adapters/xbrl/recipes.py"], d["adapters/xbrl/extract.py"], d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/registry_setup.py"], d["adapters/xbrl/comparators.py"]
        kinds = collections.Counter(x[u"種類"] for x in e[u"既存試験の赤(直す前)"])
        allowed = bounds["Q6_kinds"]
        rlo, rhi = bounds["Q6_rec_ins"]
        parts = {u"recipes.py 挿入 %d〜%d" % (rlo, rhi): rlo <= rc[u"挿入"] <= rhi, u"recipes.py 削除 0〜2": 0 <= rc[u"削除"] <= 2,
                 u"extract.py ≤ %d" % bounds["Q6_ext"]: ex[u"挿入"] + ex[u"削除"] <= bounds["Q6_ext"],
                 u"vocabulary.py ≤ %d" % bounds["Q6_voc"]: vc[u"挿入"] + vc[u"削除"] <= bounds["Q6_voc"],
                 u"registry_setup.py ≤ %d" % bounds["Q6_reg"]: rg[u"挿入"] + rg[u"削除"] <= bounds["Q6_reg"],
                 u"comparators.py 0 行": cp[u"挿入"] == 0 and cp[u"削除"] == 0, u"core/ 0 行": d[u"core/"][u"差の行数"] == 0,
                 u"既存試験の赤は種類の中だけ(数 / state の門・人間の決定の字の門は 0)": all(k in allowed for k in kinds)}
        J[u"Q-6"] = {u"実測": u"recipes.py 挿入 %d・削除 %d、extract.py 挿入 %d・削除 %d、vocabulary.py 挿入 %d・削除 %d、registry_setup.py 挿入 %d・削除 %d、comparators.py %d/%d、core/ %d 行。既存試験の赤(直す前)%d 本、種類 %s" % (
            rc[u"挿入"], rc[u"削除"], ex[u"挿入"], ex[u"削除"], vc[u"挿入"], vc[u"削除"], rg[u"挿入"], rg[u"削除"], cp[u"挿入"], cp[u"削除"], d[u"core/"][u"差の行数"],
            len(e[u"既存試験の赤(直す前)"]), json.dumps(kv(kinds), ensure_ascii=False)),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"Q7" in rec:
        q = rec[u"Q7"]
        parts = {u"「違う」の節の合計 = P26 の VALUE_MISMATCH": q[u"違う(節)の合計"] == q[u"VALUE_MISMATCH(state)の合計"],
                 u"書類ごとにも一致": all(p[u"違う(節の件数)"] == p[u"VALUE_MISMATCH(state)"] for p in q[u"書類別"]),
                 u"3 つの理由の行は全部「要確認」の節": q[u"3 つの理由の行"] > 0 and list(q[u"3 つの理由の行が入った節"]) == [u"要確認"],
                 u"登録簿の理由 19 で全部表にある": (q[u"登録簿の理由"][u"合計"], q[u"登録簿の理由"][u"表 REASON_JA にある"]) == (19, 19)}
        J[u"Q-7"] = {u"実測": u"P26 明示の %d 書類: 「違う」の節の合計 %d・VALUE_MISMATCH %d。3 つの理由の %d 行が入った節 %s。登録簿の理由 %d(POINTER_NOT_FOUND %d・UNVERIFIABLE %d)のうち表にある %d" % (
            len(q[u"書類別"]), q[u"違う(節)の合計"], q[u"VALUE_MISMATCH(state)の合計"], q[u"3 つの理由の行"], json.dumps(q[u"3 つの理由の行が入った節"], ensure_ascii=False),
            q[u"登録簿の理由"][u"合計"], q[u"登録簿の理由"][u"POINTER_NOT_FOUND"], q[u"登録簿の理由"][u"UNVERIFIABLE"], q[u"登録簿の理由"][u"表 REASON_JA にある"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    J[u"Q-8"] = {u"実測": u"段 2(既定)は封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §3 の基準で、新しい標本を取ってから。この実行では何も変えていない(DEFAULT_PROFILE = %s)" % V.DEFAULT_PROFILE,
                 u"判定": u"判定しない(段 2)"}
    return J


def seal_bounds():
    u"""封の予測の幅を封の字から読む(幅を手で持たない)。"""
    with io.open(os.path.join(ROOT, SEAL), encoding="utf-8") as fh:
        t = fh.read()
    lines = dict((m.group(1), m.group(0)) for m in re.finditer(r"(?m)^\| \*\*Q-(\d)\*\* \|.*$", t))
    rng = lambda line, pat: tuple(int(x.replace(",", "")) for x in re.search(pat, line).groups())
    b = {"Q1_vm": rng(lines["1"], r"VALUE_MISMATCH \*\*(\d+)〜(\d+)\*\*"), "Q1_g_out": rng(lines["1"], r"GROUNDED → 非 GROUNDED \*\*(\d+)〜(\d+)\*\*"),
         "Q2_wrong": rng(lines["2"], r"「文が本当に違う」\*\*(\d+)〜(\d+)\*\*"), "Q3_rit": rng(lines["3"], r"儀式 通した \*\*(\d+)〜(\d+)\*\*"),
         "Q6_rec_ins": rng(lines["6"], r"recipes \*\*\+(\d+)〜\+(\d+) / −0〜−2\*\*"),
         "Q6_ext": int(re.search(r"extract \*\*≤ (\d+)\*\*", lines["6"]).group(1)), "Q6_voc": int(re.search(r"vocabulary \*\*≤ (\d+)\*\*", lines["6"]).group(1)),
         "Q6_reg": int(re.search(r"registry_setup \*\*≤ (\d+)\*\*", lines["6"]).group(1)),
         "Q6_kinds": (u"sha・指紋", u"profile の一覧", u"登録簿と理由の表", u"変異の予測")}
    return b


# ====================================================================================================
G = {}      # fork した子プロセスが読む(run() が pool を作る前に埋める)


def _t_plain(doc_id):
    zb, _text = G["texts"][doc_id]
    return doc_id, plain_doc(doc_id, zb)


def _t_flag(doc_id):
    zb, _text = G["texts"][doc_id]
    return doc_id, flag_doc(doc_id, zb)


def _t_hole_b(doc_id):
    zb, text = G["texts"][doc_id]
    rows, ns, nm = LB.hole_b_doc(doc_id, zb, text)
    return doc_id, (relabel(rows), ns, nm)


def _t_inj(args):
    doc_id, rows = args
    zb, text0 = G["texts"][doc_id]
    return doc_id, LB.injections_doc(doc_id, zb, text0, rows)


def _t_diff(doc_id):
    zb, text = G["texts"][doc_id]
    return doc_id, diff_pm1_doc(doc_id, zb, text)


def _t_prov(doc_id):
    zb, _t = G["texts"][doc_id]
    return doc_id, provenance_doc(doc_id, zb)


def _t_ritual(_):
    return "ritual", ritual(G["label_shas"])


def _t_s2(_):
    work = tempfile.mkdtemp(prefix="p26_s2_", dir=os.environ.get("TMPDIR"))
    try:
        return "s2", s2(work)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


def run(stage, only_docs=None, readings=None, readings_path=None, mutations=None, mutations_path=None, existing_red=None, jobs=4):
    t_all = time.time()
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        raise SystemExit(2)
    register_flag_profiles()
    zips = PP.list_zips()
    texts_of, ids67, ids_out = {}, [], []
    for doc_id, path in zips:
        if only_docs and doc_id not in only_docs:
            continue
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts_of[doc_id] = (zb, text)
            ids67.append(doc_id)
        else:
            ids_out.append(doc_id)
    ids67.sort()
    G["texts"], G["label_shas"] = texts_of, label_shas
    rec = {u"step": u"**P26 の段 1 の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"環境": env_block(label_shas), u"書類の数": {u"経営分析の文を持つ": len(ids67), u"67 の外": len(ids_out)}}
    secs = {}
    want = lambda *names: stage in names or stage == "all"
    ctx = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, jobs), mp_context=ctx) as ex:
        moved_all = []
        if want("q1", "q2", "dossier"):
            t = time.time()
            res = dict(ex.map(_t_plain, ids67))
            per, moved, reread = [], [], []
            for d in ids67:
                p, m, rr = res[d]
                per.append(p)
                moved.extend(m)
                reread.extend(rr)
            moved_all = moved
            keep = (lambda r: r) if stage == "dossier" else (lambda r: dict((k, v) for k, v in r.items() if k != u"dossier"))
            rec[u"Q1"] = {u"書類": per, u"動いた行": [keep(r) for r in moved], u"読みが変わった行": reread}
            rec[u"Q1"][u"集計"] = plain_summary(rec[u"Q1"])
            q2, q2b = q2_rows(rec[u"Q1"][u"動いた行"])
            rec[u"Q2"] = {u"行": q2}
            rec[u"Q2b"] = {u"行": q2b}
            if readings:
                attach_readings(rec, readings)
            secs[u"Q1 Q2"] = round(time.time() - t, 1)
        futs = {}
        if want("flags"):
            futs["flags"] = [ex.submit(_t_flag, d) for d in ids67]
        if want("q3"):
            futs["hole"] = [ex.submit(_t_hole_b, d) for d in ids67]
            futs["ritual"] = ex.submit(_t_ritual, None)
            futs["s2"] = ex.submit(_t_s2, None)
        if want("prov"):
            futs["prov"] = [ex.submit(_t_prov, d) for d in ids67]
        if want("q5"):
            futs["diff"] = [ex.submit(_t_diff, d) for d in ids67]
        if want("q4"):
            if not moved_all:
                raise SystemExit(u"--stage q4 は単独では走らせない(動いた行が要る)。--stage all で")
            by_doc = collections.defaultdict(list)
            for r in moved_all:
                by_doc[r[u"doc"]].append(r)
            futs["inj"] = [ex.submit(_t_inj, (d, by_doc[d])) for d in sorted(by_doc)]
        if "flags" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["flags"])
            per = [res[d] for d in ids67]
            agg = {}
            for g, _name in FLAG_PROFILES:
                st = lambda s: sum(p[u"旗"][g][u"states"].get(s, 0) for p in per)
                mv = collections.Counter()
                for p in per:
                    mv.update(p[u"旗"][g][u"動いた向き"])
                agg[g] = {u"GROUNDED": st("GROUNDED"), u"VALUE_MISMATCH": st("VALUE_MISMATCH"), u"UNVERIFIABLE": st("UNVERIFIABLE"),
                          u"POINTER_NOT_FOUND": st("POINTER_NOT_FOUND"), u"動いた行": sum(mv.values()), u"動いた向き": kv(dict(mv))}
            rec[u"旗ごと"] = {u"対照 P25 の state": dict((s, sum(p[u"states P25"].get(s, 0) for p in per)) for s in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")),
                           u"旗": agg, u"注": u"旗 1 つずつは P25 に ``dataclasses.replace`` で 1 つだけ足した profile(この script の中だけで ``V.PROFILES`` に足す。engine には登録しない)。"}
            secs[u"旗ごと"] = round(time.time() - t, 1)
        if "hole" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["hole"])
            rows, per = [], []
            for d in ids67:
                r, ns, nm = res[d]
                rows.extend(r)
                per.append({u"書類": d, u"site": ns, u"作れた": nm})
            e = futs["ritual"].result()[1]
            s2rows = futs["s2"].result()[1]
            rec[u"Q3"] = {u"穴 B": {u"書類別": per, u"行": rows, u"集計": hole_b_summary(rows),
                                 u"対照: P25 の再計算と P25 の記録": (hole_b_vs_lastbranch(rows) if not only_docs else None)},
                          u"儀式": dict(e, **{u"集計": ritual_summary(e)}),
                          u"段 2": {u"行": s2rows, u"集計": s2_summary(s2rows), u"対照: P25 の再計算と P25 の記録": s2_vs_lastbranch(s2rows)}}
            secs[u"Q3"] = round(time.time() - t, 1)
        if "prov" in futs:
            res = dict(f.result() for f in futs["prov"])
            tot = collections.Counter()
            for d in ids67:
                tot.update(res[d])
            rec[u"provenance"] = kv(dict(tot))
        if "diff" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["diff"])
            rows = []
            for d in ids67:
                rows.extend(res[d])
            rec[u"Q5"] = {u"行": rows, u"集計": diff_pm1_summary(rows)}
            secs[u"Q5"] = round(time.time() - t, 1)
        if "inj" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["inj"])
            rows = []
            for d in sorted(res):
                rows.extend(res[d])
            rec[u"Q4"] = {u"行": rows, u"集計": injection_summary(rows, len(moved_all))}
            secs[u"Q4"] = round(time.time() - t, 1)
    if want("q6"):
        rec[u"Q6"] = {u"engine の差分": numstat(), u"既存試験の赤(直す前)": list(existing_red or [])}
    if want("q7"):
        t = time.time()
        rec[u"Q7"] = report_block(ids67)
        secs[u"Q7"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"入力の sha256"] = inputs_block(ids67, ids_out, readings_path, mutations_path)
    if mutations:
        rec[u"変異(engine。手で走らせた)"] = mutations
    rec[u"予測の判定"] = judge(rec, seal_bounds())
    rec[u"limits"] = [
        u"手元の cache の 67 書類(経営分析の文を持つ)。規則はこの 67 書類を読んで作った(試作 2 回)。無作為ではない。67 書類での違う 0 は新しい標本での違う 0 を意味しない。",
        u"新しい標本は手元に無い: 手元の cache の 67 の外 214 書類は全部 jpsps(特定有価証券)で、67 と同じ抽出は経営分析の文を取れず claim は 0。",
        u"Q-1・Q-3〜Q-5 は試作の再現で、外れるなら実装が試作と違う。本当に外れうるのは Q-2(実装席が読み直す)と、新しい標本での判定(Q-8)。",
        u"読み(Q-2)は実装席のエージェントの読みで人間ではない。門では縛れない(数と行の対応だけ縛る)。『分からない』は『分からない』のまま数えた。",
        u"Q-4 の注入は『末尾の桁 ±3・10 倍』の 2 型で、1 回に 1 件。向きの語の反転・ほかの誤りの作り方では未測定。",
        u"Q-5 の注入は『末尾の桁 ±1』で、P25 で GROUNDED の差の主張に限る。P25 で GROUNDED でない差の主張・差でない主張の ±1 は未測定。",
        u"Q-3 の儀式は同梱 1 書類(S100Z4Q1)。注入は型 V1・V2 だけ。数の読み取り(G5)で円銭の注入は表から消えるので、同じ注入を手で P26 に当てた。",
        u"代価(封 §3): 差の主張の 1 単位の書き誤りは『違う』でなく『要確認』に出る。G4 は同じ形の正しい結びも外しうる。『違う』に残る正しい文の主因(区分の取り違えの疑い・向きの語の残り)はこの封では直らない。",
        u"顧客の出力(verify_document)には provenance の欄が無い。名指した fact・差を見せるのは日本語の報告形の封で決める。"]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"P26 の段 1 の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["q1", "q3", "q4", "q5", "q6", "q7", "flags", "prov", "dossier", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--readings", default=None, help=u"人の読みの JSON({Q2: {doc:id: {読み, 根拠}}, Q2b: …}。Q-2 の行に写す)")
    ap.add_argument("--mutations", default=None, help=u"engine の変異(手で走らせた)の表の JSON({注記, 表}。記録に写す)")
    ap.add_argument("--existing-red", default=None, help=u"既存試験の赤(直す前)の JSON(配列。Q-6 に写す)")
    ap.add_argument("--jobs", type=int, default=4, help=u"並列の子プロセスの数")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    load = lambda p: None if not p else json.load(io.open(p, encoding="utf-8"))
    readings, mutations, red = load(a.readings), load(a.mutations), load(a.existing_red)
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, readings=readings, readings_path=a.readings, mutations=mutations,
              mutations_path=a.mutations, existing_red=red, jobs=a.jobs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== P26 の段 1(%s → %s・手元の cache・鍵なし・0 USD)===" % (OLD, NEW))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
