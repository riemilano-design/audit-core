# -*- coding: utf-8 -*-
u"""測定: 候補の欄(``candidate``)を足した engine が、他を壊さず、止めた行にだけ候補を付けるか ― 2026-10-30。

封 ``docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md``(commit ``0df5222``)§3(CA-1〜CA-11)・§4(K-1〜K-4)・§6-4・§7-5 と、その承認の追記(commit ``db68a2c``、人間 2026-10-30)の測定。
**engine(``core/``・``adapters/``)は 0 行。この script は測る側。** 既存の記録は書き換えない(別の記録を足す)。0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。
評価用・調整用(``~/.cache/audit-core/edinetdb-p27/``)は開かない。

    cd audit-core
    python3 measure/xbrl_unnamed_candidate_2026-10-29.py --base-dir <空の dir> --procs 4                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_unnamed_candidate_2026-10-29.py --base-dir <空の dir> --docs 2 --out <scratch の file>   # 試走(先頭 n 書類。配線の門はその n 書類の分)

測るもの:

  (a) 97 書類(67 + 新しい標本 30)の有報の原文で、P22・P27・P27C(旗が真。``V.PROFILES["P27C"]``)を走らせ、30 書類だけ P27E と P27EC(= ``replace(P27E, name="P27EC", unnamed_candidate_2026_10_29=True)``。
      実行中だけ ``V.PROFILES`` に差し込み ``finally`` で戻す。戻せていなければ止める)も走らせる。
      比べる側 = ``020ffc0`` の engine を ``git archive`` で ``--base-dir`` に取り出し(commit の blob と byte 一致を確かめる)、別の process で同じ入力に P22・P27(30 書類は P27E も)を走らせた出力。
      CA-1 CA-2 CA-3 CA-4 CA-5 CA-7 と、客向けの報告(``render_markdown``。既定と ``--full``。標準ラベル 3 file は名簿の sha256 で照合したものだけ)の CA-8 CA-10。
  (b) 注入 741 行は診断の便の配線(``measure/xbrl_stop_reason_2026-10-29.py`` を ``_mod`` で読み、``RE.work_doc`` を書類ごとに呼ぶ。自分で注入の規則・対応付けを書かない)。観測する profile は P22・P27・P27C。CA-6。
  K-1〜K-4 は記録に ``採用`` の欄として機械で求める。CA-9・CA-11 は engine を走らせる測定でなく既存の試験の赤の数(段 1 の試験の結果)で、この script は測らない。

配線の門(1 つでも違えば記録を書かずに止める): ZIP の sha256 が ``p26_2026-10-21.json``・``fetched_2026-10-21.json``・``regress97_2026-10-27.json`` と一致 / 比べる側の P22・P27 の 4 state が ``regress97`` と書類ごとに一致 /
  P27(旗が偽。いまの engine)の 4 state も書類ごとに ``regress97`` と一致 / 注入の 741 行の前の便の門(4 欄・id の集合・120 組)と、P27・P27C の注入後の claim(state・reason・pointers・recomputed ほか)が ``stop_reason_2026-10-29.json`` と行ごとに一致 /
  P27C が ``V.PROFILES`` に在り旗が真・P27・P27E の旗が偽 / 標準ラベルが全部名簿どおり。
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
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
#: 比べる側(``020ffc0`` の engine の写し)の process だけが替える。測る側は ROOT のまま
ENGINE_ROOT = os.environ.get("CAND_ENGINE_ROOT") or ROOT
IS_BASE = ENGINE_ROOT != ROOT
sys.path.insert(0, os.path.join(ENGINE_ROOT, "core", "py"))
sys.path.insert(0, ENGINE_ROOT)
if not IS_BASE:
    sys.path.insert(1, HERE)

from adapters.xbrl import verify_document as VD    # noqa: E402
from adapters.xbrl import vocabulary as V          # noqa: E402
from adapters.xbrl import report_customer as RC    # noqa: E402

SEAL_REL = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"
SEAL_COMMIT = "0df5222"
APPROVAL_COMMIT = "db68a2c"
BASE_COMMIT = "020ffc0"
OUT_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
P26_REL = "fixtures/xbrl/p26_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
STOP_REL = "fixtures/xbrl/stop_reason_2026-10-29.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
FRESH_REC_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
DEFAULT27_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
ROSTER_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
INPUT_RELS = (P26_REL, FETCHED_REL, REGRESS_REL, STOP_REL, UNNAMED_REL, FRESH_REC_REL, DEFAULT27_REL, ROSTER_REL)
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
TAXONOMY_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
NSV = "no_same_value"
NOW_PROFILES_67 = ("P22", "P27", "P27C")
NOW_PROFILES_30 = ("P22", "P27", "P27C", "P27E", "P27EC")
BASE_PROFILES_67 = ("P22", "P27")
BASE_PROFILES_30 = ("P22", "P27", "P27E")
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py",
                "adapters/xbrl/resolve.py", "adapters/xbrl/comparators.py", "adapters/xbrl/verify_document.py")
REPORT_FILE = "adapters/xbrl/report_customer.py"
CANDIDATE_MARK = u"。候補: "
LABELS = {"labels": None, "meta": None}


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_text(t):
    return sha_bytes(t.encode("utf-8"))


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return sha_bytes(fh.read())


def sha16_at(root, rel):
    with io.open(os.path.join(root, rel), "rb") as fh:
        return sha_bytes(fh.read())[:16]


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def names_sha(folder):
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return {u"件数": len(names), u"名前の一覧の sha256": sha_text(u"\n".join(names))}


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


# ----------------------------------------------------------------------------------------------------------------
def doc_lists():
    u"""regress97 の script の ``doc_lists()`` と同じ(67 = p26 の key の並び、30 = fetched の 使う順)。"""
    p26 = jload(P26_REL)
    sha67 = p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
    fetched = jload(FETCHED_REL)
    rows30 = [r for r in fetched[u"取得した書類"] if r.get(u"使う")]
    sha30 = dict((r["docID"], r["sha256"]) for r in rows30)
    ids30 = [r["docID"] for r in sorted(rows30, key=lambda r: r[u"使う順"])]
    if sorted(ids30) != sorted(fetched[u"使う書類"]):
        raise SystemExit(u"**使う書類が取得の記録の `使う書類` と合わない。止める**")
    return sorted(sha67), sha67, ids30, sha30


def zip_path(doc, fresh):
    return os.path.join(FRESH_DIR if fresh else EXISTING_CACHE, doc + ".zip")


def drop_dump(out, drop_profile):
    u"""封 §3 の「欄を落とした出力」: 各 claim から ``candidate`` を消し、``engine`` を除いた ``sort_keys`` の JSON(``drop_profile`` なら ``profile`` も除く。封 §6-4)。"""
    d = dict(out)
    d.pop("engine", None)
    if drop_profile:
        d.pop("profile", None)
    d["claims"] = [dict((k, v) for k, v in c.items() if k != "candidate") for c in out["claims"]]
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def row_of(c):
    return [c["id"], c["state"], c["reason"], list(c["pointers"]), c["recomputed"], c.get("candidate")]


def load_labels():
    roster = RC.load_roster(os.path.join(ROOT, ROSTER_REL))
    labels, meta = RC.load_labels_with_meta(TAXONOMY_DIR, None, roster)
    if not meta or any(m["status"] != RC.STATUS_USED for m in meta) or sorted(m["file"] for m in meta) != sorted(roster):
        raise SystemExit(u"**標準ラベルが名簿どおりに読めない: %s。止める**" % dumps(meta))
    LABELS["labels"], LABELS["meta"] = labels, meta


def doc_job(args):
    u"""1 書類・渡された profile の列。出力の sha256(3 通り)・4 state・行・報告の本文(P27・P27C だけ)を返す。span・value は行の candidate 以外返さない。"""
    doc, fresh, expect_sha, profiles = args
    with io.open(zip_path(doc, fresh), "rb") as fh:
        zb = fh.read()
    if sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"fresh": fresh, u"zip の sha256": expect_sha, u"profiles": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        rows = [row_of(c) for c in out["claims"]]
        item = {u"sha256": sha_text(drop_dump(out, False)), u"sha256(profile も除く)": sha_text(drop_dump(out, True)), u"出力の profile": out["profile"],
                u"rows": rows, u"claims": len(rows), u"欄": sorted(out["claims"][0].keys()) if out["claims"] else [],
                u"欄の並び": list(out["claims"][0].keys()) if out["claims"] else []}
        if p in ("P27", "P27C"):
            item[u"md"] = [RC.render_markdown(out, LABELS["labels"], False), RC.render_markdown(out, LABELS["labels"], True)]
        res[u"profiles"][p] = item
    return res


def run_pool(jobs, procs):
    if procs <= 1:
        return [doc_job(j) for j in jobs]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(procs) as pool:
        return list(pool.imap(doc_job, jobs, chunksize=1))


def make_jobs(base, n_docs):
    ids67, sha67, ids30, sha30 = doc_lists()
    if n_docs is not None:
        ids67, ids30 = ids67[:n_docs], ids30[:n_docs]
    p67 = BASE_PROFILES_67 if base else NOW_PROFILES_67
    p30 = BASE_PROFILES_30 if base else NOW_PROFILES_30
    jobs = [(d, False, sha67[d], p67) for d in ids67] + [(d, True, sha30[d], p30) for d in ids30]
    return jobs, ids67, ids30, sha67, sha30


def extract_base(base_dir):
    u"""``020ffc0`` の adapters・core を ``git archive`` で ``base_dir`` に取り出し、adapters/xbrl の .py が commit の blob と byte 一致かを確かめる。"""
    if os.path.exists(base_dir) and os.listdir(base_dir):
        raise SystemExit(u"**--base-dir が空でない。止める**")
    os.makedirs(base_dir, exist_ok=True)
    arc = subprocess.run(["git", "-C", REPO, "archive", BASE_COMMIT, "audit-core/adapters", "audit-core/core"], stdout=subprocess.PIPE, check=True)
    subprocess.run(["tar", "-x", "-C", base_dir], input=arc.stdout, check=True)
    root = os.path.join(base_dir, "audit-core")
    files = {}
    for rel in ["adapters/xbrl/%s" % f for f in sorted(os.listdir(os.path.join(root, "adapters", "xbrl"))) if f.endswith(".py")]:
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:audit-core/%s" % (BASE_COMMIT, rel)], stdout=subprocess.PIPE, check=True).stdout
        with io.open(os.path.join(root, rel), "rb") as fh:
            if fh.read() != blob:
                raise SystemExit(u"**取り出した写しが commit の blob と違う: %s。止める**" % rel)
        files[rel] = sha_bytes(blob)
    return root, files


def run_base(base_dir, procs, n_docs, work):
    root, files = extract_base(base_dir)
    out_json = os.path.join(work, "base_dump.json")
    env = dict(os.environ, CAND_ENGINE_ROOT=root)
    cmd = [sys.executable, os.path.abspath(__file__), "--dump-only", "--procs", str(procs), "--out", out_json]
    if n_docs is not None:
        cmd += ["--docs", str(n_docs)]
    subprocess.run(cmd, env=env, check=True)
    with io.open(out_json, encoding="utf-8") as fh:
        dump = json.load(fh)
    return root, files, dump


# ----------------------------------------------------------------------------------------------------------------
def md_diff(old, new):
    u"""本文 ``old``(比べる側)と ``new`` の行の差。行数が違えば None。返すのは (違う行の数, 違う行ごとの (見出し, 新しい行に「。候補: 」が 1 回, 古い行 = 新しい行から候補の節を除いた字))。"""
    a, b = old.split(u"\n"), new.split(u"\n")
    if len(a) != len(b):
        return None
    heading = u""
    out = []
    for x, y in zip(a, b):
        if y.startswith(u"#"):
            heading = y
        if x != y:
            once = y.count(CANDIDATE_MARK) == 1
            stripped_ok = False
            if once:
                i = y.index(CANDIDATE_MARK)
                stripped_ok = (y[:i] + u" |") == x and y.endswith(u" |")
            out.append((heading, once, stripped_ok, y.startswith(u"| ")))
    return out


def summarize_doc(d, now, base, expect_states, n_docs_full):
    u"""1 書類の記録の行。"""
    P = now[u"profiles"]
    B = base[u"profiles"]
    out = {u"標本": u"新しい標本 30" if now[u"fresh"] else u"手元の 67", u"zip の sha256": now[u"zip の sha256"], u"claims": P["P27"][u"claims"], u"profiles": {}, u"比べる側": {}}
    for p, it in P.items():
        states = collections.Counter(r[1] for r in it["rows"])
        dict_rows = sum(1 for r in it["rows"] if r[5] is not None)
        nsv_rows = sum(1 for r in it["rows"] if r[2] == NSV)
        both = sum(1 for r in it["rows"] if r[5] is not None and r[2] == NSV)
        out[u"profiles"][p] = {u"4 state": dict((s, states.get(s, 0)) for s in STATES), u"claims": it[u"claims"],
                               u"sha256(§3 の字: candidate・engine を除く)": it[u"sha256"], u"sha256(profile も除く)": it[u"sha256(profile も除く)"],
                               u"出力の profile の字": it[u"出力の profile"], u"欄の並び": it[u"欄の並び"],
                               u"候補が辞書の行": dict_rows, u"reason が no_same_value の行": nsv_rows,
                               u"辞書で no_same_value の行": both, u"no_same_value で辞書でない行": nsv_rows - both, u"辞書で no_same_value でない行": dict_rows - both}
    for p, it in B.items():
        states = collections.Counter(r[1] for r in it["rows"])
        out[u"比べる側"][p] = {u"4 state": dict((s, states.get(s, 0)) for s in STATES), u"claims": it[u"claims"], u"sha256": it[u"sha256"],
                           u"sha256(profile も除く)": it[u"sha256(profile も除く)"], u"出力の profile の字": it[u"出力の profile"], u"欄の並び": it[u"欄の並び"]}
    # 行ごと(id・state・reason・pointers・recomputed の 5 つ)
    def same_rows(a, b):
        ra = [r[:5] for r in a["rows"]]
        rb = [r[:5] for r in b["rows"]]
        if [x[0] for x in ra] != [x[0] for x in rb]:
            return None
        return sum(1 for x, y in zip(ra, rb) if x == y)
    rw = {u"P27C と P27(旗が偽。いまの engine)": same_rows(P["P27C"], P["P27"]), u"P27C と 比べる側の P27": same_rows(P["P27C"], B["P27"]),
          u"P27(いまの engine)と 比べる側の P27": same_rows(P["P27"], B["P27"]), u"P22(いまの engine)と 比べる側の P22": same_rows(P["P22"], B["P22"]),
          u"claims": P["P27"][u"claims"]}
    if now[u"fresh"]:
        rw[u"P27EC と P27E(旗が偽。いまの engine)"] = same_rows(P["P27EC"], P["P27E"])
        rw[u"P27E(いまの engine)と 比べる側の P27E"] = same_rows(P["P27E"], B["P27E"])
    out[u"行ごとの一致(5 欄)"] = rw
    # 報告
    rep = {}
    for mode, k in ((u"既定", 0), (u"--full", 1)):
        old = B["P27"]["md"][k]
        flag_off = P["P27"]["md"][k]
        flag_on = P["P27C"]["md"][k]
        diff = md_diff(old, flag_on)
        rep[mode] = {u"旗が偽の本文が比べる側と byte 一致": flag_off == old, u"本文の sha256(比べる側)": sha_text(old), u"本文の sha256(P27 いまの engine)": sha_text(flag_off),
                     u"本文の sha256(P27C)": sha_text(flag_on), u"行数が同じ": diff is not None,
                     u"違う行": None if diff is None else len(diff),
                     u"違う行のうち「。候補: 」を 1 回だけ持つ行": None if diff is None else sum(1 for x in diff if x[1]),
                     u"違う行のうち、候補の節を除くと比べる側の行と同じ行": None if diff is None else sum(1 for x in diff if x[2]),
                     u"違う行のうち、表の行(「| 」で始まる)": None if diff is None else sum(1 for x in diff if x[3]),
                     u"違う行の見出し": None if diff is None else dict(collections.Counter(x[0] for x in diff))}
    out[u"客向けの報告"] = rep
    return out


def p27_states_ok(states_by_doc, reg, label):
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    ok = 0
    for d, st in states_by_doc.items():
        ok += int(all(st[p] == dict((k, regd[d][u"4 state"][p].get(k, 0)) for k in STATES) for p in st))
    return ok


# ----------------------------------------------------------------------------------------------------------------
# 注入 741 行(診断の便の配線)
def load_wiring():
    u"""止めた理由の script を ``_mod`` で読み、観測する profile を P22・P27・P27C にする(``RE.work_doc`` を使う側。注入の規則は書かない)。"""
    def _mod(rel, name):
        sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m
    SR = _mod("measure/xbrl_stop_reason_2026-10-29.py", "stop_reason_for_candidate")
    RE = SR.RE
    RE.OBS = ("P22", "P27", "P27C")
    RE.ALLP = tuple(sorted(set(RE.PROFILES5) | set(RE.OBS)))
    if "candidate" not in RE.CLAIM_KEYS:
        RE.CLAIM_KEYS = RE.CLAIM_KEYS + ("candidate",)
    return SR, RE


WIRING = {}


def run_doc(a):
    u"""書類 1 本(別の process)。``RE.work_doc`` をそのまま呼ぶ(pickle できる位置に置く入れ物)。"""
    return WIRING["RE"].work_doc(a)


def after_of(r, p):
    x = r[u"profile"][p]
    return x["claim"] if r[u"型"] == "T3_ABSENT" else x[u"注入後"]["claim"]


def head_of(c):
    return ((c or {}).get("pointers") or [None])[0]


def g(c, k):
    return None if c is None else c.get(k)


def run_wiring(RE, procs, n_docs):
    FR, IJ, ED, A1 = RE.FR, RE.IJ, RE.ED, RE.A1
    rec_fresh = RE.jload(RE.FRESH_REC_REL)
    rows_rec = rec_fresh[u"注入の行"]
    by_id = dict((r["id"], r) for r in rows_rec)
    docs_all, rows_fetched, fetched = FR.used_docs()
    docs = docs_all if n_docs is None else docs_all[:n_docs]
    seed, meta = IJ.verify_seed_sealed(FR.SEED_FILE)
    work_root = tempfile.mkdtemp(prefix="unnamed_candidate_", dir=os.environ.get("TMPDIR"))
    jobs = []
    for d in docs:
        w = os.path.join(work_root, d)
        os.makedirs(w)
        jobs.append((d, rows_fetched, seed, w, by_id, rec_fresh[u"注入の件数(書類別)"][d]))
    ED.CACHE_DIR = FR.FRESH_DIR
    ctx = multiprocessing.get_context("fork")
    res = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=procs, mp_context=ctx) as ex:
        futs = dict((ex.submit(run_doc, j), j[0]) for j in sorted(jobs, key=lambda j: -rows_fetched[j[0]]["bytes"]))
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            res[r["doc"]] = r
            print(u"完了(注入)%d / %d 書類 (%d 行, %d 秒)" % (len(res), len(docs), len(r[u"rows"]), r[u"秒"]), file=sys.stderr)
            sys.stderr.flush()
    shutil.rmtree(work_root, ignore_errors=True)
    return docs, res, rows_rec, meta, seed


CLAIM_CMP = ("id", "kind", "form", "value", "unit", "span", "state", "reason", "pointers", "recomputed")


def wiring_rows(docs, res, stop, unnamed):
    srow = dict((r["id"], r) for r in stop[u"rows"])
    urow = dict((r["id"], r) for r in unnamed[u"rows"])
    out = []
    w1 = collections.Counter()
    for d in docs:
        for row in res[d][u"rows"]:
            t = row[u"型"]
            o = srow[row["id"]]
            ocl = o[u"profile"]["P27"]["claim"] if t == "T3_ABSENT" else o[u"profile"]["P27"][u"注入後"]["claim"]
            cC, c27, c22 = after_of(row, "P27C"), after_of(row, "P27"), after_of(row, "P22")
            def cmpkeys(c):
                return None if c is None else dict((k, c.get(k)) for k in CLAIM_CMP)
            same27 = dumps(cmpkeys(c27)) == dumps(None if ocl is None else dict((k, ocl.get(k)) for k in CLAIM_CMP))
            sameC = dumps(cmpkeys(cC)) == dumps(None if ocl is None else dict((k, ocl.get(k)) for k in CLAIM_CMP))
            w1[u"P27"] += int(same27)
            w1[u"P27C"] += int(sameC)
            w1[u"P27C state・reason・pointers"] += int(g(cC, "state") == g(ocl, "state") and g(cC, "reason") == g(ocl, "reason") and g(cC, "pointers") == g(ocl, "pointers"))
            cand = g(cC, "candidate")
            if t == "T3_ABSENT":
                base_head_live = None
            else:
                bc = row[u"profile"]["P27C"][u"無改変"]["claim"]
                base_head_live = head_of(bc)
            out.append({u"doc": d, u"id": row["id"], u"型": t, u"state": g(cC, "state"), u"reason": g(cC, "reason"), u"pointers": g(cC, "pointers"),
                        u"candidate": cand,
                        u"P27(旗が偽)の candidate": g(c27, "candidate"), u"P27(旗が偽)の candidate の欄が在る": c27 is not None and "candidate" in c27,
                        u"state・reason・pointers が stop_reason の P27 と同じ": bool(g(cC, "state") == g(ocl, "state") and g(cC, "reason") == g(ocl, "reason") and g(cC, "pointers") == g(ocl, "pointers")),
                        u"claim の 10 欄が stop_reason の P27 と同じ": sameC,
                        u"基準の先頭(P27C の無改変。この process で引いた)": base_head_live, u"P22 の注入後の先頭(この process で引いた)": head_of(c22)})
    return out, w1


# ----------------------------------------------------------------------------------------------------------------
def tally(rec, reg, unnamed):
    u"""記録から CA-1〜CA-8・CA-10 の数と K-1〜K-4 を求める(封 §3・§4)。CA-9・CA-11 は測らない(段 1 の試験の結果)。門は別の書き方で求め直す。"""
    docs = rec[u"書類(出てくる順)"]
    per = rec[u"書類ごと"]
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    fresh = [d for d in docs if per[d][u"標本"] == u"新しい標本 30"]
    old67 = [d for d in docs if per[d][u"標本"] != u"新しい標本 30"]
    t = collections.OrderedDict()
    # CA-1
    c1 = {}
    for p in ("P22", "P27"):
        c1[p + u" の欄を落とした出力の sha256 が比べる側と一致した書類"] = [sum(1 for d in docs if per[d][u"profiles"][p][u"sha256(§3 の字: candidate・engine を除く)"] == per[d][u"比べる側"][p][u"sha256"]), len(docs)]
    c1[u"旗が偽の profile(P22・P27・30 書類は P27E も)で候補が辞書の行"] = sum(per[d][u"profiles"][p][u"候補が辞書の行"] for d in docs for p in per[d][u"profiles"] if p in ("P22", "P27", "P27E"))
    c1[u"P27 の claims の和"] = sum(per[d][u"profiles"]["P27"][u"claims"] for d in docs)
    c1[u"旗が偽の行(P22・P27・P27E の claims の和)"] = sum(per[d][u"profiles"][p][u"claims"] for d in docs for p in per[d][u"profiles"] if p in ("P22", "P27", "P27E"))
    t["CA-1"] = c1
    # CA-2
    c2 = {}
    c2[u"4 state が regress97 の P27 と同じ書類"] = [sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"4 state"] == dict((k, regd[d][u"4 state"]["P27"].get(k, 0)) for k in STATES)), len(docs)]
    c2[u"行ごと(5 欄)が旗が偽の P27 と同じ行"] = [sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と P27(旗が偽。いまの engine)"] for d in docs), sum(per[d][u"claims"] for d in docs)]
    c2[u"行ごと(5 欄)が比べる側の P27 と同じ行"] = [sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と 比べる側の P27"] for d in docs), sum(per[d][u"claims"] for d in docs)]
    c2[u"欄を落とした出力の sha256(§3 の字)が比べる側の P27 と一致した書類"] = [sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"sha256(§3 の字: candidate・engine を除く)"] == per[d][u"比べる側"]["P27"][u"sha256"]), len(docs)]
    c2[u"profile も除いた sha256 が比べる側の P27 と一致した書類(§6-4 の補い。判定に使わない)"] = [sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"sha256(profile も除く)"] == per[d][u"比べる側"]["P27"][u"sha256(profile も除く)"]), len(docs)]
    c2[u"出力の profile の字が P27C の書類"] = [sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"出力の profile の字"] == "P27C"), len(docs)]
    t["CA-2"] = c2
    # CA-3(30 書類)・CA-4(67 書類)
    def block(ds):
        dict_rows = sum(per[d][u"profiles"]["P27C"][u"候補が辞書の行"] for d in ds)
        nsv_rows = sum(per[d][u"profiles"]["P27C"][u"reason が no_same_value の行"] for d in ds)
        both = sum(per[d][u"profiles"]["P27C"][u"辞書で no_same_value の行"] for d in ds)
        return {u"候補が辞書の行": dict_rows, u"reason が no_same_value の行": nsv_rows, u"両方の行": both,
                u"no_same_value で候補が None の行": nsv_rows - both, u"no_same_value でなく候補が辞書の行": dict_rows - both}
    t["CA-3"] = block(fresh)
    t["CA-4"] = block(old67)
    # CA-5
    named = dict(((x["doc"], x["id"]), x) for x in unnamed[u"plain_rows"])
    rows30 = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["doc"] in set(fresh) and x["candidate"] is not None]
    t["CA-5"] = {u"辞書の行": len(rows30),
                 u"pointer が診断の named と同じ": sum(1 for x in rows30 if (x["doc"], x["id"]) in named and named[(x["doc"], x["id"])][u"named"] == x["candidate"]["pointer"]),
                 u"value が診断の named の value と同じ": sum(1 for x in rows30 if (x["doc"], x["id"]) in named and named[(x["doc"], x["id"])][u"named の value"] == x["candidate"]["value"]),
                 u"basis が no_same_value": sum(1 for x in rows30 if x["candidate"]["basis"] == NSV),
                 u"診断の記録に無い行": sum(1 for x in rows30 if (x["doc"], x["id"]) not in named)}
    # CA-6
    r741 = rec[u"注入 741 行"]
    urow = dict((x["id"], x) for x in unnamed[u"rows"])
    dr = [x for x in r741 if x["candidate"] is not None]
    mains = [x for x in dr if x[u"型"] != "T3_ABSENT"]
    t3 = [x for x in dr if x[u"型"] == "T3_ABSENT"]
    t["CA-6"] = {u"行": len(r741), u"state・reason・pointers が stop_reason の P27 と同じ行": sum(1 for x in r741 if x[u"state・reason・pointers が stop_reason の P27 と同じ"]),
                 u"候補が辞書の行": len(dr), u"型別": dict(collections.Counter(x[u"型"] for x in dr)),
                 u"pointer が unnamed_fact の named と同じ": sum(1 for x in dr if urow[x["id"]][u"named"] == x["candidate"]["pointer"]),
                 u"T1・T2・T5: pointer が原本の基準の先頭と同じ": [sum(1 for x in mains if urow[x["id"]][u"基準の先頭"] == x["candidate"]["pointer"]), len(mains)],
                 u"T3: pointer が P22 の注入後の先頭と同じ": [sum(1 for x in t3 if urow[x["id"]][u"P22 の注入後の先頭"] == x["candidate"]["pointer"]), len(t3)],
                 u"候補が None の行": len(r741) - len(dr),
                 u"旗が偽の P27 の候補が辞書の行": sum(1 for x in r741 if x[u"P27(旗が偽)の candidate"] is not None)}
    # CA-7
    e = rec[u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)"]
    moved = [x for x in e if x[u"P27 の reason"] == NSV and x["reason"] != NSV]
    t["CA-7"] = {u"候補が辞書の行": sum(1 for x in e if x["candidate"] is not None), u"P27EC の reason が no_same_value の行": sum(1 for x in e if x["reason"] == NSV),
                 u"P27 の no_same_value の行": sum(1 for x in e if x[u"P27 の reason"] == NSV), u"B が動かした行": len(moved),
                 u"B が動かした行のうち VALUE_MISMATCH": sum(1 for x in moved if x["state"] == "VALUE_MISMATCH"),
                 u"候補が付く行と B が動かした行の積": sum(1 for x in moved if x["candidate"] is not None),
                 u"no_same_value で候補が None の行": sum(1 for x in e if x["reason"] == NSV and x["candidate"] is None),
                 u"no_same_value でなく候補が辞書の行": sum(1 for x in e if x["reason"] != NSV and x["candidate"] is not None)}
    # CA-8・CA-10
    t["CA-8"] = dict(((m, [sum(1 for d in docs if per[d][u"客向けの報告"][m][u"旗が偽の本文が比べる側と byte 一致"]), len(docs)]) for m in (u"既定", u"--full")))
    c10 = {}
    for m in (u"既定", u"--full"):
        c10[m] = {u"違う行": sum(per[d][u"客向けの報告"][m][u"違う行"] for d in fresh),
                 u"「。候補: 」を 1 回だけ持つ行": sum(per[d][u"客向けの報告"][m][u"違う行のうち「。候補: 」を 1 回だけ持つ行"] for d in fresh),
                 u"候補の節を除くと比べる側の行と同じ行": sum(per[d][u"客向けの報告"][m][u"違う行のうち、候補の節を除くと比べる側の行と同じ行"] for d in fresh),
                 u"表の行": sum(per[d][u"客向けの報告"][m][u"違う行のうち、表の行(「| 」で始まる)"] for d in fresh),
                 u"要確認の見出しの下の行": sum(n for d in fresh for h, n in per[d][u"客向けの報告"][m][u"違う行の見出し"].items() if u"要確認" in h),
                 u"書類ごとの違う行 = その書類の候補が辞書の行": [sum(1 for d in fresh if per[d][u"客向けの報告"][m][u"違う行"] == per[d][u"profiles"]["P27C"][u"候補が辞書の行"]), len(fresh)],
                 u"行数が同じ書類": [sum(1 for d in fresh if per[d][u"客向けの報告"][m][u"行数が同じ"]), len(fresh)]}
    t["CA-10"] = c10
    t["CA-10"][u"既定と --full で書類ごとの違う行の数が同じ書類"] = [sum(1 for d in fresh if per[d][u"客向けの報告"][u"既定"][u"違う行"] == per[d][u"客向けの報告"][u"--full"][u"違う行"]), len(fresh)]
    # K
    k = collections.OrderedDict()
    k["K-1"] = bool(c2[u"行ごと(5 欄)が旗が偽の P27 と同じ行"][0] == c2[u"行ごと(5 欄)が旗が偽の P27 と同じ行"][1]
                    and c2[u"行ごと(5 欄)が比べる側の P27 と同じ行"][0] == c2[u"行ごと(5 欄)が比べる側の P27 と同じ行"][1]
                    and c2[u"4 state が regress97 の P27 と同じ書類"][0] == c2[u"4 state が regress97 の P27 と同じ書類"][1])
    k["K-2"] = bool(t["CA-6"][u"state・reason・pointers が stop_reason の P27 と同じ行"] == t["CA-6"][u"行"])
    k["K-3"] = bool(all(v[0] == v[1] for key, v in c1.items() if key.endswith(u"一致した書類")) and c1[u"旗が偽の profile(P22・P27・30 書類は P27E も)で候補が辞書の行"] == 0
                    and all(v[0] == v[1] for v in t["CA-8"].values()))
    k["K-4"] = bool(t["CA-3"][u"no_same_value で候補が None の行"] == 0 and t["CA-3"][u"no_same_value でなく候補が辞書の行"] == 0
                    and t["CA-4"][u"no_same_value で候補が None の行"] == 0 and t["CA-4"][u"no_same_value でなく候補が辞書の行"] == 0)
    k[u"全部"] = all(k.values())
    return t, k


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--docs", type=int, default=None, help="先頭 n 書類だけ(試走。67 側・30 側とも n。正本の記録は全部)")
    ap.add_argument("--base-dir", default=None, help="比べる側の engine を取り出す空の dir")
    ap.add_argument("--dump-only", action="store_true", help="(内部)比べる側の engine で出力だけ書く")
    a = ap.parse_args()
    if a.dump_only:
        if not IS_BASE:
            raise SystemExit(u"**--dump-only は CAND_ENGINE_ROOT を替えた process だけ。止める**")
        load_labels()
        jobs, _a, _b, _c, _d = make_jobs(True, a.docs)
        res = run_pool(jobs, a.procs)
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        return
    if IS_BASE:
        raise SystemExit(u"**測る側の process で CAND_ENGINE_ROOT が替わっている。止める**")
    if os.path.exists(a.out):
        print(u"既に在る(測り直さない): %s" % a.out)
        return
    if not a.base_dir:
        raise SystemExit(u"**--base-dir が要る。止める**")
    t_start = time.time()
    before = {u"edinet": names_sha(EXISTING_CACHE), u"edinet-fresh-2026-10-21": names_sha(FRESH_DIR)}
    # ---- 旗・登録の確認(測る側)
    if "P27C" not in V.PROFILES or not V.PROFILES["P27C"].unnamed_candidate_2026_10_29:
        raise SystemExit(u"**P27C が登録されていないか旗が偽。止める**")
    if V.PROFILES["P27"].unnamed_candidate_2026_10_29 or V.PROFILES["P27E"].unnamed_candidate_2026_10_29 or V.DEFAULT_PROFILE != "P27":
        raise SystemExit(u"**既定の P27・P27E の旗が真、または DEFAULT_PROFILE が P27 でない。止める**")
    if "P27EC" in V.PROFILES:
        raise SystemExit(u"**P27EC が最初から登録されている。止める**")
    load_labels()
    work = tempfile.mkdtemp(prefix="unnamed_candidate_", dir=os.environ.get("TMPDIR"))
    # ---- (a) 比べる側 → いまの engine
    base_root, base_files, base_dump = run_base(a.base_dir, a.procs, a.docs, work)
    now_files = dict((rel, sha16_at(ROOT, rel)) for rel in ENGINE_FILES + (REPORT_FILE,))
    base_sha16 = dict((rel, sha16_at(base_root, rel)) for rel in ENGINE_FILES + (REPORT_FILE,))
    jobs, ids67, ids30, sha67, sha30 = make_jobs(False, a.docs)
    V.PROFILES["P27EC"] = dataclasses.replace(V.P27E, name="P27EC", unnamed_candidate_2026_10_29=True)
    try:
        now_res = run_pool(jobs, a.procs)
    finally:
        V.PROFILES.pop("P27EC", None)
    if "P27EC" in V.PROFILES:
        raise SystemExit(u"**P27EC を V.PROFILES から戻せていない。止める**")
    reg = jload(REGRESS_REL)
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    now_by = dict((r["doc"], r) for r in now_res)
    base_by = dict((r["doc"], r) for r in base_dump)
    docs97 = ids67 + ids30
    # ---- 配線の門(a)
    gate_a = {}
    gate_a[u"ZIP の sha256 が p26・fetched・regress97 と一致"] = all(regd[d][u"zip の sha256"] == (sha67[d] if d in sha67 else sha30[d]) for d in docs97)
    st_base = dict((d, dict((p, dict((s, collections.Counter(r[1] for r in base_by[d][u"profiles"][p]["rows"]).get(s, 0)) for s in STATES)) for p in ("P22", "P27"))) for d in docs97)
    st_now = dict((d, dict((p, dict((s, collections.Counter(r[1] for r in now_by[d][u"profiles"][p]["rows"]).get(s, 0)) for s in STATES)) for p in ("P22", "P27"))) for d in docs97)
    gate_a[u"比べる側の P22・P27 の 4 state が regress97 と一致した書類"] = [p27_states_ok(st_base, reg, "base"), len(docs97)]
    gate_a[u"いまの engine の P22・P27(旗が偽)の 4 state が regress97 と一致した書類"] = [p27_states_ok(st_now, reg, "now"), len(docs97)]
    st_e = dict((d, {"P27E": dict((s, collections.Counter(r[1] for r in now_by[d][u"profiles"]["P27E"]["rows"]).get(s, 0)) for s in STATES)}) for d in ids30)
    gate_a[u"いまの engine の P27E(旗が偽。30 書類)の 4 state が regress97 と一致した書類"] = [p27_states_ok(st_e, reg, "now"), len(ids30)]
    gate_a[u"標準ラベルを名簿どおりに読んだ file"] = [len(LABELS["meta"]), len(LABELS["meta"])]
    gate_a[u"通った"] = bool(gate_a[u"ZIP の sha256 が p26・fetched・regress97 と一致"]
                          and all(v[0] == v[1] for k, v in gate_a.items() if isinstance(v, list)))
    if not gate_a[u"通った"]:
        raise SystemExit(u"**配線の門(97 書類)が通らない: %s。記録を書かずに止める**" % dumps(gate_a))
    per_doc = collections.OrderedDict()
    for d in docs97:
        per_doc[d] = summarize_doc(d, now_by[d], base_by[d], None, None)
    # 候補の行(いずれかの profile で reason が no_same_value か候補が辞書の行)
    cand_rows = []
    for d in docs97:
        P = now_by[d][u"profiles"]
        for r in P["P27C"]["rows"]:
            if r[5] is not None or r[2] == NSV:
                cand_rows.append({u"doc": d, u"id": r[0], u"state": r[1], u"reason": r[2], u"candidate": r[5]})
    p27e_rows = []
    for d in ids30:
        P = now_by[d][u"profiles"]
        p27 = dict((r[0], r) for r in P["P27"]["rows"])
        for r in P["P27EC"]["rows"]:
            q = p27[r[0]]
            if r[5] is not None or r[2] == NSV or q[2] == NSV:
                p27e_rows.append({u"doc": d, u"id": r[0], u"P27 の state": q[1], u"P27 の reason": q[2], u"state": r[1], u"reason": r[2], u"candidate": r[5]})
    # ---- (b) 741 行
    SR, RE = load_wiring()
    WIRING["RE"] = RE
    stop = RE.jload(STOP_REL)
    unnamed = RE.jload(UNNAMED_REL)
    engine_now = dict((rel, RE.sha16(rel)) for rel in RE.ENGINE_FILES)
    changed = {"adapters/xbrl/vocabulary.py", "adapters/xbrl/verify_document.py"}
    for rel, v in engine_now.items():
        if rel not in changed and stop[u"engine sha16"][rel] != v:
            raise SystemExit(u"**変えない engine の file の sha16 が stop_reason の記録と違う: %s。走らせずに止める**" % rel)
    docs741, res741, rows_rec, seed_meta, _seed = run_wiring(RE, a.procs, a.docs)
    wiring = [x for d in docs741 for x in res741[d][u"wiring"]]
    rows741, w1c = wiring_rows(docs741, res741, stop, unnamed)
    n_match = sum(1 for w in wiring if w[u"一致"][u"4 欄とも一致"])
    n_pairs = len(docs741) * len(RE.INJECT_TYPES)
    n_pairs_ok = sum(1 for d in docs741 for t in RE.INJECT_TYPES if res741[d][u"counts"][t][u"3 つの数が記録と一致"])
    rec_ids = sorted(r["id"] for r in rows_rec if r["doc"] in docs741)
    mine_ids = sorted(w["id"] for w in wiring)
    gate_b = {u"前の便の門(4 欄とも一致)": [n_match, len(wiring)], u"id の集合が記録と同じ": rec_ids == mine_ids, u"記録の注入の行(対象の書類)": len(rec_ids),
              u"注入の件数の組": [n_pairs_ok, n_pairs], u"行": len(rows741),
              u"P27(旗が偽)の claim が stop_reason と一致した行": [w1c[u"P27"], len(rows741)],
              u"P27C の claim が stop_reason の P27 と一致した行(10 欄)": [w1c[u"P27C"], len(rows741)],
              u"P27C の state・reason・pointers が stop_reason の P27 と一致した行": [w1c[u"P27C state・reason・pointers"], len(rows741)]}
    gate_b[u"通った"] = bool(gate_b[u"id の集合が記録と同じ"] and n_match == len(wiring) == len(rec_ids) and n_pairs_ok == n_pairs
                          and w1c[u"P27"] == w1c[u"P27C"] == w1c[u"P27C state・reason・pointers"] == len(rows741))
    if not gate_b[u"通った"]:
        raise SystemExit(u"**配線の門(741 行)が通らない: %s。記録を書かずに止める**" % dumps(gate_b))
    after = {u"edinet": names_sha(EXISTING_CACHE), u"edinet-fresh-2026-10-21": names_sha(FRESH_DIR)}
    if before != after:
        raise SystemExit(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    with io.open(os.path.abspath(__file__), "rb") as fh:
        script_sha = sha_bytes(fh.read())
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"測定の記録(封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §7-5)。engine は 0 行(段 1 の実装をそのまま測った)。既存の記録は書き換えない。"
                  u"候補の正しさは測っていない(封 §4)。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT, u"承認の追記の commit": APPROVAL_COMMIT}
    rec[u"全書類"] = a.docs is None
    rec[u"HEAD"] = git("rev-parse", "HEAD")
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"この script の sha256"] = script_sha
    rec[u"engine sha16"] = now_files
    rec[u"比べる側"] = {u"commit": BASE_COMMIT, u"取り出し方": u"git archive <commit> audit-core/adapters audit-core/core を --base-dir に取り出し、adapters/xbrl の .py が commit の blob と byte 一致かを確かめ、同じ script を CAND_ENGINE_ROOT を替えた別 process で走らせた",
                    u"engine sha16": base_sha16, u"adapters/xbrl の file の sha256(commit の blob)": base_files}
    rec[u"読んだ入力の sha256"] = dict((rel, sha64(rel)) for rel in INPUT_RELS)
    rec[u"ラベル"] = {u"dir": u"~/.cache/audit-core/edinet-taxonomy/2025-11-01", u"名簿": ROSTER_REL, u"読んだ file": LABELS["meta"],
                    u"書類自身のラベル": u"読まない(標準ラベルだけ。ZIP の *_lab.xml は渡さない)"}
    rec[u"書類(出てくる順)"] = docs97
    rec[u"注入の書類(出てくる順)"] = docs741
    rec[u"profile"] = {u"いまの engine": {"P22": u"旗が偽", "P27": u"旗が偽(既定)", "P27C": u"旗が真(封 (イ)。登録済み)", "P27E": u"旗が偽", "P27EC": u"旗が真(replace(P27E, name=P27EC, 旗=True)。実行中だけ V.PROFILES に差し込み、finally で戻した)"},
                     u"比べる側": {"P22": u"旗なし", "P27": u"旗なし", "P27E": u"旗なし"}}
    rec[u"書類ごと"] = per_doc
    rec[u"配線の門"] = {u"97 書類": gate_a, u"741 行": gate_b, u"通った": bool(gate_a[u"通った"] and gate_b[u"通った"])}
    rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] = cand_rows
    rec[u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)"] = p27e_rows
    rec[u"注入 741 行"] = rows741
    rec[u"cache"] = {u"開始": before, u"終了": after, u"変化なし": before == after}
    rec[u"CA の数"], rec[u"採用"] = tally(rec, reg, unnamed)
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"候補の正しさは測っていない(封 §4)。候補が付く無改変の行に正解は無い。『同じ』は字の一致で、人の目は入らない。",
        u"CA-9(既存の golden)・CA-11(既存の試験の赤の数)は engine を走らせる測定でなく、段 1 の試験の結果を文書に写した。この記録は測っていない。",
        u"報告は標準ラベル 3 file だけで描いた(書類自身のラベルは渡していない)。書類自身のラベルを渡すと候補の要素名・区分の字が変わりうるが、違う行の数は変わらない見込みで測っていない。",
        u"67 書類・30 書類・741 行の観測で、他の書類で同じ数になるとは言えない。",
        u"P27EC は実行中だけ V.PROFILES に差し込んだ profile で、engine に登録していない。既定の P27・P27E は旗が偽のまま。",
    ]
    rec[u"key_leaks"] = []
    blob = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    for needle in (u"api_key", u"API_KEY", u"Bearer ", u"sk-"):
        if needle in blob:
            raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % needle)
    shutil.rmtree(work, ignore_errors=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"-> %s 所要秒 %d" % (a.out, rec[u"所要秒"]))


if __name__ == "__main__":
    main()
