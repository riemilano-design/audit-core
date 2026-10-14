# -*- coding: utf-8 -*-
"""欠陥 A の修正を before / after で比べる(封 docs/DEFECT_A_EVAL_SEAL_2026-10-14.md §3)。

``dump`` は**この木の engine のまま**で 8 書類の主張を全部書き出す。
修正を当てた worktree で同じ段を走らせ、``diff`` で 2 つの書き出しを比べる。
**修正は共有の木にも feature 枝にも commit しない。**

比べるのは主張ごとの ``(result, pointer, recomputed, form)``。
  動いた行          ``VALUE_MISMATCH`` -> ``GROUNDED``(封の L_A)
  F-3 に数える行    それ以外の向きに動いた行(奪われた・緩んだ・逆行)

profile は既定(P20)と P16 の両方で出す(封 §3)。通信しない。
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

DRAW = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "draw_2026-10-14.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "before_after_2026-10-14.json")
PROFILES = ("P20", "P16")


def docs_list():
    return json.load(io.open(DRAW, encoding="utf-8"))["docs"]


def ptr(claim):
    p = claim.get("pointer")
    if p is None:
        return None
    return [p] if isinstance(p, str) else list(p)


def stage_dump(path):
    from adapters.xbrl import recipes as R, vocabulary as V, edinet, instance as I, extract as E
    out = {}
    for prof in PROFILES:
        rows = {}
        for d in docs_list():
            zb = io.open(edinet.cache_path(d), "rb").read()
            num, txt = R.build_raw_claims(zb, V.PROFILES[prof])
            inst = I.load_instance(zb)
            mdna = I.select_mdna(inst["textblocks"])
            sents = E.split_sentences(I.strip_html(inst["textblocks"][mdna]), V.PROFILES[prof].paren_sentence)
            for kind, claims in (("num", num), ("text", txt)):
                for c in claims:
                    rows["%s:%s" % (d, c["id"])] = {
                        "docID": d, "kind": kind, "result": c.get("result"),
                        "pointer": ptr(c), "recomputed": c.get("recomputed"),
                        "form": c.get("form"), "unit": c.get("unit"),
                        "value": c.get("value"), "claim_scale": c.get("claim_scale"),
                        "subject": c.get("subject"), "span": c.get("span"),
                        "sentence": sents[c["sentence"]] if c.get("sentence") is not None else None}
        out[prof] = rows
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("profiles %s / 行 %s -> %s" % (list(out), {k: len(v) for k, v in out.items()}, path))


def compare(before, after):
    """profile ごとに、動いた行とそれ以外の動きを分ける。"""
    res = {}
    for prof in before:
        b, a = before[prof], after[prof]
        if set(b) != set(a):
            raise AssertionError("%s: 主張の集合が違う(前 %d 後 %d)" % (prof, len(b), len(a)))
        moved, other = [], []
        for cid in sorted(b):
            x, y = b[cid], a[cid]
            same = (x["result"] == y["result"] and x["pointer"] == y["pointer"]
                    and x["recomputed"] == y["recomputed"] and x["form"] == y["form"])
            if same:
                continue
            rec = {"id": cid, "docID": x["docID"], "kind": x["kind"], "unit": x["unit"],
                   "value": x["value"], "claim_scale": x["claim_scale"], "span": x["span"],
                   "before": {k: x[k] for k in ("result", "pointer", "recomputed", "form")},
                   "after": {k: y[k] for k in ("result", "pointer", "recomputed", "form")}}
            if x["result"] == "VALUE_MISMATCH" and y["result"] == "GROUNDED":
                moved.append(rec)
            else:
                other.append(rec)
        res[prof] = {"moved": moved, "other": other,
                     "claims": len(b),
                     "L_A": len(moved), "F3": len(other)}
    return res


def stage_diff(before_path, after_path):
    before = json.load(io.open(before_path, encoding="utf-8"))
    after = json.load(io.open(after_path, encoding="utf-8"))
    res = compare(before, after)
    for prof, r in res.items():
        print("[%s] 主張 %d 件 / 動いた行 L_A = %d / それ以外の動き F-3 = %d"
              % (prof, r["claims"], r["L_A"], r["F3"]))
        kinds = collections.Counter((m["kind"], m["unit"]) for m in r["moved"])
        for k, n in sorted(kinds.items(), key=lambda kv: (str(kv[0]),)):
            print("    動いた行の内訳 %-6s %-5s %d" % (k[0], k[1], n))
        for o in r["other"]:
            print("    F-3: %s %s -> %s" % (o["id"], o["before"]["result"], o["after"]["result"]))
    out = {"purpose": "欠陥 A の修正の before/after(封 §3)。合否は結果文書に書く",
           "seal": "docs/DEFECT_A_EVAL_SEAL_2026-10-14.md",
           "docs": docs_list(), "result": res}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", OUT)
    return out


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "dump":
        stage_dump(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "diff":
        stage_diff(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("usage: dump <path> | diff <before> <after>")


if __name__ == "__main__":
    main()
