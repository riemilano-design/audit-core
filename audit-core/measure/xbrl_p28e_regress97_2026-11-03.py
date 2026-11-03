# -*- coding: utf-8 -*-
u"""手元の 97 書類の有報の原文で、P28E(= P27E + O)が他を壊さないか・何行が動くかの測定。封 ``docs/XBRL_P28E_SEAL_2026-11-03.md`` §3-2(E-5・E-6)・§5。

    cd audit-core
    python3 measure/xbrl_p28e_regress97_2026-11-03.py [--out fixtures/xbrl/p28e/regress97_2026-11-03.json] [--procs 4]

**0 USD・通信なし・鍵は読まない・LLM の API は呼ばない。** 書類は手元の cache の ZIP だけ(``edinet/``・``edinet-fresh-2026-10-21/``。``edinet-prior-2026-11-02/`` は件数だけ数える。
読むだけで 1 file も足さない。件数と名前の一覧の sha256 を前後で記録し、変わっていれば記録を書かずに止める)。engine(``core/``・``adapters/``)は測る側から 1 行も変えない。
前の便の ``measure/xbrl_p28_regress97_2026-11-02.py`` を importlib で読み、その関数(make_jobs・run_pool・baseline_dump・dump_job・prec)を使う(写さない・編集しない。
``BASELINE_COMMIT`` と ``BASE_PROFILES`` の 2 つの定数だけ、この process の中で差し替える)。**評価用の AI の文・DB の応答は開かない**(``edinetdb-p27/`` の下を 1 file も読まない)。
記録に span・value・recomputed・文は入れない(docID は入る。``LATER_NAMING_FILES`` に宣言)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- profile は P22・P26・P27・P27E・P28・P28E。比べる engine は ``git archive a5d18e6 audit-core/adapters audit-core/core``(P28E を登録する前の engine)を TMPDIR に取り出し、
  blob と byte 一致を確かめて別 process で P22・P26・P27・P27E・P28 を走らせる(P28E はこの engine に無い)。E-5 = 5 profile のそれぞれで、97 書類の出力(``sort_keys`` の JSON。
  ``engine`` の欄を除く)の sha256 が比べる engine と一致する書類の数。
- E-6 の動いた行 = P27E と P28E で state か reason か pointers が違う行。「P28 の記録と同じ docID・id」は ``fixtures/xbrl/p28/regress97_2026-11-02.json`` の 動いた行 と比べる。
  他の向き = UNVERIFIABLE → GROUNDED 以外の向きの行(向きは P28 の記録の動いた行の 前の state → 後の state)。GROUNDED を離れる行 = P27E で GROUNDED で P28E で違う行。
- 形が真の行 = P28E の provenance の欄 ``other_subject_2026_11_02`` が在る claim。決まった行 = 欄の 決まった が真。保留 = 候補 2 以上で決まらなかった行。候補 0 = 形が真で候補 0。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R97 = load_module(os.path.join(HERE, "xbrl_p28_regress97_2026-11-02.py"), "p28_regress97_for_p28e")   # make_jobs・run_pool・baseline_dump・dump_job・prec
D = R97.D
VD = R97.VD

SEAL_REL = "docs/XBRL_P28E_SEAL_2026-11-03.md"
SEAL_COMMIT = "7bfad77"
BASELINE_COMMIT = "a5d18e6"
OUT_REL = "fixtures/xbrl/p28e/regress97_2026-11-03.json"
P28_RECORD_REL = "fixtures/xbrl/p28/regress97_2026-11-02.json"
NOW_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E")
BASE_PROFILES = ("P22", "P26", "P27", "P27E", "P28")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
KEY = D.KEY
EXPECT_DIRECTION = "UNVERIFIABLE → GROUNDED"
R97.BASELINE_COMMIT = BASELINE_COMMIT      # 前の便の baseline_dump が読む定数(この process の中だけ)
R97.BASE_PROFILES = BASE_PROFILES


def doc_job(args):
    u"""1 書類・渡された profile の列。出力の sha256(engine を除く)と claim の行を返す。P28E では provenance の形が真の行も返す(span・value・文は返さない)。"""
    doc, fresh, expect_sha, profiles, zpath = args
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if R97.sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"fresh": fresh, u"zip の sha256": expect_sha, u"profiles": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        dumped = D.dump_no_engine(out).encode("utf-8")
        res[u"profiles"][p] = {u"sha256": R97.sha_bytes(dumped), u"rows": R97._claim_rows(out), u"engine の欄を除いた JSON の bytes": len(dumped)}
    prov = D.prov_map(zb, "P28E")
    prov27e = D.prov_map(zb, "P27E")
    r27e = dict((r[0], r) for r in res[u"profiles"]["P27E"][u"rows"])
    r28e = dict((r[0], r) for r in res[u"profiles"]["P28E"][u"rows"])
    shape = []
    for cid, pr in prov.items():
        o = pr["other"]
        if o is None:
            continue
        a, b = r27e[cid], r28e[cid]
        pb = D.pointer_parts(b[3])
        row = collections.OrderedDict()
        row[u"docID"] = doc
        row[u"id"] = cid
        row[u"前期"] = o[u"前期"]
        row[u"候補"] = o[u"候補"]
        row[u"決まった"] = o[u"決まった"]
        row[u"P27E の state"], row[u"P27E の reason"] = a[1], a[2]
        row[u"P28E の state"], row[u"P28E の reason"] = b[1], b[2]
        row[u"動いた"] = (a[1], a[2], a[3]) != (b[1], b[2], b[3])
        row[u"結んだ要素"] = D.local_name(pb[0]) if pb else None
        row[u"結んだ期"] = D.period_kind(pb[1]) if pb else None
        row[u"主語なし(claim の subject が空)"] = pr["subject"] is None
        row[u"P27E の reason が no_subject"] = a[2] == "no_subject"
        shape.append(row)
    res[u"形が真の行"] = shape
    return res


def summarize(res, P, p28_moved):
    by = dict((r[u"doc"], r) for r in res)
    out = collections.OrderedDict()
    shape = [row for r in res for row in r[u"形が真の行"]]
    decided = [r for r in shape if r[u"決まった"]]
    moved = P.moved_rows(by, "P27E", "P28E")
    shape_keys = set((r[u"docID"], r[u"id"]) for r in shape)
    out[u"4 state"] = collections.OrderedDict((p, P.state_counts(by, p)) for p in NOW_PROFILES)
    out[u"claims"] = sum(len(r[u"profiles"]["P27E"][u"rows"]) for r in res)
    out[u"形が真の行"] = len(shape)
    out[u"形が真の書類"] = len(set(r[u"docID"] for r in shape))
    out[u"形が真の行で engine が P27E で GROUNDED の行"] = sum(1 for r in shape if r[u"P27E の state"] == "GROUNDED")
    out[u"決まって GROUNDED になった行"] = len(decided)
    out[u"候補 2 以上で保留の行"] = sum(1 for r in shape if r[u"候補"] is not None and r[u"候補"] >= 2 and not r[u"決まった"])
    out[u"候補 0 の行(engine が GROUNDED にした行を含む)"] = sum(1 for r in shape if r[u"候補"] == 0)
    out[u"候補の数の分布"] = collections.OrderedDict(sorted(collections.Counter(str(r[u"候補"]) for r in shape).items()))
    out[u"P27E → P28E で動いた行"] = len(moved)
    out[u"動いた行の向き"] = collections.OrderedDict(sorted(collections.Counter(P.direction(m) for m in moved).items()))
    out[u"動いた行の (docID, id)"] = [[m[u"docID"], m[u"id"]] for m in moved]
    out[u"動いた行のうち UNVERIFIABLE → GROUNDED 以外の向きの行(他の向き)"] = sum(1 for m in moved if P.direction(m) != EXPECT_DIRECTION)
    out[u"GROUNDED を離れる行(P27E で GROUNDED・P28E で違う)"] = sum(1 for m in moved if m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] != "GROUNDED")
    out[u"GROUNDED のまま pointer が替わる行"] = sum(1 for m in moved if m[u"pointer だけ替わった"] and m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] == "GROUNDED")
    out[u"形が偽の行で動いた行"] = sum(1 for m in moved if (m[u"docID"], m[u"id"]) not in shape_keys)
    out[u"動いた行のうち決まった行でない行"] = sum(1 for m in moved if (m[u"docID"], m[u"id"]) not in set((r[u"docID"], r[u"id"]) for r in decided))
    out[u"P28 の記録(regress97_2026-11-02.json)の動いた行の (docID, id)"] = [[m[u"docID"], m[u"id"]] for m in p28_moved]
    out[u"P28 の記録の動いた行の向き"] = collections.OrderedDict(sorted(collections.Counter(u"%s → %s" % (m[u"前の state"], m[u"後の state"]) for m in p28_moved).items()))
    out[u"動いた行が P28 の記録と同じ (docID, id)"] = sorted([m[u"docID"], m[u"id"]] for m in moved) == sorted([m[u"docID"], m[u"id"]] for m in p28_moved)
    out[u"P28E と P28 で出力の sha256 が同じ書類(参考。P28E は B を持つので P28 と違いうる)"] = sum(1 for r in res if r[u"profiles"]["P28E"][u"sha256"] == r[u"profiles"]["P28"][u"sha256"])
    out[u"P28E と P27E で出力の sha256 が違う書類"] = sum(1 for r in res if r[u"profiles"]["P28E"][u"sha256"] != r[u"profiles"]["P27E"][u"sha256"])
    out[u"決まった行の結んだ要素"] = collections.OrderedDict(sorted(collections.Counter(r[u"結んだ要素"] for r in decided).items()))
    out[u"決まった行のうち claim の subject が空"] = sum(1 for r in decided if r[u"主語なし(claim の subject が空)"])
    out[u"決まった行のうち P27E の reason が no_subject"] = sum(1 for r in decided if r[u"P27E の reason が no_subject"])
    return out, shape, decided, moved


def judge(T, n5, cache_same):
    J = collections.OrderedDict()
    J["E-5"] = all(n5[p][u"byte が同じ書類"] == n5[p][u"書類"] == 97 for p in BASE_PROFILES)
    J["E-6"] = bool(T[u"P27E → P28E で動いた行"] == 1 and T[u"動いた行が P28 の記録と同じ (docID, id)"] and T[u"動いた行の向き"] == {EXPECT_DIRECTION: 1}
                    and T[u"動いた行のうち UNVERIFIABLE → GROUNDED 以外の向きの行(他の向き)"] == 0 and T[u"GROUNDED を離れる行(P27E で GROUNDED・P28E で違う)"] == 0)
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"cache の前後が同じ"] = cache_same
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise R97.Stop(u"**出力が既に在る。測り直さない。止める**")
    P = R97.prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    jobs, ids67, ids30 = R97.make_jobs(NOW_PROFILES)
    work = tempfile.mkdtemp(prefix="p28e_regress97_", dir=os.environ.get("TMPDIR"))
    base, base_files = R97.baseline_dump(a.procs, work, jobs)
    res = R97.run_pool(doc_job, jobs, a.procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    cache_same = names_before == names_after
    if not cache_same:
        raise R97.Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    base_by = dict((r[u"doc"], r) for r in base)
    now_by = dict((r[u"doc"], r) for r in res)
    n5 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d for d in now_by if now_by[d][u"profiles"][p][u"sha256"] == base_by[d][u"profiles"][p][u"sha256"]]
        n5[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(now_by)), (u"違った書類", sorted(set(now_by) - set(same)))])
    p28_rec = D.jload(os.path.join(ROOT, P28_RECORD_REL))
    T, shape, decided, moved = summarize(res, P, p28_rec[u"動いた行"])
    moved_rows = []
    shape_by = dict(((r[u"docID"], r[u"id"]), r) for r in shape)
    for m in moved:
        s = shape_by.get((m[u"docID"], m[u"id"]))
        moved_rows.append(collections.OrderedDict([
            (u"docID", m[u"docID"]), (u"id", m[u"id"]), (u"前の state", m[u"前"][u"state"]), (u"前の reason", m[u"前"][u"reason"]), (u"後の state", m[u"後"][u"state"]),
            (u"結んだ要素", s[u"結んだ要素"] if s else None), (u"結んだ期", s[u"結んだ期"] if s else None), (u"候補の数", s[u"候補"] if s else None),
            (u"no_subject(claim の subject が空)", s[u"主語なし(claim の subject が空)"] if s else None), (u"形が真", s is not None)]))
    docs = []
    for d in sorted(now_by):
        r = now_by[d]
        sh = r[u"形が真の行"]
        docs.append(collections.OrderedDict([
            (u"docID", d), (u"標本", u"新しい標本 30" if r[u"fresh"] else u"手元の 67"), (u"zip の sha256", r[u"zip の sha256"]), (u"claims", len(r[u"profiles"]["P27E"][u"rows"])),
            (u"4 state", collections.OrderedDict((p, collections.OrderedDict((s, sum(1 for row in r[u"profiles"][p][u"rows"] if row[1] == s)) for s in STATES)) for p in NOW_PROFILES)),
            (u"出力の sha256(engine の欄を除く)", collections.OrderedDict((p, r[u"profiles"][p][u"sha256"]) for p in NOW_PROFILES)),
            (u"比べる側の engine の出力の sha256", collections.OrderedDict((p, base_by[d][u"profiles"][p][u"sha256"]) for p in BASE_PROFILES)),
            (u"形が真", len(sh)), (u"決まった", sum(1 for x in sh if x[u"決まった"])),
            (u"保留", sum(1 for x in sh if x[u"候補"] is not None and x[u"候補"] >= 2 and not x[u"決まった"])), (u"候補 0", sum(1 for x in sh if x[u"候補"] == 0))]))
    rec = collections.OrderedDict()
    rec[u"seal"] = u"audit-core/" + SEAL_REL
    rec[u"step"] = u"P28E ― 手元の 97 書類の有報の原文での後退と動いた行の測定(E-5・E-6)"
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"HEAD の commit"] = D.git_head()
    rec[u"この script の sha256"] = D.sha256_file(os.path.abspath(__file__))
    rec[u"前の便の script の sha256"] = D.sha256_file(os.path.join(HERE, "xbrl_p28_regress97_2026-11-02.py"))
    rec[u"engine の指紋(この tree)"] = VD.engine_fingerprint()
    rec[u"比べた engine"] = collections.OrderedDict([(u"commit", BASELINE_COMMIT), (u"取り出し方", u"git archive <commit> audit-core/adapters audit-core/core を TMPDIR に取り出し、blob と byte 一致を確かめ、前の便の script を別 process で --dump-only で走らせた"),
                                                  (u"profile", list(BASE_PROFILES)), (u"adapters/xbrl の file の sha256(commit の blob)", base_files)])
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", names_before), (u"後", names_after), (u"変化なし", cache_same)])
    rec[u"E-5"] = n5
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T, n5, cache_same)
    rec[u"動いた行"] = moved_rows
    rec[u"形が真の行"] = shape
    rec[u"書類"] = docs
    rec[u"limits"] = [u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)", u"札が無いので動いた行の正しさは見ていない(E-6 は「壊さない」の確認)", u"engine の変更は本便の vocabulary.py への挿入だけ。既定は P27 のまま"]
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise R97.Stop(u"記録に鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    for k in (u"4 state", u"形が真の行", u"決まって GROUNDED になった行", u"候補 2 以上で保留の行", u"候補 0 の行(engine が GROUNDED にした行を含む)", u"P27E → P28E で動いた行", u"動いた行の向き",
              u"動いた行の (docID, id)", u"動いた行が P28 の記録と同じ (docID, id)", u"GROUNDED を離れる行(P27E で GROUNDED・P28E で違う)", u"形が偽の行で動いた行"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(u"E-5", json.dumps(dict((p, (n5[p][u"byte が同じ書類"], n5[p][u"書類"])) for p in BASE_PROFILES)))


if __name__ == "__main__":
    main()
