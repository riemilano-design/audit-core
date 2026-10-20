# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)― 封 ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md`` の段 2 の前半(下見と材料)。

**席は 1 回も呼ばない。通信しない。``core/``・``adapters/`` は 0 行。** 本物の席の便・採点(``--stage score``)は次の席。

  --stage dryrun    材料の生成・task file・見せない字の検査・トークンの見込み・P-7 の判定を、**本番と同じ配線**で通す。
                    task file と記録は repo の外(``$TMPDIR/hybrid_s2/dry/``)。repo には何も書かない。
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
  4. ``MB.PROFILE`` ― 既定 profile(``vocabulary.DEFAULT_PROFILE`` = P21)。段 1 と同じ ``席の前に出せる分``
     (各行の Core 自身 = 既定 P21 の state と参照先)。

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
    MB.PROFILE = V.DEFAULT_PROFILE
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
        if rec.get("profile") != V.DEFAULT_PROFILE:
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--stage", required=True, choices=["dryrun", "material"],
                    help=u"score は次の席(この script にはまだ無い)")
    a = ap.parse_args(argv)
    return {"dryrun": stage_dryrun, "material": stage_material}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())
