# -*- coding: utf-8 -*-
"""限定確認(docs/HOLDOUT_P16_CONDITIONS_2026-10-13.md)の採点。**回答が 1 つも無い状態で書いて固定する。**

段 1 ``labels``: 2 席の回答から確定ラベルを作る(前回 e2 と同じ規則)。
  - 確定 = 両席とも「独立判定」で、(要素の局所名, context) の**集合**が同値類 v0
    (``measure/grounds_eval.canon``: 末尾 SummaryOfBusinessResults を落とす・TotalAssets→Assets)で一致。
  - 厳密にも一致すれば ``厳密一致 = true``。v0 でだけ一致した行はラベルの fact に**席 1 の fact** を採り、
    席 2 の fact を「同値の他の候補」に入れ、``v0_only = true`` を付ける(件数を報告する)。
  - 片側だけ判定不能 → 判定不能(片側)、両側 → 判定不能(両側)、集合が違う → 不一致。L に入れない。
  - 形はラベルに ``[席1の形, 席2の形]``。方向の形 = 席 1 の形が「符号・方向」(grounds_eval と同じ)。
段 2 ``dumps``: P7・P13・P16 と P16 の旗落とし 6 本を 2 書類で回し、行の鍵ごとに state・pointers を書く。
  - 母集団は P16 の Claim(claim id で対応)。P7・P13 は内容の鍵(前後の抜粋|値|語)で対応。無ければ MISSING。
段 3 ``score``: grounds_eval で採点し、合算 L の S1〜S3・S4、書類別、形別、v0 を併記。失敗なら §3 の帰属表を出す。

通信しない。engine は変えない。回答ファイルは読むだけで書き換えない。
"""

import collections
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)

import grounds_eval as GE  # noqa: E402

DOCS = ("S100Z39P", "S100Z4N9")
BASE = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p16")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
ABLATIONS = ("taxonomy_labels_all_ns", "statement_facts_first", "period_cue",
             "flow_item_from_label", "pct_change_phrase", "ratio_table")
THRESH = {"S1_E1_over_L_min": 0.50, "S2_E2_over_G_max": 0.10, "S3_E3_over_L_max": 0.40, "S4_warn_pt": 15.0}
L_MIN = 100


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def local(name):
    return name.split(":", 1)[-1]


def fact_set(row):
    return {(local(f["要素"]), f["context"]) for f in row.get("fact") or []}


def v0(s):
    return {(GE.canon(e), c) for e, c in s}


# ---------------------------------------------------------------- 段 1
def build_labels():
    out, counts = [], collections.Counter()
    for doc in DOCS:
        a1 = json.load(io.open(os.path.join(BASE, "answers_seat1", "answer_%s.json" % doc), encoding="utf-8"))
        a2 = json.load(io.open(os.path.join(BASE, "answers_seat2", "answer_%s.json" % doc), encoding="utf-8"))
        mat = json.load(io.open(os.path.join(BASE, "seat", "material_%s.json" % doc), encoding="utf-8"))
        keys = [r["行の鍵"] for r in mat["行"]]
        r1 = {r["行の鍵"]: r for r in a1["行"]}
        r2 = {r["行の鍵"]: r for r in a2["行"]}
        for k in keys:
            x, y = r1.get(k), r2.get(k)
            row = {"id": "%s:%s" % (doc, k), "docID": doc, "鍵": k}
            if x is None or y is None:
                row["分類"] = "回答なし(%s)" % ("席1" if x is None else "席2")
            else:
                j1, j2 = x.get("判定") == "独立判定", y.get("判定") == "独立判定"
                row["形"] = [x.get("形"), y.get("形")]
                if j1 and j2:
                    s1, s2 = fact_set(x), fact_set(y)
                    if s1 == s2:
                        row["分類"], row["厳密一致"], row["v0_only"] = "確定(同値類v0)", True, False
                    elif v0(s1) == v0(s2):
                        row["分類"], row["厳密一致"], row["v0_only"] = "確定(同値類v0)", False, True
                    else:
                        row["分類"] = "不一致"
                    row["fact"] = sorted(s1) if row["分類"].startswith("確定") else None
                    cands = [[c.get("要素"), c.get("context")] for r in (x, y) for c in (r.get("同値の他の候補") or [])]
                    if row.get("v0_only"):
                        cands += [[e, c] for e, c in sorted(s2)]
                    row["同値の他の候補"] = cands
                    if row["分類"] == "不一致":
                        row["席1"], row["席2"] = sorted(s1), sorted(s2)
                elif j1 or j2:
                    row["分類"] = "判定不能(片側)"
                else:
                    row["分類"] = "判定不能(両側)"
            counts[(doc, row["分類"])] += 1
            out.append(row)
    rec = {"purpose": "限定確認の確定ラベル(2 席 memoryless、同値類 v0 で集合一致した行だけ)",
           "conditions": "docs/HOLDOUT_P16_CONDITIONS_2026-10-13.md",
           "sources_sha256": {doc: {"seat1": sha_file(os.path.join(BASE, "answers_seat1", "answer_%s.json" % doc)),
                                    "seat2": sha_file(os.path.join(BASE, "answers_seat2", "answer_%s.json" % doc))}
                              for doc in DOCS},
           "counts": {"%s|%s" % k: v for k, v in sorted(counts.items())},
           "labels": out}
    p = os.path.join(BASE, "labels_holdout_p16_2026-10-13.json")
    if os.path.exists(p):
        raise SystemExit("既に在る。上書きしない: %s" % p)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print(json.dumps(rec["counts"], ensure_ascii=False, indent=1))
    print("labels ->", p, sha_file(p)[:16])


# ---------------------------------------------------------------- 段 2
def _profiles():
    import dataclasses
    from adapters.xbrl import vocabulary as V
    out = {"P7": V.PROFILES["P7"], "P13": V.PROFILES["P13"], "P16": V.PROFILES["P16"]}
    for flag in ABLATIONS:
        out["P16-" + flag] = dataclasses.replace(V.PROFILES["P16"], name="P16-" + flag, **{flag: False})
    return out


def _run(doc, prof):
    from tests.golden import _instrument as H
    from adapters.xbrl import recipes as R
    zb = open(os.path.join(CACHE, doc + ".zip"), "rb").read()
    rl, res, _ = H.run_verification(doc, prof, lambda: zb)
    num, txt = R.build_raw_claims(zb, prof)
    raw = {c["id"]: c for c in num + txt}
    out = {}
    for r in rl:
        x = res[r.claim.id]
        c = raw.get(r.claim.id, {})
        ptrs = [(q if isinstance(q, str) else q.scheme + ":" + q.locator) for q in x.pointers]
        out[r.claim.id] = {"state": x.state.name, "pointers": ptrs,
                           "subject": r.claim.subject, "span": r.claim.provenance.get("span"), "reason": x.reason,
                           "ckey": "%s|%s|%s" % (c.get("span"), c.get("value"), c.get("word"))}
    return out


def build_dumps():
    profs = _profiles()
    for doc in DOCS:
        key = json.load(io.open(os.path.join(BASE, "commander_only", "key_%s.json" % doc), encoding="utf-8"))
        rows = key["rows_map"]
        for pn, prof in profs.items():
            run = _run(doc, prof)
            by_ckey = collections.defaultdict(list)
            for cid, v in run.items():
                by_ckey[v["ckey"]].append(cid)
            dump, missing = {}, 0
            for r in rows:
                k = "%s:%s" % (doc, r["行の鍵"])
                if pn.startswith("P16"):
                    v = run.get(r["claim_id"])
                else:
                    ids = by_ckey.get(r["content_key"], [])
                    v = run[ids[0]] if len(ids) == 1 else None
                if v is None:
                    missing += 1
                    continue
                dump[k] = {kk: vv for kk, vv in v.items() if kk != "ckey"}
            p = os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (pn, doc))
            with io.open(p, "w", encoding="utf-8") as fh:
                json.dump(dump, fh, ensure_ascii=False, indent=1)
            print("%-28s %s rows %3d missing %2d" % (pn, doc, len(dump), missing))


# ---------------------------------------------------------------- 段 3
def _load_dump(pn):
    d = {}
    for doc in DOCS:
        d.update(json.load(io.open(os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (pn, doc)), encoding="utf-8")))
    return d


def score():
    labels = GE.load_labels(os.path.join(BASE, "labels_holdout_p16_2026-10-13.json"))
    res = {}
    rows_by = {}
    for pn in ["P7", "P13", "P16"] + ["P16-" + f for f in ABLATIONS]:
        rows = GE.score(_load_dump(pn), labels)
        rows_by[pn] = rows
        res[pn] = {"all": GE.summarize(rows),
                   "value_form": GE.summarize(rows, lambda r: not r["direction"]),
                   "direction_form": GE.summarize(rows, lambda r: r["direction"])}
        for doc in DOCS:
            res[pn][doc] = GE.summarize(rows, lambda r, d=doc: r["id"].startswith(d))
    m16, m7 = res["P16"]["all"], res["P7"]["all"]
    L, G = m16["L"], m16["G"] or 1
    s1, s2, s3 = m16["E1_strict"] / (L or 1), m16["E2_strict"] / G, m16["E3"] / (L or 1)
    s4 = 100.0 * (m16["E1_strict"] - m7["E1_strict"]) / (L or 1)
    verdict = {"L": L, "L_min_ok": L >= L_MIN,
               "S1": {"value": round(s1, 4), "pass": s1 >= THRESH["S1_E1_over_L_min"]},
               "S2": {"value": round(s2, 4), "pass": s2 <= THRESH["S2_E2_over_G_max"]},
               "S3": {"value": round(s3, 4), "pass": s3 <= THRESH["S3_E3_over_L_max"]},
               "S4_pt": round(s4, 1), "S4_warn": s4 < THRESH["S4_warn_pt"]}
    verdict["success"] = bool(verdict["L_min_ok"] and verdict["S1"]["pass"] and verdict["S2"]["pass"] and verdict["S3"]["pass"])
    verdict["judgement"] = ("判定不能(L < %d)" % L_MIN) if not verdict["L_min_ok"] else ("成功" if verdict["success"] else "失敗")
    # §3 帰属(失敗時のみ意味を持つが、常に出す)
    p16 = {r["id"]: r for r in rows_by["P16"]}
    e2_rows = [i for i, r in p16.items() if r["state"] == "GROUNDED" and not r["strict"]]
    e3_rows = [i for i, r in p16.items() if r["state"] not in ("GROUNDED", "MISSING")]
    attrib = collections.Counter()
    per_row = {}
    for i in e2_rows:
        resp = []
        for f in ABLATIONS:
            q = {r["id"]: r for r in rows_by["P16-" + f]}.get(i)
            if q is None or q["state"] != p16[i]["state"] or q.get("arm") != p16[i].get("arm"):
                resp.append(f)
        per_row[i] = resp or ["P13以前"]
        for f in per_row[i]:
            attrib[f] += 1
    stop_reasons = collections.Counter((p16[i]["state"], str(p16[i].get("reason"))[:40]) for i in e3_rows)
    out = {"thresholds": THRESH, "verdict": verdict, "metrics": res,
           "E2_rows_P16": {i: {"arm": p16[i]["arm"], "label": p16[i]["label"], "responsible": per_row[i]} for i in e2_rows},
           "E2_attribution": dict(attrib),
           "E3_stop_reasons": {"%s|%s" % k: v for k, v in stop_reasons.most_common()},
           "labels_sha256": sha_file(os.path.join(BASE, "labels_holdout_p16_2026-10-13.json"))}
    p = os.path.join(BASE, "commander_only", "score_report_2026-10-13.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    for pn in ("P7", "P13", "P16"):
        print(GE.report(rows_by[pn], pn))
    print(json.dumps(verdict, ensure_ascii=False, indent=1))
    print("E2 attribution:", dict(attrib))
    print("report ->", p)


if __name__ == "__main__":
    {"labels": build_labels, "dumps": build_dumps, "score": score}[sys.argv[1]]()
