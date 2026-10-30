# -*- coding: utf-8 -*-
u"""診断: 評価用・調整用 P27 の注入で、差し替えが「基準の claim」に届いたかを数える ― 2026-10-29。

封 ``docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md``(commit ``071abb4``)§2・§5 の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。既存の記録 ``fixtures/xbrl/p27/eval_inject_2026-10-27.json``・``tune_inject_2026-10-27.json``・
``tune_p27_inject_2026-10-27.json`` は書き換えない(別の記録を足す)。** 0 USD・通信なし・鍵は読まない・席(LLM)は呼ばない。

    cd audit-core
    python3 measure/xbrl_p27_inject_reach_2026-10-29.py --procs 6                                  # 調整用 → 配線の門 → 評価用(本番の 1 回)。出力が既に在れば測り直さない
    python3 measure/xbrl_p27_inject_reach_2026-10-29.py --set 調整用 --docs 2 --out <scratch の file>   # 試走(調整用の先頭 n 書類だけ。評価用は開かない)

**盲検**: 評価用・調整用の文・DB の応答・指示文は、段 1 の ``read_report``(``ctx.read_report``)が読んで engine に渡すだけ。標準出力・止める文言・記録に文・値を入れない
(記録に持つ欄は id・旗・state・reason・文の番号と位置(整数)・分類・件数・sha256 だけ。``ALLOWED_KEYS`` の外の鍵が 1 つでも在れば書かずに止まる)。
``~/.cache/audit-core/edinetdb-p27/`` の下はこの script の ``ctx.read_report`` だけが開く。``~/.cache/audit-core/edinet/`` は読まず書かない(``cache_snapshot`` が件数と名前の一覧の sha256 を取るだけ)。
``edinet-fresh-2026-10-21/`` は ZIP を読むだけ。

配線(封 §2-1): 関数は写さず import する。評価用の script ``xbrl_p27_eval_2026-10-27.py`` を 1 回読み(module E)、E が読んだ段 1 の module(``E.T``)を、評価用と調整用の両方の唯一の T とする。
注入は ``E.T.inject_doc`` を書類ごとに呼ぶ(注入の規則・site・土台・対応付け・分類を自分で書かない)。評価用の ``run_inject`` は ``preflight`` が既定の profile を P26 と求めるので今の HEAD では走らない
→ ``EvalCtx`` と ``inject_doc`` を直接呼ぶ。観測のために包むのは 2 か所だけ(返り値は変えない): backend の ``verify``(``_RawTap`` + ``verify_raw``)と ``E.T.claim_for_p27``。
配線の門: 走らせ直した行が既存の記録の同じ (docID, id) の行と、型・文体・基準の claim・r・r を決めた回・profile ごとの対応・結果・state・reason で全行一致すること。
**1 つでも違えば記録を書かずに止める。** 調整用を先に走らせて門を当て、通ってから評価用を開く。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, ROOT, os.path.join(ROOT, "core", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


E = _mod("measure/xbrl_p27_eval_2026-10-27.py", "p27_eval_for_p27_reach")
T = E.T                                                         # 評価用と調整用の両方の唯一の T(段 1 の script)
RR = _mod("measure/xbrl_p27_tune_rerun_2026-10-27.py", "p27_rerun_for_p27_reach")
RCH = _mod("measure/xbrl_inject_reach_2026-10-28.py", "reach_for_p27_reach")
LB, T2D = RCH.LB, RCH.T2D
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

Stop = T.Stop
SEAL_REL = "docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md"
SEAL_COMMIT = "071abb4"
OUT_REL = "fixtures/xbrl/p27/inject_reach_2026-10-29.json"
FIX = "fixtures/xbrl/p27/"
EVAL_INJECT_REL = FIX + "eval_inject_2026-10-27.json"
TUNE_INJECT_REL = FIX + "tune_inject_2026-10-27.json"
TUNE_P27_INJECT_REL = FIX + "tune_p27_inject_2026-10-27.json"
INPUT_RELS = (EVAL_INJECT_REL, TUNE_INJECT_REL, TUNE_P27_INJECT_REL, FIX + "eval_2026-10-27.json", FIX + "tune_p27_2026-10-27.json",
              FIX + "reports_2026-10-27.json", "fixtures/xbrl/fresh/fetched_2026-10-21.json", FIX + "dbfetch_2026-10-27.json")
ENGINE_FILES = RCH.ENGINE_FILES
PROFILES = ("P22", "P26", "P27", "P27E")
GROUP_TUNE, GROUP_EVAL = u"調整用", u"評価用"
ROUNDTRIP_PIN = {GROUP_EVAL: 113, GROUP_TUNE: 122}              # 封 §2-1(人が決めた数は字で留める)
K_BOTH, K_VALUE, K_NONE = u"値と字", u"値だけ", u"対応が付かない"
CHECK_FIELDS = (u"型", u"文体", u"基準の claim", u"r", u"r を決めた回")

#: 記録に持てる欄(封 §2-5 と §6-5 の字)。この外の鍵が 1 つでも在れば書かずに止まる。
ALLOWED_KEYS = frozenset([
    u"注意", u"封", u"file", u"commit", u"期待する commit", u"全書類", u"頭", u"HEAD の commit", u"DEFAULT_PROFILE", u"engine sha16", u"engine の指紋",
    u"adapter_xbrl_py_sha256", u"adapter_xbrl_py_files", u"core_py_sha256", u"core_py_files", u"git_commit",
    u"種", u"file", u"sealed_in_commit", u"seed_file_sha256", u"読んだ入力の sha256", u"cache", u"開始", u"終了", u"cache_snapshot が同じ", u"対象",
    u"PROFILES4 が同じ", u"段 1 の file の sha256 が同じ", u"engine に未 commit の差が無い", u"観測する profile", u"組の順",
    u"配線", u"行", u"一致", u"記録の行", u"(docID, id) の集合が同じ", u"書類別の数えの組", u"書類別の数えが一致した組", u"round-trip", u"round-trip の期待",
    u"包みの呼ばれた回数", u"対応を数えた行 × 4", u"claim の一覧の id() が控えに在る", u"通った",
    u"書類ごと", u"組", u"docID", u"書類の位置", u"文の sha256", u"文の sha256 が一致", u"ZIP の sha256 が一致", u"書類別の数え", u"書類別の数えが記録と一致",
    u"claim の数", u"文の数", u"秒", u"所要秒", u"limits", u"key_leaks",
    u"rows", u"注入の id", u"型", u"文体", u"r", u"r を決めた回", u"基準の claim", u"基準の対応の付け方", u"profile",
    u"注入後の claim の id", u"注入後の id が基準と同じ", u"注入後の対応の付け方", u"基準の claim の無改変の state", u"基準の claim の文の番号", u"基準の claim の文の中の位置",
    u"数の始まり", u"数の終わり", u"token の文の番号", u"文の中で最初に違う位置", u"文の数(無改変, 注入後)", u"注入後の claim の文の番号",
    u"届いた(文)", u"届いた(数)", u"state", u"reason", u"結果", u"注入後の state が無改変の同じ id と同じ", u"注入後の pointers が在る",
    u"注入後の pointers の先頭が基準と同じ", u"分類", u"細目",
    u"配線の行ごと", u"不一致の欄",
    u"作れる site", u"採った", u"両方 GROUNDED", u"どちらも GROUNDED でない", u"基準に対応が付かない", u"円族の token", u"r が決まらず site にしない",
    u"P22 のみ GROUNDED", u"P26 のみ GROUNDED", u"profile 間で claim が合わない", u"T1_VALUE", u"T8_REL", u"P22", u"P26", u"P27", u"P27E",
    u"edinet", u"edinet-fresh-2026-10-21", u"調整用", u"評価用",
] + list(ENGINE_FILES) + list(INPUT_RELS))


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha16(rel):
    return sha64(rel)[:16]


def git(*a):
    r = subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def count_dir(d):
    return len(os.listdir(d)) if os.path.isdir(d) else None


def jload(rel):
    return T.read_json(os.path.join(ROOT, rel))


# ----------------------------------------------------------------------------------------------------------------
# 対応付け(どの枝で 1 件に決まったか。指す claim が本物と同じことは呼び出し側で確かめる)
def branch(claims, value, digits, unit):
    u"""``T.find_base_claim`` / ``T.claim_for_p27`` と同じ順(値と字 → 値だけ → None)。(枝の語, claim)。"""
    target = T.scaled(value, unit)
    hit = [c for c in claims if c.get("value") is not None and T.same_number(T.claim_scaled(c), target)]
    c1 = [c for c in hit if c.get("span") and digits in c["span"]]
    if len(c1) == 1:
        return K_BOTH, c1[0]
    if len(hit) == 1:
        return K_VALUE, hit[0]
    return K_NONE, None


def classify6(after_id, sentence_known, reached, state):
    return RCH.classify_row(None if after_id is None else {"id": after_id}, sentence_known, reached, state)


def detail(cls, reached_num, same_id, same_state):
    u"""細目(封 §6-5): 届いた(文)は数の位置、届かない(止めた・通した の両方)は id と state。"""
    if cls in (RCH.C_RS, RCH.C_RP):
        return RCH.D_NUM if reached_num else RCH.D_OTHER
    if cls in (RCH.C_NS, RCH.C_NP):
        if not same_id:
            return RCH.D_DIFFID
        return RCH.D_SAMEID_SAME if same_state else RCH.D_SAMEID_MOVED
    return None


# ----------------------------------------------------------------------------------------------------------------
# 包み 2 か所(観測のため。返り値は変えない)
class ObsBackend(object):
    u"""``inner`` の backend を包み、``verify`` だけを ``observe(zb, profile, text) -> (out, raw, sents)`` に替える。返すのは ``out`` の object そのもの。
    claim の一覧の ``id()`` を鍵に、その呼び出しの profile・文の sha256・raw・文の一覧・claim の一覧(生かしておく)を控える。"""

    def __init__(self, inner, observe):
        self.inner = inner
        self.observe = observe
        self.caps = {}
        self.name = getattr(inner, "name", "wrapped")

    def __getattr__(self, k):
        return getattr(self.inner, k)

    def verify(self, zb, profile, text):
        out, raw, sents = self.observe(zb, profile, text)
        self.caps[id(out["claims"])] = {"profile": profile, "text_sha": sha256_bytes(text.encode("utf-8")), "raw": raw, "sents": sents, "claims": out["claims"]}
        return out


def make_wrapper(orig, calls):
    u"""``claim_for_p27`` の包み。本物を呼び、返り値の object をそのまま返し、(注入・claim の一覧の id()・返した claim)を残す。"""
    def wrap(claims, inj, unit):
        r = orig(claims, inj, unit)
        calls.append({"inj": inj, "cid": id(claims), "after": None if r is None else r["id"], "unit": unit, "ret": r})
        return r
    return wrap


def wrap_identity_problems(wrapper_factory):
    u"""包みの門 (i) の一部: 包みが本物の返り値の object をそのまま返すか(作り物の本物で見る)。問題の列。"""
    out = []
    marker = {"id": "N001", "value": 1.0}
    for ret in (marker, None):
        for typ in T.INJECT_TYPES:
            calls = []
            w = wrapper_factory(lambda claims, inj, unit: ret, calls)
            got = w([marker], {"id": "x", "type": typ}, u"円")
            if got is not ret:
                out.append(u"包みが本物の返り値の object をそのまま返さない(%s・None: %r)" % (typ, ret is None))
            if len(calls) != 1:
                out.append(u"包みが呼び出しを 1 回で残さない")
    return out


def run_wrapped(ctx, backend, doc, seed, work, observe, wrapper_factory=make_wrapper, cap=None):
    u"""``T.inject_doc`` を、backend と ``T.claim_for_p27`` を包んで呼ぶ。(rows, full, counts, calls, obs_backend)。属性は必ず戻し、戻ったことを ``is`` で確かめる。"""
    orig = T.claim_for_p27
    calls = []
    be = ObsBackend(backend, observe)
    T.claim_for_p27 = wrapper_factory(orig, calls)
    try:
        rows, full, counts = T.inject_doc(ctx, be, doc, seed, work, T.INJECT_CAP if cap is None else cap)
    finally:
        T.claim_for_p27 = orig
    if T.claim_for_p27 is not orig:
        raise Stop(u"**claim_for_p27 を戻せていない。止める**")
    return rows, full, counts, calls, be


def wrap_gate_problems(ctx, backend_factory, doc, seed, work_root, observe_for, wrapper_factory=make_wrapper):
    u"""包みの門 (i): 包んだときと包まないときの ``inject_doc`` の返り値(行・外の行・数え)が JSON の byte で同じか。問題の列。"""
    w1, w2 = os.path.join(work_root, "plain"), os.path.join(work_root, "wrapped")
    os.makedirs(w1)
    os.makedirs(w2)
    plain = T.inject_doc(ctx, backend_factory(), doc, seed, w1, T.INJECT_CAP)
    inner = backend_factory()
    rows, full, counts, _calls, _be = run_wrapped(ctx, inner, doc, seed, w2, observe_for(inner), wrapper_factory)
    a = json.dumps(plain, ensure_ascii=False, sort_keys=True)
    b = json.dumps((rows, full, counts), ensure_ascii=False, sort_keys=True)
    out = []
    if a != b:
        out.append(u"包んだときの inject_doc の返り値が、包まないときと byte で違う")
    out += wrap_identity_problems(wrapper_factory)
    return out


# ----------------------------------------------------------------------------------------------------------------
def real_observe(tap):
    return lambda zb, profile, text: LB.verify_raw(tap, zb, profile, text)


def work_doc(ctx, backend, observe_factory, doc, seed, work, wrapper_factory=make_wrapper):
    u"""1 書類。(観測の行, inject_doc の行, 数え, 包みの回数, 書類ごとの情報)。tap は ``observe_factory`` が作る(本番は ``_RawTap`` の中で ``verify_raw``)。"""
    t0 = time.time()
    text, tb = ctx.read_report(doc)
    tsha = sha256_bytes(tb)
    text_sha = sha256_bytes(text.encode("utf-8"))
    toks = dict(((t.start, t.end), t) for t in T.N.scan(text))
    with observe_factory() as observe:
        rows, _full, counts, calls, be = run_wrapped(ctx, backend, doc, seed, work, observe, wrapper_factory)
    del _full                                                    # 元の字・後の字・新しい値は捨てる(書かない・印字しない)
    base = {}
    for cap in be.caps.values():
        if cap["text_sha"] == text_sha:
            if cap["profile"] in base:
                raise Stop(u"**無改変の控えが 1 profile に 2 つ。止める**")
            base[cap["profile"]] = cap
    if set(base) != set(PROFILES):
        raise Stop(u"**無改変の控えが 4 profile に無い。止める**")
    by_inj = collections.defaultdict(list)
    for c in calls:
        by_inj[c["inj"]["id"]].append(c)
    out_rows = []
    for row in rows:
        cs = by_inj[row["id"]]
        if len(cs) != len(PROFILES):
            raise Stop(u"**包みの呼び出しが 4 回でない。止める**")
        inj = cs[0]["inj"]
        s, e = inj["span"]
        tok = toks[(s, e)]
        digits = text[s:e]
        kind0, own0 = branch(base["P22"]["claims"], tok.value, digits, tok.unit)
        real0 = T.find_base_claim(base["P22"]["claims"], tok.value, digits, tok.unit)
        if (own0 or {}).get("id") != (real0 or {}).get("id") or (real0 or {}).get("id") != row[u"基準の claim"]:
            raise Stop(u"**基準の枝の判定が本物と違う。止める**")
        o = {u"組": None, u"docID": doc, u"注入の id": row["id"], u"型": row[u"型"], u"文体": row[u"文体"], u"基準の claim": row[u"基準の claim"],
             u"基準の対応の付け方": kind0, u"profile": {}}
        if "r" in row:
            o[u"r"], o[u"r を決めた回"] = row["r"], row[u"r を決めた回"]
        for p, c in zip(PROFILES, cs):
            cap1 = be.caps.get(c["cid"])
            if cap1 is None or cap1["profile"] != p:
                raise Stop(u"**注入後の控えが見つからないか profile が違う。止める**")
            cap0 = base[p]
            kind1, own1 = branch(cap1["claims"], inj["new_value"], inj["replacement"], c["unit"])
            if (own1 or {}).get("id") != c["after"]:
                raise Stop(u"**注入後の枝の判定が本物と違う。止める**")
            by0 = dict((x["id"], x) for x in cap0["claims"])
            r0 = cap0["raw"].get(row[u"基準の claim"], {})
            s0, s1 = cap0["sents"], cap1["sents"]
            si = r0.get("sentence")
            ns = RCH.num_span(s0[si] if si is not None else None, r0.get("pos"))
            tidx, toff = T2D.diff_sentence(s0, s1)
            reached = bool(tidx is not None and si == tidx)
            reached_num = bool(reached and ns is not None and toff is not None and ns[0] <= toff <= ns[1] + 2)
            aid = c["after"]
            st = row[p][u"state"]
            if aid is not None and c["ret"]["state"] != st:
                raise Stop(u"**state が行と違う。止める**")
            u0 = by0.get(aid)
            same_state = None if (aid is None or u0 is None) else (u0["state"] == st)
            base_c = by0.get(row[u"基準の claim"]) or {}
            bp = base_c.get("pointers") or []
            ap = (c["ret"] or {}).get("pointers") or []
            cls = classify6(aid, tidx is not None, reached, st)
            o[u"profile"][p] = {
                u"注入後の claim の id": aid, u"注入後の id が基準と同じ": aid == row[u"基準の claim"], u"注入後の対応の付け方": kind1,
                u"基準の claim の無改変の state": base_c.get("state"),
                u"基準の claim の文の番号": si, u"基準の claim の文の中の位置": r0.get("pos"),
                u"数の始まり": None if ns is None else ns[0], u"数の終わり": None if ns is None else ns[1],
                u"token の文の番号": tidx, u"文の中で最初に違う位置": toff, u"文の数(無改変, 注入後)": [len(s0), len(s1)],
                u"注入後の claim の文の番号": None if aid is None else cap1["raw"].get(aid, {}).get("sentence"),
                u"届いた(文)": reached, u"届いた(数)": reached_num, u"state": st, u"reason": row[p][u"reason"], u"結果": row[p][u"結果"],
                u"注入後の state が無改変の同じ id と同じ": same_state, u"注入後の pointers が在る": bool(ap),
                u"注入後の pointers の先頭が基準と同じ": bool(ap) and bool(bp) and ap[0] == bp[0],
                u"分類": cls, u"細目": detail(cls, reached_num, aid == row[u"基準の claim"], same_state)}
        out_rows.append(o)
    ids_ok = all(c["cid"] in be.caps for c in calls)
    info = {u"文の sha256": tsha, u"文の数": dict((p, len(base[p]["sents"])) for p in PROFILES),
            u"claim の数": dict((p, len(base[p]["claims"])) for p in PROFILES), u"秒": round(time.time() - t0),
            u"claim の一覧の id() が控えに在る": ids_ok}
    return out_rows, rows, counts, len(calls), info


# ----------------------------------------------------------------------------------------------------------------
# 書類ごとの並行(段 1 の ``run_parallel`` と同じ fork。関数は pickle しない)
_JOB = {}


def _job_worker(doc):
    j = _JOB
    work = os.path.join(j["work"], doc)
    os.makedirs(work, exist_ok=True)

    class Tap(object):
        def __enter__(self):
            self.tap = LB._RawTap()
            self.tap.__enter__()
            return real_observe(self.tap)

        def __exit__(self, *a):
            return self.tap.__exit__(*a)
    return work_doc(j["ctx"], T.RealBackend(), Tap, doc, j["seed"], work)


def _proc_main(doc, conn):
    try:
        conn.send(("ok", _job_worker(doc)))
    except BaseException as exc:                                # Stop を含む。文言に値は入っていない
        conn.send(("err", type(exc).__name__, str(exc) if isinstance(exc, SystemExit) else ""))
    finally:
        conn.close()


def run_parallel(docs, procs):
    mp = multiprocessing.get_context("fork")
    pending, running, results = list(docs), {}, {}
    try:
        while pending or running:
            while pending and len(running) < procs:
                d = pending.pop(0)
                parent, child = mp.Pipe(duplex=False)
                proc = mp.Process(target=_proc_main, args=(d, child))
                proc.start()
                child.close()
                running[d] = (proc, parent)
            for d, (proc, conn) in list(running.items()):
                if conn.poll(0.05):
                    msg = conn.recv()
                    proc.join()
                    del running[d]
                    if msg[0] == "err":
                        raise Stop(msg[2] or u"**worker が止まった(%s)。止める**" % msg[1])
                    results[d] = msg[1]
                elif not proc.is_alive() and not conn.poll():
                    raise Stop(u"**worker が結果を返さずに終わった。止める**")
    finally:
        for proc, _conn in running.values():
            proc.terminate()
    return results


# ----------------------------------------------------------------------------------------------------------------
def wiring_check(rows, per_doc_counts, old_records, docs, group):
    u"""配線の門(封 §2-1)。``old_records`` = {記録の名: (行の列, 書類別の数え, 照らす profile)}。
    (行ごとの旗の列, 集合が同じ, 書類別の数えの組, 一致した組, 問題の列)。問題は id と欄の名だけ(文・値を入れない)。"""
    flags, problems = [], []
    maps = dict((name, dict(((r["docID"], r["id"]), r) for r in recs if r["docID"] in docs)) for name, (recs, _c, _p) in old_records.items())
    mine = set((r["docID"], r["id"]) for r in rows)
    same_set = all(mine == set(m) for m in maps.values())
    for r in rows:
        k = (r["docID"], r["id"])
        bad = []
        for name, (_recs, _c, profs) in old_records.items():
            a = maps[name].get(k)
            if a is None:
                bad.append(u"記録に行が無い(%s)" % name)
                continue
            for f in CHECK_FIELDS:
                if (f in r) != (f in a) or r.get(f) != a.get(f):
                    bad.append(u"%s(%s)" % (f, name))
            for p in profs:
                if r[p] != a[p]:
                    bad.append(u"%s(%s)" % (p, name))
        flags.append({u"組": group, u"docID": r["docID"], u"注入の id": r["id"], u"一致": not bad, u"不一致の欄": bad})
        if bad:
            problems.append((r["docID"], r["id"], bad))
    n_pair = n_ok = 0
    for d in docs:
        for t in T.INJECT_TYPES:
            n_pair += 1
            mine_c = json.dumps(per_doc_counts[d][t], ensure_ascii=False, sort_keys=True)
            ok = all(json.dumps(c[d][t], ensure_ascii=False, sort_keys=True) == mine_c for _recs, c, _p in old_records.values())
            n_ok += 1 if ok else 0
    return flags, same_set, n_pair, n_ok, problems


def run_group(ctx, group, docs, old_records, expected_roundtrip, seed, work_root, procs, full_run):
    u"""1 組(調整用か評価用)を走らせ、配線の門を当てる。(観測の行, 書類ごと, 配線, 配線の行ごと)。通らなければ Stop(記録は書かない)。"""
    _JOB.update(ctx=ctx, seed=seed, work=work_root)
    if procs > 1:
        res = run_parallel(docs, procs)
    else:
        res = dict((d, _job_worker(d)) for d in docs)
    obs_rows, inj_rows, per_counts, per_doc, ncalls, adopted, ids_ok = [], [], {}, [], 0, 0, True
    for i, d in enumerate(docs):
        orows, rows, counts, nc, info = res[d]
        for o in orows:
            o[u"組"] = group
        obs_rows += orows
        inj_rows += rows
        per_counts[d] = counts
        ncalls += nc
        adopted += sum(counts[t].get(u"採った", 0) for t in counts)
        ids_ok = ids_ok and info[u"claim の一覧の id() が控えに在る"]
        entry = dict((k, v) for k, v in info.items() if k != u"claim の一覧の id() が控えに在る")
        entry.update({u"組": group, u"docID": d, u"書類の位置": i + 1, u"行": len(rows), u"ZIP の sha256 が一致": True, u"書類別の数え": counts,
                      u"文の sha256 が一致": info[u"文の sha256"] == ctx.report_sha[d]})
        per_doc.append(entry)
    flags, same_set, n_pair, n_ok, problems = wiring_check(inj_rows, per_counts, old_records, set(docs), group)
    for e in per_doc:
        e[u"書類別の数えが記録と一致"] = all(json.dumps(per_counts[e[u"docID"]][t], ensure_ascii=False, sort_keys=True) ==
                                   json.dumps(c[e[u"docID"]][t], ensure_ascii=False, sort_keys=True)
                                   for _r, c, _p in old_records.values() for t in T.INJECT_TYPES)
    n_match = sum(1 for f in flags if f[u"一致"])
    want_rt = expected_roundtrip
    gate = {u"行": len(flags), u"一致": n_match, u"記録の行": sum(1 for r in next(iter(old_records.values()))[0] if r["docID"] in docs),
            u"(docID, id) の集合が同じ": same_set, u"書類別の数えの組": n_pair, u"書類別の数えが一致した組": n_ok,
            u"round-trip": adopted, u"round-trip の期待": want_rt, u"包みの呼ばれた回数": ncalls, u"対応を数えた行 × 4": len(inj_rows) * len(PROFILES),
            u"claim の一覧の id() が控えに在る": ids_ok}
    gate[u"通った"] = bool(same_set and n_match == len(flags) == gate[u"記録の行"] and n_pair == n_ok and adopted == want_rt and
                         ncalls == gate[u"対応を数えた行 × 4"] and ids_ok and (not full_run or adopted == ROUNDTRIP_PIN[group]))
    if not gate[u"通った"]:
        raise Stop(u"**配線の門が通らない(%s: 行 %d / %d、集合 %s、組 %d / %d、round-trip %d / %d、包み %d / %d)。記録を書かずに止める**(不一致の例 %s)" % (
            group, n_match, len(flags), same_set, n_ok, n_pair, adopted, want_rt, ncalls, gate[u"対応を数えた行 × 4"], [(d, i, b) for d, i, b in problems[:3]]))
    return obs_rows, per_doc, gate, flags


def dump_record(rec, rowkeys):
    u"""rows と配線の行ごとは 1 行 1 件の compact JSON。それ以外は indent=1。妥当な JSON。"""
    parts = []
    for k, v in rec.items():
        if k in rowkeys:
            body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in v) + u"\n ]"
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace(u"\n", u"\n ")
        parts.append(u" %s: %s" % (json.dumps(k, ensure_ascii=False), body))
    return u"{\n" + u",\n".join(parts) + u"\n}\n"


def walk_keys(o):
    return T.walk_keys(o)


def assert_allowed_keys(rec):
    extra = sorted(set(k for k in walk_keys(rec) if k not in ALLOWED_KEYS))
    if extra:
        raise Stop(u"**持てる欄の一覧に無い鍵がある(%d 個)。書かずに止める**" % len(extra))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--set", dest="which", default=u"両方", choices=(u"調整用", "tune", u"両方", "both"))
    ap.add_argument("--docs", type=int, default=None, help="調整用の先頭 n 書類だけ(試走)。評価用は受け付けない")
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--work-dir", default=None)
    args = ap.parse_args(argv)
    which = {u"tune": u"調整用", "both": u"両方"}.get(args.which, args.which)
    if os.path.exists(args.out):
        print(u"既に在る(測り直さない): %s" % os.path.basename(args.out))
        return
    if which == u"両方" and args.docs is not None:
        raise Stop(u"**評価用は --docs を受け付けない(本番の 1 回だけ全 10 書類を走らせる)。止める**")
    t_start = time.time()
    T.PROFILES = PROFILES
    if tuple(RR.PROFILES4) != PROFILES or tuple(E.PROFILES) != PROFILES:
        raise Stop(u"**PROFILES4 が評価用の script と違う。止める**")
    tune_file = os.path.join(HERE, "xbrl_p27_tune_2026-10-27.py")
    file_sha = sha256_bytes(T.read_bytes(tune_file))
    for mod in (E.T, RR.T):
        if sha256_bytes(T.read_bytes(mod.__file__)) != file_sha:
            raise Stop(u"**段 1 の file の sha256 が違う。止める**")
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "audit-core/adapters", "audit-core/core"], cwd=os.path.dirname(ROOT)).returncode != 0:
        raise Stop(u"**engine に未 commit の差が在る。止める**")
    zip_dir, cache_root, existing_dir = T.DB.default_zip_dir(), T.DB.default_cache_root(), T.DB.default_existing_cache_dir()
    cache0 = {u"edinet": count_dir(existing_dir), u"edinet-fresh-2026-10-21": count_dir(zip_dir)}
    work_root = tempfile.mkdtemp(prefix="p27_reach_", dir=args.work_dir or os.environ.get("TMPDIR"))
    for prot in (existing_dir, zip_dir):
        if T.inside(work_root, prot):
            raise Stop(u"**作業 folder が既存の cache か ZIP の folder の中。止める**")
    seed, meta = T.IJ.verify_seed_sealed(T.SEED_FILE)
    w = jload(T.REPORTS_REL)
    tune_all = [c["docID"] for c in w[u"会社"] if c[u"区分"] == GROUP_TUNE]
    tune_docs = tune_all if args.docs is None else tune_all[:args.docs]
    ctx_t = T.Ctx(ROOT, zip_dir, cache_root, existing_dir, None, work_root, tune_docs)
    snap0 = T.cache_snapshot(ctx_t)
    inputs = dict((rel, sha64(rel)) for rel in INPUT_RELS)
    old_tune_p27, old_tune, old_eval = jload(TUNE_P27_INJECT_REL), jload(TUNE_INJECT_REL), jload(EVAL_INJECT_REL)
    for d in tune_docs:                                          # 文と ZIP の sha256 を先に照らす(違えば止まる)
        ctx_t.read_report(d)
        ctx_t.read_zip(d)
    sel = set(tune_docs)
    rt_tune = sum(c[t].get(u"採った", 0) for d, c in old_tune_p27[u"書類別の数え"].items() if d in sel for t in c)
    groups, per_docs, gates, flags_all, obs = [], [], {}, [], []
    wd = os.path.join(work_root, "tune")
    os.makedirs(wd)
    r, pd, g, fl = run_group(ctx_t, GROUP_TUNE, tune_docs,
                             collections.OrderedDict([("tune_p27_inject", (old_tune_p27[u"行"], old_tune_p27[u"書類別の数え"], PROFILES)),
                                                      ("tune_inject", (old_tune[u"行"], old_tune[u"書類別の数え"], ("P22", "P26")))]),
                             rt_tune, seed, wd, args.procs, args.docs is None)
    obs += r
    per_docs += pd
    gates[GROUP_TUNE] = g
    flags_all += fl
    groups.append(GROUP_TUNE)
    print(u"調整用: 配線の門 行 %d / %d・組 %d / %d・round-trip %d・%d 秒" % (g[u"一致"], g[u"行"], g[u"書類別の数えが一致した組"], g[u"書類別の数えの組"], g[u"round-trip"], round(time.time() - t_start)))
    sys.stdout.flush()
    if which == u"両方":
        eval_docs = [c["docID"] for c in w[u"会社"] if c[u"区分"] == GROUP_EVAL]
        ctx_e = E.EvalCtx(ROOT, zip_dir, cache_root, existing_dir, None, work_root, eval_docs)
        ctx_e.load_materials(db=False)                           # 文と ZIP の sha256 を 10 書類の全部で先に照らす
        rt_eval = old_eval[u"round-trip"][u"確かめた注入の数"]
        wd = os.path.join(work_root, "eval")
        os.makedirs(wd)
        r, pd, g, fl = run_group(ctx_e, GROUP_EVAL, eval_docs, collections.OrderedDict([("eval_inject", (old_eval[u"行"], old_eval[u"書類別の数え"], PROFILES))]),
                                 rt_eval, seed, wd, args.procs, True)
        obs += r
        per_docs += pd
        gates[GROUP_EVAL] = g
        flags_all += fl
        groups.append(GROUP_EVAL)
        print(u"評価用: 配線の門 行 %d / %d・組 %d / %d・round-trip %d・%d 秒" % (g[u"一致"], g[u"行"], g[u"書類別の数えが一致した組"], g[u"書類別の数えの組"], g[u"round-trip"], round(time.time() - t_start)))
    snap1 = T.cache_snapshot(ctx_t)
    shutil.rmtree(work_root, ignore_errors=True)
    cache1 = {u"edinet": count_dir(existing_dir), u"edinet-fresh-2026-10-21": count_dir(zip_dir)}
    if snap0 != snap1 or cache0 != cache1:
        raise Stop(u"**既存の cache か ZIP の folder の件数か名前が変わった。記録を書かずに止める**")
    rec = collections.OrderedDict()
    rec[u"注意"] = u"診断の記録(封 docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md §5)。engine は 0 行。評価用・調整用の既存の記録は書き換えない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT}
    rec[u"全書類"] = args.docs is None and which == u"両方"
    rec[u"頭"] = {u"HEAD の commit": git("rev-parse", "HEAD"), u"DEFAULT_PROFILE": V.DEFAULT_PROFILE,
                 u"engine sha16": dict((rel, sha16(rel)) for rel in ENGINE_FILES), u"engine の指紋": VD.engine_fingerprint(),
                 u"種": {u"file": u"measure/SEED.json", u"sealed_in_commit": meta.get("sealed_in_commit"), u"seed_file_sha256": meta.get("seed_file_sha256")}, u"読んだ入力の sha256": inputs, u"PROFILES4 が同じ": True, u"段 1 の file の sha256 が同じ": True,
                 u"engine に未 commit の差が無い": True, u"cache": {u"開始": cache0, u"終了": cache1}, u"cache_snapshot が同じ": snap0 == snap1,
                 u"対象": groups}
    rec[u"観測する profile"] = list(PROFILES)
    rec[u"組の順"] = groups
    rec[u"配線"] = gates
    rec[u"書類ごと"] = per_docs
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"評価用 10 社・調整用 10 社・1 書類あたり型ごとに 40 件までの観測。土台で絞られた site(どちらも GROUNDED でない・基準に対応が付かない)の側は見ない。Core 全体の振る舞いを断定しない。",
        u"『届いた(文)』は engine の文の一覧の番号の一致で、claim が読む数そのものの一致ではない(届いた(数)は位置の整数)。",
        u"『届かない』『名指したが別の値』は測定の対応付けの数で、engine の数ではない。pointers の字・claim の span・値は持たない(旗だけ)。",
        u"基準は無改変の P22 と P26 の両方で GROUNDED の claim。P27・P27E の無改変の state は土台の条件に入らない(基準の claim の無改変の state を欄に持つ)。",
        u"文の番号は engine の文の一覧の中の番号で、本文の位置ではない。差し替えが文の切り方を変えると『決まらない』になる。読みは無い(機械の値)。",
    ]
    rec[u"rows"] = obs
    rec[u"配線の行ごと"] = flags_all
    assert_allowed_keys(rec)
    T.assert_record_clean(rec)
    blob = dump_record(rec, (u"rows", u"配線の行ごと"))
    leaks = T.record_key_leaks(json.loads(blob))
    if leaks:
        raise Stop(u"**鍵らしい字が在る。書かずに止める**")
    rec[u"key_leaks"] = []
    blob = dump_record(rec, (u"rows", u"配線の行ごと"))
    T.assert_record_clean(json.loads(blob))
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    back = json.loads(io.open(args.out, encoding="utf-8").read())
    if T.record_key_leaks(back):
        os.remove(args.out)
        raise Stop(u"**書いた後の記録に鍵らしい字が在った。消して止める**")
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", os.path.basename(args.out))


if __name__ == "__main__":
    main()
