# -*- coding: utf-8 -*-
u"""手元の 97 書類の有報の原文で、P28(= P27 + O。「その他」の主語の結び直し)が他を壊さないか・何行を決めるかの測定。
封 ``docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md`` §3-2(N-1〜N-8)・§5-2・§5-3。

    cd audit-core
    python3 measure/xbrl_p28_regress97_2026-11-02.py --out fixtures/xbrl/p28/regress97_2026-11-02.json --dossier-dir <repo の外> [--procs 4]
    python3 measure/xbrl_p28_regress97_2026-11-02.py --readings <repo の外の dir>      # 席の答え(seat1.json・seat2.json)から読みの記録を書く

**0 USD・通信なし・鍵は読まない・LLM の API は呼ばない。** 書類は手元の cache の ZIP だけ(``edinet/``・``edinet-fresh-2026-10-21/``。``edinet-prior-2026-11-02/`` は件数だけ数える。
読むだけで 1 file も足さない。件数と名前の一覧の sha256 を前後で記録し、変わっていれば記録を書かずに止める)。engine(``core/``・``adapters/``)は測る側から 1 行も変えない。
前例 ``measure/xbrl_p27_regress97_2026-10-27.py`` は 1 行も変えず、その関数(doc_lists・zip_path・names_sha・dump_no_engine・moved_rows・state_counts・direction)を importlib で読んで使う。
**評価用の AI の文・DB の応答は開かない**(``edinetdb-p27/`` の下を 1 file も読まない)。記録に span・value・recomputed・文は入れない(読みの束 dossier は repo の外に書く)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- profile は P22・P26・P27・P28。比べる engine は ``git archive c4b8221 audit-core/adapters audit-core/core``(封の commit c6cbfae と engine は同じ)を TMPDIR に取り出し、blob と byte 一致を確かめて別 process で走らせる。
  N-1 = P22・P26・P27 のそれぞれで、97 書類の出力(``sort_keys`` の JSON。``engine`` の欄を除く)の sha256 が比べる engine と一致する書類の数。
- 形が真の行 = provenance の欄 ``other_subject_2026_11_02`` が在る claim。決まった行 = 欄の 決まった が真。保留 = 候補 2 以上で決まらなかった行。
  候補 0 の行 = 形が真で候補 0(engine が GROUNDED にした行を含む。封 O-5 の字)。
- N-4 の向き = 「P27 → P28 で state か reason か pointers が違う行」の (前の state → 後の state)。許す向きは (VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND) → GROUNDED だけ。
  GROUNDED のまま pointer が替わる行 0 ・GROUNDED を離れる行 0・形が偽の行(provenance に欄が無い claim)で動いた行 0 も求める。
- N-6 の R1: 決まった行の「結んだ要素」が、P27 が指していた要素 E(P27 の pointers の 1 つ目。無ければ provenance の no_same_value の named)の計算リンクの近傍
  (``measure/xbrl_other_rule_2026-11-02.py`` の ``neighbourhood``。arcs は ``measure/xbrl_derivation_full_2026-11-02.py`` の ``parse_cal``)に在れば「R1 でも同じ fact」。
  決まった行は R0 の候補がちょうど 1 つなので R1 の候補は 0 か 1(同じ fact)。E が取れない行は「指せず」。**判定に使う割合の分母は決まった行の全部(指せず = 同じでない)**。
  E の取れた行だけを分母にした割合は参考として別に書く。
- 読み(§5-3): 決まった行を (docID, id) の順に並べ、``measure/SEED.json`` の種(``inject.verify_seed_sealed``)で ``random.Random("<seed>|P28_READ").sample`` で最大 30 行を引き、(docID, id) の順に並べ直す。
  束は ``--dossier-dir`` に dossier.json として書く(repo の外)。席の指示文は ``READER_PROMPT`` の字で固定。
  読みの割合の分母は引いた行の全部(判定不能・欠けた答え = 「合う」でない)。参考に判定不能が無い行だけの割合も書く。
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
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
ENGINE_ROOT = os.environ.get("P28_ENGINE_ROOT") or ROOT          # 比べる側(封の時点の engine の写し)を別の process で測るときだけ替える
sys.path.insert(0, os.path.join(ENGINE_ROOT, "core", "py"))
sys.path.insert(0, ENGINE_ROOT)

from adapters.xbrl import verify_document as VD   # noqa: E402
from adapters.xbrl import vocabulary as V         # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


D = load_module(os.path.join(HERE, "xbrl_p28_ai_prose_2026-11-02.py"), "p28_ai_prose_for_regress")   # prov_map・pointer_parts などの共通部品(同じ便の script)

SEAL_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md"
SEAL_COMMIT = "c6cbfae"
BASELINE_COMMIT = "c4b8221"
OUT_REL = "fixtures/xbrl/p28/regress97_2026-11-02.json"
READ_REL = "fixtures/xbrl/p28/readings_2026-11-02.json"
PRECEDENT_REL = "measure/xbrl_p27_regress97_2026-10-27.py"
FULL_REL = "measure/xbrl_derivation_full_2026-11-02.py"
OTHER_REL = "measure/xbrl_other_rule_2026-11-02.py"
SEED_REL = "measure/SEED.json"
CACHES = collections.OrderedDict([("edinet", os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")),
                                  ("edinet-fresh-2026-10-21", os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")),
                                  ("edinet-prior-2026-11-02", os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02"))])
NOW_PROFILES = ("P22", "P26", "P27", "P28")
BASE_PROFILES = ("P22", "P26", "P27")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
KEY = D.KEY
BOUNDS = collections.OrderedDict([("N-2", (40, 300)), ("N-3", (10, 120)), ("N-6", 85.0), ("N-7 合う", 90.0), ("N-7 違う項目", (0, 1)),
                                  ("K-3 違う項目", 1), ("K-3 合う", 85.0), ("K-4", 80.0)])
READ_N = 30
ANSWERS = ("合う", "違う項目", "判定不能")
READER_PROMPT = u"""あなたは有価証券報告書の数の点検の読み手です。次の「束」を読み、問いに答えてください。

束には、有価証券報告書の本文のある 1 文(文)、その文の中の 1 つの数(数)、機械がその数に結びつけた XBRL の要素の名前と日本語の標準ラベル(要素・ラベル)、
その要素の fact の値と期(値・期)、(参考)機械の別の仕組みが先に指していた要素(別の仕組みが指していた要素)が書いてあります。

問い: 「文のこの数は、この要素(ラベル)のこの期の値ですか。」

答えは次の 3 つのうち 1 つだけです。
  合う      … 文のこの数は、この要素のこの期の値を言っていると読める(文が「その他」の項目の金額を言っていて、この要素がその「その他」にあたる)。
  違う項目  … 文のこの数は、この要素とは別の項目の金額を言っていて、値がたまたま一致しただけに見える。
  判定不能  … 束だけでは決められない。

守ること:
  - 束に書いてあることだけで答える。外のファイル・ネットワーク・他の書類は見ない。特に ~/Desktop/sgogi-coach-handoff/ と ~/.cache/audit-core/edinetdb-p27/ は開かない。道具(engine)は動かさない。
  - 値が合っているかどうかではなく、「この数が指している項目が、この要素の項目か」を読む。
  - 理由は 1 文。
  - 答えは次の JSON を 1 つだけ返す: {"答え": "合う" | "違う項目" | "判定不能", "理由": "<1 文>"}
"""
READER_PROMPT_SHA256 = hashlib.sha256(READER_PROMPT.encode("utf-8")).hexdigest()


class Stop(SystemExit):
    pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def prec():
    return load_module(os.path.join(ROOT, PRECEDENT_REL), "p27_regress97_precedent")


# ---------------------------------------------------------------- 1 書類

_MODS = {}


def mods():
    if not _MODS:
        _MODS["full"] = load_module(os.path.join(ROOT, FULL_REL), "p28_full")
        _MODS["other"] = load_module(os.path.join(ROOT, OTHER_REL), "p28_other")
    return _MODS


def _claim_rows(out):
    return [(c["id"], c["state"], c["reason"], tuple(c["pointers"])) for c in out["claims"]]


def labels_of(zb, inst, local):
    u"""dossier 用: 要素の局所名の日本語ラベル(標準タクソノミ → 会社拡張の順。無ければ None)。"""
    from adapters.xbrl import instance as I
    import zipfile
    try:
        m = I.taxonomy_label_map(None)
        if local in m:
            return m[local]
    except Exception:
        pass
    try:
        z = zipfile.ZipFile(io.BytesIO(zb))
        for eid, label in I.labels_from_zip(z, inst["names"]).items():
            if eid.rsplit("_", 1)[-1] == local:
                return label
    except Exception:
        pass
    return None


def doc_job(args):
    u"""1 書類・渡された profile の列。出力の sha256(engine を除く)と claim の行、P28 では形が真の行の詳細を返す(span・value・recomputed・文は返さない。dossier 用の束は ``_dossier`` に別に持つ)。"""
    doc, fresh, expect_sha, profiles, zpath = args
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"fresh": fresh, u"zip の sha256": expect_sha, u"profiles": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        dumped = D.dump_no_engine(out).encode("utf-8")
        res[u"profiles"][p] = {u"sha256": sha_bytes(dumped), u"rows": _claim_rows(out), u"engine の欄を除いた JSON の bytes": len(dumped)}
    if "P28" in profiles:
        res[u"形が真の行"] = shape_details(zb, doc, zpath, res)
    return res


def shape_details(zb, doc, zpath, res):
    u"""P28 で provenance の欄が在る claim の詳細(R1 の判定・no_subject を含む)。決まった行には dossier 用の束を ``_dossier`` に添える。"""
    M = mods()
    arcs, _n = M["full"].parse_cal(zpath)
    prov27, prov28 = D.prov_map(zb, "P27"), D.prov_map(zb, "P28")
    r27 = dict((r[0], r) for r in res[u"profiles"]["P27"][u"rows"])
    r28 = dict((r[0], r) for r in res[u"profiles"]["P28"][u"rows"])
    shape = []
    for cid, pr in prov28.items():
        o = pr["other"]
        if o is None:
            continue
        a, b = r27[cid], r28[cid]
        pa, pb = D.pointer_parts(a[3]), D.pointer_parts(b[3])
        nsv = prov27[cid]["no_same_value"]
        e_src, e = (u"pointers", pa) if pa else ((u"no_same_value", D.pointer_parts([nsv["named"]])) if nsv and D.pointer_parts([nsv["named"]]) else (None, None))
        row = collections.OrderedDict()
        row[u"docID"] = doc
        row[u"id"] = cid
        row[u"前期"] = o[u"前期"]
        row[u"候補"] = o[u"候補"]
        row[u"決まった"] = o[u"決まった"]
        row[u"P27 の state"], row[u"P27 の reason"] = a[1], a[2]
        row[u"P28 の state"], row[u"P28 の reason"] = b[1], b[2]
        row[u"動いた"] = (a[1], a[2], a[3]) != (b[1], b[2], b[3])
        row[u"pointer だけ替わった"] = bool(row[u"動いた"] and a[1] == b[1] and a[2] == b[2] and a[3] != b[3])
        row[u"結んだ要素"] = D.local_name(pb[0]) if pb else None
        row[u"結んだ期"] = D.period_kind(pb[1]) if pb else None
        row[u"結んだ context"] = pb[1] if pb else None
        row[u"E の出どころ"] = e_src
        row[u"E"] = D.local_name(e[0]) if e else None
        if o[u"決まった"]:
            if e is None:
                row[u"R1"] = u"指せず"
            else:
                nb = M["other"].neighbourhood(e[0], arcs)
                row[u"R1"] = u"同じ" if pb[0] in nb else u"違う"
        else:
            row[u"R1"] = None
        row[u"主語なし(claim の subject が空)"] = prov28[cid]["subject"] is None
        row[u"P27 の reason が no_subject"] = a[2] == "no_subject"
        if o[u"決まった"]:
            row[u"_dossier"] = dossier_item(zb, cid, pa, nsv, pb)
        shape.append(row)
    return shape


def dossier_item(zb, cid, pa, nsv, pb):
    u"""読みの束 1 行(repo の外に書く)。文・数・要素・ラベル・fact の値と期・P27 の要素。"""
    from adapters.xbrl import extract as E
    from adapters.xbrl import instance as I
    from adapters.xbrl import recipes as R
    prof = V.PROFILES["P28"]
    inst = I.load_instance(zb)
    tbs = inst["textblocks"]
    mdna = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna]) if mdna else ""
    sentences = E.split_sentences(text, prof.paren_sentence)
    nums, _t = R.build_raw_claims(zb, prof)
    c = [x for x in nums if x["id"] == cid][0]
    s = sentences[c["sentence"]]
    a = c["pos"]
    b = [b2 for (a2, b2, _v, _u, _p) in R._numbers_of(prof, s) if a2 == a][0]
    f = [x for x in inst["facts"] if x["name"] == pb[0] and x["context"] == pb[1]][0]
    local = D.local_name(pb[0])
    p27_el = pa or (D.pointer_parts([nsv["named"]]) if nsv else None)
    return collections.OrderedDict([
        (u"文", s), (u"数", s[a:b]), (u"要素", local), (u"ラベル", labels_of(zb, inst, local)),
        (u"値", f["value"]), (u"期", D.period_kind(pb[1]) + u"(" + pb[1] + u")"),
        (u"別の仕組みが指していた要素", (D.local_name(p27_el[0]) + u"@" + p27_el[1]) if p27_el else None)])


def run_pool(fn, jobs, procs):
    if procs <= 1:
        return [fn(j) for j in jobs]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(procs) as pool:
        return list(pool.imap(fn, jobs, chunksize=1))


def make_jobs(profiles):
    P = prec()
    ids67, sha67, ids30, sha30 = P.doc_lists()
    jobs = [(d, False, sha67[d], tuple(profiles), P.zip_path(d, False)) for d in ids67] + [(d, True, sha30[d], tuple(profiles), P.zip_path(d, True)) for d in ids30]
    return jobs, ids67, ids30


# ---------------------------------------------------------------- 比べる engine

def baseline_dump(procs, work, jobs):
    base = os.path.join(work, "baseline_engine")
    os.makedirs(base)
    arc = subprocess.run(["git", "-C", REPO, "archive", BASELINE_COMMIT, "audit-core/adapters", "audit-core/core"], stdout=subprocess.PIPE, check=True)
    subprocess.run(["tar", "-x", "-C", base], input=arc.stdout, check=True)
    root = os.path.join(base, "audit-core")
    files = collections.OrderedDict()
    for rel in ["adapters/xbrl/%s" % f for f in sorted(os.listdir(os.path.join(root, "adapters", "xbrl"))) if f.endswith(".py")]:
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:audit-core/%s" % (BASELINE_COMMIT, rel)], stdout=subprocess.PIPE, check=True).stdout
        with io.open(os.path.join(root, rel), "rb") as fh:
            if fh.read() != blob:
                raise Stop(u"**取り出した写しが commit の blob と違う: %s。止める**" % rel)
        files[rel] = sha_bytes(blob)
    jobs_json = os.path.join(work, "baseline_jobs.json")
    out_json = os.path.join(work, "baseline_dump.json")
    with io.open(jobs_json, "w", encoding="utf-8") as fh:
        json.dump([list(j[:3]) + [list(BASE_PROFILES), j[4]] for j in jobs], fh)
    env = dict(os.environ, P28_ENGINE_ROOT=root)
    subprocess.run([sys.executable, os.path.abspath(__file__), "--dump-only", "--jobs", jobs_json, "--procs", str(procs), "--out", out_json], env=env, check=True)
    with io.open(out_json, encoding="utf-8") as fh:
        return json.load(fh), files


def dump_job(args):
    doc, fresh, expect_sha, profiles, zpath = args
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"profiles": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        res[u"profiles"][p] = {u"sha256": sha_bytes(D.dump_no_engine(out).encode("utf-8"))}
    return res


# ---------------------------------------------------------------- 集計

def summarize(res, P):
    by = dict((r[u"doc"], r) for r in res)
    out = collections.OrderedDict()
    shape = [row for r in res for row in r.get(u"形が真の行", [])]
    decided = [r for r in shape if r[u"決まった"]]
    moved = P.moved_rows(by, "P27", "P28")
    shape_keys = set((r[u"docID"], r[u"id"]) for r in shape)
    out[u"4 state"] = collections.OrderedDict((p, P.state_counts(by, p)) for p in NOW_PROFILES)
    out[u"claims"] = sum(len(r[u"profiles"]["P27"][u"rows"]) for r in res)
    out[u"形が真の行"] = len(shape)
    out[u"形が真の行で engine が P27 で GROUNDED の行"] = sum(1 for r in shape if r[u"P27 の state"] == "GROUNDED")
    out[u"決まって GROUNDED になった行"] = len(decided)
    out[u"候補 2 以上で保留の行"] = sum(1 for r in shape if r[u"候補"] is not None and r[u"候補"] >= 2 and not r[u"決まった"])
    out[u"候補 0 の行(engine が GROUNDED にした行を含む)"] = sum(1 for r in shape if r[u"候補"] == 0)
    out[u"候補の数の分布"] = collections.OrderedDict(sorted(collections.Counter(str(r[u"候補"]) for r in shape).items()))
    out[u"形が真の書類"] = len(set(r[u"docID"] for r in shape))
    out[u"決まった行のある書類"] = len(set(r[u"docID"] for r in decided))
    # N-4
    out[u"P27 → P28 で動いた行"] = len(moved)
    out[u"動いた行の向き"] = collections.OrderedDict(sorted(collections.Counter(P.direction(m) for m in moved).items()))
    allowed = {("VALUE_MISMATCH", "GROUNDED"), ("UNVERIFIABLE", "GROUNDED"), ("POINTER_NOT_FOUND", "GROUNDED")}
    out[u"許す向き以外の行"] = sum(1 for m in moved if (m[u"前"][u"state"], m[u"後"][u"state"]) not in allowed)
    out[u"GROUNDED のまま pointer が替わる行"] = sum(1 for m in moved if m[u"pointer だけ替わった"] and m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] == "GROUNDED")
    out[u"GROUNDED を離れる行"] = sum(1 for m in moved if m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] != "GROUNDED")
    out[u"形が偽の行で動いた行"] = sum(1 for m in moved if (m[u"docID"], m[u"id"]) not in shape_keys)
    out[u"動いた行のうち決まった行でない行"] = sum(1 for m in moved if (m[u"docID"], m[u"id"]) not in set((r[u"docID"], r[u"id"]) for r in decided))
    out[u"決まった行のうち動いていない行(P27 でも GROUNDED)"] = sum(1 for r in decided if not r[u"動いた"])
    # N-6
    out[u"N-6 決まった行の R1"] = collections.OrderedDict((k, sum(1 for r in decided if r[u"R1"] == k)) for k in (u"同じ", u"違う", u"指せず"))
    out[u"N-6 割合(分母 = 決まった行の全部。判定に使う)"] = pct(out[u"N-6 決まった行の R1"][u"同じ"], len(decided))
    ev = out[u"N-6 決まった行の R1"][u"同じ"] + out[u"N-6 決まった行の R1"][u"違う"]
    out[u"N-6 割合(参考。分母 = E の取れた行だけ)"] = pct(out[u"N-6 決まった行の R1"][u"同じ"], ev)
    out[u"N-6 E の出どころ(決まった行)"] = collections.OrderedDict(sorted(collections.Counter(str(r[u"E の出どころ"]) for r in decided).items()))
    # N-8 判定しない
    out[u"N-8 結んだ要素の分布(決まった行)"] = collections.OrderedDict(sorted(collections.Counter(r[u"結んだ要素"] for r in decided).items(), key=lambda kv: (-kv[1], kv[0])))
    out[u"N-8 決まった行の期"] = collections.OrderedDict(sorted(collections.Counter(r[u"結んだ期"] for r in decided).items()))
    out[u"N-8 決まった行の前の state"] = collections.OrderedDict((s, sum(1 for r in decided if r[u"P27 の state"] == s)) for s in STATES)
    out[u"N-8 no_subject: 決まった行のうち claim の subject が空"] = sum(1 for r in decided if r[u"主語なし(claim の subject が空)"])
    out[u"N-8 no_subject: 決まった行のうち P27 の reason が no_subject"] = sum(1 for r in decided if r[u"P27 の reason が no_subject"])
    out[u"N-8 no_subject: 形が真の行のうち claim の subject が空"] = sum(1 for r in shape if r[u"主語なし(claim の subject が空)"])
    out[u"N-8 no_subject: 動いた行のうち P27 の reason が no_subject"] = sum(1 for m in moved if m[u"前"][u"reason"] == "no_subject")
    out[u"N-8 書類ごとの決まった行の数(上位)"] = collections.OrderedDict(sorted(collections.Counter(r[u"docID"] for r in decided).items(), key=lambda kv: (-kv[1], kv[0]))[:10])
    return out, shape, decided, moved


def judge(T, n1, cache_same):
    J = collections.OrderedDict()
    J["N-1"] = all(n1[p][u"byte が同じ書類"] == n1[p][u"書類"] == 97 for p in BASE_PROFILES)
    J["N-2"] = BOUNDS["N-2"][0] <= T[u"形が真の行"] <= BOUNDS["N-2"][1]
    J["N-3"] = BOUNDS["N-3"][0] <= T[u"決まって GROUNDED になった行"] <= BOUNDS["N-3"][1]
    J["N-4"] = bool(T[u"許す向き以外の行"] == 0 and T[u"GROUNDED のまま pointer が替わる行"] == 0 and T[u"GROUNDED を離れる行"] == 0 and T[u"形が偽の行で動いた行"] == 0)
    J["N-5"] = T[u"候補 2 以上で保留の行"] <= T[u"決まって GROUNDED になった行"]
    J["N-6"] = T[u"N-6 割合(分母 = 決まった行の全部。判定に使う)"] is not None and T[u"N-6 割合(分母 = 決まった行の全部。判定に使う)"] >= BOUNDS["N-6"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out["N-7"] = u"読みの記録(readings_2026-11-02.json)で判定"
    out["N-8"] = u"判定しない"
    out[u"cache の前後が同じ"] = cache_same
    return out


def record_key_leaks(rec):
    text = json.dumps(rec, ensure_ascii=False)
    return [p for p in D.KEY_PATTERNS if re.search(p, text)]


def draw_reading_rows(decided):
    IJ = load_module(os.path.join(HERE, "inject.py"), "p28_inject")
    seed, meta = IJ.verify_seed_sealed(os.path.join(ROOT, SEED_REL))
    rows = sorted(decided, key=lambda r: (r[u"docID"], r[u"id"]))
    picked = rows if len(rows) <= READ_N else random.Random("%s|P28_READ" % seed).sample(rows, READ_N)
    picked = sorted(picked, key=lambda r: (r[u"docID"], r[u"id"]))
    return picked, meta


def write_dossier(dossier_dir, picked):
    os.makedirs(dossier_dir, exist_ok=True)
    items = [collections.OrderedDict([(u"key", u"%s:%s" % (r[u"docID"], r[u"id"])), (u"束", r[u"_dossier"])]) for r in picked]
    with io.open(os.path.join(dossier_dir, "dossier.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(collections.OrderedDict([(u"席の指示文", READER_PROMPT), (u"席の指示文の sha256", READER_PROMPT_SHA256), (u"行", items)]), ensure_ascii=False, indent=1) + u"\n")
    return len(items)


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


# ---------------------------------------------------------------- 読みの記録

def read_answers(path):
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    out = {}
    for x in data:
        ans = x.get(u"答え")
        if ans not in ANSWERS:
            raise Stop(u"答えが 3 値でない: %s %s" % (x.get(u"key"), ans))
        out[x[u"key"]] = ans
    return out


def readings_record(rdir, out_path):
    with io.open(os.path.join(rdir, "dossier.json"), encoding="utf-8") as fh:
        dossier = json.load(fh)
    if dossier[u"席の指示文の sha256"] != READER_PROMPT_SHA256:
        raise Stop(u"dossier の指示文の sha256 が script の READER_PROMPT と違う")
    keys = [x[u"key"] for x in dossier[u"行"]]
    s1, s2 = read_answers(os.path.join(rdir, "seat1.json")), read_answers(os.path.join(rdir, "seat2.json"))
    for name, s in (("seat1", s1), ("seat2", s2)):
        if sorted(s) != sorted(keys):
            raise Stop(u"%s の行が dossier の行と合わない(欠け %s・余り %s)" % (name, sorted(set(keys) - set(s)), sorted(set(s) - set(keys))))
    rows = [collections.OrderedDict([(u"docID", k.split(":")[0]), (u"id", k.split(":")[1]), (u"席 1", s1[k]), (u"席 2", s2[k])]) for k in keys]
    n = len(rows)
    both_ok = sum(1 for r in rows if r[u"席 1"] == r[u"席 2"] == u"合う")
    both_other = sum(1 for r in rows if r[u"席 1"] == r[u"席 2"] == u"違う項目")
    any_unk = sum(1 for r in rows if u"判定不能" in (r[u"席 1"], r[u"席 2"]))
    disagree = sum(1 for r in rows if r[u"席 1"] != r[u"席 2"])
    clear = n - any_unk
    T = collections.OrderedDict([(u"読んだ行", n), (u"2 席とも合う", both_ok), (u"2 席とも違う項目", both_other), (u"どちらかが判定不能", any_unk), (u"2 席の答えが違う行", disagree),
                                 (u"2 席とも合う割合(分母 = 読んだ行の全部。判定に使う)", pct(both_ok, n)),
                                 (u"2 席とも合う割合(参考。分母 = どちらも判定不能でない行)", pct(both_ok, clear)),
                                 (u"2 席の一致率(答えが同じ行 / 読んだ行)", pct(n - disagree, n)),
                                 (u"席 1 の答えの分布", collections.OrderedDict((a, sum(1 for r in rows if r[u"席 1"] == a)) for a in ANSWERS)),
                                 (u"席 2 の答えの分布", collections.OrderedDict((a, sum(1 for r in rows if r[u"席 2"] == a)) for a in ANSWERS))])
    J = collections.OrderedDict()
    J["N-7"] = bool(n and T[u"2 席とも合う割合(分母 = 読んだ行の全部。判定に使う)"] >= BOUNDS["N-7 合う"] and BOUNDS["N-7 違う項目"][0] <= both_other <= BOUNDS["N-7 違う項目"][1])
    J["K-3"] = bool(n and both_other <= BOUNDS["K-3 違う項目"] and T[u"2 席とも合う割合(分母 = 読んだ行の全部。判定に使う)"] >= BOUNDS["K-3 合う"])
    rec = collections.OrderedDict()
    rec[u"注意"] = u"決まった行から種で引いた行を 2 席(同じ model の subagent)が読んだ答えの記録。文・値・理由は入れない(束と理由は repo の外)。2 席の一致は独立した証拠に数えない。"
    rec[u"封"] = collections.OrderedDict([(u"file", SEAL_REL), (u"commit", SEAL_COMMIT)])
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"席の指示文の sha256"] = READER_PROMPT_SHA256
    rec[u"種の file"] = SEED_REL
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    rec[u"limits"] = [u"同じ model の 2 席の読み。独立した 2 つの証拠ではない(H-08・H-13)", u"決まった行の全部でなく、種で引いた最大 30 行"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    if os.path.exists(out_path):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"written: %s" % out_path)
    print(json.dumps(T, ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--dossier-dir", default=None)
    ap.add_argument("--readings", default=None, help="席の答え(seat1.json・seat2.json)と dossier.json の在る dir。読みの記録を書く")
    ap.add_argument("--readings-out", default=os.path.join(ROOT, READ_REL))
    ap.add_argument("--dump-only", action="store_true", help="(内部)比べる側の engine で出力の sha256 だけ書く")
    ap.add_argument("--jobs", default=None)
    a = ap.parse_args(argv)
    if a.dump_only:
        with io.open(a.jobs, encoding="utf-8") as fh:
            jobs = [tuple(j) for j in json.load(fh)]
        res = run_pool(dump_job, jobs, a.procs)
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        return
    if a.readings:
        readings_record(a.readings, a.readings_out)
        return
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る。測り直さない。止める**")
    if a.dossier_dir is None:
        raise Stop(u"--dossier-dir(repo の外)を指定する")
    if os.path.realpath(a.dossier_dir).startswith(os.path.realpath(REPO) + os.sep):
        raise Stop(u"dossier は repo の外に書く")
    P = prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in CACHES.items())
    jobs, ids67, ids30 = make_jobs(NOW_PROFILES)
    work = tempfile.mkdtemp(prefix="p28_regress97_", dir=os.environ.get("TMPDIR"))
    base, base_files = baseline_dump(a.procs, work, jobs)
    res = run_pool(doc_job, jobs, a.procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in CACHES.items())
    cache_same = names_before == names_after
    if not cache_same:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    base_by = dict((r[u"doc"], r) for r in base)
    now_by = dict((r[u"doc"], r) for r in res)
    n1 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d for d in now_by if now_by[d][u"profiles"][p][u"sha256"] == base_by[d][u"profiles"][p][u"sha256"]]
        n1[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(now_by)), (u"違った書類", sorted(set(now_by) - set(same)))])
    T, shape, decided, moved_sh = summarize(res, P)
    picked, seed_meta = draw_reading_rows(decided)
    n_dossier = write_dossier(a.dossier_dir, picked)
    moved = P.moved_rows(now_by, "P27", "P28")
    shape_by = dict(((r[u"docID"], r[u"id"]), r) for r in shape)
    moved_rows = []
    for m in moved:
        s = shape_by.get((m[u"docID"], m[u"id"]))
        moved_rows.append(collections.OrderedDict([
            (u"docID", m[u"docID"]), (u"id", m[u"id"]), (u"前の state", m[u"前"][u"state"]), (u"前の reason", m[u"前"][u"reason"]), (u"後の state", m[u"後"][u"state"]),
            (u"結んだ要素", s[u"結んだ要素"] if s else None), (u"結んだ期", s[u"結んだ期"] if s else None), (u"候補の数", s[u"候補"] if s else None),
            (u"R1", s[u"R1"] if s else None), (u"no_subject(claim の subject が空)", s[u"主語なし(claim の subject が空)"] if s else None),
            (u"P27 の reason が no_subject", m[u"前"][u"reason"] == "no_subject"), (u"形が真", s is not None)]))
    shape_rows = [collections.OrderedDict((k, v) for k, v in r.items() if not k.startswith("_")) for r in shape]
    docs = []
    for d in sorted(now_by):
        r = now_by[d]
        sh = [x for x in r.get(u"形が真の行", [])]
        docs.append(collections.OrderedDict([
            (u"docID", d), (u"標本", u"新しい標本 30" if r[u"fresh"] else u"手元の 67"), (u"zip の sha256", r[u"zip の sha256"]), (u"claims", len(r[u"profiles"]["P27"][u"rows"])),
            (u"4 state", collections.OrderedDict((p, collections.OrderedDict((s, sum(1 for row in r[u"profiles"][p][u"rows"] if row[1] == s)) for s in STATES)) for p in NOW_PROFILES)),
            (u"出力の sha256(engine の欄を除く)", collections.OrderedDict((p, r[u"profiles"][p][u"sha256"]) for p in NOW_PROFILES)),
            (u"比べる側の engine の出力の sha256", collections.OrderedDict((p, base_by[d][u"profiles"][p][u"sha256"]) for p in BASE_PROFILES)),
            (u"形が真", len(sh)), (u"決まった", sum(1 for x in sh if x[u"決まった"])),
            (u"保留", sum(1 for x in sh if x[u"候補"] is not None and x[u"候補"] >= 2 and not x[u"決まった"])), (u"候補 0", sum(1 for x in sh if x[u"候補"] == 0))]))
    rec = collections.OrderedDict()
    rec[u"seal"] = u"audit-core/" + SEAL_REL
    rec[u"step"] = u"P28 ― 手元の 97 書類の有報の原文での後退と決めた行の測定(N-1〜N-8)"
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"前例の script の sha256"] = sha256_file(os.path.join(ROOT, PRECEDENT_REL))
    rec[u"engine の指紋(この tree)"] = VD.engine_fingerprint()
    rec[u"比べた engine"] = collections.OrderedDict([(u"commit", BASELINE_COMMIT), (u"取り出し方", u"git archive <commit> audit-core/adapters audit-core/core を TMPDIR に取り出し、blob と byte 一致を確かめ、同じ script を別 process で --dump-only で走らせた"),
                                                  (u"adapters/xbrl の file の sha256(commit の blob)", base_files)])
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", names_before), (u"後", names_after), (u"変化なし", cache_same)])
    rec[u"N-1"] = n1
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T, n1, cache_same)
    rec[u"動いた行"] = moved_rows
    rec[u"形が真の行"] = shape_rows
    rec[u"読みの行の引き方"] = collections.OrderedDict([(u"種の file", SEED_REL), (u"種の確認", seed_meta if isinstance(seed_meta, dict) else str(seed_meta)),
                                                  (u"引き方", u"決まった行を (docID, id) の順に並べ random.Random('<seed>|P28_READ').sample で最大 %d 行 → (docID, id) の順" % READ_N),
                                                  (u"決まった行", len(decided)), (u"引いた行", n_dossier), (u"席の指示文の sha256", READER_PROMPT_SHA256),
                                                  (u"引いた行(docID, id)", [[r[u"docID"], r[u"id"]] for r in picked])])
    rec[u"書類"] = docs
    rec[u"limits"] = [u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)", u"札が無いので決まった行の正しさは R1 の近傍と読み(同じ model の 2 席)でしか見られない",
                     u"R1 の近傍は E(P27 が指していた要素)が取れた行だけで比べられる。取れない行は「指せず」", u"engine の変更は本便の挿入だけ。既定は P27 のまま"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    for k in (u"4 state", u"形が真の行", u"決まって GROUNDED になった行", u"候補 2 以上で保留の行", u"候補 0 の行(engine が GROUNDED にした行を含む)", u"動いた行の向き", u"許す向き以外の行",
              u"形が偽の行で動いた行", u"N-6 決まった行の R1", u"N-6 割合(分母 = 決まった行の全部。判定に使う)", u"N-6 割合(参考。分母 = E の取れた行だけ)",
              u"N-8 no_subject: 決まった行のうち claim の subject が空", u"N-8 no_subject: 決まった行のうち P27 の reason が no_subject"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(u"N-1", json.dumps(dict((p, (n1[p][u"byte が同じ書類"], n1[p][u"書類"])) for p in BASE_PROFILES)))
    print(u"dossier: %d 行 -> %s" % (n_dossier, os.path.join(a.dossier_dir, "dossier.json")))


if __name__ == "__main__":
    main()
