# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)― 封 ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md`` の段 2 の前半(下見と材料)。

**席は 1 回も呼ばない。通信しない。``core/``・``adapters/`` は 0 行。** 本物の席の便・採点(``--stage score``)は次の席。

  --stage dryrun    材料の生成・task file・見せない字の検査・トークンの見込み・P-7 の判定を、**本番と同じ配線**で通す。
                    task file と記録は repo の外(``$TMPDIR/hybrid_s2/dry/``)。repo には何も書かない。
  --stage score     段 2 の採点(0 USD。席は呼ばない)。材料・席の答え 8 本・便の記録 csv を読み、
                    ``fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json`` を書く(既に在れば止まる)。
  --stage material  同じ配線で、task file を ``$TMPDIR/hybrid_s2/tasks/``(repo の外)に、記録を
                    ``fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json`` に書く。

**C1 の材料(``xbrl_gen_c1_2026-10-20.py --stage material``)と同じ配線。** cd8 の材料 module ``MB`` を import して
``MB.main`` をそのまま回し、**注入の型の選び方(``MB.pick_injections``)だけ**を差し替える。問いの文・席に見せる字の作り方
(``MB.seat_text``)・行の選び方・Core/D′/D″ を当てる経路は ``MB`` のまま。差し替えは次の 4 つで、**どれも module の global を
ジョブの間だけ替えて戻す**(``patched``):

  1. ``MB.pick_injections`` ― 8 件 = T6_PRIOR 3・T7_ROUND 3・T2_UNIT 2(``inject.select(..., quota=...)``)。
     作れない型は quota を外して同じ順(T6 → T7 → T2)の巡回で他の型が埋める。3 型で 8 に届かない書類は、
     最後の手段として既存の T1_VALUE で埋める(``fallback``。司令塔の決定 2026-10-20)。
  2. ``MB.build_rows`` ― **T2_UNIT の行を注入の行と数えるための直し。** cd8 の ``build_rows`` は数の桁
     (``t.start``〜``t.end``)だけを注入の範囲と突き合わせる。T2 は単位の字だけを替える(範囲は桁の外)ので、そのままだと
     T2 の注入が「無改変の行」に数えられる。ここでは数 + 単位(``t.start``〜``t.unit_end``)で突き合わせる。他は同じ。
  3. ``MB.A1.gold_of`` ― 新しい型の ``正解``。cd8 の ``gold_of`` は T5/T3 以外を「値がどこにも無い」とする
     (T6 は値が書類に在る)ので、新しい 3 型だけ別の欄を返す。既存の型は元の関数。
  4. ``MB.PROFILE`` ― 測った当時の既定 profile = P21(``PROFILE_AT_MEASURE``)。段 1 と同じ ``席の前に出せる分``
     (各行の Core 自身 = P21 の state と参照先)。2026-10-20 段 2(期を縛る P22。封 ``docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md``)で
     ``vocabulary.DEFAULT_PROFILE`` が P22 になったので、記録を再現できるよう測った当時の P21 を字で留める。

見せない字: **封の字の 9 語(``C1.SPEC_BANNED``)を、task file を読み直して 0 件**(P-7 の主の判定。司令塔の決定 2026-10-20)。
依頼文が足した 5 語(T6・T7・T2・前期・丸め)は封の外で、**補助の欄**に件数だけ残す(「前期」は有価証券報告書の本文の字で、
C1 の task にも在る。C1 の task での件数も並べる)。故障(語を 1 つ混ぜた task)を作って検査が当たることも記録に残す。

    cd audit-core
    TMPDIR=<repo の外> python3 measure/xbrl_hybrid_s2_2026-10-20.py --stage dryrun
    TMPDIR=<repo の外> python3 measure/xbrl_hybrid_s2_2026-10-20.py --stage material
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


#: 段 1 の script(Core 自身の当て直しの経路・engine の留め)。**書き直さない**。
HT = _mod("measure/xbrl_hybrid_trust_2026-10-20.py", "hybrid_trust_for_s2")
C1, MB, G0 = HT.C1, HT.MB, HT.G0
IJ = MB.IJ
V = HT.V
# 記録(hybrid_s2_*.json)を測った時点の既定は P21。2026-10-20 段 2(期を縛る P22)で vocabulary.DEFAULT_PROFILE は P22 になったので、
# 測った当時の P21 を字で留める(profile を省く経路と、段 2 より前は同じ結果)。
PROFILE_AT_MEASURE = "P21"

SEAL = "docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md"
SEAL_COMMIT = "4a4df01"
GEN = C1.GEN
OUT = os.path.join(GEN, "hybrid_s2_material_2026-10-20.json")

#: 封 §2。1 書類 8 件 = T6 3・T7 3・T2 2。**字で留める**。
QUOTA = collections.OrderedDict([("T6_PRIOR", 3), ("T7_ROUND", 3), ("T2_UNIT", 2)])
#: 3 型で 8 に届かないときだけ使う既存の型(最後の手段)。
FALLBACK = ["T1_VALUE"]
ALL_TYPES = list(QUOTA) + FALLBACK
N_INJECT, N_PLAIN = 8, 16
NEW_TYPES = ("T6_PRIOR", "T7_ROUND")
#: 封 §2 の「見せない字」。C1 の 9 語に、段 2 の注入の型の名と、型の説明に使う語を足す。
EXTRA_BANNED = (u"T6", u"T7", u"T2", u"前期", u"丸め")
ALL_BANNED = tuple(C1.SPEC_BANNED) + EXTRA_BANNED
#: 封 §2 P-7 / 依頼文。
LEN_BAND = 0.30
TOKEN_TOTAL_CAP = 1600000
TOKEN_RUN_CAP = 250000


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def base_dirs(stage):
    u"""``$TMPDIR/hybrid_s2``(dryrun は ``.../dry``)。repo の中なら止まる。"""
    tmp = os.environ.get("TMPDIR")
    if not tmp:
        raise SystemExit(u"**TMPDIR が未設定。task file を repo の外に置くため、scratchpad を TMPDIR に向ける**")
    root = os.path.realpath(os.path.join(tmp, "hybrid_s2"))
    if root.startswith(os.path.realpath(ROOT) + os.sep):
        raise SystemExit(u"**task file の置き場が repo の中。止める: %s**" % root)
    if stage == "dryrun":
        root = os.path.join(root, "dry")
    return root, os.path.join(root, "work"), os.path.join(root, "tasks")


# ------------------------------------------------------------------ 差し替える 3 つの関数
def pick_s2(text, refs, seed, doc):
    u"""``MB.pick_injections`` の代わり。戻りは (chosen, counts)。counts は型ごとの {作れる site, 割当, 採った}。"""
    chosen, cat, _allowed, _withheld = IJ.select(text, refs, "xbrl", seed, doc, N_INJECT,
                                                 types=list(QUOTA), quota=dict(QUOTA), fallback=FALLBACK)
    got = collections.Counter(c["type"] for c in chosen)
    counts = {t: {u"作れる site": cat[t], u"割当": QUOTA.get(t, 0), u"採った": got.get(t, 0)} for t in ALL_TYPES}
    return chosen, counts


def build_rows_s2(text, chosen, placements):
    u"""``MB.build_rows`` と同じ。違いは注入の範囲との突き合わせだけ: 数の桁でなく **数 + 単位**(T2 は単位の字だけを替える)。"""
    inj_by_span = {}
    for c in chosen:
        a, b = placements[c["id"]]
        inj_by_span[(a, b)] = c
    rows, plain = [], []
    for t in MB.quantity_tokens(text):
        t_end = t.unit_end if t.unit else t.end
        hit = None
        for (a, b), c in inj_by_span.items():
            if not (t_end <= a or t.start >= b):
                hit = c
                break
        rec = {"数の字面": t.text, "値": t.value, "単位": t.unit,
               "span": [t.start, t.end], "抜粋": MB.excerpt(text, t.start, t.end)}
        if hit is not None:
            rec["**注入**"] = hit["id"]
            rows.append(rec)
        else:
            plain.append(rec)
    rows.extend(plain[:N_PLAIN])
    for i, r in enumerate(sorted(rows, key=lambda r: r["span"][0]), 1):
        r["id"] = "R%03d" % i
    return sorted(rows, key=lambda r: r["span"][0]), len(plain)


_ORIG_GOLD = MB.A1.gold_of


def gold_s2(inj):
    u"""新しい 3 型(T6・T7・T2)の ``正解``。既存の型は元の ``gold_of``。**参照先の正解は使わない**(採点は ``注入か``)。"""
    t, d = inj["type"], inj["detail"]
    A1 = MB.A1
    if t == "T6_PRIOR":
        return {u"種類": u"値は書類に在る(同じ要素の前期の値)", u"正解": A1.norm_pointer(d["true_ref_key"]),
                u"前期の側": A1.norm_pointer(d["prior_ref_key"])}
    if t == "T7_ROUND":
        return {u"種類": u"最後の桁が ±1(%+d)" % d["last_digit_delta"], u"正解": None, u"前期の側": None}
    if t == "T2_UNIT":
        return {u"種類": u"単位が違う(%s -> %s)" % (d["unit_before"], d["unit_after"]), u"正解": None, u"前期の側": None}
    return _ORIG_GOLD(inj)


@contextlib.contextmanager
def patched():
    old = (MB.pick_injections, MB.build_rows, MB.A1.gold_of, MB.PROFILE)
    MB.pick_injections, MB.build_rows, MB.A1.gold_of = pick_s2, build_rows_s2, gold_s2
    MB.PROFILE = PROFILE_AT_MEASURE
    try:
        yield
    finally:
        MB.pick_injections, MB.build_rows, MB.A1.gold_of, MB.PROFILE = old


# ------------------------------------------------------------------ 再構成(門が使う)
def rebuild(doc, work, seed):
    u"""本文から注入・行・task を**組み直す**(``patched`` の中で呼ぶ)。戻りは dict。"""
    old, MB.A1.TMP = MB.A1.TMP, work
    try:
        text, refs = MB.A1.material(doc)
    finally:
        MB.A1.TMP = old
    chosen, counts = MB.pick_injections(text, refs, seed, doc)
    tampered, placements = IJ.apply_edits(text, chosen)
    if IJ.revert(tampered, chosen, placements, text) != text:
        raise SystemExit(u"**round-trip が合わない: %s。止める**" % doc)
    rows, plain_total = MB.build_rows(tampered, chosen, placements)
    task = MB.seat_text(rows, tampered, refs)
    return {"text": text, "refs": refs, "chosen": chosen, "counts": counts, "tampered": tampered,
            "placements": placements, "rows": rows, "plain_total": plain_total, "task": task}


def site_diagnostics(text, refs):
    u"""site が少ない / 0 の書類の理由を 1 段ずつ読むための件数(``inject.t6_sites`` / ``t7_sites`` の絞り込みの段)。"""
    import random
    d6, d7 = collections.OrderedDict(), collections.OrderedDict()
    IJ.t6_sites(text, refs, d6)
    IJ.t7_sites(text, refs, random.Random(0), d7)
    return {u"T6_PRIOR の絞り込み(各段を通った数。出ない段は 0)": dict(sorted(d6.items())),
            u"T7_ROUND の絞り込み(各段を通った数)": dict(sorted(d7.items()))}


def banned_found(blob):
    return {w: blob.count(w) for w in ALL_BANNED if w in blob}


def banned_control_s2(tasks_dir):
    u"""見せない字の検査(``banned_found``)が**効いている**ことを、故障(語を 1 つ混ぜた task)を作って当てて確かめる。"""
    d0 = sorted(f for f in os.listdir(tasks_dir) if f.endswith("_task.txt"))[0]
    blob = io.open(os.path.join(tasks_dir, d0), encoding="utf-8").read()
    base = banned_found(blob)
    res = []
    for w in ALL_BANNED:
        # 混ぜる前の件数から 1 増えることを見る(元の task に在る語でも、混ぜた分を数える)
        found = banned_found(blob + w)
        res.append({u"混ぜた語": w, u"混ぜる前の件数": base.get(w, 0), u"混ぜた後の件数": found.get(w, 0),
                    u"当たった": found.get(w, 0) == base.get(w, 0) + 1})
    return {u"混ぜる前の task": d0, u"混ぜる前に見つかった語": base, u"語ごと": res,
            u"全語で当たった": all(r[u"当たった"] for r in res)}


SEC_BODY, SEC_DATA, SEC_ROWS = u"\n---- 文章 ----\n", u"\n---- 数値データの一覧 ----\n", u"\n---- 判定する行 ----\n"


def banned_by_place(task):
    u"""見つかった語が task file のどの部分に在るか(問いの文 / 文章 / 数値データの一覧 / 判定する行)。"""
    i, j, k = task.index(SEC_BODY), task.index(SEC_DATA), task.index(SEC_ROWS)
    return {u"問いの文": banned_found(task[:i]), u"文章": banned_found(task[i:j]),
            u"数値データの一覧": banned_found(task[j:k]), u"判定する行(抜粋は文章の一部の写し)": banned_found(task[k:])}


def inj_detail(c, text, placements, row_id):
    return {u"id": c["id"], u"型": c["type"], u"行 id": row_id,
            u"元の span": c["span"], u"改変後の span": placements[c["id"]],
            u"元の字": text[c["span"][0]:c["span"][1]], u"後の字": c["replacement"],
            u"元の値": c["detail"].get("original_value", c["new_value"]),   # T2 は数を替えない(新しい値 = 元の値)
            u"後の値": c["new_value"], u"detail": c["detail"]}


def c1_task(doc, work, seed, mat_doc):
    u"""C1 の task(cd8 の ``pick_injections`` / ``build_rows`` のまま = 差し替えの外)を本文から組み直す。
    sha256 が C1 の材料の記録(``fixtures/xbrl/gen_c/material_2026-10-20.json``)と一致しなければ止まる。"""
    old, MB.A1.TMP = MB.A1.TMP, work
    try:
        text, refs = MB.A1.material(doc)
    finally:
        MB.A1.TMP = old
    chosen, _counts = MB.pick_injections(text, refs, seed, doc)
    tampered, placements = IJ.apply_edits(text, chosen)
    rows, _n = MB.build_rows(tampered, chosen, placements)
    task = MB.seat_text(rows, tampered, refs)
    if hashlib.sha256(task.encode("utf-8")).hexdigest() != mat_doc[u"材料"][u"sha256"]:
        raise SystemExit(u"**組み直した C1 の task の sha256 が C1 の材料の記録と合わない: %s。止める**" % doc)
    return task


def build(work, tasks, tmp_rec, docs):
    u"""材料を組み、task file を ``tasks`` に置き、記録(dict)を返す。"""
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    with patched():
        rec = C1.run_material(C1.GEN_DRAW, work, tmp_rec, docs)
        if rec.get("profile") != PROFILE_AT_MEASURE:
            raise SystemExit(u"**材料の profile が既定でない: %r**" % rec.get("profile"))
        details = {}
        for p in rec[u"書類ごと"]:
            doc = p["docID"]
            rb = rebuild(doc, work, seed)
            if hashlib.sha256(rb["task"].encode("utf-8")).hexdigest() != p[u"材料"][u"sha256"]:
                raise SystemExit(u"**再構成した task の sha256 が材料の記録と合わない: %s**" % doc)
            if sorted(r["id"] for r in rb["rows"]) != sorted(p[u"席の前に出せる分"]):
                raise SystemExit(u"**再構成した行の id が材料の記録と合わない: %s**" % doc)
            row_of = {r["**注入**"]: r["id"] for r in rb["rows"] if r.get("**注入**")}
            details[doc] = {
                u"注入の明細": [inj_detail(c, rb["text"], rb["placements"], row_of.get(c["id"]))
                           for c in sorted(rb["chosen"], key=lambda c: c["span"][0])],
                u"型ごと": rb["counts"], u"診断": site_diagnostics(rb["text"], rb["refs"]),
                u"語の出どころ": {u"原文の本文": banned_found(rb["text"]), u"改変後の本文": banned_found(rb["tampered"]),
                             u"問いの文": banned_found(MB.PROMPT)}}
    for d in docs:
        shutil.copyfile(os.path.join(work, "%s_task.txt" % d), os.path.join(tasks, "%s_task.txt" % d))
    if sorted(os.listdir(tasks)) != sorted("%s_task.txt" % d for d in docs):
        raise SystemExit(u"**tasks/ に task file 8 本以外が在る**")
    return rec, details


def doc_row(p, det, tasks, c1_chars):
    doc = p["docID"]
    path = os.path.join(tasks, "%s_task.txt" % doc)
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8")
    banned14 = banned_found(text)
    banned = {w: n for w, n in banned14.items() if w in C1.SPEC_BANNED}      # 封の字の 9 語(主)
    aux = {w: n for w, n in banned14.items() if w in EXTRA_BANNED}          # 依頼文が足した 5 語(補助。封の外)
    tok = C1.token_views(len(text), text)
    got = collections.Counter(x[u"型"] for x in det[u"注入の明細"])
    made = {t: got.get(t, 0) for t in QUOTA}
    t1 = got.get("T1_VALUE", 0)
    ratio = len(text) / float(c1_chars)
    shortfall = {t: {u"割当": QUOTA[t], u"採れた": made[t], u"作れる site": det[u"型ごと"][t][u"作れる site"]}
                 for t in QUOTA if made[t] < QUOTA[t]}
    pre = p[u"席の前に出せる分"]
    rows_inj = sum(1 for v in pre.values() if v[u"注入か"])
    return {
        u"docID": doc,
        u"注入": {u"件数": len(det[u"注入の明細"]), u"**8 件そろったか**": len(det[u"注入の明細"]) == N_INJECT,
                u"型の内訳": dict(sorted(got.items())), u"作れた型の数(T6/T7/T2)": made,
                u"T1_VALUE で埋めた数": t1,
                u"割当どおりか(T6 3・T7 3・T2 2)": made == dict(QUOTA) and t1 == 0,
                u"型ごと(作れる site・割当・採った)": det[u"型ごと"],
                u"割当に届かなかった型": shortfall,
                u"届かなかった型を埋めた型": {t: made[t] - QUOTA[t] for t in QUOTA if made[t] > QUOTA[t]},
                u"割当とのずれ": {t: {u"割当": QUOTA[t], u"実数": made[t], u"差": made[t] - QUOTA[t]} for t in QUOTA},
                u"明細": det[u"注入の明細"]},
        u"理由(site の絞り込みの各段)": det[u"診断"],
        u"行": {u"合計": len(pre), u"注入の行": rows_inj, u"無改変の行": len(pre) - rows_inj,
               u"無改変の候補の総数": p[u"行"][u"無改変の候補の総数"],
               u"**24 行そろったか**": len(pre) == N_INJECT + N_PLAIN and rows_inj == N_INJECT},
        u"task": {u"字数": len(text), u"sha256": sha_bytes(raw),
                  u"記録(材料 script)の字数": p[u"材料"][u"字数"], u"記録(材料 script)の sha256": p[u"材料"][u"sha256"],
                  u"記録と一致": len(text) == p[u"材料"][u"字数"] and sha_bytes(raw) == p[u"材料"][u"sha256"],
                  u"C1 の task の字数": c1_chars, u"C1 比": round(ratio, 4),
                  u"C1 の ±30% の中": abs(ratio - 1.0) <= LEN_BAND + 1e-12},
        u"見せない字": {u"検査した語(主。封の字の 9 語)": list(C1.SPEC_BANNED),
                    u"task file を読み直して見つかった(封の字の 9 語)": banned,
                    u"材料 script の検査(MB.BANNED)で見つかった": p[u"**見せない字**"][u"見つかった"],
                    u"**0 件か**(封の字の 9 語)": (not banned) and not p[u"**見せない字**"][u"見つかった"],
                    u"補助(封の外。依頼文が足した 5 語 T6・T7・T2・前期・丸め)": {
                        u"検査した語": list(EXTRA_BANNED), u"task file を読み直して見つかった": aux,
                        u"見つかった語の出どころ(件数)": det[u"語の出どころ"],
                        u"見つかった語の task の中の場所(件数)": banned_by_place(text)}},
        u"トークン見込み": tok,
        u"他の行への影響(判定が動いた)": p[u"**他の行への影響の検査**"][u"**判定が動いた**"],
    }


def run(stage):
    t_start = time.time()
    env = C1.no_keys()
    root, work, tasks = base_dirs(stage)
    if stage == "material" and os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(作り直さない)" % OUT)
    for d in (work, tasks):
        if os.path.exists(d) and os.listdir(d):
            raise SystemExit(u"**空でない: %s(作り直さない。消すのは人)**" % d)
        if not os.path.exists(d):
            os.makedirs(d)
    draw = C1._load(C1.GEN_DRAW)
    docs = draw[u"引いた 8 件"]
    for d in docs:
        if not os.path.exists(C1.ED.cache_path(d)):
            raise SystemExit(u"**ZIP が無い: %s**" % d)
    tmp_rec = os.path.join(root, "material_tmp.json")
    if os.path.exists(tmp_rec):
        raise SystemExit(u"**既に在る: %s(作り直さない)**" % tmp_rec)
    c1_mat = C1._load(C1.GEN_MAT)
    c1_chars = {p["docID"]: p[u"材料"][u"字数"] for p in c1_mat[u"書類ごと"]}
    t0 = time.time()
    rec, details = build(work, tasks, tmp_rec, docs)
    t_mat = time.time() - t0
    if [p["docID"] for p in rec[u"書類ごと"]] != docs:
        raise SystemExit(u"**材料の書類が draw の 8 件と合わない**")
    per = [doc_row(p, details[p["docID"]], tasks, c1_chars[p["docID"]]) for p in rec[u"書類ごと"]]
    bad = [r[u"docID"] for r in per if not r[u"task"][u"記録と一致"]]
    if bad:
        raise SystemExit(u"**task file が記録と合わない: %s**" % bad)
    ctrl = banned_control_s2(tasks)

    # ---- 合計
    by_type = collections.Counter()
    inj_total = plain_total = 0
    for r in per:
        by_type.update(r[u"注入"][u"型の内訳"])
        inj_total += r[u"行"][u"注入の行"]
        plain_total += r[u"行"][u"無改変の行"]
    toks = [r[u"トークン見込み"][u"傾き(席の往復 + 傾き × 字数)"] for r in per]
    naive = [r[u"トークン見込み"][u"素朴(材料だけ。ASCII は 4 字で 1・日本語は 1 字で 1。席の往復を含まない)"] for r in per]
    c1_est = c1_mat[u"**K-1 の数**"][u"集計"][u"合計"][u"トークン見込み(傾き)"]
    c1_run = C1.seat_runs()
    tok_view = {
        u"方法": u"C1 の「傾き」(cd8 の下見 cost_breakdown_2026-10-17.json の過去の 2 点から 席の往復 + 傾き × 字数)。素朴は併記(平均しない)",
        u"見込み(傾き)の書類ごと": {r[u"docID"]: t for r, t in zip(per, toks)},
        u"見込み(傾き)の合計": sum(toks), u"見込み(傾き)の 1 便の最大": max(toks),
        u"見込み(素朴。席の往復を含まない)の合計": sum(naive),
        u"上限": {u"合計": TOKEN_TOTAL_CAP, u"1 便": TOKEN_RUN_CAP},
        u"合計が上限以下": sum(toks) <= TOKEN_TOTAL_CAP, u"1 便がどれも上限以下": max(toks) <= TOKEN_RUN_CAP,
        u"**上限の中か**": sum(toks) <= TOKEN_TOTAL_CAP and max(toks) <= TOKEN_RUN_CAP,
        u"C1 の見込み(傾き)の合計": c1_est, u"C1 の実測の合計": c1_run[u"合計トークン"],
        u"C1 の見込みに対する実測の比": round(c1_run[u"合計トークン"] / float(c1_est), 4),
        u"封 P-5 の幅(参考。実測は席の便の後)": [700000, 1200000]}
    # ---- 補助(封の外): 依頼文が足した 5 語の件数。C1 の task(sha256 が C1 の記録と一致するもの)での件数を並べる
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    c1_aux = {}
    for p in c1_mat[u"書類ごと"]:
        t = c1_task(p["docID"], work, seed, p)
        c1_aux[p["docID"]] = {w: n for w, n in banned_found(t).items() if w in EXTRA_BANNED}
    ctrl9 = all(x[u"当たった"] for x in ctrl[u"語ごと"] if x[u"混ぜた語"] in C1.SPEC_BANNED)
    len_ok = all(r[u"task"][u"C1 の ±30% の中"] for r in per)
    zero9 = all(r[u"見せない字"][u"**0 件か**(封の字の 9 語)"] for r in per)
    aux_total = dict(sum((collections.Counter(r[u"見せない字"][u"補助(封の外。依頼文が足した 5 語 T6・T7・T2・前期・丸め)"][u"task file を読み直して見つかった"])
                          for r in per), collections.Counter()))
    p7 = {
        u"中身": u"封 P-7: 見せない字 0(封の字の 9 語)かつ task の字数が C1 の ±30%(書類ごと)。司令塔の決定 2026-10-20 で、"
               u"依頼文が足した 5 語(T6・T7・T2・前期・丸め)は封の外 = 補助の欄に数だけ残す",
        u"見せない字 0(8 書類とも。封の字の 9 語)": zero9,
        u"字数が C1 の ±30% の中(8 書類とも)": len_ok,
        u"見せない字の検査の対照(故障を作って封の字の 9 語すべてで当たった)": ctrl9,
        u"書類ごと": [{u"docID": r[u"docID"], u"字数": r[u"task"][u"字数"], u"C1 の字数": r[u"task"][u"C1 の task の字数"],
                    u"C1 比": r[u"task"][u"C1 比"], u"±30% の中": r[u"task"][u"C1 の ±30% の中"],
                    u"見せない字(封の字の 9 語)": r[u"見せない字"][u"task file を読み直して見つかった(封の字の 9 語)"]} for r in per],
        u"補助(封の外。依頼文が足した 5 語。判定には使わない)": {
            u"この task で見つかった語の合計": aux_total,
            u"書類ごと(この task)": {r[u"docID"]: r[u"見せない字"][u"補助(封の外。依頼文が足した 5 語 T6・T7・T2・前期・丸め)"][u"task file を読み直して見つかった"] for r in per},
            u"C1 の task(sha256 が C1 の記録と一致)での件数": c1_aux,
            u"C1 の task での合計": dict(sum((collections.Counter(v) for v in c1_aux.values()), collections.Counter())),
            u"note": u"「前期」は有価証券報告書の本文の字。C1 の task にも在る。この task との差は判定行の抜粋の違い",
            u"14 語(封の 9 語 + 5 語)で 0 件か(参考)": zero9 and not aux_total}}
    p7[u"**P-7 の判定**"] = u"緑" if (zero9 and len_ok and ctrl9) else u"赤"
    gate_ok = (all(r[u"行"][u"**24 行そろったか**"] for r in per) and p7[u"**P-7 の判定**"] == u"緑"
               and tok_view[u"**上限の中か**"])

    pins = HT.engine_pins()
    prompt_sha = rec[u"問いの sha256"]
    rec["spec"] = MB.SPEC
    rec["cd8 の script の既定値だった seal"] = rec.pop("seal")
    rec["seal"] = SEAL + u" §2(段 2)・§3・§4"
    rec["step"] = (u"**席と Core の一致の信頼 段 2 の前半(下見と材料)。0 USD・席を 1 回も呼んでいない・通信していない**"
                   if stage == "material" else u"**段 2 の下見(dryrun)。記録は repo の外**")
    rec[u"引いた 8 件"] = docs
    rec[u"draw"] = "fixtures/xbrl/gen_c/draw_2026-10-20.json"
    rec[u"環境"] = env
    rec[u"engine の留め"] = pins
    rec[u"問いの sha256 が C1 の字(PROMPT_SHA)と一致"] = prompt_sha == C1.PROMPT_SHA
    rec[u"問いの sha256(C1 の PROMPT_SHA)"] = C1.PROMPT_SHA
    rec[u"注入の種"] = {"file": "measure/SEED.json", u"note": u"inject.verify_seed_sealed が通った(追跡され、コミット内容と一致)",
                     u"種の字": IJ.verify_seed_sealed(MB.SEED_FILE)[0]}
    t7_stage = collections.OrderedDict()
    for r in per:
        for k, v in r[u"理由(site の絞り込みの各段)"][u"T7_ROUND の絞り込み(各段を通った数)"].items():
            t7_stage[k] = t7_stage.get(k, 0) + v
    rec[u"注入の型"] = {u"1 書類 8 件の割当": dict(QUOTA),
                    u"作り方": u"inject.select(..., types=[T6_PRIOR, T7_ROUND, T2_UNIT], quota=割当, fallback=[T1_VALUE])。"
                           u"割当に届かない型は quota を外し同じ順の巡回で他の型が埋め、3 型で 8 に届かないときだけ既存の T1_VALUE で埋める。"
                           u"1 つの数に注入は 1 件",
                    u"T7 の site の条件": u"値が refs に在る数 + 最後の桁 ±1 で桁数が変わらず正 + (a) 字面の桁が 3 桁以上(±1 が 1% 以下)"
                                      u" + (b) 後の値が refs のどの fact の値とも一致しない",
                    u"T7 の絞りの段ごとの site の数(8 書類の合計)": dict(t7_stage),
                    u"T7 の絞りの前に採っていた T7 の注入の数(司令塔の決定の前。dryrun 1 回目)": 31,
                    u"既存の型が材料に在る件数": {t: by_type.get(t, 0) for t in ("T1_VALUE", "T3_ABSENT", "T5_COINCIDENT")},
                    u"T1_VALUE は 3 型で 8 に届かなかった書類を埋めた数だけ": by_type.get("T1_VALUE", 0)}
    rec[u"書類ごと(段 2)"] = per
    rec[u"合計(段 2)"] = {
        u"書類": len(per), u"注入の行": inj_total, u"無改変の行": plain_total,
        u"型別の注入": {t: by_type.get(t, 0) for t in ALL_TYPES},
        u"割当の合計(書類 8 × 割当)": {t: QUOTA[t] * len(per) for t in QUOTA},
        u"割当とのずれ": {t: {u"割当(封の 24/24/16)": QUOTA[t] * len(per), u"実数": by_type.get(t, 0),
                          u"差": by_type.get(t, 0) - QUOTA[t] * len(per)} for t in QUOTA},
        u"割当とのずれ(note)": u"採点の席が封の予測 P-1 の型別の分母に使う。T1 は割当 0 で、3 型で届かなかった分を埋めた数",
        u"T1_VALUE で埋めた書類": [r[u"docID"] for r in per if r[u"注入"][u"T1_VALUE で埋めた数"]],
        u"割当どおりだった書類": sum(1 for r in per if r[u"注入"][u"割当どおりか(T6 3・T7 3・T2 2)"]),
        u"T6 を 1 件も作れなかった書類": [r[u"docID"] for r in per if r[u"注入"][u"作れた型の数(T6/T7/T2)"]["T6_PRIOR"] == 0],
        u"8 書類とも注入 8 件・24 行そろった": all(r[u"行"][u"**24 行そろったか**"] for r in per)}
    rec[u"トークンの見込み"] = tok_view
    rec[u"**P-7**"] = p7
    rec[u"見せない字の検査の対照(故障を作って当てた)"] = ctrl
    rec[u"task file の置き場"] = {u"絶対 path": tasks, u"repo の外か": not os.path.realpath(tasks).startswith(
        os.path.realpath(ROOT) + os.sep), u"file 数": len(os.listdir(tasks)),
        u"note": u"席は自分の task file 1 つだけを読む。(ア) の中間 file は別の work/ に在り tasks/ には無い"}
    rec[u"割当とのずれ"] = rec[u"合計(段 2)"][u"割当とのずれ"]
    rec[u"**下見の総合**"] = {u"段 2 に進めるか": gate_ok,
                         u"中身": u"8 書類とも 24 行(注入 8)・P-7 緑(封の字の 9 語)・トークン見込みが上限の中。赤なら段 2 はやらない(封)"}
    rec[u"所要秒"] = {u"材料": round(t_mat, 1), u"全体": round(time.time() - t_start, 1)}
    rec["limits"] = rec["limits"] + [
        u"**task file は repo に入れていない。**sha256 と字数だけを記録に書いた(門は本文から組み直して突き合わせる)",
        u"席は呼んでいない。トークンは見込みで、実測は席の便の後",
        u"cd8 の ``build_rows`` は T2 の注入を無改変の行に数える(桁だけで突き合わせる)ので、この script は数 + 単位で突き合わせる版に替えた",
        u"新しい型 T6・T7 の ``正解`` は cd8 の ``gold_of`` に無い型なので、この script の ``gold_s2`` が返す(参照先の正解は採点に使わない)",
        u"site が作れない書類が出た。作れた数は ``書類ごと(段 2)`` に書き、分母から外さない",
        u"P-7 の主の判定は封の字の 9 語。依頼文が足した 5 語は封の外で補助の欄(司令塔の決定 2026-10-20)"]
    return rec, tmp_rec, gate_ok


def stage_dryrun(a):
    rec, tmp_rec, ok = run("dryrun")
    root = base_dirs("dryrun")[0]
    out = os.path.join(root, "dryrun_record.json")
    C1._dump(rec, out)
    os.remove(tmp_rec)
    summarize(rec, u"下見")
    print("-> %s(repo の外。repo には何も書いていない)" % out)
    return 0


def stage_material(a):
    rec, tmp_rec, ok = run("material")
    dry = os.path.join(base_dirs("dryrun")[0], "dryrun_record.json")
    if os.path.exists(dry):
        d = C1._load(dry)
        same = {r[u"docID"]: r[u"task"][u"sha256"] for r in d[u"書類ごと(段 2)"]} == \
               {r[u"docID"]: r[u"task"][u"sha256"] for r in rec[u"書類ごと(段 2)"]}
        rec[u"下見(dryrun)の task の sha256 と一致"] = same
    else:
        rec[u"下見(dryrun)の task の sha256 と一致"] = None
    C1._dump(rec, OUT)
    os.remove(tmp_rec)
    summarize(rec, u"材料")
    print("->", OUT)
    return 0


def summarize(rec, label):
    t = rec[u"合計(段 2)"]
    print(u"=== 段 2 %s: 書類 %d / 注入の行 %d / 無改変の行 %d / 型別 %s ===" % (
        label, t[u"書類"], t[u"注入の行"], t[u"無改変の行"], t[u"型別の注入"]))
    for r in rec[u"書類ごと(段 2)"]:
        print(u"  %s T6/T7/T2 %s +T1 %d 行 %d(注入 %d) 字数 %d(C1 比 %.3f) 見せない字 %s" % (
            r[u"docID"], r[u"注入"][u"作れた型の数(T6/T7/T2)"], r[u"注入"][u"T1_VALUE で埋めた数"], r[u"行"][u"合計"], r[u"行"][u"注入の行"],
            r[u"task"][u"字数"], r[u"task"][u"C1 比"],
            r[u"見せない字"][u"task file を読み直して見つかった(封の字の 9 語)"] or u"0 件"))
    print(u"  トークン見込み(傾き)合計 %d / 1 便最大 %d(上限 %d / %d)" % (
        rec[u"トークンの見込み"][u"見込み(傾き)の合計"], rec[u"トークンの見込み"][u"見込み(傾き)の 1 便の最大"],
        TOKEN_TOTAL_CAP, TOKEN_RUN_CAP))
    print(u"  P-7(封の字の 9 語)%s / 下見の総合 %s" % (rec[u"**P-7**"][u"**P-7 の判定**"], rec[u"**下見の総合**"][u"段 2 に進めるか"]))


# ------------------------------------------------------------------ 採点(--stage score。0 USD・席を呼ばない・通信しない)
SCORE_OUT = os.path.join(GEN, "hybrid_s2_2026-10-20.json")
ANS_DIR = os.path.join(GEN, "hybrid_s2_answers")
RUNS_CSV = os.path.join(GEN, "hybrid_s2_runs_2026-10-20.csv")
S1_REC = os.path.join(GEN, "hybrid_trust_2026-10-20.json")

#: 封 §2 の段 2 の予測の幅(封の字。門は封の本文から読み直して突き合わせる)。
P1_RANGE = (6, 20)           # 席が支持した注入 / 64
P1_T7 = (3, 12)              # / 24(封の分母。実数は 10)
P1_T2 = (0, 4)               # / 16(封の分母。実数は 44)
P2_RANGE = (0, 6)            # Core が通した注入(α 型 GROUNDED) / 64
P3_G1 = (70, 92)             # G1 の精度(%)
P3_G2_PT = 5                 # G2 >= G1 + 5 pt
P3_G3_PT = 10                # G3 <= G1 - 10 pt
P4_NUM = 2                   # G3 に落ちる数 >= 席が支持した注入の 2/3
P4_DEN = 3
P5_TOTAL = (700000, 1200000)
P5_RUN_CAP = 250000
P6_G1_UNMOD = (60, 90)       # G1 の無改変
P6_FALSE = (0, 3)            # 偽警報
P6_G3_SHARE = (25, 45)       # G3 の無改変 / G1 の無改変(%)
SEAT_WORDS = (u"確認済み", u"誤りが在る", u"判定できない")
INJ_TYPES = ("T6_PRIOR", "T7_ROUND", "T2_UNIT")
T2_FAMILY = {"money": u"金額系", "ratio": u"％系", "count_item": u"件→回"}
GROUP_KEYS = (u"T6_PRIOR", u"T7_ROUND", u"T2_UNIT", u"T2_UNIT 金額系", u"T2_UNIT ％系", u"T2_UNIT 件→回")


def ratio_pct(a, b):
    from fractions import Fraction
    return Fraction(100 * a, b) if b else None


def runs_of_csv():
    import csv
    with io.open(RUNS_CSV, encoding="utf-8", newline="") as fh:
        rd = list(csv.reader(fh))
    body = rd[1:]
    rows = [{u"docID": r[0], u"model": r[1], u"合計トークン": int(r[2]), u"所要 ms": int(r[3]), u"行数": int(r[4]),
             u"開始(UTC)": r[5]} for r in body]
    tok = [r[u"合計トークン"] for r in rows]
    return {u"file": os.path.relpath(RUNS_CSV, ROOT), u"列": rd[0], u"便の数": len(rows), u"書類ごと": rows,
            u"model": sorted({r[u"model"] for r in rows}), u"合計トークン": sum(tok), u"最小": min(tok), u"最大": max(tok),
            u"1 便が上限を超えた便": [r[u"docID"] for r in rows if r[u"合計トークン"] > P5_RUN_CAP],
            u"行数が 24 でない便": [r[u"docID"] for r in rows if r[u"行数"] != 24]}


def score_work_dir():
    tmp = os.environ.get("TMPDIR")
    if not tmp:
        raise SystemExit(u"**TMPDIR が未設定。中間 file を repo の外に置くため、scratchpad を TMPDIR に向ける**")
    root = os.path.realpath(os.path.join(tmp, "hybrid_s2_score"))
    if root.startswith(os.path.realpath(ROOT) + os.sep):
        raise SystemExit(u"**中間 file の置き場が repo の中。止める: %s**" % root)
    work = os.path.join(root, "work")
    if not os.path.exists(work):
        os.makedirs(work)
    return work


def type_keys(r):
    u"""行の型別の集計キー(注入でない行は空)。T2 は系も数える。"""
    if not r[u"注入か"]:
        return []
    t = r[u"注入の型"]
    ks = [t]
    if t == "T2_UNIT":
        ks.append(u"T2_UNIT %s" % r[u"T2 の系"])
    return ks


def stage_score(a):
    t_start = time.time()
    env = C1.no_keys()
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s(採り直さない)" % a.out)
    mat = C1._load(OUT)
    if mat.get("profile") != PROFILE_AT_MEASURE or PROFILE_AT_MEASURE != "P21":
        raise SystemExit(u"**材料の profile が P21 でない(記録を測った当時の profile)。止める**")
    docs = [p["docID"] for p in mat[u"書類ごと"]]
    if len(docs) != 8:
        raise SystemExit(u"**材料の書類が 8 でない**")
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    registry = HT.RS.register_all(HT.core.Registry.default())
    work = score_work_dir()
    inputs = {
        u"材料 hybrid_s2_material_2026-10-20.json": C1.sha_file(OUT),
        u"席の答え(hybrid_s2_answers)": {fn: C1.sha_file(os.path.join(ANS_DIR, fn))
                                   for fn in sorted(os.listdir(ANS_DIR)) if fn.endswith("_answer.json")},
        u"便の記録 hybrid_s2_runs_2026-10-20.csv": C1.sha_file(RUNS_CSV),
        u"段 1 の記録 hybrid_trust_2026-10-20.json": C1.sha_file(S1_REC),
        u"draw": C1.sha_file(C1.GEN_DRAW),
        u"封": C1.sha_file(os.path.join(ROOT, SEAL))}
    if sorted(inputs[u"席の答え(hybrid_s2_answers)"]) != sorted("%s_answer.json" % d for d in docs):
        raise SystemExit(u"**席の答えの file が 8 書類と合わない**")

    rows_all, answer_check, item_of = [], {}, {}
    t0 = time.time()
    with patched():
        for p in mat[u"書類ごと"]:
            doc = p["docID"]
            det_doc = next(x for x in mat[u"書類ごと(段 2)"] if x["docID"] == doc)
            rb = rebuild(doc, work, seed)
            if hashlib.sha256(rb["task"].encode("utf-8")).hexdigest() != p[u"材料"][u"sha256"]:
                raise SystemExit(u"**再構成した task の sha256 が材料の記録と合わない: %s**" % doc)
            pre = p[u"席の前に出せる分"]
            if sorted(r["id"] for r in rb["rows"]) != sorted(pre):
                raise SystemExit(u"**再構成した行の id が材料の記録と合わない: %s**" % doc)
            by_id = HT.AL.answers_by_id(ANS_DIR, doc)
            answer_check[doc] = {u"答えの行数": len(by_id), u"id が 24 行と一致": sorted(by_id) == sorted(pre),
                                 u"判定語": dict(sorted(collections.Counter(str(v.get(u"判定")) for v in by_id.values()).items()))}
            chosen = {c["id"]: c for c in rb["chosen"]}
            mdet = {x[u"行 id"]: x for x in det_doc[u"注入"][u"明細"]}
            dc = HT.AL.DocCtx(doc)
            for m in sorted(rb["rows"], key=lambda r: r["id"]):
                rid = m["id"]
                inj_id = m.get("**注入**")
                if bool(inj_id) != bool(pre[rid][u"注入か"]) or bool(inj_id) != (rid in mdet):
                    raise SystemExit(u"**注入の行が材料の記録と合わない: %s %s**" % (doc, rid))
                typ = fam = None
                orig = after = None
                if inj_id:
                    c = chosen[inj_id]
                    typ = c["type"]
                    if typ != mdet[rid][u"型"]:
                        raise SystemExit(u"**注入の型が材料の記録と合わない: %s %s**" % (doc, rid))
                    if typ == "T2_UNIT":
                        fam = T2_FAMILY[c["detail"]["unit_family"]]
                    orig, after = mdet[rid][u"元の字"], mdet[rid][u"後の字"]
                seat = HT.AL.SC.seat_row(by_id.get(rid))
                if seat[u"判定"] not in SEAT_WORDS:
                    raise SystemExit(u"**席の判定が 3 語の外(欠け): %s %s %r**" % (doc, rid, seat))
                al = None
                if seat[u"参照先"] is not None:
                    raw = str(by_id[rid][u"参照先"]).strip()
                    al = HT.AL.engine_item(dc, registry, m, raw, u"席 A の参照先", "S2", with_reading=True)
                    item_of[(doc, rid)] = al
                core_c = pre[rid]["Core"]
                cs = HT.core_state(core_c)
                a_state = al[u"engine の state"] if al else u"参照先なし"
                g1 = seat[u"判定"] == u"確認済み"
                grp_a = (u"G2" if a_state == "GROUNDED" else u"G3") if g1 else None
                grp_s = (u"G2" if cs == "GROUNDED" else u"G3") if g1 else None
                use = u"α 型" if al is not None else u"Core 自身"
                use_state = a_state if al is not None else cs
                rows_all.append({
                    u"doc": doc, u"id": rid, u"注入か": bool(inj_id), u"注入 id": inj_id, u"注入の型": typ, u"T2 の系": fam,
                    u"元の字": orig, u"後の字": after, u"正解": pre[rid][u"正解"],
                    u"材料の値": m[u"値"], u"材料の単位": m[u"単位"], u"数の字面": m[u"数の字面"], u"抜粋": m[u"抜粋"],
                    u"席の判定": seat[u"判定"], u"席の参照先": seat[u"参照先"],
                    u"α 型の state": a_state, u"α 型の参照先": al[u"参照先(原文)"] if al else None,
                    u"α 型の reason": al[u"engine の reason"] if al else None,
                    u"α 型の held": al[u"held(製品の経路)"] if al else None,
                    u"α 型の hold_rules": list(al[u"hold_rules(製品の経路)"]) if al else None,
                    u"α 型の露出 U": al[u"露出 U(単位の種類が違う)"] if al else None,
                    u"α 型の露出 (d)": al[u"露出 (d)(同額の次元兄弟)"] if al else None,
                    u"α 型の露出 P": al[u"露出 P(同額の期間兄弟)"] if al else None,
                    u"α 型の参照先の fact の値": al[u"参照先の fact の値"] if al else None,
                    u"Core 自身(既定)の state": cs, u"Core 自身(既定)の参照先": core_c["参照先"],
                    u"Core 自身(既定)の言うこと": core_c[u"言うこと"],
                    u"G1(席が確認済み)": g1, u"群(α 型)": grp_a, u"群(Core 自身)": grp_s,
                    u"H の Core の出どころ": use, u"H の Core の state": use_state,
                    u"H の出力": HT.h_rule(seat[u"判定"], use_state == "GROUNDED")})
    t_run = time.time() - t0
    if len(rows_all) != 192 or sum(1 for r in rows_all if r[u"注入か"]) != 64:
        raise SystemExit(u"**行が 192 / 注入が 64 でない**")

    # ---- 集計(行から数える)
    rs = rows_all
    inj = [r for r in rs if r[u"注入か"]]
    unc = [r for r in rs if not r[u"注入か"]]
    sc = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
    seat_facts = {u"行": len(rs), u"注入": len(inj), u"無改変": len(unc),
                  u"席が確認済みにした注入(見逃し)": sc(inj, u"確認済み"), u"席が誤りが在るにした注入(検出)": sc(inj, u"誤りが在る"),
                  u"席が判定できないにした注入": sc(inj, u"判定できない"),
                  u"席が確認済みにした無改変": sc(unc, u"確認済み"), u"席が判定できないにした無改変": sc(unc, u"判定できない"),
                  u"席の偽警報(無改変で誤りが在る)": sc(unc, u"誤りが在る")}
    ga = HT.tally_groups(rs, u"α 型の state", u"群(α 型)")
    gs = HT.tally_groups(rs, u"Core 自身(既定)の state", u"群(Core 自身)")
    g1_rows = [r for r in rs if r[u"G1(席が確認済み)"]]
    hout = {}
    for kind, m in ((u"無改変", unc), (u"注入", inj), (u"全部", rs)):
        hout[kind] = dict(sorted(collections.Counter(r[u"H の出力"] for r in m).items()))
    passed = lambda m: sum(1 for r in m if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))

    by_type = collections.OrderedDict()
    for key in GROUP_KEYS:
        m = [r for r in inj if key in type_keys(r)]
        g1m = [r for r in m if r[u"G1(席が確認済み)"]]
        al_m = [r for r in m if r[u"α 型の state"] != u"参照先なし"]
        by_type[key] = {
            u"注入": len(m),
            u"席の判定": {w: sc(m, w) for w in SEAT_WORDS},
            u"席の見逃し(確認済み)": HT.frac(len(g1m), len(m)),
            u"α 型を当てた注入(席が参照先を名指した)": len(al_m),
            u"α 型の state(注入の行の全部)": dict(sorted(collections.Counter(r[u"α 型の state"] for r in m).items())),
            u"Core が通した(α 型 GROUNDED。注入の行の全部)": HT.frac(sum(1 for r in m if r[u"α 型の state"] == "GROUNDED"), len(m)),
            u"Core 自身が GROUNDED": HT.frac(sum(1 for r in m if r[u"Core 自身(既定)の state"] == "GROUNDED"), len(m)),
            u"席の見逃しのうち G2(α 型 GROUNDED)": sum(1 for r in g1m if r[u"群(α 型)"] == u"G2"),
            u"席の見逃しのうち G3(α 型)": sum(1 for r in g1m if r[u"群(α 型)"] == u"G3"),
            u"席の見逃しのうち G3 の α 型の state": dict(sorted(collections.Counter(r[u"α 型の state"] for r in g1m if r[u"群(α 型)"] == u"G3").items())),
            u"保留規則の発火(hold_rules。α 型を当てた注入)": {
                k: sum(1 for r in al_m if k in r[u"α 型の hold_rules"]) for k in ("d", "P", "U")},
            u"保留(held)": sum(1 for r in al_m if r[u"α 型の held"]),
            u"露出(条件が揃った。発火とは別)": {
                u"U": sum(1 for r in al_m if r[u"α 型の露出 U"]), u"(d)": sum(1 for r in al_m if r[u"α 型の露出 (d)"]),
                u"P": sum(1 for r in al_m if r[u"α 型の露出 P"])},
            u"H の出力": dict(sorted(collections.Counter(r[u"H の出力"] for r in m).items())),
            u"誤りを通した(二重確認か Core のみ確認)": HT.frac(passed(m), len(m))}
    # 書類別
    by_doc = collections.OrderedDict()
    for d in docs:
        m = [r for r in inj if r["doc"] == d]
        by_doc[d] = {u"注入": len(m), u"型": dict(sorted(collections.Counter(r[u"注入の型"] for r in m).items())),
                     u"席が確認済みにした注入": sc(m, u"確認済み"),
                     u"席が確認済みにした無改変": sc([r for r in unc if r["doc"] == d], u"確認済み")}
    missed = [{u"doc": r["doc"], u"id": r["id"], u"型": r[u"注入の型"], u"T2 の系": r[u"T2 の系"], u"元の字": r[u"元の字"],
               u"後の字": r[u"後の字"], u"抜粋": r[u"抜粋"], u"α 型の state": r[u"α 型の state"], u"群(α 型)": r[u"群(α 型)"],
               u"Core 自身(既定)の state": r[u"Core 自身(既定)の state"], u"H の出力": r[u"H の出力"]}
              for r in inj if r[u"G1(席が確認済み)"]]
    g3_unc_a = sum(1 for r in g1_rows if r[u"群(α 型)"] == u"G3" and not r[u"注入か"])
    g3_unc_s = sum(1 for r in g1_rows if r[u"群(Core 自身)"] == u"G3" and not r[u"注入か"])
    g1_unc = sc(unc, u"確認済み")
    vm_view = []
    for r in g1_rows:
        if r[u"α 型の state"] == "VALUE_MISMATCH":
            x = item_of[(r["doc"], r["id"])]
            vm_view.append({u"doc": r["doc"], u"id": r["id"], u"注入か": r[u"注入か"], u"型": r[u"注入の型"],
                            u"材料の値": x[u"材料の値"], u"材料の単位": x[u"材料の単位"], u"抜粋": x[u"抜粋"],
                            u"席の参照先": x[u"参照先(原文)"], u"参照先の fact の値": x[u"参照先の fact の値"],
                            u"engine の reason": x[u"engine の reason"], u"読みの材料(α-2)": x.get(u"読みの材料(α-2)")})
    runs = runs_of_csv()

    # ---- 予測 P-1〜P-7
    n_missed = seat_facts[u"席が確認済みにした注入(見逃し)"]
    p1_ok = inr_(n_missed, P1_RANGE)
    t7, t2 = by_type[u"T7_ROUND"], by_type[u"T2_UNIT"]
    p1 = {u"全体": HT.frac(n_missed, 64), u"全体の幅": list(P1_RANGE), u"全体の当たり": p1_ok,
          u"型別(封の分母 T7 24・T2 16。実数の分母は T7 10・T2 44)": {
              u"T7_ROUND": t7[u"席の見逃し(確認済み)"], u"T2_UNIT": t2[u"席の見逃し(確認済み)"],
              u"T6_PRIOR": by_type[u"T6_PRIOR"][u"席の見逃し(確認済み)"],
              u"T2 金額系": by_type[u"T2_UNIT 金額系"][u"席の見逃し(確認済み)"],
              u"T2 ％系": by_type[u"T2_UNIT ％系"][u"席の見逃し(確認済み)"],
              u"T2 件→回": by_type[u"T2_UNIT 件→回"][u"席の見逃し(確認済み)"]},
          u"型別の部分": u"判定しない(分母が封と違う: T7 24 → 10、T2 16 → 44)"}
    through_a = {k: by_type[k][u"Core が通した(α 型 GROUNDED。注入の行の全部)"][u"分子"] for k in GROUP_KEYS}
    n_through = sum(1 for r in inj if r[u"α 型の state"] == "GROUNDED")
    p2_ok = inr_(n_through, P2_RANGE) and through_a[u"T6_PRIOR"] == 0 and through_a[u"T2_UNIT"] == 0
    p2 = {u"Core が通した注入(α 型 GROUNDED)": HT.frac(n_through, 64), u"幅": list(P2_RANGE),
          u"型別": {k: through_a[k] for k in GROUP_KEYS}, u"T6・T2 で GROUNDED が 0": through_a[u"T6_PRIOR"] == 0 and through_a[u"T2_UNIT"] == 0,
          u"補助: Core 自身が GROUNDED にした注入": HT.frac(sum(1 for r in inj if r[u"Core 自身(既定)の state"] == "GROUNDED"), 64),
          u"補助: 席が確認済み ∧ α 型 GROUNDED の注入(G2 の注入)": ga["G2"][u"注入"]}
    acc = lambda g: ratio_pct(ga[g][u"無改変"], ga[g][u"行"])
    a1, a2, a3 = acc("G1"), acc("G2"), acc("G3")
    if None in (a1, a2, a3):
        p3_ok = None
    else:
        p3_ok = bool(P3_G1[0] <= a1 <= P3_G1[1] and a2 >= a1 + P3_G2_PT and a3 <= a1 - P3_G3_PT)
    p3 = {u"G1": ga["G1"][u"精度(注入でない行 / 群)"], u"G2": ga["G2"][u"精度(注入でない行 / 群)"], u"G3": ga["G3"][u"精度(注入でない行 / 群)"],
          u"G1 の精度の幅(%)": list(P3_G1), u"G2 - G1(pt)": None if None in (a1, a2) else round(float(a2 - a1), 1),
          u"G3 - G1(pt)": None if None in (a1, a3) else round(float(a3 - a1), 1),
          u"G2 ≥ G1 + 5 pt": None if None in (a1, a2) else bool(a2 >= a1 + P3_G2_PT),
          u"G3 ≤ G1 - 10 pt": None if None in (a1, a3) else bool(a3 <= a1 - P3_G3_PT),
          u"G1 の精度が幅の中": None if a1 is None else bool(P3_G1[0] <= a1 <= P3_G1[1]),
          u"補助(副。Core 自身)": {g: gs[g][u"精度(注入でない行 / 群)"] for g in ("G1", "G2", "G3")}}
    inj_g1 = ga["G1"][u"注入"]
    inj_g3 = ga["G3"][u"注入"]
    p4_ok = None if not inj_g1 else bool(P4_DEN * inj_g3 >= P4_NUM * inj_g1)
    p4 = {u"席が支持した注入": inj_g1, u"うち Core(α 型)が G3 に落とした": inj_g3,
          u"率": HT.frac(inj_g3, inj_g1), u"2/3 以上": p4_ok,
          u"G3 の α 型の state": dict(sorted(collections.Counter(r[u"α 型の state"] for r in g1_rows if r[u"注入か"] and r[u"群(α 型)"] == u"G3").items())),
          u"補助: 参照先なしで G3 に数えた注入": sum(1 for r in g1_rows if r[u"注入か"] and r[u"α 型の state"] == u"参照先なし"),
          u"補助(副。Core 自身で G3)": gs["G3"][u"注入"]}
    p5_files = {d: (answer_check[d][u"答えの行数"] == 24 and answer_check[d][u"id が 24 行と一致"]) for d in docs}
    p5_ok = bool(runs[u"便の数"] == 8 and not runs[u"行数が 24 でない便"] and runs[u"model"] == ["sonnet"]
                 and P5_TOTAL[0] <= runs[u"合計トークン"] <= P5_TOTAL[1] and not runs[u"1 便が上限を超えた便"] and all(p5_files.values()))
    p5 = {u"便の数": runs[u"便の数"], u"合計トークン": runs[u"合計トークン"], u"幅": list(P5_TOTAL), u"1 便の最大": runs[u"最大"],
          u"1 便の上限": P5_RUN_CAP, u"1 便が上限を超えた便": runs[u"1 便が上限を超えた便"], u"行数が 24 でない便": runs[u"行数が 24 でない便"],
          u"答えの file が 24 行・id 一致(8 書類)": p5_files}
    sh = HT.frac(g3_unc_a, g1_unc)
    share = ratio_pct(g3_unc_a, g1_unc)
    p6_parts = {u"G1 の無改変": inr_(g1_unc, P6_G1_UNMOD), u"偽警報": inr_(seat_facts[u"席の偽警報(無改変で誤りが在る)"], P6_FALSE),
                u"G3 の無改変 / G1 の無改変": bool(share is not None and P6_G3_SHARE[0] <= share <= P6_G3_SHARE[1])}
    p6_ok = all(p6_parts.values())
    p6 = {u"G1 の無改変(席が確認済みにした無改変)": HT.frac(g1_unc, 128), u"幅": list(P6_G1_UNMOD),
          u"偽警報(無改変で誤りが在る)": HT.frac(seat_facts[u"席の偽警報(無改変で誤りが在る)"], 128), u"偽警報の幅": list(P6_FALSE),
          u"G3 の無改変(α 型。Core の代価)": sh, u"G3 の無改変の幅(G1 の無改変に対する %)": list(P6_G3_SHARE),
          u"部分ごと": p6_parts, u"補助(副。Core 自身で G3 の無改変)": HT.frac(g3_unc_s, g1_unc)}
    p7r = mat[u"**P-7**"]
    p7_ok = bool(p7r[u"**P-7 の判定**"] == u"緑" and p7r[u"見せない字 0(8 書類とも。封の字の 9 語)"] and p7r[u"字数が C1 の ±30% の中(8 書類とも)"])
    p7 = {u"材料の記録の P-7": p7r[u"**P-7 の判定**"], u"見せない字 0(封の字の 9 語)": p7r[u"見せない字 0(8 書類とも。封の字の 9 語)"],
          u"字数が C1 の ±30% の中": p7r[u"字数が C1 の ±30% の中(8 書類とも)"]}
    preds = [
        {u"記号": "P-1", u"予測": u"席が支持した注入(見逃し) 6〜20 / 64。型別では T7_ROUND が最多(3〜12 / 24)、T2_UNIT が最少(0〜4 / 16)",
         u"実測": p1, u"当たり": p1_ok, u"型別の部分": u"判定しない"},
        {u"記号": "P-2", u"予測": u"Core が通した注入(α 型 GROUNDED) 0〜6 / 64。T6・T2 では 0", u"実測": p2, u"当たり": p2_ok},
        {u"記号": "P-3", u"予測": u"3 群の精度(α 型): G2 ≥ G1 + 5 pt、G3 ≤ G1 − 10 pt、G1 の精度は 70〜92%", u"実測": p3, u"当たり": p3_ok},
        {u"記号": "P-4", u"予測": u"席が支持した注入のうち Core が G3 に落とす数 ≥ その 2/3", u"実測": p4, u"当たり": p4_ok},
        {u"記号": "P-5", u"予測": u"8 便とも完走。トークン合計 700,000〜1,200,000、1 便 250,000 以下", u"実測": p5, u"当たり": p5_ok},
        {u"記号": "P-6", u"予測": u"無改変 128 行での G1 の無改変 60〜90、偽警報 0〜3、G3 の無改変は G1 の無改変の 25〜45%",
         u"実測": p6, u"当たり": p6_ok},
        {u"記号": "P-7", u"予測": u"下見(0 USD)が緑: 見せない字 0・task の字数が C1 の ±30%", u"実測": p7, u"当たり": p7_ok}]

    rec = {
        u"step": u"**席と Core の一致の信頼 段 2 の採点。0 USD・席は呼ばない・通信しない・engine 0 行**",
        u"seal": SEAL + u" §2(段 2)・§3・§4", u"seal の commit": SEAL_COMMIT,
        u"環境": env, u"入力の sha256(読むだけ。1 文字も直していない)": inputs,
        u"engine の留め": HT.engine_pins(),
        u"席の答えの形": answer_check,
        u"行": rows_all,
        u"集計": {
            u"席の字": seat_facts, u"3 群(α 型)": ga, u"3 群(Core 自身)": gs,
            u"H の出力": hout, u"H の確認(二重確認 + Core のみ確認)": HT.frac(passed(rs), len(rs)),
            u"誤りを通した(注入の行が二重確認か Core のみ確認)": HT.frac(passed(inj), 64),
            u"G1 のうち参照先なしの行(α 型が効かない)": sum(1 for r in g1_rows if r[u"α 型の state"] == u"参照先なし"),
            u"α 型を当てた行(席が参照先を名指した)": sum(1 for r in rs if r[u"α 型の state"] != u"参照先なし"),
            u"α 型を当てた注入の行": sum(1 for r in inj if r[u"α 型の state"] != u"参照先なし"),
            u"型別": by_type, u"書類別": by_doc},
        u"席が確認済みにした注入の行(見逃し)": missed,
        u"VALUE_MISMATCH の行(α 型・G1。読みの材料つき。読みは付けていない)": vm_view,
        u"便の記録": runs,
        u"分母と封の割当": {u"封の割当(書類 8 × 3/3/2)": {u"T6_PRIOR": 24, u"T7_ROUND": 24, u"T2_UNIT": 16},
                       u"実数": {k: by_type[k][u"注入"] for k in INJ_TYPES}},
        u"**予測 P-1〜P-7**": preds,
        u"所要秒": {u"席の字の読みと α 型": round(t_run, 1), u"全体": round(time.time() - t_start, 1)},
        "limits": [
            u"精度の物差しは『注入か』だけ。無改変の行の値が正しいこと(原文のまま)は前提で測っていない",
            u"T2 の注入 44 件のうち ％系 18(％↔ポイント)は数が正しいままで、『注入か』の物差しの限界(席が『確認済み』にしても数の誤りを見逃したとは限らない)",
            u"席は 1 席(sonnet)× 1 便の答え。席を替えれば表は変わる。書類は C1 と同じ 8 書類で、書類の汎化ではない",
            u"型別の分母は実数(T6 10・T7 10・T2 44)で、封の 24/24/16 と違う。型別の部分の予測は判定しない",
            u"α 型は席の参照先に依る。席が参照先を出さない行には効かない(G1 のうち参照先なしは G3 に数えた)",
            u"材料の『絞る前の T7 31』は使わない(再現できない数)"]}
    C1._dump(rec, a.out)
    print(u"=== 段 2 の採点(0 USD)===")
    for pr in preds:
        print(u"  %-4s %s" % (pr[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"判定しない"}[pr[u"当たり"]]),
              json.dumps(pr[u"実測"], ensure_ascii=False)[:240])
    print("->", a.out)
    return 0


def inr_(x, rng):
    return rng[0] <= x <= rng[1]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--stage", required=True, choices=["dryrun", "material", "score"],
                    help=u"score = 段 2 の採点(0 USD。席は呼ばない)")
    ap.add_argument("--out", default=SCORE_OUT, help=u"score の出力(既に在れば止まる)")
    a = ap.parse_args(argv)
    return {"dryrun": stage_dryrun, "material": stage_material, "score": stage_score}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())
