# -*- coding: utf-8 -*-
"""封 `docs/XBRL_P20_SEAL_2026-10-17.md` の実測。**profile を P16 → P20 にするだけ。**

**engine のコードは 1 行も変えない。席は呼ばない。0 USD。**
**判定は既に commit した予測** (`fixtures/xbrl/cd8/branch_a_predictions_2026-10-17.json`)
**との照合**で、予測の file は読むだけ(編集しない)。

止める条件(封 §4)はこの script の中で `SystemExit` にしてある。

    python3 measure/xbrl_p20_rerun_2026-10-17.py
"""
import collections
import hashlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
OUT = os.path.join(FX, "p20_rerun_2026-10-17.json")
SEAL = "docs/XBRL_P20_SEAL_2026-10-17.md"
PRED = os.path.join(FX, "branch_a_predictions_2026-10-17.json")

_sp = importlib.util.spec_from_file_location(
    "pnf_diag_for_p20", os.path.join(HERE, "xbrl_pnf_diag_2026-10-17.py"))
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)
A1, MB, IJ, ED, VD, V = D.A1, D.MB, D.IJ, D.ED, D.VD, D.V
OLD, NEW = "P16", "P20"


def claim_of(row, claims):
    """**材料の作り手と同じ対応付け**(直さない。数えるだけ)。"""
    for c in claims:
        if c.get("value") is None:
            continue
        if (abs(c["value"] - row[u"値"]) <= A1.TOL
                and row[u"数の字面"] in (c.get("span") or "")):
            return c["id"]
    return None


def says(claim):
    """**(ア) の関数をそのまま使う。**止めても pointer を読む側が「Core」。"""
    return {"Core": A1.core_pointer_say(claim),
            u"Core(厳しい読み方)": A1.core_say(claim)}


def rate(num, den):
    return {u"分子": num, u"分母": den,
            u"率": (round(100.0 * num / den, 1) if den else None)}


def one_variable_check():
    import dataclasses
    a = dataclasses.asdict(V.PROFILES[OLD])
    b = dataclasses.asdict(V.PROFILES[NEW])
    diff = sorted(k for k in a if a[k] != b[k])
    if diff != ["name", "nonconsolidated_fallback"]:
        raise SystemExit(u"**1 変数でない: %s。止める**(封 §4 の 2)" % diff)
    return diff


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    diff = one_variable_check()
    mat = json.load(io.open(os.path.join(FX, "material_2026-10-17.json"),
                            encoding="utf-8"))
    sc = json.load(io.open(os.path.join(FX, "score_2026-10-17.json"),
                           encoding="utf-8"))
    pred = json.load(io.open(PRED, encoding="utf-8"))
    pnf = json.load(io.open(os.path.join(FX, "pnf_diag_2026-10-17.json"),
                            encoding="utf-8"))
    pnf_rows = {(r[u"doc"], r[u"id"]) for r in pnf["rows"]}
    seat = {(r[u"doc"], r[u"id"]): r[u"席"] for r in sc[u"rows"]}
    prec = {p["docID"]: p for p in mat[u"書類ごと"]}
    pre = {}
    for d, p in prec.items():
        for rid, v in p[u"席の前に出せる分"].items():
            pre[(d, rid)] = v
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"),
                             encoding="utf-8"))[u"引いた 8 件"]

    rows, per_doc = [], {}
    t = collections.Counter()
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old_tmp, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old_tmp
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows, _n = MB.build_rows(tampered, chosen, pl)
        task = MB.seat_text(mrows, tampered, refs)
        if (hashlib.sha256(task.encode("utf-8")).hexdigest()
                != prec[doc][u"材料"]["sha256"]):
            raise SystemExit(u"**材料が封の記録と違う: %s。止める**(封 §4 の 3)" % doc)

        out16 = VD.verify_document(zb, OLD, tampered)
        out20 = VD.verify_document(zb, NEW, tampered)
        c16 = {c["id"]: c for c in out16["claims"]}
        c20 = {c["id"]: c for c in out20["claims"]}
        moved = sorted(set(c16) | set(c20))
        changed = [cid for cid in moved
                   if (c16.get(cid) or {}).get("state")
                   != (c20.get(cid) or {}).get("state")
                   or (c16.get(cid) or {}).get("pointers")
                   != (c20.get(cid) or {}).get("pointers")]
        fallback = prec[doc].get(u"**fallback の条件**")
        per_doc[doc] = {
            u"主張(P16)": len(c16), u"主張(P20)": len(c20),
            u"**state か pointers が動いた主張**": len(changed),
            u"動いた主張の id": changed[:20],
            u"明細": [{u"id": cid,
                     "P16": {u"state": c16[cid]["state"],
                             u"pointers": c16[cid]["pointers"]},
                     "P20": {u"state": c20[cid]["state"],
                             u"pointers": c20[cid]["pointers"]}}
                    for cid in changed]}

        for r in mrows:
            rid = r["id"]
            cid16 = claim_of(r, out16["claims"])
            cid20 = claim_of(r, out20["claims"])
            s16 = says(c16.get(cid16))
            s20 = says(c20.get(cid20))
            # **P16 の再現が材料の記録と一致すること**(封 §4 の 1)
            rec16 = pre[(doc, rid)]["Core"]
            if (s16["Core"][u"参照先"] != rec16[u"参照先"]
                    or s16["Core"][u"言うこと"] != rec16[u"言うこと"]):
                raise SystemExit(
                    u"**P16 の再現が材料の記録と違う: %s %s / 記録 %s / 再現 %s。"
                    u"止める**(封 §4 の 1)"
                    % (doc, rid, rec16, s16["Core"]))
            g = pre[(doc, rid)][u"正解"]
            mult16 = None
            rows.append({u"doc": doc, u"id": rid,
                         u"主張 id(P16)": cid16, u"主張 id(P20)": cid20,
                         u"正解": g,
                         u"席の参照先": seat[(doc, rid)][u"参照先"],
                         "P16": s16["Core"], "P20": s20["Core"],
                         u"**10 行の 1 つ**": (doc, rid) in pnf_rows})

    # ---- 行ごとの対応の多重度(1 対 1 の分母)。P16 の対応で数える ----
    mult = collections.Counter((r[u"doc"], r[u"主張 id(P16)"]) for r in rows
                               if r[u"主張 id(P16)"])
    for r in rows:
        key = (r[u"doc"], r[u"主張 id(P16)"])
        r[u"1 対 1"] = bool(r[u"主張 id(P16)"]) and mult[key] == 1

    def t5(r):
        g = r[u"正解"]
        return bool(g) and g.get(u"種類") == u"参照先が在る"

    for r in rows:
        if not t5(r):
            continue
        gold = r[u"正解"][u"正解"]
        t[u"T5"] += 1
        t[u"T5(1 対 1)"] += r[u"1 対 1"]
        for k in ("P16", "P20"):
            hit = r[k][u"参照先"] == gold
            t[u"特定 " + k] += hit
            if r[u"1 対 1"]:
                t[u"特定(1 対 1) " + k] += hit
            if r[k][u"参照先"] is not None and not hit:
                t[u"名指して正解でない " + k] += 1
            if r[k][u"参照先"] is not None:
                t[u"名指した " + k] += 1
        if r[u"席の参照先"] is not None and r[u"席の参照先"] != gold:
            t[u"席が外した行"] += 1
            for k in ("P16", "P20"):
                t[u"そこで Core が正解を持つ " + k] += (r[k][u"参照先"] == gold)

    ten = [r for r in rows if r[u"**10 行の 1 つ**"]]
    pnf_state = {k: sum(1 for r in ten
                        if (r[k][u"state"] == "POINTER_NOT_FOUND"))
                 for k in ("P16", "P20")}
    six = [d for d in docs if d not in ("S100YZ7E", "S100YZEV")]
    six_moved = {d: per_doc[d][u"**state か pointers が動いた主張**"] for d in six}

    # ---- 予測との照合(**予測は読むだけ**) ----
    n = pred[u"数の予測"]
    checks = [
        {u"欄": u"M-1 10 行の POINTER_NOT_FOUND",
         u"予測": n[u"10 行の POINTER_NOT_FOUND"][u"**P20 の予測**"],
         u"実測": pnf_state["P20"],
         u"当たり": pnf_state["P20"] == n[u"10 行の POINTER_NOT_FOUND"][u"**P20 の予測**"]},
        {u"欄": u"M-2 特定(T5 全部の行)",
         u"予測": n[u"Core 自身の特定(T5 全部の行)"][u"**P20 の予測**"],
         u"実測": "%d/%d" % (t[u"特定 P20"], t[u"T5"]),
         u"当たり": ("%d/%d" % (t[u"特定 P20"], t[u"T5"])
                 == n[u"Core 自身の特定(T5 全部の行)"][u"**P20 の予測**"])},
        {u"欄": u"M-2 特定(1 対 1 の行だけ)",
         u"予測": n[u"Core 自身の特定(1 対 1 の行だけ)"][u"**P20 の予測**"],
         u"実測": "%d/%d" % (t[u"特定(1 対 1) P20"], t[u"T5(1 対 1)"]),
         u"当たり": ("%d/%d" % (t[u"特定(1 対 1) P20"], t[u"T5(1 対 1)"])
                 == n[u"Core 自身の特定(1 対 1 の行だけ)"][u"**P20 の予測**"])},
        {u"欄": u"M-3 名指して正解でない行(P16 より何行増えたか)",
         u"予測": u"7 行増える",
         u"実測": u"%d 行増えた(%d → %d)"
               % (t[u"名指して正解でない P20"] - t[u"名指して正解でない P16"],
                  t[u"名指して正解でない P16"], t[u"名指して正解でない P20"]),
         u"当たり": (t[u"名指して正解でない P20"]
                 - t[u"名指して正解でない P16"]) == 7},
        {u"欄": u"M-4 連結ありの 6 書類が不変",
         u"予測": u"24 行すべて不変(1 行でも動けば外れ)",
         u"実測": six_moved,
         u"当たり": all(v == 0 for v in six_moved.values())},
        {u"欄": u"M-5 α の天井",
         u"予測": n[u"**α の天井(席が外した 7 行で Core が正解を持つ)**"][u"**P20 の予測**"],
         u"実測": "%d/%d" % (t[u"そこで Core が正解を持つ P20"], t[u"席が外した行"]),
         u"当たり": t[u"そこで Core が正解を持つ P20"] == 0},
    ]
    # 主張ごとの予測(参照先が正解か / 正解でないか)
    per_claim = []
    for x in pred[u"主張ごとの予測(10 行 = 6 主張)"]:
        want_gold = x[u"予測する参照先"].startswith(u"正解")
        for rid in x[u"行"]:
            r = next(y for y in rows
                     if y[u"doc"] == x["doc"] and y[u"id"] == rid)
            gold = r[u"正解"][u"正解"]
            got_gold = r["P20"][u"参照先"] == gold
            per_claim.append({
                u"doc": x["doc"], u"主張 id": x[u"主張 id"], u"行": rid,
                u"予測": (u"正解" if want_gold else u"正解ではない"),
                u"実測の参照先": r["P20"][u"参照先"],
                u"実測の state": r["P20"][u"state"],
                u"正解": gold,
                u"当たり": got_gold == want_gold})
    hit = sum(1 for c in checks if c[u"当たり"])
    chit = sum(1 for c in per_claim if c[u"当たり"])

    rec = {"seal": SEAL, "step": u"**封の実測。profile だけ P16 → P20。0 USD・席なし**",
           u"**1 変数の確認**": {u"profile の差": diff,
                         u"注": u"`name` と `nonconsolidated_fallback` だけ"},
           u"**P16 の再現**": u"**8 書類 192 行すべてで材料の記録と一致**(違えば止めた)",
           u"数": dict(t),
           u"M-1 10 行の state": {u"POINTER_NOT_FOUND の数": pnf_state,
                             u"明細": [{u"doc": r[u"doc"], u"id": r[u"id"],
                                      "P16": r["P16"], "P20": r["P20"],
                                      u"正解": r[u"正解"][u"正解"]}
                                     for r in ten]},
           u"M-2 特定": {u"全部の行": {"P16": rate(t[u"特定 P16"], t[u"T5"]),
                                 "P20": rate(t[u"特定 P20"], t[u"T5"])},
                      u"1 対 1 の行だけ": {
                          "P16": rate(t[u"特定(1 対 1) P16"], t[u"T5(1 対 1)"]),
                          "P20": rate(t[u"特定(1 対 1) P20"], t[u"T5(1 対 1)"])}},
           u"M-3 名指して正解でない行": {
               "P16": rate(t[u"名指して正解でない P16"], t[u"名指した P16"]),
               "P20": rate(t[u"名指して正解でない P20"], t[u"名指した P20"])},
           u"M-4 6 書類の動き": six_moved,
           u"M-5 α の天井": {"P16": "%d/%d" % (t[u"そこで Core が正解を持つ P16"],
                                           t[u"席が外した行"]),
                         "P20": "%d/%d" % (t[u"そこで Core が正解を持つ P20"],
                                           t[u"席が外した行"])},
           u"M-6 2 書類の動き": {d: per_doc[d] for d in ("S100YZ7E", "S100YZEV")},
           u"書類ごと": per_doc,
           u"**予測との照合**": {u"欄ごと": checks,
                        u"当たり": hit, u"外れ": len(checks) - hit,
                        u"主張ごと": per_claim,
                        u"主張ごとの当たり": chit,
                        u"主張ごとの外れ": len(per_claim) - chit,
                        u"注": u"**予測の file は読むだけ。編集していない**"},
           u"rows": rows,
           u"limits": [
               u"**原因仮説の検証であり、性能の証明ではない**(封 §0)",
               u"**A 対 C′ はこの封では測っていない。**席の答えは使っていない"
               u"(席が外した行を数えるためだけに読んだ)",
               u"**特定が増えても誤認定が同時に増えるなら、良くなったとは書かない**",
               u"**器の欠陥は残っている。**行 → 主張 は 1 対 1 でないので率は 2 つ並べた",
               u"**fallback の条件は変えていない。**変えるかどうかは人間が決める",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== P20 の実測(profile だけ替えた。0 USD)===")
    print(u"1 変数の確認: %s" % diff)
    print(u"M-1 10 行の POINTER_NOT_FOUND: P16 %d → **P20 %d**"
          % (pnf_state["P16"], pnf_state["P20"]))
    print(u"M-2 特定(全部の行): P16 %d/%d → **P20 %d/%d**"
          % (t[u"特定 P16"], t[u"T5"], t[u"特定 P20"], t[u"T5"]))
    print(u"M-2 特定(1 対 1):   P16 %d/%d → **P20 %d/%d**"
          % (t[u"特定(1 対 1) P16"], t[u"T5(1 対 1)"],
             t[u"特定(1 対 1) P20"], t[u"T5(1 対 1)"]))
    print(u"M-3 名指して正解でない行: P16 %d → **P20 %d**(名指した行 %d → %d)"
          % (t[u"名指して正解でない P16"], t[u"名指して正解でない P20"],
             t[u"名指した P16"], t[u"名指した P20"]))
    print(u"M-4 連結ありの 6 書類で動いた主張: %s" % six_moved)
    print(u"M-5 α の天井: P16 %d/%d → **P20 %d/%d**"
          % (t[u"そこで Core が正解を持つ P16"], t[u"席が外した行"],
             t[u"そこで Core が正解を持つ P20"], t[u"席が外した行"]))
    print(u"--- 予測との照合 ---")
    for c in checks:
        print(u"  %-44s 予測 %-30s 実測 %-30s %s"
              % (c[u"欄"], c[u"予測"], c[u"実測"],
                 u"**当たり**" if c[u"当たり"] else u"**外れ**"))
    print(u"  欄: 当たり %d / 外れ %d" % (hit, len(checks) - hit))
    print(u"  主張ごと(10 行): 当たり %d / 外れ %d" % (chit, len(per_claim) - chit))
    for c in per_claim:
        print(u"    %s %s %-6s 予測 %-8s 実測 %s"
              % (c["doc"], c[u"行"], c[u"主張 id"], c[u"予測"],
                 (c[u"実測の参照先"] or u"名指さない")[:46]))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
