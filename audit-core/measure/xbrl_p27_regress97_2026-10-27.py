# -*- coding: utf-8 -*-
u"""P27 段 2 §5 ― 手元の 97 書類(67 + 新しい標本 30)の有報の原文で、profile を足した engine が他を壊さないかの測定。
封 ``docs/XBRL_P27_SEAL_2026-10-27.md`` §3-3(N-1〜N-3)・§5。

    cd audit-core
    python3 measure/xbrl_p27_regress97_2026-10-27.py --out fixtures/xbrl/p27/regress97_2026-10-27.json [--procs 4]

**0 USD・通信なし・鍵は読まない・LLM は呼ばない。** 書類は手元の cache の ZIP だけ(``~/.cache/audit-core/edinet/`` と ``edinet-fresh-2026-10-21/``。読むだけで 1 file も足さない。
件数と名前の一覧の sha256 を前後で記録し、変わっていれば記録を書かずに止める)。engine(``core/``・``adapters/``)は測る側から 1 行も変えない。

測るもの:

  N-1  旗が偽の profile(P22・P26)で、97 書類の ``verify_document`` の出力(``sort_keys`` の JSON。``engine`` の欄を除く)が、封の時点の engine
       (commit ``29e6d0a``。``git archive`` で TMPDIR に取り出した写し。この script を別の process で走らせて測る)と 1 byte も違わない書類の数。
  N-2  P27: 67 書類・30 書類の 4 state(P26 と同じか)、P26 → P27 で動いた行(state か reason か pointer が違う行)の向きと数。
  N-3  P27E: P27 → P27E で動いた行の向きと数。

評価用の 10 社の有報の原文 ZIP はこの測定で開いてよい(封 §5・§10-5。P26 の新しい標本として既に測って読んだ書類)。**評価用の AI の文・DB の応答は開かない**
(この script は ``edinetdb-p27/`` の下を 1 file も読まない)。記録に span・value・recomputed は入れない。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
ENGINE_ROOT = os.environ.get("P27_ENGINE_ROOT") or ROOT          # 比べる側(封の時点の engine の写し)を別の process で測るときだけ替える
sys.path.insert(0, os.path.join(ENGINE_ROOT, "core", "py"))
sys.path.insert(0, ENGINE_ROOT)

from adapters.xbrl import verify_document as VD   # noqa: E402
from adapters.xbrl import vocabulary as V         # noqa: E402

SEAL = "docs/XBRL_P27_SEAL_2026-10-27.md"
BASELINE_COMMIT = "29e6d0a"                       # 封 §3-3 N-1 の「HEAD 29e6d0a の engine」
OUT_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
P26_REL = "fixtures/xbrl/p26_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
DEFAULT_P26_REL = "fixtures/xbrl/default_p26_2026-10-23.json"
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
NOW_PROFILES = ("P22", "P26", "P27", "P27E")
BASE_PROFILES = ("P22", "P26")
NO_SAME_VALUE = "no_same_value"
OTHER_CONCEPT = "other_concept"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def names_sha(folder):
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return {u"件数": len(names), u"名前の一覧の sha256": sha_bytes(u"\n".join(names).encode("utf-8"))}


def doc_lists():
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


def dump_no_engine(out):
    d = dict(out)
    d.pop("engine", None)
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def _claim_rows(out):
    return [(c["id"], c["state"], c["reason"], tuple(c["pointers"])) for c in out["claims"]]


def doc_job(args):
    u"""1 書類・渡された profile の列。出力の sha256(engine を除く)と claim の行だけを返す(span・value・recomputed は返さない)。"""
    doc, fresh, expect_sha, profiles = args
    with io.open(zip_path(doc, fresh), "rb") as fh:
        zb = fh.read()
    if sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"fresh": fresh, u"zip の sha256": expect_sha, u"profiles": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        res[u"profiles"][p] = {u"sha256": sha_bytes(dump_no_engine(out).encode("utf-8")), u"rows": _claim_rows(out),
                              u"engine の欄を除いた JSON の bytes": len(dump_no_engine(out).encode("utf-8"))}
    if V.PROFILES.get("P27") is not None and "P27" in profiles:
        res[u"規則ごと"] = rule_counts(zb, profiles)
    return res


def rule_counts(zb, profiles):
    u"""P27・P27E の raw claim から、規則ごとに当たった claim の数(封 §7 の V-6 と同じ数え方)。"""
    from adapters.xbrl import recipes as R
    out = {}
    for p in ("P27", "P27E"):
        if p not in profiles:
            continue
        nums, _texts = R.build_raw_claims(zb, V.PROFILES[p])
        out[p] = {u"C2 per_unit_counter": sum(1 for c in nums if c.get("p27_gate") == "per_unit_counter"),
                  u"C3 future_period": sum(1 for c in nums if c.get("p27_gate") == "future_period"),
                  u"C1 の窓に入った claim": sum(1 for c in nums if c.get("per_share_window_2026_10_27")),
                  u"C1 の窓に入って other_concept になった claim": sum(1 for c in nums if c.get("per_share_window_2026_10_27") and c.get("reason") == OTHER_CONCEPT),
                  u"B relative_within_rho": sum(1 for c in nums if c.get("last_branch_evidence") == "relative_within_rho")}
    return out


def run_pool(jobs, procs):
    if procs <= 1:
        return [doc_job(j) for j in jobs]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(procs) as pool:
        return list(pool.imap(doc_job, jobs, chunksize=1))


# ====================================================================================================
def baseline_dump(procs, work):
    u"""封の時点の engine を ``git archive`` で取り出し、同じ script を別の process で走らせて P22・P26 の出力の sha256 を得る。"""
    base = os.path.join(work, "baseline_engine")
    os.makedirs(base)
    arc = subprocess.run(["git", "-C", REPO, "archive", BASELINE_COMMIT, "audit-core/adapters", "audit-core/core"], stdout=subprocess.PIPE, check=True)
    subprocess.run(["tar", "-x", "-C", base], input=arc.stdout, check=True)
    root = os.path.join(base, "audit-core")
    files = {}
    for rel in ("adapters/xbrl/%s" % f for f in sorted(os.listdir(os.path.join(root, "adapters", "xbrl"))) if f.endswith(".py")):
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:audit-core/%s" % (BASELINE_COMMIT, rel)], stdout=subprocess.PIPE, check=True).stdout
        with io.open(os.path.join(root, rel), "rb") as fh:
            if fh.read() != blob:
                raise SystemExit(u"**取り出した写しが commit の blob と違う: %s。止める**" % rel)
        files[rel] = sha_bytes(blob)
    out_json = os.path.join(work, "baseline_dump.json")
    env = dict(os.environ, P27_ENGINE_ROOT=root)
    cmd = [sys.executable, os.path.abspath(__file__), "--dump-only", "--profiles", ",".join(BASE_PROFILES), "--procs", str(procs), "--out", out_json]
    subprocess.run(cmd, env=env, check=True)
    with io.open(out_json, encoding="utf-8") as fh:
        dump = json.load(fh)
    return dump, files


def run(procs, dump_only=False, profiles=None, out=None):
    ids67, sha67, ids30, sha30 = doc_lists()
    jobs = [(d, False, sha67[d], tuple(profiles or NOW_PROFILES)) for d in ids67] + [(d, True, sha30[d], tuple(profiles or NOW_PROFILES)) for d in ids30]
    results = run_pool(jobs, procs)
    return results, ids67, ids30


def moved_rows(res_by_doc, a, b):
    u"""profile a -> b で state か reason か pointers が違う行。(docID, id, 前, 後, pointer だけ替わったか)。"""
    out = []
    for doc, r in res_by_doc.items():
        ra, rb = r[u"profiles"][a][u"rows"], r[u"profiles"][b][u"rows"]
        if [x[0] for x in ra] != [x[0] for x in rb]:
            raise SystemExit(u"**claim の id の並びが違う: %s %s/%s。止める**" % (doc, a, b))
        for x, y in zip(ra, rb):
            if tuple(x[1:]) != tuple(y[1:]):
                out.append({u"docID": doc, u"id": x[0], u"前": {u"state": x[1], u"reason": x[2]}, u"後": {u"state": y[1], u"reason": y[2]},
                            u"pointer だけ替わった": x[1] == y[1] and x[2] == y[2] and list(x[3]) != list(y[3])})
    return out


def state_counts(res_by_doc, p):
    c = collections.Counter()
    for r in res_by_doc.values():
        c.update(row[1] for row in r[u"profiles"][p][u"rows"])
    return dict((s, c.get(s, 0)) for s in STATES)


def direction(m):
    return u"%s → %s" % (m[u"前"][u"state"], m[u"後"][u"state"])


def summarize(res, ids67, ids30):
    by = dict((r[u"doc"], r) for r in res)
    pops = {u"手元の 67": dict((d, by[d]) for d in ids67), u"新しい標本 30": dict((d, by[d]) for d in ids30)}
    out = {}
    for name, rows in pops.items():
        m_a = moved_rows(rows, "P26", "P27")
        m_b = moved_rows(rows, "P27", "P27E")
        st = dict((p, state_counts(rows, p)) for p in NOW_PROFILES)
        a_state = [m for m in m_a if m[u"前"][u"state"] != m[u"後"][u"state"]]
        a_ok = [m for m in a_state if (m[u"前"][u"state"], m[u"後"][u"state"]) in (("UNVERIFIABLE", "POINTER_NOT_FOUND"), ("POINTER_NOT_FOUND", "UNVERIFIABLE"))]
        a_g_ptr = [m for m in m_a if m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] == "GROUNDED" and m[u"pointer だけ替わった"]]
        b_to_vm = [m for m in m_b if m[u"前"][u"state"] == "POINTER_NOT_FOUND" and m[u"前"][u"reason"] == NO_SAME_VALUE and m[u"後"][u"state"] == "VALUE_MISMATCH"]
        b_to_oc = [m for m in m_b if m[u"前"][u"state"] == "POINTER_NOT_FOUND" and m[u"前"][u"reason"] == NO_SAME_VALUE
                   and m[u"後"][u"state"] == "POINTER_NOT_FOUND" and m[u"後"][u"reason"] == OTHER_CONCEPT]
        b_other = [m for m in m_b if m not in b_to_vm and m not in b_to_oc]
        out[name] = {
            u"書類": len(rows), u"claims": sum(len(r[u"profiles"]["P26"][u"rows"]) for r in rows.values()),
            u"4 state": st,
            u"P26 → P27": {u"動いた行(state か reason か pointer が違う)": len(m_a), u"state が違う行": len(a_state),
                         u"向き": dict(sorted(collections.Counter(direction(m) for m in a_state).items())),
                         u"UNVERIFIABLE と POINTER_NOT_FOUND の間だけの行": len(a_ok), u"他の向きの行": len(a_state) - len(a_ok),
                         u"state は同じで reason だけ違う行": sum(1 for m in m_a if m[u"前"][u"state"] == m[u"後"][u"state"] and m[u"前"][u"reason"] != m[u"後"][u"reason"]),
                         u"GROUNDED のまま pointer が替わる行": len(a_g_ptr),
                         u"VALUE_MISMATCH に入る行": sum(1 for m in m_a if m[u"後"][u"state"] == "VALUE_MISMATCH" and m[u"前"][u"state"] != "VALUE_MISMATCH"),
                         u"新しい GROUNDED": sum(1 for m in m_a if m[u"後"][u"state"] == "GROUNDED" and m[u"前"][u"state"] != "GROUNDED"),
                         u"GROUNDED を離れる行": sum(1 for m in m_a if m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] != "GROUNDED")},
            u"P27 → P27E": {u"動いた行": len(m_b), u"VALUE_MISMATCH に入る行(no_same_value → VALUE_MISMATCH)": len(b_to_vm),
                          u"名指した後に G1 で止まる行(no_same_value → other_concept)": len(b_to_oc), u"他の向きの行": len(b_other),
                          u"GROUNDED が P27 と違う行": sum(1 for m in m_b if m[u"前"][u"state"] == "GROUNDED" or m[u"後"][u"state"] == "GROUNDED")},
            u"規則ごとに当たった claim の数": dict((p, dict((k, sum(r.get(u"規則ごと", {}).get(p, {}).get(k, 0) for r in rows.values()))
                                                      for k in (u"C2 per_unit_counter", u"C3 future_period", u"C1 の窓に入った claim",
                                                                u"C1 の窓に入って other_concept になった claim", u"B relative_within_rho"))) for p in ("P27", "P27E")),
        }
        out[name][u"_moved_P26_P27"] = m_a
        out[name][u"_moved_P27_P27E"] = m_b
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--dump-only", action="store_true", help="(内部)比べる側の engine で profile を絞って出力の sha256 だけ書く")
    ap.add_argument("--profiles", default=None)
    a = ap.parse_args(argv)
    if a.dump_only:
        res, _i67, _i30 = run(a.procs, True, a.profiles.split(","))
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        return
    if os.path.exists(a.out):
        raise SystemExit(u"**出力が既に在る。測り直さない。止める**")
    before = {u"edinet": names_sha(EXISTING_CACHE), u"edinet-fresh-2026-10-21": names_sha(FRESH_DIR)}
    work = tempfile.mkdtemp(prefix="p27_regress97_", dir=os.environ.get("TMPDIR"))
    base, base_files = baseline_dump(a.procs, work)
    res, ids67, ids30 = run(a.procs)
    after = {u"edinet": names_sha(EXISTING_CACHE), u"edinet-fresh-2026-10-21": names_sha(FRESH_DIR)}
    if before != after:
        raise SystemExit(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    base_by = dict((r[u"doc"], r) for r in base)
    now_by = dict((r[u"doc"], r) for r in res)
    n1 = {}
    for p in BASE_PROFILES:
        same = [d for d in now_by if now_by[d][u"profiles"][p][u"sha256"] == base_by[d][u"profiles"][p][u"sha256"]]
        n1[p] = {u"byte が同じ書類": len(same), u"書類": len(now_by), u"違った書類": sorted(set(now_by) - set(same))}
    summ = summarize(res, ids67, ids30)
    moved = dict((name, {u"P26 → P27": s.pop(u"_moved_P26_P27"), u"P27 → P27E": s.pop(u"_moved_P27_P27E")}) for name, s in summ.items())
    head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    with io.open(os.path.abspath(__file__), "rb") as fh:
        script_sha = sha_bytes(fh.read())
    rec = {
        u"seal": u"audit-core/" + SEAL, u"step": u"P27 段 2 §5 ― 手元の 97 書類の有報の原文での後退の測定(N-1〜N-3)",
        u"HEAD の commit": head, u"この script の sha256": script_sha,
        u"engine の指紋": VD.engine_fingerprint(),
        u"比べた engine": {u"commit": BASELINE_COMMIT, u"取り出し方": u"git archive <commit> audit-core/adapters audit-core/core を TMPDIR に取り出し、同じ script を別 process で走らせた",
                        u"adapters/xbrl の file の sha256(commit の blob)": base_files},
        u"どの 97 か": u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした",
        u"評価用の AI の文・DB の応答": u"開いていない(この script は edinetdb-p27/ の下を読まない)。評価用 10 社の有報の原文 ZIP は 30 書類に含まれる(封 §5・§10-5)",
        u"cache の前後": {u"前": before, u"後": after, u"変化なし": before == after},
        u"N-1": n1, u"集計": summ, u"動いた行": moved,
        u"書類": [{u"docID": d, u"標本": u"新しい標本 30" if now_by[d][u"fresh"] else u"手元の 67", u"zip の sha256": now_by[d][u"zip の sha256"],
                  u"claims": len(now_by[d][u"profiles"]["P26"][u"rows"]),
                  u"4 state": dict((p, dict((s, sum(1 for row in now_by[d][u"profiles"][p][u"rows"] if row[1] == s)) for s in STATES)) for p in NOW_PROFILES),
                  u"出力の sha256(engine の欄を除く)": dict((p, now_by[d][u"profiles"][p][u"sha256"]) for p in NOW_PROFILES),
                  u"比べる側の engine の出力の sha256": dict((p, base_by[d][u"profiles"][p][u"sha256"]) for p in BASE_PROFILES),
                  u"規則ごとに当たった claim の数": now_by[d].get(u"規則ごと")}
                 for d in sorted(now_by)],
    }
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)


if __name__ == "__main__":
    main()
