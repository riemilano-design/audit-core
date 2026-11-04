# -*- coding: utf-8 -*-
u"""手元の 97 書類の有報の原文で、RB(丸め方の根拠が混ざる桁は両方の帯で照らす。P30E = P29E + RB)が他を壊さないか・何行が動くかの測定。封 ``docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md`` §3(D-1・D-7・D-10)・§5。

    cd audit-core
    python3 measure/xbrl_rmix_regress97_2026-11-04.py [--out fixtures/xbrl/rmix/regress97_2026-11-04.json] [--procs 4] [--only <docID>]

**0 USD・通信なし・鍵は読まない・LLM の API は呼ばない。** 書類は手元の cache の ZIP だけ(読むだけで 1 file も足さない。件数と名前の一覧の sha256 を前後で記録し、変わっていれば記録を書かずに止める)。
engine(``core/``・``adapters/``)は測る側から 1 行も変えない。数の読み取り N の便の ``xbrl_numfix_regress97_2026-11-04.py``(XR)を importlib で読み込んで差し替え(NOW・BASE・PAIRS・KEYED・封・
engine の file・前の記録)、``doc_job``・``keyed_rows``・``pair_moves``・``doc_rows``・``engine_link`` を使う(写さない・編集しない)。**評価用の AI の文・DB の応答は開かない**(``edinetdb-p27/`` の下を 1 file も読まない)。
記録に span・value・recomputed・文は入れない(docID は入る。``LATER_NAMING_FILES`` に宣言)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- profile は P22・P26・P27・P27E・P28・P28E・P29・P29E・P30E(9)。D-1 は N の便の記録 ``fixtures/xbrl/numfix/regress97_2026-11-04.json`` の各書類の ``出力の sha256(engine の欄を除く)``(P22〜P29E の 8 つ)と
  **この tree の engine の出力**を書類ごとに比べる。出力の sha256 は ``sort_keys`` の JSON(``engine`` の欄を除く)。
- D-7 の「動いた行」= P29E と P30E の両方に在る数・文の claim のうち (state, reason, pointers) が違う行。対応は **(種類, 文の番号, 位置, 同じ鍵の中の順)**(claim の数が同じなら index の対応と同じ。違っても鍵で対応を付ける)。
  「失う行」= 動いた行のうち P29E が GROUNDED で P30E が GROUNDED でない行。増えた行・消えた行(P30E にだけ・P29E にだけある鍵)も別に数える。
- D-10 の「直す試験 file の数」= 封の commit から engine の commit(封の後に engine の 3 file を最初に触った commit のうち最後のもの)までの ``git diff --name-status`` で ``tests/`` の下の変更のうち状態が M の数。
  A(新しい file)は別に書く。engine の変更が 3 file(recipes・vocabulary・comparators)だけ・削除 0 かもここで数える。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                     # 並列(--procs 2 以上)は doc_job を module 名で pickle する。登録が無いと PicklingError
    spec.loader.exec_module(mod)
    return mod


XR = load_module(os.path.join(HERE, "xbrl_numfix_regress97_2026-11-04.py"), "numfix_regress97_for_rmix")
R97, D, VD = XR.R97, XR.D, XR.VD

SEAL_REL = "docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT = "de23edc"
OUT_REL = "fixtures/xbrl/rmix/regress97_2026-11-04.json"
PREV_RECORD_REL = "fixtures/xbrl/numfix/regress97_2026-11-04.json"
NOW_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E", "P30E")
BASE_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E")
PAIRS = (("P30E 対 P29E", "P29E", "P30E"),)
KEYED = ("P29E", "P30E")
STATES = XR.STATES
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py")
#: XR の module の属性に差し替える先(使う側 ``XR.doc_job``・``XR.doc_rows``・``XR.engine_commits`` が引く名前)
SWAP_TABLE = (("SEAL_REL", SEAL_REL), ("SEAL_COMMIT", SEAL_COMMIT), ("OUT_REL", OUT_REL), ("PREV_RECORD_REL", PREV_RECORD_REL), ("NOW_PROFILES", NOW_PROFILES),
              ("BASE_PROFILES", BASE_PROFILES), ("PAIRS", PAIRS), ("KEYED", KEYED), ("ENGINE_FILES", ENGINE_FILES))


def install():
    for name, v in SWAP_TABLE:
        setattr(XR, name, v)


def wiring_problems():
    u"""XR の差し替えが全部届いているか。問題の列。"""
    return [u"XR.%s が差し替えた先でない" % name for name, v in SWAP_TABLE if getattr(XR, name) != v]


install()


def summarize_docs(docs):
    u"""``書類`` の行(記録に書く形)から集計を作る。門が記録の ``書類`` から作り直して照らすのにも使う(集計の正本はこの関数)。"""
    out = collections.OrderedDict()
    out[u"4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, sum(d[u"4 state"][p][s] for d in docs)) for s in STATES)) for p in NOW_PROFILES)
    out[u"claims"] = collections.OrderedDict((p, sum(d[u"claims"][p] for d in docs)) for p in NOW_PROFILES)
    c1 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d[u"docID"] for d in docs if d[u"出力の sha256(engine の欄を除く)"][p] == d[u"前の便の記録の sha256"][p]]
        c1[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(docs)), (u"違った書類", sorted(set(d[u"docID"] for d in docs) - set(same)))])
    out[u"D-1 旗が偽の profile の byte 一致"] = c1
    name = PAIRS[0][0]
    mv = [d[u"動いた行と増えた行"][name] for d in docs]
    moved = [x for m in mv for x in m[u"動いた既存の行"]]
    lost = [x for x in moved if x[4] == "GROUNDED" and x[5] != "GROUNDED"]
    gained = [x for x in moved if x[4] != "GROUNDED" and x[5] == "GROUNDED"]
    dirs = collections.Counter(u"%s → %s" % (x[4], x[5]) for x in moved if x[4] != x[5])
    out[u"D-7 P30E 対 P29E"] = collections.OrderedDict([
        (u"動いた既存の行", len(moved)), (u"GROUNDED を失う行", len(lost)), (u"GROUNDED になった行", len(gained)),
        (u"state が変わった行", sum(1 for x in moved if x[4] != x[5])), (u"向き別", collections.OrderedDict(sorted(dirs.items()))),
        (u"増えた行", sum(m[u"増えた行"] for m in mv)), (u"消えた行", sum(m[u"消えた行"] for m in mv)),
        (u"動いた行のある書類", sum(1 for m in mv if m[u"動いた既存の行"])),
        (u"claim の数が違う書類", sum(1 for d in docs if d[u"claims"]["P30E"] != d[u"claims"]["P29E"]))])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--only", default=None, help="この docID の 1 書類だけ(本番の記録を作らない確認用には --out を替える)")
    a = ap.parse_args(argv)
    bad = wiring_problems()
    if bad:
        raise R97.Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    if os.path.exists(a.out):
        raise R97.Stop(u"**出力が既に在る。測り直さない。止める**")
    P = R97.prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    jobs, ids67, ids30 = R97.make_jobs(NOW_PROFILES)
    prev = D.jload(os.path.join(ROOT, PREV_RECORD_REL))
    prev_by = dict((r["docID"], r) for r in prev[u"書類"])
    if sorted(prev_by) != sorted(ids67 + ids30):
        raise R97.Stop(u"**N の便の記録の書類が 97 書類の一覧と合わない。止める**")
    if a.only is not None:
        jobs = [j for j in jobs if j[0] == a.only]
        if not jobs:
            raise R97.Stop(u"**--only の docID が 97 書類に無い。止める**")
    res = R97.run_pool(XR.doc_job, jobs, a.procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    cache_same = names_before == names_after
    if not cache_same:
        raise R97.Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    docs = XR.doc_rows(res, prev_by)
    T = summarize_docs(docs)
    link = XR.engine_link()
    T[u"D-10 engine の留めの連動で直す試験 file"] = collections.OrderedDict(link)
    rec = collections.OrderedDict()
    rec[u"seal"] = u"audit-core/" + SEAL_REL
    rec[u"step"] = u"RB(丸め方の根拠が混ざる桁)― 手元の 97 書類の有報の原文での後退と動いた行の測定(D-1・D-7・D-10)"
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"HEAD の commit"] = D.git_head()
    rec[u"この script の sha256"] = D.sha256_file(os.path.abspath(__file__))
    rec[u"numfix regress97 script の sha256"] = D.sha256_file(os.path.join(HERE, "xbrl_numfix_regress97_2026-11-04.py"))
    rec[u"前の便の記録の sha256"] = D.sha256_file(os.path.join(ROOT, PREV_RECORD_REL))
    rec[u"engine の指紋(この tree)"] = VD.engine_fingerprint()
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"範囲"] = u"全 97 書類" if a.only is None else u"**--only の 1 書類だけ(本番の記録ではない)**"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", names_before), (u"後", names_after), (u"変化なし", cache_same)])
    rec[u"集計"] = T
    rec[u"書類"] = docs
    rec[u"limits"] = [u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)", u"札が無いので動いた行の正しさは見ていない(D-7 は「壊さない」の確認)",
                      u"有報は千円・百万円で書くので、丸め方の根拠が桁ごとに混ざる書類はほぼ無い。効きは言えず、壊さないことだけを見る"]
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise R97.Stop(u"記録に鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    for k in (u"D-7 P30E 対 P29E", u"claim の数の差(総数)"):
        if k in T:
            print(k, json.dumps(T[k], ensure_ascii=False))
    print(u"D-1", json.dumps(dict((p, (v[u"byte が同じ書類"], v[u"書類"])) for p, v in T[u"D-1 旗が偽の profile の byte 一致"].items())))
    print(u"D-10", json.dumps(link, ensure_ascii=False))


if __name__ == "__main__":
    main()
