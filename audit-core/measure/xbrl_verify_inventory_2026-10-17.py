# -*- coding: utf-8 -*-
"""**棚卸し: 外から渡された参照先について、今の Core が機械的に証明できること。**

人間の指示(2026-10-17): 役割を替える(LLM が特定し、Core が実証する)。
**その前に、既存機能のうち何が機械的に証明でき、何がまだできないかを棚卸しする。**

**engine は 1 行も変えない。0 USD・席は呼ばない。**
**正解との照合はここではしない**(盲検比較は別の封。ここは「何が発火するか」だけ)。

## 2 つの部分

  第 1 部  **人工の探り**。値を同じにして属性を 1 つだけ変え、
           `audit_core.verify` が止めるか通すかを見る。
           **止めなければ「その属性は検査されていない」**という機械の証拠になる。
  第 2 部  **実物での発火**。凍結した席の答え(参照先)を Core の recipe に差し替えて
           `verify` を呼び、state と reason を**数える**(正解とは照合しない)。

    python3 measure/xbrl_verify_inventory_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
OUT = os.path.join(FX, "verify_inventory_2026-10-17.json")

import audit_core as core                                   # noqa: E402
from adapters.xbrl import instance as I                     # noqa: E402
from adapters.xbrl import prose as PR                        # noqa: E402
from adapters.xbrl import recipes as R                       # noqa: E402
from adapters.xbrl import registry_setup as RS               # noqa: E402
from adapters.xbrl import resolve as RV                      # noqa: E402
from adapters.xbrl import vocabulary as V                    # noqa: E402
from adapters.xbrl import edinet as ED                       # noqa: E402

_sp = importlib.util.spec_from_file_location(
    "pnf_diag_for_inv", os.path.join(HERE, "xbrl_pnf_diag_2026-10-17.py"))
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)
A1, MB, IJ = D.A1, D.MB, D.IJ
PROFILE = D.PROFILE


def probe(facts, pointer, claim_value, unit_scale=1.0, claim_scale=1.0):
    """**1 件だけの人工の検証。**Core の `verify` と resolver をそのまま使う。"""
    resolver = RV.make_resolver(facts)
    registry = RS.register_all(core.Registry.default())
    claim = core.Claim(id="X1", form=core.Form("direct_value"), subject=u"試し",
                       value=claim_value, unit=u"円",
                       modifiers=core.Modifiers(), provenance={})
    recipe = core.Recipe(
        claim=claim, pointers=(core.Pointer("xbrl", pointer),),
        contract=core.Contract(comparator="equals_within",
                               params={"unit_scale": unit_scale,
                                       "claim_scale": claim_scale}))
    res = core.verify(recipe, resolver, registry)
    ev = (res.provenance.get("resolved_pointers") or ({},))[0]
    return {u"state": res.state.name, u"reason": res.reason,
            u"recomputed": res.recomputed,
            u"meta": (ev.get("meta") if isinstance(ev, dict) else None)}


def part1():
    """**値を同じにして属性を 1 つだけ変える。**止めなければ検査されていない。"""
    base = {"name": "jppfs_cor:CurrentAssets", "context": "CurrentYearInstant",
            "value": 771000.0, "unit": "JPY", "decimals": "-3"}
    other_unit = dict(base, unit="USD")
    prior = dict(base, context="Prior1YearInstant")
    dim = dict(base, context="CurrentYearInstant_NonConsolidatedMember")
    dup = [dict(base), dict(base, value=999000.0)]
    cases = [
        {u"探り": u"0 **対照**: すべて一致", u"facts": [base],
         u"参照先": "jppfs_cor:CurrentAssets@CurrentYearInstant",
         u"値": 771000.0,
         u"**何を試しているか**": u"**探りの器が動いているか**(GROUNDED に"
                          u"ならなければ、下の 6 件は何も示さない)"},
        {u"探り": u"1 実在しない参照先", u"facts": [base],
         u"参照先": "jppfs_cor:NoSuchElement@CurrentYearInstant", u"値": 771000.0,
         u"**何を試しているか**": u"要素・context の実在"},
        {u"探り": u"2 値が違う", u"facts": [base],
         u"参照先": "jppfs_cor:CurrentAssets@CurrentYearInstant", u"値": 123456.0,
         u"**何を試しているか**": u"値の一致"},
        {u"探り": u"3 値は同じ・**単位が違う(USD)**", u"facts": [other_unit],
         u"参照先": "jppfs_cor:CurrentAssets@CurrentYearInstant", u"値": 771000.0,
         u"**何を試しているか**": u"fact の単位(`unitRef`)を見るか"},
        {u"探り": u"4 値は同じ・**期間が違う(前期)**", u"facts": [prior],
         u"参照先": "jppfs_cor:CurrentAssets@Prior1YearInstant", u"値": 771000.0,
         u"**何を試しているか**": u"context の期間を主張の期と照らすか"},
        {u"探り": u"5 値は同じ・**次元が違う(単体 member)**", u"facts": [dim],
         u"参照先":
             "jppfs_cor:CurrentAssets@CurrentYearInstant_NonConsolidatedMember",
         u"値": 771000.0,
         u"**何を試しているか**": u"連結区分・次元を見るか"},
        {u"探り": u"6 同じ鍵の fact が 2 件(値が違う)", u"facts": dup,
         u"参照先": "jppfs_cor:CurrentAssets@CurrentYearInstant", u"値": 771000.0,
         u"**何を試しているか**": u"重複を判定に使うか(meta には出る)"},
    ]
    out = []
    for c in cases:
        r = probe(c[u"facts"], c[u"参照先"], c[u"値"])
        out.append({u"探り": c[u"探り"],
                    u"**何を試しているか**": c[u"**何を試しているか**"],
                    u"参照先": c[u"参照先"], u"主張の値": c[u"値"],
                    u"fact": [{k: f[k] for k in ("name", "context", "value",
                                                 "unit")} for f in c[u"facts"]],
                    u"**結果**": r[u"state"], u"reason": r[u"reason"],
                    u"recomputed": r[u"recomputed"], u"meta": r[u"meta"],
                    u"**止めたか**": r[u"state"] != "GROUNDED"})
    return out


def part2():
    """**実物: 席が名指した参照先を Core の recipe に差し替えて verify を呼ぶ。**

    **正解とは照合しない。**state と reason を数えるだけ。
    """
    mat = json.load(io.open(os.path.join(FX, "material_2026-10-17.json"),
                            encoding="utf-8"))
    sc = json.load(io.open(os.path.join(FX, "score_2026-10-17.json"),
                           encoding="utf-8"))
    seat = {(r[u"doc"], r[u"id"]): r[u"席"] for r in sc[u"rows"]}
    prec = {p["docID"]: p for p in mat[u"書類ごと"]}
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"),
                             encoding="utf-8"))[u"引いた 8 件"]
    t = collections.Counter()
    rows = []
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows, _n = MB.build_rows(tampered, chosen, pl)
        zb2, _e, _mm = PR.build_modified_zip(zb, tampered)
        inst = I.load_instance(zb2)
        resolver = RV.make_resolver(inst["facts"])
        registry = RS.register_all(core.Registry.default())
        recipe_list = R.build_recipes(zb2, V.PROFILES[PROFILE])
        by_claim = {rp.claim.id: rp for rp in recipe_list}
        results = {r.claim_id: r for r in
                   core.verify_all(recipe_list, resolver, registry)}
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])):
                (f["name"], f["context"]) for f in inst["facts"]}
        for r in mrows:
            rid = r["id"]
            p = seat[(doc, rid)][u"参照先"]
            if p is None:
                t[u"席が名指さなかった行"] += 1
                continue
            t[u"席が名指した行"] += 1
            cid = None
            for rp in recipe_list:
                c = rp.claim
                if c.value is None:
                    continue
                span = (c.provenance or {}).get("span") or ""
                if abs(c.value - r[u"値"]) <= A1.TOL and r[u"数の字面"] in span:
                    cid = c.id
                    break
            if cid is None:
                t[u"**Core に主張が無い(検証できない)**"] += 1
                rows.append({u"doc": doc, u"id": rid, u"席の参照先": p,
                             u"**結果**": u"主張が無い"})
                continue
            rp = by_claim[cid]
            if rp.contract is None:
                t[u"**contract が無い(検証できない)**"] += 1
                rows.append({u"doc": doc, u"id": rid, u"席の参照先": p,
                             u"主張 id": cid, u"**結果**": u"contract が無い"})
                continue
            ev_ptrs = [x for x in rp.pointers if x.scheme == "xbrl"]
            if len(ev_ptrs) != 1:
                t[u"**contract が参照先 %d 本を要る(1 本渡しでは検証できない)**"
                  % len(ev_ptrs)] += 1
                rows.append({u"doc": doc, u"id": rid, u"席の参照先": p,
                             u"主張 id": cid,
                             u"comparator": rp.contract.comparator,
                             u"元の参照先の本数": len(ev_ptrs),
                             u"**結果**": u"参照先が 1 本では検証できない"})
                continue
            raw = keys.get(p)
            loc = ("%s@%s" % raw) if raw else p
            swapped = core.Recipe(claim=rp.claim,
                                  pointers=(core.Pointer("xbrl", loc),),
                                  contract=rp.contract)
            res = core.verify(swapped, resolver, registry)
            t[u"検証できた行"] += 1
            t[u"state " + res.state.name] += 1
            if res.state.name == "POINTER_NOT_FOUND":
                t[u"**席の参照先が instance に無い**"] += 1
            rows.append({u"doc": doc, u"id": rid, u"席の参照先": p,
                         u"主張 id": cid,
                         u"Core 自身の state": results[cid].state.name,
                         u"**差し替えた結果の state**": res.state.name,
                         u"reason": res.reason,
                         u"comparator": rp.contract.comparator,
                         u"recomputed": res.recomputed})
    return dict(t), rows


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    p1 = part1()
    ctrl = p1[0]
    if ctrl[u"**結果**"] != "GROUNDED":
        raise SystemExit(
            u"**対照が GROUNDED でない(%s)。探りの器が壊れている。止める**"
            % ctrl[u"**結果**"])
    t, rows = part2()
    ctrl_name = p1[0][u"探り"]
    checked = [c for c in p1[1:] if c[u"**止めたか**"]]
    passed = [c for c in p1[1:] if not c[u"**止めたか**"]]
    rec = {
        "step": u"**棚卸し。engine 不変・0 USD・席は呼ばない・正解と照合しない**",
        u"人間の指示": u"2026-10-17(役割を替える前に、何が機械的に証明できるかを棚卸しする)",
        u"**verify が見るもの(コードから)**": {
            u"file": "core/py/audit_core/verify.py",
            u"段": [u"1. `recipe.unverifiable_reason` が在れば UNVERIFIABLE",
                  u"2. `recipe.not_found_reason` が在れば POINTER_NOT_FOUND",
                  u"3. **各 pointer を resolver で解く。解けなければ "
                  u"POINTER_NOT_FOUND(`unresolved:…`)**",
                  u"4. **contract の comparator で比べる。合えば GROUNDED、"
                  u"合わなければ VALUE_MISMATCH**"],
            u"state は 4 つだけ": [s.name for s in core.State],
            u"**comparator が読む欄**": u"`evidence[0].value` と "
                              u"`contract.params`(`unit_scale`・`claim_scale`・"
                              u"`rounding` 等)。**`evidence[0].unit` は読まない**",
            u"linkbase": u"**読んでいない**(`calculation`/`presentation`/"
                        u"`definition` のリンクベースを読む場所が無い)"},
        u"**第 1 部 人工の探り**": p1,
        u"**第 1 部の読み**": {
            u"対照(GROUNDED になるべき探り)": {
                u"探り": ctrl_name, u"結果": p1[0][u"**結果**"],
                u"注": u"**対照は「通す」のが正しい。**下の 2 つの一覧から外してある"},
            u"止めた探り": [c[u"探り"] for c in checked],
            u"**通した探り(= その属性は検査されていない)**":
                [c[u"探り"] for c in passed]},
        u"**第 2 部 実物での発火**": {u"数": t, u"rows": rows},
        u"limits": [
            u"**これは棚卸しであり、精度の測定ではない。**正解とは照合していない",
            u"**第 1 部は人工の 1 件ずつである。**実物の分布を代表しない",
            u"**第 2 部は席が名指した参照先を差し替えただけ。**"
            u"どちらが正しいかはここでは判定しない(盲検比較は別の封)",
            u"**「できない」は今のコードについてである。**"
            u"材料(期間・次元・単位)は instance に在るので、"
            u"**検査を足せないという意味ではない**",
            u"**engine は 1 行も変えていない。**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 第 1 部 人工の探り(値を同じにして属性を 1 つ変える)===")
    for i, c in enumerate(p1):
        if i == 0:
            note = u"**対照(通すのが正しい)**"
        else:
            note = (u"**止めた**" if c[u"**止めたか**"]
                    else u"**通した(検査していない)**")
        print(u"  %-34s %-18s %s" % (c[u"探り"], c[u"**結果**"], note))
    print(u"=== 第 2 部 実物での発火(席の参照先を差し替えた)===")
    for k, v in sorted(t.items()):
        print(u"  %-36s %d" % (k, v))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
