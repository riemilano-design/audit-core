# -*- coding: utf-8 -*-
"""P17 の測定(計画 docs/P17_PLAN_2026-10-14.md §0・§3)。通信しない。

1. 訓練 2 書類(S100Z39P・S100Z4N9): 確定ラベル 217 件に対する P16 / P17 の根拠レベルの指標。
2. 設計に使っていない S100Z4Q1 の AI 文(独立ラベル 183 件): 同じ指標。
3. キャッシュの 16 書類: claim ごとの P16 → P17 の state の変化(GROUNDED → GROUNDED でない を数える)。

使い方::  python3 -B measure/p17_measure_2026-10-14.py [--docs S100Z39P,S100Z4N9,...]
出力: fixtures/xbrl/p17/{dump_P1x_<doc>.json, score_2026-10-14.json}
"""

import collections
import hashlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "tests", "golden"))

from adapters.xbrl import vocabulary as V, recipes as R  # noqa: E402
from tests.golden import _instrument as H  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
HOLD = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p16")
FIX = os.path.join(ROOT, "fixtures", "xbrl")
OUT = os.path.join(FIX, "p17")
TRAIN_DOCS = ("S100Z39P", "S100Z4N9")
DEV_DOC = "S100Z4Q1"
DEV_ZIP_SHA = "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6"
DEV_MOD_SHA = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
PROFS = ["P16", "P17"]   # --base/--new で差し替え


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GE = _load("grounds_eval", os.path.join(HERE, "grounds_eval.py"))


def run(zb, doc, prof):
    rl, res, _ = H.run_verification(doc, prof, lambda: zb)
    out = {}
    for r in rl:
        x = res[r.claim.id]
        out[r.claim.id] = {"state": x.state.name,
                           "pointers": [(q if isinstance(q, str) else q.scheme + ":" + q.locator) for q in x.pointers],
                           "subject": r.claim.subject, "span": r.claim.provenance.get("span"), "reason": x.reason}
    return out


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    return p


def train_scores():
    labels = GE.load_labels(os.path.join(HOLD, "labels_holdout_p16_2026-10-13.json"))
    dumps = {pn: {} for pn in PROFS}
    for doc in TRAIN_DOCS:
        key = json.load(io.open(os.path.join(HOLD, "commander_only", "key_%s.json" % doc), encoding="utf-8"))
        zb = open(os.path.join(CACHE, doc + ".zip"), "rb").read()
        for pn in PROFS:
            r = run(zb, doc, V.PROFILES[pn])
            d = {}
            missing = 0
            for row in key["rows_map"]:
                v = r.get(row["claim_id"])
                if v is None:
                    missing += 1
                    continue
                d["%s:%s" % (doc, row["行の鍵"])] = v
            save("dump_%s_%s.json" % (pn, doc), d)
            dumps[pn].update(d)
            print("train %s %s rows %d missing %d" % (pn, doc, len(d), missing))
    res = {}
    for pn in PROFS:
        rows = GE.score(dumps[pn], labels)
        res[pn] = {"all": GE.summarize(rows),
                   "value_form": GE.summarize(rows, lambda r: not r["direction"]),
                   "direction_form": GE.summarize(rows, lambda r: r["direction"])}
        for doc in TRAIN_DOCS:
            res[pn][doc] = GE.summarize(rows, lambda r, d=doc: r["id"].startswith(d))
        res[pn]["rows"] = {r["id"]: {"state": r["state"], "strict": r["strict"]} for r in rows}
    return res


def dev_scores():
    from adapters.xbrl import edinet
    builder = _load("ai_prose_claims", os.path.join(FIX, "ai_prose_claims_2026-10-09.py"))
    zb = edinet.read_cached(DEV_DOC, expected_sha256=DEV_ZIP_SHA)
    with io.open(os.path.join(FIX, "ai_prose_2026-10-09.txt"), encoding="utf-8") as fh:
        prose = fh.read()
    mod_zb, _m, _s = builder.build_modified_zip(zb, prose)
    assert hashlib.sha256(mod_zb).hexdigest() == DEV_MOD_SHA
    labels = GE.load_labels()
    res = {}
    for pn in PROFS:
        d = run(mod_zb, DEV_DOC, V.PROFILES[pn])
        save("dump_%s_%s_ai_prose.json" % (pn, DEV_DOC), d)
        rows = GE.score(d, labels)
        res[pn] = {"all": GE.summarize(rows), "value_form": GE.summarize(rows, lambda r: not r["direction"]),
                   "rows": {r["id"]: {"state": r["state"], "strict": r["strict"]} for r in rows}}
        print("dev %s %s" % (pn, json.dumps(res[pn]["all"], ensure_ascii=False)))
    return res


def all_docs_diff(docs):
    out = {}
    for doc in docs:
        zb = open(os.path.join(CACHE, doc + ".zip"), "rb").read()
        a = run(zb, doc, V.PROFILES[PROFS[0]])
        b = run(zb, doc, V.PROFILES[PROFS[1]])
        same_ids = set(a) == set(b)
        trans = collections.Counter()
        ex = []
        for cid in a:
            if cid not in b:
                continue
            sa, sb = a[cid]["state"], b[cid]["state"]
            if sa != sb:
                trans["%s->%s" % (sa, sb)] += 1
                if sa == "GROUNDED":
                    ex.append({"id": cid, "span": a[cid]["span"], "p16": a[cid]["pointers"], "p17": b[cid]["pointers"], "p17_state": sb})
            elif sa == "GROUNDED" and a[cid]["pointers"] != b[cid]["pointers"]:
                trans["GROUNDED(pointer changed)"] += 1
                ex.append({"id": cid, "span": a[cid]["span"], "p16": a[cid]["pointers"], "p17": b[cid]["pointers"], "p17_state": sb})
        out[doc] = {"claims_p16": len(a), "claims_p17": len(b), "same_ids": same_ids,
                    "transitions": dict(trans), "grounded_lost_or_rebound": ex}
        print("diff %s claims %d/%d same_ids %s %s" % (doc, len(a), len(b), same_ids, dict(trans)))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    docs = sorted(n[:-4] for n in os.listdir(CACHE) if n.endswith(".zip"))
    tag = ""
    while argv:
        if argv[0] == "--docs":
            docs = argv[1].split(","); argv = argv[2:]
        elif argv[0] == "--tag":
            tag = "_" + argv[1]; argv = argv[2:]
        elif argv[0] == "--base":
            PROFS[0] = argv[1]; argv = argv[2:]
        elif argv[0] == "--new":
            PROFS[1] = argv[1]; argv = argv[2:]
        else:
            raise SystemExit("unknown arg %r" % argv[0])
    rep = {"train": train_scores(), "dev": dev_scores(), "all_docs": all_docs_diff(docs)}
    g_lost = sum(sum(v for k, v in d["transitions"].items() if k.startswith("GROUNDED->")) for d in rep["all_docs"].values())
    rep["summary"] = {
        "profiles": list(PROFS),
        "train_base": rep["train"][PROFS[0]]["all"], "train_new": rep["train"][PROFS[1]]["all"],
        "dev_base": rep["dev"][PROFS[0]]["all"], "dev_new": rep["dev"][PROFS[1]]["all"],
        "grounded_to_non_grounded_total": g_lost,
    }
    p = save("score_2026-10-14%s.json" % tag, rep)
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
    print("->", p)


if __name__ == "__main__":
    main()
