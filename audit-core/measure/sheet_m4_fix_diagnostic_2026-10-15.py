# -*- coding: utf-8 -*-
"""直した engine を**今回の 24 件**に当てる ― **診断だけ**(封 §0・§7)。

**この記録は性能の証拠ではない。**人間の指示:
  「今回の 24 件は、修正の影響を予測するための診断用データとしてのみ使います。」
  「同じ 24 件で改善を確認して、それを新しい性能の証拠にすることは認めない。」

したがってこの script は:
  - 合格線を 1 本も計算しない(`overall` も `lines` も書かない)
  - 封じた予測(docs/DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md §3-1)を**文書から読み**、
    実測と突き合わせて**当たり/外れ**だけを出す
  - ラベルは凍結したものをそのまま使う(**取り直さない**)
  - 当てるのは **1 回**。回数を記録する
"""
import collections
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
REPORT = os.path.join(FX, "m4_report_2026-10-15.json")
FROZEN_SCORE = os.path.join(FX, "m4_score_2026-10-15.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md")
OUT = os.path.join(FX, "m4_fix_diagnostic_2026-10-15.json")

VERDICTS = {
    "正しい接続": "正しい接続",
    "誤接続": "誤接続",
    "正しく保留": "正しく保留",
    "判定不能なのに接続": "根拠なし/判定不能なのに接続した",
    "結べなかった": "結べなかった(誤接続ではない)",
}
FIELDS = ("会計", "階層", "科目名", "列")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m4fix", os.path.join(HERE, "sheet_m4_engine_fix_2026-10-15.py"))
M2 = E.M2
norm = M2.norm


# --------------------------------------------- 封から予測を読む(字を写さない)
def read_prediction():
    """封 §3-1 の表を読む。**手で写すと封と食い違うので文書から読む。**"""
    doc = io.open(SEAL, encoding="utf-8").read()
    pred = {}
    for line in doc.splitlines():
        if not line.startswith("| R0"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cid, now, want = cells[0], cells[1], cells[2]
        plain = re.sub(r"[*`]", "", want)
        src = now if plain.startswith("変わらず") else plain
        hit = [v for k, v in VERDICTS.items() if k in src]
        if len(hit) != 1:
            raise AssertionError("封の予測が読めない: %s / %r" % (cid, want))
        pred[cid] = {"predicted": hit[0], "now": [v for k, v in VERDICTS.items()
                                                  if k in now][0],
                     "unchanged": plain.startswith("変わらず"), "raw": want}
    if len(pred) != 24:
        raise AssertionError("封の予測が 24 件でない: %d" % len(pred))
    return pred


# --------------------------------------------- 凍結した採点の規則(写し。変えない)
def engine_key(b):
    if b["state"] != "GROUNDED":
        return None
    e = b["evidence"] or {}
    level = norm(e.get("level")) or ""
    name = "" if level in (norm("会計"), norm("合計")) else (norm(e.get("name")) or "")
    return ("label", (norm(e.get("scope")) or "", level, name,
                      norm(e.get("column")) or ""))


def verdict_of(label, ek):
    """凍結した `sheet_m4_score_2026-10-15.py` と**同じ分け方**。合格線は出さない。"""
    if label[0] == "label":
        if ek == label:
            return "正しい接続"
        return "誤接続" if ek is not None else "結べなかった(誤接続ではない)"
    return "正しく保留" if ek is None else "根拠なし/判定不能なのに接続した"


def main():
    pred = read_prediction()
    frozen = json.load(io.open(FROZEN_SCORE, encoding="utf-8"))
    rows_before = {r["id"]: r for r in frozen["rows"]}
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    out = E.run(report,
                M2.parse_soukatu(books[M2.SOUKATU]),
                M2.parse_kessan(books[M2.KESSAN]),
                M2.parse_meisai(books[M2.MEISAI]))
    binds = {b["claim_id"]: b for b in out["binds"]}

    # 旧の行と**(文の番号, 値)**で合わせる(id は数が変われば動くので使わない)
    new_by_key = {}
    for c in out["claims"]:
        if c.get("skipped"):
            continue
        new_by_key.setdefault((c["sentence_index"], c["value"]), []).append(c)
    old_claims = json.load(io.open(os.path.join(FX, "m4_binds_2026-10-15.json"),
                                   encoding="utf-8"))["claims"]
    old_by_id = {c["id"]: c for c in old_claims}

    rows, hit, miss, unmatched = [], 0, 0, []
    for cid in sorted(rows_before):
        oc = old_by_id[cid]
        key = (oc["sentence_index"], oc["value"])
        cands = new_by_key.get(key, [])
        if len(cands) != 1:
            unmatched.append({"id": cid, "key": list(key), "found": len(cands)})
            continue
        nc = cands[0]
        b = binds[nc["id"]]
        ek = engine_key(b)
        label = tuple(rows_before[cid]["label"])
        label = (label[0], tuple(label[1]) if isinstance(label[1], list) else label[1])
        got = verdict_of(label, ek)
        ok = (got == pred[cid]["predicted"])
        hit += 1 if ok else 0
        miss += 0 if ok else 1
        rows.append({"id": cid, "new_claim_id": nc["id"],
                     "before": rows_before[cid]["verdict"],
                     "predicted": pred[cid]["predicted"], "after": got,
                     "prediction_hit": ok,
                     "state": b["state"], "route": b["route"],
                     "pointer": b["pointer"], "hold_reason": b.get("hold_reason"),
                     "subject": nc["subject"], "column": nc["column"],
                     "column_ambiguous": nc.get("column_ambiguous"),
                     "candidates": b["candidates"],
                     "distinct_keys": b.get("distinct_keys"),
                     "duplicates": b.get("duplicates"),
                     "engine_key": ek,
                     "moved": got != rows_before[cid]["verdict"],
                     "pointer_changed": b["pointer"] != rows_before[cid]["engine_pointer"]})

    moved = [r for r in rows if r["moved"]]
    counts = {
        "動いた": len(moved), "動かない": len(rows) - len(moved),
        "GROUNDED から保留へ": sum(1 for r in rows
                                   if rows_before[r["id"]]["engine_state"] == "GROUNDED"
                                   and r["state"] != "GROUNDED"),
        "未接続から正しい接続へ": sum(1 for r in moved
                                     if r["after"] == "正しい接続"
                                     and r["before"].startswith("結べなかった")),
        "保留から誤受理へ": sum(1 for r in moved
                               if r["before"] == "正しく保留"
                               and r["after"] != "正しく保留"),
        "GROUNDED のまま根拠が差し替わった": sum(
            1 for r in rows if r["state"] == "GROUNDED"
            and rows_before[r["id"]]["engine_state"] == "GROUNDED"
            and r["pointer_changed"]),
        "残る誤受理": sum(1 for r in rows if r["after"] in
                         ("誤接続", "根拠なし/判定不能なのに接続した")),
    }
    verdicts = collections.Counter(r["after"] for r in rows)
    print("予測 当たり %d / 外れ %d(全 %d 件)" % (hit, miss, len(rows)))
    for r in rows:
        if not r["prediction_hit"]:
            print("  外れ %s: 予測 %s / 実測 %s" % (r["id"], r["predicted"], r["after"]))
    print("件数:", json.dumps(counts, ensure_ascii=False))
    print("判定の内訳:", json.dumps(dict(verdicts), ensure_ascii=False))
    print("別名表:", json.dumps(out["alias"]["table"], ensure_ascii=False))
    print("未確認の別名:", json.dumps(out["alias"]["unconfirmed"], ensure_ascii=False))
    print("ルート:", json.dumps(dict(collections.Counter(
        b["route"] for b in out["binds"] if b["route"])), ensure_ascii=False))
    if unmatched:
        print("合わせられなかった行:", unmatched)

    rec = {"purpose": "直した engine を今回の 24 件に当てた**診断**。性能の証拠ではない",
           "not_performance_evidence": True,
           "human_instruction": "同じ 24 件で改善を確認して、それを新しい性能の証拠に"
                                "することは認めない(2026-10-15)",
           "seal": "docs/DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md",
           "engine": "measure/sheet_m4_engine_fix_2026-10-15.py",
           "frozen_engine_untouched": "measure/sheet_m4_engine_2026-10-15.py",
           "applied_times": 1,
           "labels": "凍結したものをそのまま使った(取り直していない)",
           "prediction_hits": hit, "prediction_misses": miss,
           "counts": counts, "verdicts": dict(verdicts),
           "alias": out["alias"], "column_cues": out["column_cues"],
           "claims_total": len(out["claims"]), "unmatched": unmatched,
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
