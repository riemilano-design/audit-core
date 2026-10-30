# -*- coding: utf-8 -*-
u"""診断: 注入 741 行で「道具が止めた理由」と「名指し」を分類し、P27E を同じ 741 行で測る ― 2026-10-29。

封 ``docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md``(commit ``6bea94b``)§2 と、その §6-5 の追記(member ありは「単体の member」と「それ以外」に分けて数える)の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。既存の記録(``fresh_2026-10-21.json``・``inject_reach_2026-10-28.json``・``p27/regress97_2026-10-27.json``)は書き換えない(別の記録を足す)。**
0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。

    cd audit-core
    python3 measure/xbrl_stop_reason_2026-10-29.py --procs 6                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_stop_reason_2026-10-29.py --docs 2 --out <scratch の file>   # 試走(先頭 n 書類。配線の門はその n 書類の分)

配線(封 §2-1): 前の便の script ``measure/xbrl_inject_reach_2026-10-28.py``(以下 RE)を読み込み、その module の値を 3 つだけ替えてから ``RE.work_doc`` を書類ごとに呼ぶ。
  ``RE.OBS = (P22, P26, P27, P27E)``・``RE.ALLP = P22〜P27 と P27E の 7 つ``・``RE.CLAIM_KEYS = 前の 9 つ + recomputed``。
  前の便の script の file は触らない。**自分で注入の規則・対応付けを書かない**(材料・注入・対応付けは RE の中で ``xbrl_fresh_2026-10-21.py`` の関数が使われる)。
無改変の 4 state は、書類ごとに同じ process の中で ``VD.verify_document(zb, p, None)`` を P22・P26・P27・P27E で呼んで取る(``RE.work_doc`` の無改変の一覧とは別の呼び出し)。

配線の門(1 つでも違えば記録を書かずに止める):
  W-1 (i) 前の便の門(741 / 741 の 4 欄・id の集合・注入の件数 120 組)、(ii) P22・P26・P27 の欄が ``inject_reach_2026-10-28.json`` と欄ごと(state・reason・pointers・分類)・全欄(recomputed と 名指し を除く)で 741 / 741。
  W-2 無改変の 4 state が ``regress97`` と書類 × profile で一致、P27 → P27E で動いた claim の集合が regress97 の 24 行と同じ(前 = POINTER_NOT_FOUND・no_same_value、後 = VALUE_MISMATCH・None)。
  W-3 差し替えが使う側に届いたこと(profile の鍵の並び・結果に P27E・claim に recomputed)。
分類(止めの語 13 語)は ``stop_word`` の 1 か所、要素名の切り出しは ``split_pointer`` の 1 か所。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import importlib.util
import io
import json
import multiprocessing
import os
import re
import shutil
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


RE = _mod("measure/xbrl_inject_reach_2026-10-28.py", "reach_for_stop_reason")
P4 = ("P22", "P26", "P27", "P27E")
RE.OBS = P4                                                       # 封 §2-1: 観測する profile を 4 つに
RE.ALLP = tuple(sorted(set(RE.PROFILES5) | set(RE.OBS)))         # P22〜P27 と P27E の 7 つ(注入後は 7 つとも verify_raw で走る)
RE.CLAIM_KEYS = RE.CLAIM_KEYS + ("recomputed",)                  # view が recomputed も写す
FR, VD, ED, IJ, V = RE.FR, RE.VD, RE.ED, RE.IJ, RE.V

SEAL_REL = "docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md"
SEAL_COMMIT = "6bea94b"
OUT_REL = "fixtures/xbrl/stop_reason_2026-10-29.json"
REACH_REL = "fixtures/xbrl/inject_reach_2026-10-28.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
FRESH_REC_REL = RE.FRESH_REC_REL
FETCHED_REL = RE.FETCHED_REL
INJECT_TYPES = RE.INJECT_TYPES
MAIN_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT")

# 分類 13 語(封 §2-3)
W_NOMAP, W_PASS = u"(対応が付かない)", u"(通した)"
W_NAMED, W_OTHERFACT, W_NOBASE = u"(名指した・原本)", u"(名指した・別の fact)", u"(名指した・基準なし)"
W_NOSAME, W_OTHERCON, W_NOELEM, W_NOPTR = u"(要確認・証拠が無く名指さない)", u"(要確認・別の概念)", u"(要確認・要素が無い)", u"(要確認・pointer が引けない)"
W_NOSUBJ, W_AMBIG, W_FRAME, W_OUT = u"(要確認・主語が無い)", u"(要確認・候補が複数)", u"(要確認・主張の形で保留)", u"(形の外)"
WORDS = (W_NOMAP, W_PASS, W_NAMED, W_OTHERFACT, W_NOBASE, W_NOSAME, W_OTHERCON, W_NOELEM, W_NOPTR, W_NOSUBJ, W_AMBIG, W_FRAME, W_OUT)
HOLD_REASONS = ("other_frame", "rounded_diff_within_double_band", "per_unit_counter", "target_or_plan", "state_word(no line)", "direction_on_cause_item", "prior is 0")

STD_PREFIX = re.compile(r"jp[a-z]+_cor")
PERIOD = re.compile(r"^(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)")
SOLE_MEMBER = "NonConsolidatedMember"


def stop_word(typ, after, base):
    u"""封 §2-3: 注入後の claim ``after``(None なら対応が付かない)と基準の claim ``base`` から、先に当たった 1 語(分類を決める 1 か所)。"""
    if after is None:
        return W_NOMAP
    state, reason, pts = after["state"], after["reason"], after.get("pointers") or []
    if state == "GROUNDED":
        return W_PASS
    if state == "VALUE_MISMATCH" and pts:
        if typ == "T3_ABSENT":
            return W_NOBASE
        if same_head(after, base):
            return W_NAMED
        return W_OTHERFACT
    if state == "POINTER_NOT_FOUND" and reason is not None:
        if reason == "no_same_value":
            return W_NOSAME
        if reason == "other_concept":
            return W_OTHERCON
        if reason == "no_element" or reason.startswith("no_element(") or reason == "no_prior_member_context":
            return W_NOELEM
        if reason == "no_pointer" or reason.startswith("unresolved:"):
            return W_NOPTR
    if state == "UNVERIFIABLE" and reason is not None:
        if reason == "no_subject":
            return W_NOSUBJ
        if reason.startswith("ambiguous("):
            return W_AMBIG
        if reason in HOLD_REASONS:
            return W_FRAME
    return W_OUT


def same_head(after, base):
    u"""注入後の pointers が空でなく、基準の pointers が空でなく、両方の先頭の字が同じ。"""
    if after is None or base is None:
        return False
    a, b = after.get("pointers") or [], base.get("pointers") or []
    return bool(a) and bool(b) and a[0] == b[0]


def same_recomputed(after, base):
    u"""先頭が同じ、かつ recomputed が ``==`` で同じ(どちらも None なら同じと数えない)。"""
    if not same_head(after, base):
        return False
    ra, rb = after.get("recomputed"), base.get("recomputed")
    return ra is not None and rb is not None and ra == rb


def split_pointer(p):
    u"""封 §2-5: 先頭の pointer の字を scheme・接頭辞・名前・context・期・member の有無・標準の接頭辞かに切る(要素名の切り出しを決める 1 か所)。"""
    if p is None:
        return None
    if not p.startswith("xbrl:"):
        return {u"scheme": p.split(":", 1)[0], u"接頭辞": None, u"名前": None, u"要素名": u"(xbrl でない)", u"context": None,
                u"期": None, u"member": None, u"member が単体のみ": None, u"標準の接頭辞": None}
    name, _at, ctx = p[5:].partition("@")
    pre, _c, loc = name.partition(":")
    m = PERIOD.match(ctx)
    tail = ctx.split("_", 1)[1] if "_" in ctx else ""
    has_member = "Member" in tail
    return {u"scheme": u"xbrl", u"接頭辞": pre, u"名前": loc, u"要素名": name, u"context": ctx,
            u"期": (m.group(1) + m.group(2)) if m else u"その他", u"member": has_member,
            u"member が単体のみ": bool(has_member and tail == SOLE_MEMBER), u"標準の接頭辞": bool(STD_PREFIX.fullmatch(pre))}


def named_cell(typ, x):
    u"""RE の 1 行 1 profile の欄 ``x`` に足す ``名指し``(封 §2-2)。"""
    if typ == "T3_ABSENT":
        after, base = x["claim"], None
        reach = x[u"届いた"]
    else:
        after, base = x[u"注入後"]["claim"], x[u"無改変"]["claim"]
        reach = x[u"届いた(文)"]
    word = stop_word(typ, after, base)
    head = ((after or {}).get("pointers") or [None])[0]
    return {
        u"語": word,
        u"止めた": word not in (W_NOMAP, W_PASS),
        u"届いた(文)": None if typ == "T3_ABSENT" else bool(reach),
        u"先頭が同じ": same_head(after, base),
        u"recomputed が同じ": same_recomputed(after, base),
        u"先頭の pointer": head,
        u"先頭の切り方": split_pointer(head),
        u"基準の state": None if base is None else base["state"],
        u"基準が GROUNDED": None if base is None else base["state"] == "GROUNDED",
    }


def strip_keys(v, drop):
    if isinstance(v, dict):
        return dict((k, strip_keys(w, drop)) for k, w in v.items() if k not in drop)
    return v


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def after_of(r, p):
    x = r[u"profile"][p]
    return x["claim"] if r[u"型"] == "T3_ABSENT" else x[u"注入後"]["claim"]


def work(a):
    u"""書類 1 本(別の process)。RE.work_doc + 無改変の 4 state。"""
    doc, rows_fetched = a[0], a[1]
    zb = FR.read_zip(doc, rows_fetched)
    plain = {}
    for p in P4:
        out = VD.verify_document(zb, p, None)
        plain[p] = [(c["id"], c["state"], c["reason"]) for c in out["claims"]]
    r = RE.work_doc(a)
    for row in r[u"rows"]:
        for p in P4:
            x = row[u"profile"][p]
            x[u"名指し"] = named_cell(row[u"型"], x)            # W-1(ii) の比べは 名指し を除いて行う(main の側)
    r[u"plain4"] = plain
    return r


def dump_record(rec, rowkeys):
    return RE.dump_record(rec, rowkeys)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--docs", type=int, default=None, help="先頭 n 書類だけ(試走。正本の記録は 30 書類全部)")
    ap.add_argument("--procs", type=int, default=6)
    args = ap.parse_args()
    if os.path.exists(args.out):
        print(u"既に在る(測り直さない): %s" % args.out)
        return
    t_start = time.time()
    rec_fresh = RE.jload(FRESH_REC_REL)
    reach = RE.jload(REACH_REL)
    reg = RE.jload(REGRESS_REL)
    rows_rec = rec_fresh[u"注入の行"]
    by_id = dict((r["id"], r) for r in rows_rec)
    docs_all, rows_fetched, fetched = FR.used_docs()
    docs = docs_all if args.docs is None else docs_all[:args.docs]
    cache0 = {u"edinet": RE.count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": RE.count_zip(FR.FRESH_DIR)}
    seed, meta = IJ.verify_seed_sealed(FR.SEED_FILE)
    work_root = tempfile.mkdtemp(prefix="stop_reason_")
    jobs = []
    for d in docs:
        w = os.path.join(work_root, d)
        os.makedirs(w)
        jobs.append((d, rows_fetched, seed, w, by_id, rec_fresh[u"注入の件数(書類別)"][d]))
    ED.CACHE_DIR = FR.FRESH_DIR
    ctx = multiprocessing.get_context("fork")
    res = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.procs, mp_context=ctx) as ex:
        futs = dict((ex.submit(work, j), j[0]) for j in sorted(jobs, key=lambda j: -rows_fetched[j[0]]["bytes"]))
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            res[r["doc"]] = r
            print(u"完了 %d / %d 書類 (%d 行, %d 秒)" % (len(res), len(docs), len(r[u"rows"]), r[u"秒"]), file=sys.stderr)
            sys.stderr.flush()
    shutil.rmtree(work_root, ignore_errors=True)
    out_rows = [x for d in docs for x in res[d][u"rows"]]
    wiring = [x for d in docs for x in res[d][u"wiring"]]

    # ---- W-1 (i): 前の便の門
    rec_ids = sorted(r["id"] for r in rows_rec if r["doc"] in docs)
    mine_ids = sorted(w["id"] for w in wiring)
    n_match = sum(1 for w in wiring if w[u"一致"][u"4 欄とも一致"])
    n_pairs = len(docs) * len(INJECT_TYPES)
    n_pairs_ok = sum(1 for d in docs for t in INJECT_TYPES if res[d][u"counts"][t][u"3 つの数が記録と一致"])
    # ---- W-1 (ii): P22・P26・P27 の欄が inject_reach の記録と
    rid = dict((r["id"], r) for r in reach[u"rows"])
    f = collections.Counter()
    missing = 0
    for r in out_rows:
        o = rid.get(r["id"])
        if o is None:
            missing += 1
            continue
        ok = dict((k, True) for k in ("state", "reason", "pointers", "分類", "全欄"))
        for p in ("P22", "P26", "P27"):
            x, y = r[u"profile"][p], o[u"profile"][p]
            ax, ay = after_of(r, p), after_of(o, p)
            g = lambda c, k: None if c is None else c.get(k)
            ok["state"] &= g(ax, "state") == g(ay, "state")
            ok["reason"] &= g(ax, "reason") == g(ay, "reason")
            ok["pointers"] &= g(ax, "pointers") == g(ay, "pointers")
            ok[u"分類"] &= x[u"分類"] == y[u"分類"]
            ok[u"全欄"] &= dumps(strip_keys(x, ("recomputed", u"名指し"))) == dumps(y)
        for k, v in ok.items():
            f[k] += int(v)
    w1 = {u"前の便の門(4 欄とも一致)": [n_match, len(wiring)], u"記録の注入の行(対象の書類)": len(rec_ids), u"id の集合が記録と同じ": rec_ids == mine_ids,
          u"注入の件数の組": [n_pairs_ok, n_pairs], u"inject_reach に無い行": missing, u"行": len(out_rows),
          u"P22・P26・P27 の state": f["state"], u"P22・P26・P27 の reason": f["reason"], u"P22・P26・P27 の pointers": f["pointers"],
          u"P22・P26・P27 の分類(6 語)": f[u"分類"], u"P22・P26・P27 の全欄(recomputed と 名指し を除く)": f[u"全欄"]}
    w1[u"通った"] = bool(w1[u"id の集合が記録と同じ"] and n_match == len(wiring) == len(rec_ids) and n_pairs_ok == n_pairs and missing == 0
                      and all(f[k] == len(out_rows) for k in ("state", "reason", "pointers", "分類", "全欄")))

    # ---- W-2: 無改変の 4 state と P27 → P27E で動いた行
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    per_state, w2_ok = {}, 0
    moved_mine = []
    for d in docs:
        pl = res[d]["plain4"]
        per_state[d] = {}
        good = True
        for p in P4:
            c = collections.Counter(s for _i, s, _r in pl[p])
            per_state[d][p] = dict((k, c.get(k, 0)) for k in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"))
            want = regd[d][u"4 state"][p]
            good &= all(per_state[d][p][k] == want.get(k, 0) for k in per_state[d][p])
        w2_ok += int(good)
        a27 = dict((i, (s, r_)) for i, s, r_ in pl["P27"])
        for i, s, r_ in pl["P27E"]:
            if a27[i] != (s, r_):
                moved_mine.append({u"doc": d, u"id": i, u"前": [a27[i][0], a27[i][1]], u"後": [s, r_]})
    moved_reg = [x for x in reg[u"動いた行"][u"新しい標本 30"][u"P27 → P27E"] if x["docID"] in docs]
    key_mine = sorted((m[u"doc"], m[u"id"], tuple(m[u"前"]), tuple(m[u"後"])) for m in moved_mine)
    key_reg = sorted((x["docID"], x["id"], (x[u"前"]["state"], x[u"前"]["reason"]), (x[u"後"]["state"], x[u"後"]["reason"])) for x in moved_reg)
    all_pnf = all(m[u"前"] == ["POINTER_NOT_FOUND", "no_same_value"] and m[u"後"] == ["VALUE_MISMATCH", None] for m in moved_mine)
    w2 = {u"書類の 4 state が regress97 と一致": [w2_ok, len(docs)], u"動いた行(今回)": len(moved_mine), u"動いた行(regress97。対象の書類)": len(moved_reg),
          u"動いた行の集合が同じ": key_mine == key_reg, u"動いた行は全部 前 = POINTER_NOT_FOUND・no_same_value、後 = VALUE_MISMATCH・None": all_pnf}
    w2[u"通った"] = bool(w2_ok == len(docs) and key_mine == key_reg and all_pnf and (args.docs is not None or len(moved_mine) == 24))

    # ---- W-3: 差し替えが使う側に届いたか
    n_keys = n_res = n_rec = n_claims = 0
    for r in out_rows:
        n_keys += int(list(r[u"profile"]) == list(P4))
        n_res += int("P27E" in r[u"結果(P22〜P27)"])
        cl = [after_of(r, p) for p in P4]
        if r[u"型"] != "T3_ABSENT":
            cl += [r[u"profile"][p][u"無改変"]["claim"] for p in P4]
        cl = [c for c in cl if c is not None]
        n_claims += len(cl)
        n_rec += sum(1 for c in cl if "recomputed" in c)
    w3 = {u"profile の鍵が 4 つの順": [n_keys, len(out_rows)], u"結果(P22〜P27)に P27E": [n_res, len(out_rows)], u"claim に recomputed の鍵": [n_rec, n_claims]}
    w3[u"通った"] = bool(n_keys == n_res == len(out_rows) and n_rec == n_claims)

    gate = {u"W-1": w1, u"W-2": w2, u"W-3": w3}
    gate[u"通った"] = bool(w1[u"通った"] and w2[u"通った"] and w3[u"通った"])
    if not gate[u"通った"]:
        raise SystemExit(u"**配線の門が通らない: %s。記録を書かずに止める**" % dumps(gate))

    cache1 = {u"edinet": RE.count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": RE.count_zip(FR.FRESH_DIR)}
    per_doc = {}
    for d in docs:
        per_doc[d] = {u"材料の sha256": rows_fetched[d]["sha256"], u"材料の sha256 が取得の記録と一致": True, u"注入の件数": res[d][u"counts"],
                      u"claims": res[d][u"claims"], u"無改変の 4 state": per_state[d], u"文の数": res[d][u"文の数"], u"秒": res[d][u"秒"]}
    rec = collections.OrderedDict()
    rec[u"注意"] = u"診断の記録(封 docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md §5)。engine は 0 行。fresh_2026-10-21.json・inject_reach_2026-10-28.json・regress97_2026-10-27.json は書き換えない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": RE.git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT}
    rec[u"全書類"] = args.docs is None
    rec[u"HEAD"] = RE.git("rev-parse", "HEAD")
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"engine sha16"] = dict((rel, RE.sha16(rel)) for rel in RE.ENGINE_FILES)
    rec[u"種"] = meta
    rec[u"読んだ入力の sha256"] = dict((rel, RE.sha64(rel)) for rel in (FRESH_REC_REL, FETCHED_REL, REACH_REL, REGRESS_REL))
    rec[u"観測する profile"] = list(P4)
    rec[u"書類(出てくる順)"] = docs
    rec[u"書類ごと"] = per_doc
    rec[u"配線の門"] = gate
    rec[u"P27 → P27E で動いた無改変の行"] = moved_mine
    rec[u"cache"] = {u"開始": cache0, u"終了": cache1}
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"『名指した』は、注入後の claim の pointers の先頭が無改変の基準の先頭と同じ、という字の一致。その名指しが人の目に正しいかは測っていない。基準の結び付きが正しいかも測っていない。",
        u"P27E を有報の原文に当てる使い方は想定しない。無改変の 30 書類で 24 行を VALUE_MISMATCH に入れる(偽の『違う』かは確かめていない)。",
        u"評価用 10 社の名指しの率とは別物(材料も型も分母の作り方も違う)。差を良し悪しと読まない。",
        u"要素名の分布は、この 30 書類の文の書き方と IJ.select の site の取り方に依る。",
        u"30 書類・741 行・1 書類あたり型ごとに 40 件までの IJ.select の順の観測。通さなかった site に同じ形が無いとは言えない。Core 全体の振る舞いを断定しない。",
        u"語 6〜12 は reason の字の束ね方で、どの枝のどの条件で落ちたか(recipes の中の行)は記録に無い。reason の字が同じでも落ちた枝が違うことがある。",
        u"『届いた(文)』は engine の文の一覧の番号の一致で、claim が読む数そのものの一致ではない。",
        u"仮説は測るまで断定しない。読みは無い(機械の値)。",
    ]
    rec[u"rows"] = out_rows
    rec[u"配線の行ごと"] = wiring
    blob = dump_record(rec, (u"rows", u"配線の行ごと", u"P27 → P27E で動いた無改変の行"))
    leaks = FR.key_leaks(blob)
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    rec[u"key_leaks"] = []
    blob = dump_record(rec, (u"rows", u"配線の行ごと", u"P27 → P27E で動いた無改変の行"))
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"配線の門 W-1 %s W-2 %s W-3 %s" % (dumps(w1), dumps(w2), dumps(w3)))
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", args.out)


if __name__ == "__main__":
    main()
