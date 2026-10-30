# -*- coding: utf-8 -*-
"""欠陥 A の候補の差分が「既に使った書類」で何を動かすかを測る(2026-10-14)。

封じた評価(`docs/DEFECT_A_EVAL_SEAL_2026-10-14.md`)は新しい 8 書類で F-3 = 0 だった。
人間の指摘: 「差の枝が水準一致の枝より先に走る以上、**別の標本で既存の正しい接続を奪う
可能性は残ります**」。ここで測るのはその 1 点である。

**未使用の封じた書類には当てない**(holdout を焼かないため)。
対象は `tests/adapters/xbrl/test_verify_entry.py` が数を固定している 14 書類 +
同ファイルの holdout 2 書類 = **16 書類すべて使用済み**。

    dump <audit-core root> <out.json>   その木の engine のまま書き出す
    diff <base.json> <impl.json>        2 つを比べて fixtures に記録を書く

通信しない。`PYTHONDONTWRITEBYTECODE=1` を付けて走らせる(Apple python の pyc 対策)。
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "used_docs_impact_2026-10-14.json")

DOCS = ["S100YMFV", "S100Z1WR", "S100Z35K", "S100Z37J", "S100Z3BW", "S100Z3CO",
        "S100Z3HP", "S100Z3JY", "S100Z3V1", "S100Z433", "S100Z4B6", "S100Z4DE",
        "S100Z4PA", "S100Z4Q1", "S100Z39P", "S100Z4N9"]
PROFILES = ("P20", "P16")
FIELDS = ("result", "pointer", "recomputed", "form")


def ptr(claim):
    p = claim.get("pointer")
    if p is None:
        return None
    return [p] if isinstance(p, str) else list(p)


def stage_dump(root, path):
    sys.path.insert(0, root)
    from adapters.xbrl import recipes as R, vocabulary as V, edinet, instance as I, extract as E
    out = {}
    for prof in PROFILES:
        rows = {}
        for d in DOCS:
            p = str(edinet.cache_path(d))
            if not os.path.exists(p):
                raise SystemExit("材料が無い: %s(取得はしない。無い書類は測らないと書く)" % d)
            zb = io.open(p, "rb").read()
            num, txt = R.build_raw_claims(zb, V.PROFILES[prof])
            inst = I.load_instance(zb)
            mdna = I.select_mdna(inst["textblocks"])
            sents = E.split_sentences(I.strip_html(inst["textblocks"][mdna]),
                                      V.PROFILES[prof].paren_sentence)
            for kind, claims in (("num", num), ("text", txt)):
                for c in claims:
                    rows["%s:%s" % (d, c["id"])] = {
                        "docID": d, "kind": kind, "result": c.get("result"),
                        "pointer": ptr(c), "recomputed": c.get("recomputed"),
                        "form": c.get("form"), "unit": c.get("unit"), "value": c.get("value"),
                        "claim_scale": c.get("claim_scale"), "unit_scale": c.get("unit_scale"),
                        "subject": c.get("subject"),
                        "span": c.get("span"), "match": c.get("match"),
                        "sentence": sents[c["sentence"]] if c.get("sentence") is not None else None}
        out[prof] = rows
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("書類 %d / 行 %s -> %s" % (len(DOCS), {k: len(v) for k, v in out.items()}, path))


def offset_units(row):
    """``recomputed`` が主張の数から**書かれた桁で**何単位ずれているか。

    engine が自分で持っている ``unit_scale``・``claim_scale`` だけで出す
    (単位の表を書き写すと、engine の表と食い違っても気づけない)。
    """
    if row["recomputed"] is None or row["value"] is None or not row["claim_scale"]:
        return None
    target = abs(row["value"]) * (row["unit_scale"] or 1.0)
    return round((abs(row["recomputed"]) - target) / row["claim_scale"], 3)


def compare(before, after):
    res = {}
    for prof in before:
        b, a = before[prof], after[prof]
        if set(b) != set(a):
            raise AssertionError("%s: 主張の集合が違う(前 %d 後 %d)" % (prof, len(b), len(a)))
        moved, other = [], []
        for cid in sorted(b):
            x, y = b[cid], a[cid]
            if all(x[k] == y[k] for k in FIELDS):
                continue
            rec = {"id": cid, "docID": x["docID"], "unit": x["unit"], "value": x["value"],
                   "claim_scale": x["claim_scale"], "subject": x["subject"], "span": x["span"],
                   "sentence": x["sentence"],
                   "before": dict([(k, x[k]) for k in FIELDS] + [("match", x["match"])]),
                   "after": dict([(k, y[k]) for k in FIELDS] + [("match", y["match"])])}
            if x["result"] == "VALUE_MISMATCH" and y["result"] == "GROUNDED":
                rec["offset_units"] = offset_units(y)
                moved.append(rec)
            else:
                rec["offset_units"] = offset_units(y)
                other.append(rec)
        res[prof] = {"claims": len(b), "moved": len(moved), "other": len(other),
                     "moved_by_doc": dict(collections.Counter(m["docID"] for m in moved)),
                     "moved_ids": [m["id"] for m in moved],
                     "moved_offset_units": dict(collections.Counter(
                         m["offset_units"] for m in moved)),
                     "other_rows": other}
    return res


def stage_diff(before_path, after_path):
    before = json.load(io.open(before_path, encoding="utf-8"))
    after = json.load(io.open(after_path, encoding="utf-8"))
    res = compare(before, after)
    for prof, r in res.items():
        print("[%s] 主張 %d / VALUE_MISMATCH->GROUNDED %d / それ以外の動き %d"
              % (prof, r["claims"], r["moved"], r["other"]))
        for o in r["other_rows"]:
            print("    奪った行 %s %s %s -> %s %s"
                  % (o["id"], o["before"]["form"], o["before"]["recomputed"],
                     o["after"]["form"], o["after"]["recomputed"]))
    out = {"purpose": "欠陥 A の候補の差分を使用済み 16 書類に当てた影響。合否ではなく観測",
           "candidate": "docs/DEFECT_A_PATCH_CANDIDATE_2026-10-14.patch",
           "docs": DOCS, "note": "未使用の封じた書類には当てていない", "result": res}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", OUT)
    return out


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "dump":
        stage_dump(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "diff":
        stage_diff(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("usage: dump <audit-core root> <out.json> | diff <base> <impl>")


if __name__ == "__main__":
    main()
