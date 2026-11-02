# -*- coding: utf-8 -*-
u"""engine が止めた真の文 53 の中身(封 docs/XBRL_DERIVATION_STOPPED_SEAL_2026-11-02.md)。

engine を走らせず、既にある記録だけを突き合わせる: engine の判定(entry。P16)の pointers・recomputed・reason と、
主語の制約の便の記録の K0 の判定・候補の fact と、盲検の札の根拠の字。53 行(札 真・num・GROUNDED でない)を
封 §2 の型 T1〜T6 に分けて数える。材料は全部 repo の中(封 §0 の 4 file。sha256 を照らす)。
engine(core/・adapters/)は import しない。前の便の script も読まない(候補は記録に在る)。通信しない。

    python3 measure/xbrl_derivation_stopped_2026-11-02.py [--out fixtures/xbrl/derivation_stopped_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- pointers は ``xbrl:prefix:Local@context`` の形だけを要素と context に分ける(それ以外の形は数に入れず、行に「読めなかった pointer」として残す)。
- 「要素が根拠に在る」は local name(``:`` の後)が札の根拠の字に部分文字列として在ること(主語の制約の便の「根拠に要素名」と同じ)。
- T2 の engine の帯の参考は、候補の v と文の数 t'(前の便の記録)の大きさ(絶対値)で、round(|v| − |t| の絶対値 ≤ u / 2)と
  truncate(0 ≤ |v| − |t| < u)の両方を書く。判定には使わない。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_DERIVATION_STOPPED_SEAL_2026-11-02.md"
SEAL_COMMIT = "ab2ad5b"
OUT_REL = "fixtures/xbrl/derivation_stopped_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"prev_rec", ("fixtures/xbrl/derivation_subject_2026-11-02.json", "6703ae50e2fcee8bf6340fc96c89b7bd530b472b5b103efc83e2e40c0eb02de0")),
])
STATES = (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
SEAL_STATE_COUNTS = collections.OrderedDict([(u"VALUE_MISMATCH", 23), (u"UNVERIFIABLE", 18), (u"POINTER_NOT_FOUND", 12)])
TYPES_T = (u"T1 指せず", u"T2 同じ fact", u"T3 導出の量", u"T4 同じ要素・別の期", u"T5 別の要素", u"T6 導出も決めない")
VERDICTS = (u"導出一致", u"保留", u"不一致")
BOUNDS = {u"J-1": 53, u"J-2": (10, 18), u"J-3": (0, 2), u"J-4": (3, 6), u"J-5": (1, 4), u"J-6": (3, 8), u"J-7": 10, u"J-8": (6, 12), u"J-9": (0, 5)}
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- 封 §1: 行ごとに引く字

def local_name(element):
    return element.split(u":")[-1]


def parse_pointers(pointers):
    u"""``xbrl:prefix:Local@context`` の列を (要素, context) の列に。読めない形は別に返す。"""
    ok, bad = [], []
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            ok.append((m.group(1), m.group(2)))
        else:
            bad.append(p)
    return ok, bad


def in_grounds(element, grounds):
    return local_name(element) in (grounds or u"")


def any_in_grounds(elements, grounds):
    elements = list(elements)
    if not elements:
        return None
    return any(in_grounds(e, grounds) for e in elements)


# ---------------------------------------------------------------- 封 §2: 型

def classify(ptrs, clue, verdict, cand):
    u"""封 §2 の表を上から順に。``ptrs`` は (要素, context) の列、``cand`` は K0 の候補(導出一致なら 1 つ)。"""
    if not ptrs:
        return TYPES_T[0]
    if not clue or verdict != u"導出一致" or not cand:
        return TYPES_T[5]
    facts = [(f[u"name"], f[u"context"]) for f in cand[u"fact"]]
    if cand[u"型"] == u"D1":
        name, ctx = facts[0]
        if (name, ctx) in set(ptrs):
            return TYPES_T[1]
    else:
        return TYPES_T[2]
    if name in set(e for e, _ in ptrs):
        return TYPES_T[3]
    return TYPES_T[4]


def band_reference(cand, t, u):
    u"""T2 の参考: engine の帯の形(comparators.py の _match_value の字。読むだけ)で候補の v が入るか。"""
    v = abs(cand[u"v"])
    t = abs(t)
    d = v - t
    return collections.OrderedDict([(u"|v| − |t|", d), (u"round(|d| ≤ u / 2)", abs(d) <= u / 2.0), (u"truncate(0 ≤ d < u)", 0 <= d < u)])


def build_rows(prev_rows, entry_claims, labels, texts):
    rows = []
    for pr in prev_rows:
        if not pr.get(u"母数"):
            continue
        cid = pr[u"id"]
        ec = entry_claims[cid]
        lab = labels[cid]
        grounds = lab.get(u"根拠") or u""
        ptrs, bad = parse_pointers(ec.get(u"pointers"))
        clue = bool(pr.get(u"手がかりあり"))
        verdict = pr.get(u"判定") if clue else None
        cands = pr.get(u"候補") or []
        cand = cands[0] if (clue and verdict == u"導出一致" and cands) else None
        T = classify(ptrs, clue, verdict, cand)
        r = collections.OrderedDict()
        r[u"id"] = cid
        r[u"札"] = lab.get(u"札")
        r[u"state"] = ec.get(u"state")
        r[u"state が前の便の記録と一致"] = ec.get(u"state") == pr.get(u"state")
        r[u"form"] = ec.get(u"form")
        r[u"unit"] = pr.get(u"unit")
        r[u"value"] = pr.get(u"value")
        r[u"t'"] = pr.get(u"t'")
        r[u"u"] = pr.get(u"u")
        r[u"subject"] = ec.get(u"subject")
        r[u"reason"] = ec.get(u"reason")
        r[u"pointers"] = [collections.OrderedDict([(u"要素", e), (u"context", c)]) for e, c in ptrs]
        r[u"読めなかった pointer"] = bad
        r[u"recomputed"] = ec.get(u"recomputed")
        r[u"手がかりあり"] = clue
        r[u"S"] = pr.get(u"S") or []
        r[u"K0 の判定"] = verdict
        r[u"候補の型"] = cand[u"型"] if cand else None
        r[u"候補の fact"] = [collections.OrderedDict([(u"要素", f[u"name"]), (u"context", f[u"context"])]) for f in cand[u"fact"]] if cand else []
        r[u"候補の v"] = cand[u"v"] if cand else None
        r[u"engine の要素が根拠に在る"] = any_in_grounds((e for e, _ in ptrs), grounds)
        r[u"候補の要素が根拠に在る"] = any_in_grounds((f[u"name"] for f in cand[u"fact"]), grounds) if cand else None
        r[u"engine の要素が S に在る"] = (any(e in set(r[u"S"]) for e, _ in ptrs) if (clue and ptrs) else None)
        r[u"engine の要素が候補の要素に在る"] = (any(e in set(f[u"name"] for f in cand[u"fact"]) for e, _ in ptrs) if (cand and ptrs) else None)
        r[u"型"] = T
        r[u"導出が engine の取り違えを正した形"] = bool(cand and ptrs and r[u"候補の要素が根拠に在る"] and r[u"engine の要素が根拠に在る"] is False)
        r[u"engine の帯の参考(T2)"] = band_reference(cand, pr[u"t'"], pr[u"u"]) if T == TYPES_T[1] else None
        r[u"根拠"] = grounds
        r[u"文"] = (texts.get(cid) or {}).get(u"文")
        rows.append(r)
    return rows


# ---------------------------------------------------------------- 封 §3: 数えるもの

def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def tally(rows):
    T = collections.OrderedDict()
    T[u"母数"] = len(rows)
    T[u"手がかりあり"] = sum(1 for r in rows if r[u"手がかりあり"])
    T[u"手がかりなし"] = T[u"母数"] - T[u"手がかりあり"]
    T[u"札が 真"] = sum(1 for r in rows if r[u"札"] == u"真")
    T[u"state の分布"] = collections.OrderedDict((s, sum(1 for r in rows if r[u"state"] == s)) for s in STATES)
    T[u"state が前の便の記録と一致した行"] = sum(1 for r in rows if r[u"state が前の便の記録と一致"])
    T[u"読めなかった pointer の在る行"] = sum(1 for r in rows if r[u"読めなかった pointer"])
    T[u"型の件数"] = collections.OrderedDict((t, sum(1 for r in rows if r[u"型"] == t)) for t in TYPES_T)
    T[u"state × 型"] = collections.OrderedDict((s, collections.OrderedDict((t, sum(1 for r in rows if r[u"state"] == s and r[u"型"] == t)) for t in TYPES_T)) for s in STATES)
    T[u"型ごとの id"] = collections.OrderedDict((t, [r[u"id"] for r in rows if r[u"型"] == t]) for t in TYPES_T)
    vm = [r for r in rows if r[u"state"] == u"VALUE_MISMATCH"]
    T[u"VALUE_MISMATCH"] = len(vm)
    T[u"VALUE_MISMATCH で pointers が空でない"] = sum(1 for r in vm if r[u"pointers"])
    T[u"VALUE_MISMATCH で engine の要素が根拠に無い"] = sum(1 for r in vm if r[u"engine の要素が根拠に在る"] is False)
    T[u"VALUE_MISMATCH で engine の要素が根拠に無い id"] = [r[u"id"] for r in vm if r[u"engine の要素が根拠に在る"] is False]
    T[u"VALUE_MISMATCH で engine の要素が根拠に在る"] = sum(1 for r in vm if r[u"engine の要素が根拠に在る"] is True)
    T[u"VALUE_MISMATCH で form が derived_value"] = sum(1 for r in vm if r[u"form"] == u"derived_value")
    T[u"VALUE_MISMATCH の form の分布"] = _cnt(r[u"form"] for r in vm)
    un = [r for r in rows if r[u"state"] == u"UNVERIFIABLE"]
    T[u"UNVERIFIABLE"] = len(un)
    T[u"UNVERIFIABLE の reason の分布"] = _cnt((r[u"reason"] or u"(無し)") for r in un)
    T[u"UNVERIFIABLE の reason の最多"] = max(T[u"UNVERIFIABLE の reason の分布"].values()) if un else 0
    T[u"UNVERIFIABLE で pointers が空でない"] = sum(1 for r in un if r[u"pointers"])
    T[u"UNVERIFIABLE で engine の要素が根拠に無い"] = sum(1 for r in un if r[u"engine の要素が根拠に在る"] is False)
    pnf = [r for r in rows if r[u"state"] == u"POINTER_NOT_FOUND"]
    T[u"POINTER_NOT_FOUND"] = len(pnf)
    T[u"POINTER_NOT_FOUND で pointers が空"] = sum(1 for r in pnf if not r[u"pointers"])
    T[u"POINTER_NOT_FOUND の K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in pnf if r[u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"導出が engine の取り違えを正した形"] = sum(1 for r in rows if r[u"導出が engine の取り違えを正した形"])
    T[u"導出が engine の取り違えを正した形の id"] = [r[u"id"] for r in rows if r[u"導出が engine の取り違えを正した形"]]
    t3 = [r for r in rows if r[u"型"] == TYPES_T[2]]
    T[u"T3 で engine の要素が候補の要素に在る"] = sum(1 for r in t3 if r[u"engine の要素が候補の要素に在る"])
    T[u"T3 の候補の型の分布"] = _cnt(r[u"候補の型"] for r in t3)
    t2 = [r for r in rows if r[u"型"] == TYPES_T[1]]
    T[u"T2 の engine の帯の参考"] = collections.OrderedDict([(u"round で入る", sum(1 for r in t2 if r[u"engine の帯の参考(T2)"][u"round(|d| ≤ u / 2)"])),
                                                    (u"truncate で入る", sum(1 for r in t2 if r[u"engine の帯の参考(T2)"][u"truncate(0 ≤ d < u)"]))])
    clue_ptr = [r for r in rows if r[u"手がかりあり"] and r[u"pointers"]]
    T[u"手がかりあり で pointers が空でない"] = len(clue_ptr)
    T[u"手がかりあり で engine の要素が S に在る"] = sum(1 for r in clue_ptr if r[u"engine の要素が S に在る"])
    one = [r for r in rows if r[u"K0 の判定"] == u"導出一致"]
    T[u"K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in rows if r[u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"導出一致の候補の型の分布"] = _cnt(r[u"候補の型"] for r in one)
    T[u"導出一致で候補の要素が根拠に在る"] = sum(1 for r in one if r[u"候補の要素が根拠に在る"])
    T[u"導出一致で engine の要素が根拠に在る"] = _cnt(r[u"engine の要素が根拠に在る"] for r in one)
    return T


def judge(T):
    b = BOUNDS
    J = collections.OrderedDict()
    J[u"J-1"] = (T[u"state の分布"] == SEAL_STATE_COUNTS and T[u"state が前の便の記録と一致した行"] == b[u"J-1"])
    J[u"J-2"] = b[u"J-2"][0] <= T[u"VALUE_MISMATCH で engine の要素が根拠に無い"] <= b[u"J-2"][1]
    J[u"J-3"] = b[u"J-3"][0] <= T[u"型の件数"][TYPES_T[1]] <= b[u"J-3"][1]
    J[u"J-4"] = b[u"J-4"][0] <= T[u"T3 で engine の要素が候補の要素に在る"] <= b[u"J-4"][1]
    J[u"J-5"] = b[u"J-5"][0] <= T[u"型の件数"][TYPES_T[3]] <= b[u"J-5"][1]
    J[u"J-6"] = b[u"J-6"][0] <= T[u"型の件数"][TYPES_T[4]] <= b[u"J-6"][1]
    J[u"J-7"] = T[u"UNVERIFIABLE の reason の最多"] >= b[u"J-7"]
    J[u"J-8"] = b[u"J-8"][0] <= T[u"導出が engine の取り違えを正した形"] <= b[u"J-8"][1]
    J[u"J-9"] = b[u"J-9"][0] <= T[u"VALUE_MISMATCH で form が derived_value"] <= b[u"J-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"J-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % a.out)
    shas = collections.OrderedDict()
    for k, (rel, want) in MATERIALS.items():
        got = sha256_file(os.path.join(ROOT, rel))
        if got != want:
            raise Stop(u"%s の sha256 が封と違う: %s" % (rel, got))
        shas[rel] = got
    prev_rec = jload(os.path.join(ROOT, MATERIALS[u"prev_rec"][0]))
    texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))[u"claims"]}
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    entry_claims = {c[u"id"]: c for c in entry[u"claims"]}
    rows = build_rows(prev_rec[u"行"], entry_claims, labels, texts)
    T = tally(rows)
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) 前の便の記録の行が 302・母数 53・手がかりあり 34"] = (len(prev_rec[u"行"]) == 302 and T[u"母数"] == 53 and T[u"手がかりあり"] == 34)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) 53 行の id が entry と札に在り、札は全部 真"] = (T[u"札が 真"] == T[u"母数"])
    W[u"(e) state が前の便の記録と一致した行"] = T[u"state が前の便の記録と一致した行"]
    W[u"(f) 読めなかった pointer の在る行"] = T[u"読めなかった pointer の在る行"]
    W[u"(g) 手がかりあり で pointers が空でない行のうち engine の要素が S に在る"] = u"%d / %d" % (T[u"手がかりあり で engine の要素が S に在る"], T[u"手がかりあり で pointers が空でない"])
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) 前の便の記録の行が 302・母数 53・手がかりあり 34"] and W[u"(d) 53 行の id が entry と札に在り、札は全部 真"]
                      and W[u"(e) state が前の便の記録と一致した行"] == 53 and W[u"(f) 読めなかった pointer の在る行"] == 0)
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"engine(P16)が止めた真の文 53 行について、engine の pointers・recomputed・reason と、主語の制約つきの導出(深さ 1・6 型)の候補の fact と、"
                  u"盲検の札の根拠の字を突き合わせ、止めた理由を型 T1〜T6 に分けた記録。engine は走らせていない。1 書類・1 model の AI の文。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"型", list(TYPES_T)), (u"型の順", u"封 §2 の表を上から。最初に当たった型"),
                                         (u"要素が根拠に在る", u"local name が札の根拠の字に部分文字列として在る"),
                                         (u"T2 の engine の帯の参考", u"round: |d| ≤ u / 2、truncate: 0 ≤ d < u(d = |v| − |t|)。判定に使わない"),
                                         (u"予測の幅", BOUNDS), (u"封の state の分布", SEAL_STATE_COUNTS)])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"entry は P16 の判定。いまの既定 P27 の行ごとの記録は無い", u"型は字の突き合わせ。どちらが正しいかは札の根拠との部分一致で見るだけ",
                     u"1 書類・1 model の AI の文。導出は深さ 1・6 型", u"直す場所を決めるのは人間"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False))
    print(json.dumps(T[u"型の件数"], ensure_ascii=False))
    print(json.dumps(T[u"state × 型"], ensure_ascii=False))
    for k in (u"VALUE_MISMATCH で engine の要素が根拠に無い", u"VALUE_MISMATCH で form が derived_value", u"UNVERIFIABLE の reason の分布", u"UNVERIFIABLE で pointers が空でない",
              u"導出が engine の取り違えを正した形", u"T3 で engine の要素が候補の要素に在る", u"T2 の engine の帯の参考"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
