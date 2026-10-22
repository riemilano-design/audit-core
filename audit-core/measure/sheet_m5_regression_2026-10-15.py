# -*- coding: utf-8 -*-
"""封 §5 の検出条件: **既存の正しい接続を壊していないか**だけを見る。

**性能の証拠ではない。**合格線を 1 本も計算しない。人間の指示(2026-10-15):
  「既存の正しい接続 11 件は、変化があれば原因を個別に記録する。」

封 §5 は `agree_6` で見ると書いたが、**今回の 24 件のラベルは 4 欄しか無い**
(親は次の報告文の採点仕様で初めて席に尋ねる)。だから **`agree_6` は計算できない。**
代わりに、壊れていないことを**より強い条件**で見る:
  1. まだ `GROUNDED` であること
  2. 旧 4 欄が凍結ラベルと一致していること(`agree_4`)
  3. **指しているセル(pointer)が診断のときと同じであること**
3 は `agree_6` より強い(同じセルなら親も同じ)。この読み替えは封に追記で開示する。
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
REPORT = os.path.join(FX, "m4_report_2026-10-15.json")
FROZEN = os.path.join(FX, "m4_score_2026-10-15.json")
DIAG = os.path.join(FX, "m4_fix_diagnostic_2026-10-15.json")
OLDBINDS = os.path.join(FX, "m4_binds_2026-10-15.json")
OUT = os.path.join(FX, "m5_regression_2026-10-15.json")

MUST_KEEP = ("R004", "R008", "R009", "R013", "R015",
             "R017", "R018", "R019", "R020", "R021", "R022")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm


def key4(b):
    if b["state"] != "GROUNDED":
        return None
    e = b["evidence"] or {}
    level = norm(e.get("level")) or ""
    name = "" if level in (norm("会計"), norm("合計")) else (norm(e.get("name")) or "")
    return (norm(e.get("scope")) or "", level, name, norm(e.get("column")) or "")


def main():
    frozen = {r["id"]: r for r in json.load(io.open(FROZEN, encoding="utf-8"))["rows"]}
    diag = {r["id"]: r for r in json.load(io.open(DIAG, encoding="utf-8"))["rows"]}
    old = {c["id"]: c for c in json.load(io.open(OLDBINDS, encoding="utf-8"))["claims"]}
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    out = E.run(report,
                M2.parse_soukatu(books[M2.SOUKATU]),
                M2.parse_kessan(books[M2.KESSAN]),
                M2.parse_meisai(books[M2.MEISAI]))
    binds = {b["claim_id"]: b for b in out["binds"]}
    by_key = {}
    for c in out["claims"]:
        if not c.get("skipped"):
            by_key.setdefault((c["sentence_index"], c["value"]), []).append(c)

    rows, broken, unmatched = {}, [], []
    for cid in sorted(frozen):
        k = (old[cid]["sentence_index"], old[cid]["value"])
        cands = by_key.get(k, [])
        if len(cands) != 1:
            unmatched.append({"id": cid, "found": len(cands)})
            continue
        nc = cands[0]
        b = binds[nc["id"]]
        lab = frozen[cid]["label"]
        label4 = tuple(lab[1]) if lab[0] == "label" else None
        got4 = key4(b)
        rec = {"state": b["state"], "route": b["route"], "pointer": b["pointer"],
               "pointer_before": diag[cid]["pointer"],
               "hold_reason": b.get("hold_reason"),
               "level": nc.get("level"), "column": nc.get("column"),
               "subject": nc.get("subject"),
               "parent": (b["evidence"] or {}).get("parent"),
               "agree_4": (got4 is not None and got4 == label4),
               "label_is_verdict": label4 is None,
               "diagnostic_verdict": diag[cid]["after"],
               "distinct_keys": b.get("distinct_keys"),
               "unconfirmed_scope": b.get("unconfirmed_scope")}
        rows[cid] = rec
        if cid in MUST_KEEP:
            why = []
            if b["state"] != "GROUNDED":
                why.append("state が %s になった(%s)" % (b["state"], b.get("hold_reason")))
            if not rec["agree_4"]:
                why.append("旧 4 欄が一致しなくなった: %s vs %s" % (got4, label4))
            if b["pointer"] != rec["pointer_before"]:
                why.append("pointer が %s -> %s に動いた"
                           % (rec["pointer_before"], b["pointer"]))
            if why:
                broken.append({"id": cid, "why": why})

    moved = {cid: {"before": diag[cid]["after"], "state": r["state"],
                   "hold_reason": r["hold_reason"]}
             for cid, r in rows.items()
             if (r["state"] == "GROUNDED") != (diag[cid]["state"] == "GROUNDED")}

    print("封 §5 の検出: 守るべき %d 件 / **壊れた %d 件**" % (len(MUST_KEEP), len(broken)))
    for b in broken:
        print("  壊れた %s: %s" % (b["id"], " / ".join(b["why"])))
    print("接続の有無が動いた行 %d 件:" % len(moved))
    for cid, m in sorted(moved.items()):
        print("  %s %s -> %s %s" % (cid, m["before"], m["state"], m["hold_reason"] or ""))
    print("別名: 通った %d / 未確認 %d" % (len(out["alias"]["table"]),
                                          len(out["alias"]["unconfirmed"])))
    print("一意でない階層:", out["duplication"]["levels_not_unique"])
    print("状態:", json.dumps(dict(collections.Counter(
        r["state"] for r in rows.values())), ensure_ascii=False))
    if unmatched:
        print("合わせられなかった行:", unmatched)

    rec = {"purpose": "封 §5 の検出条件だけを見る回帰。**性能の証拠ではない**",
           "not_performance_evidence": True,
           "seal": "docs/DOMAIN1_M5_SEAL_2026-10-15.md",
           "engine": "measure/sheet_m5_engine_2026-10-15.py",
           "note": "この 24 件のラベルは 4 欄しか無いので agree_6 は計算できない。"
                   "pointer の同一で代える(封への追記 1 で開示)",
           "must_keep": list(MUST_KEEP), "broken": broken,
           "moved_binding": moved, "unmatched": unmatched,
           "alias_passed": sorted(out["alias"]["table"]),
           "alias_unconfirmed": len(out["alias"]["unconfirmed"]),
           "duplication": out["duplication"],
           "states": dict(collections.Counter(r["state"] for r in rows.values())),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
