# -*- coding: utf-8 -*-
u"""手元の 97 書類の有報の原文で、数の読み取り N(P29 = P28 + N・P29E = P28E + N)が他を壊さないか・何行が動くかの測定。封 ``docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md`` §3(C-2・C-3・C-4・C-13)・§5-2。

    cd audit-core
    python3 measure/xbrl_numfix_regress97_2026-11-04.py [--out fixtures/xbrl/numfix/regress97_2026-11-04.json] [--procs 4] [--only <docID>]

**0 USD・通信なし・鍵は読まない・LLM の API は呼ばない。** 書類は手元の cache の ZIP だけ(``edinet/``・``edinet-fresh-2026-10-21/``。``edinet-prior-2026-11-02/`` は件数だけ数える。
読むだけで 1 file も足さない。件数と名前の一覧の sha256 を前後で記録し、変わっていれば記録を書かずに止める)。engine(``core/``・``adapters/``)は測る側から 1 行も変えない。
前の便の ``measure/xbrl_p28_regress97_2026-11-02.py``(make_jobs・run_pool)と ``measure/xbrl_p27_regress97_2026-10-27.py``(moved 系の考え方)を importlib で読んで使う(写さない・編集しない)。
**評価用の AI の文・DB の応答は開かない**(``edinetdb-p27/`` の下を 1 file も読まない)。記録に span・value・recomputed・文は入れない(docID は入る。``LATER_NAMING_FILES`` に宣言)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- profile は P22・P26・P27・P27E・P28・P28E・P29・P29E。C-2 の「HEAD の engine の出力」は **この tree の engine** で取り、前の便の記録 ``fixtures/xbrl/p28e/regress97_2026-11-03.json`` の
  各書類の ``出力の sha256(engine の欄を除く)``(P22〜P28E の 6 つ)と書類ごとに比べる(比べる側の engine を別に取り出さない。前の便が測った値をそのまま基準にする)。
  出力の sha256 は ``sort_keys`` の JSON(``engine`` の欄を除く)。
- 動いた既存の行(C-3)= profile a と b の両方に在る数・文の claim のうち (state, reason, pointers) が違う行。claim の対応は **(種類, 文の番号, 文の中の位置, 同じ鍵の中の順)**
  (id は P29 で新しい数の claim が前に入ると替わるので使わない。claim の数が同じ書類も同じ鍵で対応を付ける)。
  増えた claim(C-4)= b にあって a に鍵が無い行(新しい行)。P29E 対 P28E と P29 対 P28 の両方を書く。判定の C-3・C-4 は P29E 対 P28E と P29 対 P28 の両方。
- C-13 の「直す試験 file の数」= 封の commit から engine の commit(封の後に engine の 3 file を最初に触った commit のうち最後のもの)までの ``git diff --name-status`` で ``tests/`` の下の
  変更のうち状態が M(既存の file を直した)の数。A(新しい file)は別に書く。engine の変更が 3 file だけ・削除 0 かもここで数える。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R97 = load_module(os.path.join(HERE, "xbrl_p28_regress97_2026-11-02.py"), "p28_regress97_for_numfix")   # make_jobs・run_pool・prec・Stop
D = R97.D
VD = R97.VD
from adapters.xbrl import recipes as R    # noqa: E402

SEAL_REL = "docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT = "48e7078"
OUT_REL = "fixtures/xbrl/numfix/regress97_2026-11-04.json"
PREV_RECORD_REL = "fixtures/xbrl/p28e/regress97_2026-11-03.json"
NOW_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E")
BASE_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E")
PAIRS = (("P29 対 P28", "P28", "P29"), ("P29E 対 P28E", "P28E", "P29E"))
KEYED = ("P28", "P29", "P28E", "P29E")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py")


def keyed_rows(zb, pname):
    u"""{(種類, 文の番号, 位置, 順): (state, reason, pointers)}。種類 = num / text(raw の並び: 数の claim → 文の claim)。"""
    prof = R97.V.PROFILES[pname]
    out = VD.verify_document(zb, pname, None)
    nums, texts = R.build_raw_claims(zb, prof)
    raws = [("num", r) for r in nums] + [("text", r) for r in texts]
    cl = out["claims"]
    if len(cl) != len(raws) or any(c["id"] != r["id"] for c, (_k, r) in zip(cl, raws)):
        raise R97.Stop(u"**検証の出力と raw claim の並びが合わない。止める**")
    seen = collections.Counter()
    rows = collections.OrderedDict()
    for c, (kind, r) in zip(cl, raws):
        base = (kind, r["sentence"], r["pos"])
        key = base + (seen[base],)
        seen[base] += 1
        rows[key] = (c["state"], c["reason"], tuple(c["pointers"]))
    return rows


def doc_job(args):
    u"""1 書類。8 profile の出力の sha256(engine を除く)と claim の行、P28・P29・P28E・P29E は位置の鍵つきの行。span・value・文は返さない。"""
    doc, fresh, expect_sha, profiles, zpath = args
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if R97.sha_bytes(zb) != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    res = {u"doc": doc, u"fresh": fresh, u"zip の sha256": expect_sha, u"profiles": {}, u"keyed": {}}
    for p in profiles:
        out = VD.verify_document(zb, p, None)
        dumped = D.dump_no_engine(out).encode("utf-8")
        res[u"profiles"][p] = {u"sha256": R97.sha_bytes(dumped), u"rows": R97._claim_rows(out)}
    for p in KEYED:
        res[u"keyed"][p] = keyed_rows(zb, p)
    return res


def pair_moves(res, a, b):
    u"""profile a → b。(動いた既存の行の列, 増えた行の列, 消えた行の列)。行 = (種類, 文の番号, 位置, 順)。"""
    ka, kb = res[u"keyed"][a], res[u"keyed"][b]
    moved = [k for k in kb if k in ka and ka[k] != kb[k]]
    added = [k for k in kb if k not in ka]
    gone = [k for k in ka if k not in kb]
    return moved, added, gone


def git(*args):
    r = subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise R97.Stop(u"**git が失敗: %s。止める**" % u" ".join(args[:2]))
    return r.stdout.decode("utf-8", "replace").strip()


def engine_commits():
    u"""(封の commit, engine の commit, numstat の行, tests の name-status の行)。engine の commit = 封の後に engine の 3 file を最初に触った commit のうち、子孫にあたる最後のもの。"""
    seal = [c for c in git("log", "--diff-filter=A", "--format=%H", "--", PREFIX + SEAL_REL).split() if c]
    if len(seal) != 1 or not seal[0].startswith(SEAL_COMMIT):
        raise R97.Stop(u"**封の commit が 1 つに決まらないか %s でない。止める**" % SEAL_COMMIT)
    seal = seal[0]
    firsts = []
    for rel in ENGINE_FILES:
        lst = [c for c in git("log", "--format=%H", seal + "..HEAD", "--", PREFIX + rel).split() if c]
        if not lst:
            raise R97.Stop(u"**封の後に engine の file を触った commit が無い: %s。止める**" % rel)
        firsts.append(lst[-1])
    e = firsts[0]
    for c in firsts[1:]:
        if subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor", e, c]).returncode == 0:
            e = c
    num = [x for x in git("diff", "--numstat", seal, e, "--", PREFIX + "adapters", PREFIX + "core").splitlines() if x]
    tests = [x for x in git("diff", "--name-status", seal, e, "--", PREFIX + "tests").splitlines() if x]
    return seal, e, num, tests


def engine_link():
    seal, e, num, tests = engine_commits()
    status = collections.Counter(t.split("\t")[0][0] for t in tests)
    ins = dict((x.split("\t")[2], int(x.split("\t")[0])) for x in num)
    dele = dict((x.split("\t")[2], int(x.split("\t")[1])) for x in num)
    return collections.OrderedDict([
        (u"封の commit", seal), (u"engine の commit", e),
        (u"engine の変更 file", sorted(p[len(PREFIX):] for p in ins)), (u"engine の挿入の行数", sum(ins.values())), (u"engine の削除の行数", sum(dele.values())),
        (u"直した file(M)", status.get("M", 0)), (u"新しい file(A)", status.get("A", 0)), (u"消した file(D)", status.get("D", 0)),
        (u"tests の変更 file", len(tests))])


def summarize_docs(docs):
    u"""``書類`` の行(記録に書く形)から集計を作る。門が記録の ``書類`` から作り直して照らすのにも使う(集計の正本はこの関数)。"""
    out = collections.OrderedDict()
    out[u"4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, sum(d[u"4 state"][p][s] for d in docs)) for s in STATES)) for p in NOW_PROFILES)
    out[u"claims"] = collections.OrderedDict((p, sum(d[u"claims"][p] for d in docs)) for p in NOW_PROFILES)
    c2 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d[u"docID"] for d in docs if d[u"出力の sha256(engine の欄を除く)"][p] == d[u"前の便の記録の sha256"][p]]
        c2[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(docs)),
                                         (u"違った書類", sorted(set(d[u"docID"] for d in docs) - set(same)))])
    out[u"C-2 旗が偽の profile の byte 一致"] = c2
    out[u"C-3 動いた既存の行"] = collections.OrderedDict((n, sum(len(d[u"動いた行と増えた行"][n][u"動いた既存の行"]) for d in docs)) for n, _a, _b in PAIRS)
    out[u"C-4 増えた claim"] = collections.OrderedDict((b, sum(d[u"動いた行と増えた行"][n][u"増えた行"] for d in docs)) for n, _a, b in PAIRS)
    out[u"消えた行(a にあって b に鍵が無い行)"] = collections.OrderedDict((n, sum(d[u"動いた行と増えた行"][n][u"消えた行"] for d in docs)) for n, _a, _b in PAIRS)
    out[u"増えた claim のある書類"] = collections.OrderedDict((b, sum(1 for d in docs if d[u"動いた行と増えた行"][n][u"増えた行"])) for n, _a, b in PAIRS)
    out[u"claim の数の差(総数)"] = collections.OrderedDict((b, out[u"claims"][b] - out[u"claims"][a]) for _n, a, b in PAIRS)
    return out


def doc_rows(res, prev_by):
    docs = []
    for r in sorted(res, key=lambda x: x[u"doc"]):
        d = r[u"doc"]
        moves = collections.OrderedDict()
        for name, a, b in PAIRS:
            mv, add, gone = pair_moves(r, a, b)
            ka, kb = r[u"keyed"][a], r[u"keyed"][b]
            moves[name] = collections.OrderedDict([
                (u"動いた既存の行", [[k[0], k[1], k[2], k[3], ka[k][0], kb[k][0], ka[k][1], kb[k][1], ka[k][2] != kb[k][2]] for k in mv]),
                (u"増えた行", len(add)), (u"増えた行の state", collections.OrderedDict((s, sum(1 for k in add if kb[k][0] == s)) for s in STATES)),
                (u"消えた行", len(gone))])
        docs.append(collections.OrderedDict([
            (u"docID", d), (u"標本", u"新しい標本 30" if r[u"fresh"] else u"手元の 67"), (u"zip の sha256", r[u"zip の sha256"]),
            (u"claims", collections.OrderedDict((p, len(r[u"profiles"][p][u"rows"])) for p in NOW_PROFILES)),
            (u"4 state", collections.OrderedDict((p, collections.OrderedDict((s, sum(1 for row in r[u"profiles"][p][u"rows"] if row[1] == s)) for s in STATES)) for p in NOW_PROFILES)),
            (u"出力の sha256(engine の欄を除く)", collections.OrderedDict((p, r[u"profiles"][p][u"sha256"]) for p in NOW_PROFILES)),
            (u"前の便の記録の sha256", collections.OrderedDict((p, prev_by[d][u"出力の sha256(engine の欄を除く)"][p]) for p in BASE_PROFILES)),
            (u"動いた行と増えた行", moves)]))
    return docs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--only", default=None, help="この docID の 1 書類だけ(本番の記録を作らない確認用には --out を替える)")
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise R97.Stop(u"**出力が既に在る。測り直さない。止める**")
    P = R97.prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    jobs, ids67, ids30 = R97.make_jobs(NOW_PROFILES)
    prev = D.jload(os.path.join(ROOT, PREV_RECORD_REL))
    prev_by = dict((r["docID"], r) for r in prev[u"書類"])
    if sorted(prev_by) != sorted(ids67 + ids30):
        raise R97.Stop(u"**前の便の記録の書類が 97 書類の一覧と合わない。止める**")
    if a.only is not None:
        jobs = [j for j in jobs if j[0] == a.only]
        if not jobs:
            raise R97.Stop(u"**--only の docID が 97 書類に無い。止める**")
    res = R97.run_pool(doc_job, jobs, a.procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    cache_same = names_before == names_after
    if not cache_same:
        raise R97.Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    docs = doc_rows(res, prev_by)
    T = summarize_docs(docs)
    link = engine_link()
    T[u"C-13 engine の留めの連動で直す試験 file"] = collections.OrderedDict(link)
    rec = collections.OrderedDict()
    rec[u"seal"] = u"audit-core/" + SEAL_REL
    rec[u"step"] = u"数の読み取り N ― 手元の 97 書類の有報の原文での後退と動いた行の測定(C-2・C-3・C-4・C-13)"
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"HEAD の commit"] = D.git_head()
    rec[u"この script の sha256"] = D.sha256_file(os.path.abspath(__file__))
    rec[u"前の便の script の sha256"] = D.sha256_file(os.path.join(HERE, "xbrl_p28_regress97_2026-11-02.py"))
    rec[u"前の便の記録の sha256"] = D.sha256_file(os.path.join(ROOT, PREV_RECORD_REL))
    rec[u"engine の指紋(この tree)"] = VD.engine_fingerprint()
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"範囲"] = u"全 97 書類" if a.only is None else u"**--only の 1 書類だけ(本番の記録ではない)**"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", names_before), (u"後", names_after), (u"変化なし", cache_same)])
    rec[u"集計"] = T
    rec[u"書類"] = docs
    rec[u"limits"] = [u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)", u"札が無いので動いた行の正しさは見ていない(C-3 は「壊さない」の確認)",
                      u"有報は千円・百万円で書くので、万・億のコンマの形は 97 書類で 2 つ(封 §0-1 の 3)。効きは言えず、壊さないことだけを見る"]
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise R97.Stop(u"記録に鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    for k in (u"C-3 動いた既存の行", u"C-4 増えた claim", u"増えた claim のある書類", u"消えた行(a にあって b に鍵が無い行)", u"claim の数の差(総数)"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(u"C-2", json.dumps(dict((p, (v[u"byte が同じ書類"], v[u"書類"])) for p, v in T[u"C-2 旗が偽の profile の byte 一致"].items())))
    print(u"C-13", json.dumps(link, ensure_ascii=False))


if __name__ == "__main__":
    main()
