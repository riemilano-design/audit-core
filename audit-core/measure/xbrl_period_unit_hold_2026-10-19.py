# -*- coding: utf-8 -*-
u"""封 `docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md`(commit `f78c775`)の実測。

**規則 P(同額の期間兄弟)・U(単位の種類)を (d) と合成して、注入した穴を通さなくなるか、
正しい参照先を何件保留にするか(代価)を測る。精度の改善は測らない。**

材料の組み立て・対照・露出の数え方は (d) の `xbrl_dim_hold_2026-10-17.py` と同じ
(そこから `tol_of`・`compose`・`PASS`・`verdict_word`・`rate` を import)。

**engine は 1 行も変えない。0 USD・席は呼ばない。**

    python3 measure/xbrl_period_unit_hold_2026-10-19.py
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
OUT = os.path.join(FX, "period_unit_hold_2026-10-19.json")
SEAL = "docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md"


def _load(name, mod):
    sp = importlib.util.spec_from_file_location(mod, os.path.join(HERE, name))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


DH = _load("xbrl_dim_hold_2026-10-17.py", "dim_hold_measure_for_pu")
R = _load("xbrl_period_unit_hold_rule_2026-10-19.py", "pu_rule_for_measure")
H, AT = DH.H, DH.AT
VE, A1, MB, IJ, PR, I, ED = AT.VE, AT.A1, AT.MB, AT.IJ, AT.PR, AT.I, AT.ED
tol_of, compose, PASS, verdict_word, rate = (DH.tol_of, DH.compose, DH.PASS,
                                             DH.verdict_word, DH.rate)


def spec_of(val, unit, loc):
    return {"kind": "single_value", "value": val, "unit": unit, "pointers": [loc]}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    swap = json.load(io.open(os.path.join(FX, "role_swap_2026-10-17.json"), encoding="utf-8"))
    b_by = {(x[u"doc"], x[u"id"]): x for x in swap["rows"]}
    score = {(x["doc"], x["id"]): x for x in json.load(
        io.open(os.path.join(FX, "score_2026-10-17.json"), encoding="utf-8"))["rows"]}
    v1 = json.load(io.open(os.path.join(FX, "contract_v1_2026-10-17.json"), encoding="utf-8"))
    v1_by = {(x[u"doc"], x[u"id"]): x for x in v1["rows"]}
    dh = json.load(io.open(os.path.join(FX, "dim_hold_2026-10-17.json"), encoding="utf-8"))
    dh_by = {(x[u"doc"], x[u"id"]): x for x in dh["rows"]}
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"), encoding="utf-8"))[u"引いた 8 件"]

    rows = []
    ctrl = collections.Counter()
    expo = collections.defaultdict(list)
    before_state, after_state = collections.Counter(), collections.Counter()
    fired = {"d": [], "P": [], "U": []}
    pointer_changed = 0
    d_same_as_record = True
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
        facts = I.load_instance(zb2)["facts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
        for r in mrows:
            b = b_by[(doc, r["id"])]
            sc = score[(doc, r["id"])]
            seat_word, ptr = b[u"A(席の判定)"], b[u"席の参照先"]
            unit, val = r[u"単位"], r[u"値"]
            tol = tol_of(unit)
            rec = {u"doc": doc, u"id": r["id"], u"注入か": b[u"注入か"],
                   u"単位": unit, u"値": val, u"席の参照先": ptr}

            # --- 第 2 部 露出(**状態を変えない**。参照先の fact 自身で)
            for name, p in ((u"D2 席が名指した 85 行", ptr),
                            (u"D4 正解(T5)の参照先 50 件", (sc[u"正解"] or {}).get(u"正解"))):
                if not p:
                    continue
                f = keys.get(A1.norm_pointer(p))
                if f is None:
                    expo[name + u"/解けない"].append((doc, r["id"]))
                    continue
                psibs = R.period_siblings(facts, f, tol)
                umis, cc, fc = R.unit_mismatch(unit, f)
                if psibs:
                    expo[name + u"/P"].append((doc, r["id"]))
                if umis:
                    expo[name + u"/U"].append((doc, r["id"], cc, fc))
                if name.startswith("D2") and not b[u"注入か"]:
                    expo[u"D3 分母"].append((doc, r["id"]))
                    if psibs:
                        expo[u"D3 無改変で名指した 42 行/P"].append((doc, r["id"]))
                    if umis:
                        expo[u"D3 無改変で名指した 42 行/U"].append((doc, r["id"]))

            # --- 第 1 部 規則の適用(GROUNDED だけが動く)
            if ptr is None:
                rec.update({u"v1 の state": None, u"**合成の後**": None,
                            u"**B′ の最終判定(前)**": v1_by[(doc, r["id"])][u"**B′ の最終判定**"]})
                rec[u"**最終判定(後)**"] = rec[u"**B′ の最終判定(前)**"]
                rows.append(rec)
                continue
            f = keys.get(A1.norm_pointer(ptr))
            loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
            out = VE.verify_external(spec_of(val, unit, loc), facts)
            before_state[out["state"]] += 1
            new, fr = R.apply_all(out, f, facts, tol, unit)
            after_state[new["state"]] += 1
            if tuple(new["pointers"]) != tuple(out["pointers"]):
                pointer_changed += 1
            for k in fr:
                if fr[k]:
                    fired[k].append((doc, r["id"]))
            # (d) の発火が 10-17 の記録と同じか(規則を壊していないか)
            if dh_by[(doc, r["id"])].get(u"**発火**", False) != fr["d"]:
                d_same_as_record = False
            why = new["reason"] if new["state"] == VE.UNPROVABLE else None
            final = compose(seat_word, None, why) if why else compose(seat_word, new["state"], None)
            rec.update({u"v1 の state": out["state"], u"**合成の後**": new["state"],
                        u"発火": fr, u"理由": new.get("reason"),
                        u"**B′ の最終判定(前)**": v1_by[(doc, r["id"])][u"**B′ の最終判定**"],
                        u"**最終判定(後)**": final})

            # --- 対照(**故障を作って当てる**。1 回に 1 件。GROUNDED の 24 行すべて)
            if out["state"] == H.GROUNDED:
                for branch, label, point_at_injected in (
                        (u"期間(注入)", u"C-期間(注入)", False),
                        (u"単位", u"C-単位", True),
                        (u"次元", u"C-次元", False)):
                    fs, key, bad = AT.inject(facts, f, branch)
                    if key is None:
                        ctrl[(label, u"作れなかった")] += 1
                        continue
                    ctrl[(label, u"作れた")] += 1
                    if point_at_injected:
                        f2 = [g for g in fs if "%s@%s" % (g["name"], g["context"]) == key][0]
                        o2 = VE.verify_external(spec_of(val, unit, key), fs)
                    else:
                        f2 = f
                        o2 = VE.verify_external(spec_of(val, unit, loc), fs)
                    ctrl[(label, u"v1 が通した")] += (o2["state"] == H.GROUNDED)
                    _n2, fr2 = R.apply_all(o2, f2, fs, tol, unit)
                    for k in fr2:
                        ctrl[(label, u"**発火 %s**" % k)] += bool(fr2[k])
            rows.append(rec)

    pass_before = [x for x in rows if x[u"**B′ の最終判定(前)**"] == PASS]
    pass_after = [x for x in rows if x[u"**最終判定(後)**"] == PASS]
    n85 = sum(1 for k in b_by.values() if k[u"席の参照先"])
    gold_total = sum(1 for k in score.values() if (k[u"正解"] or {}).get(u"正解"))
    d2p, d3p, d4p = (len(expo[u"D2 席が名指した 85 行/P"]), len(expo[u"D3 無改変で名指した 42 行/P"]),
                     len(expo[u"D4 正解(T5)の参照先 50 件/P"]))
    d2u, d4u = len(expo[u"D2 席が名指した 85 行/U"]), len(expo[u"D4 正解(T5)の参照先 50 件/U"])
    vm_rec = sum(1 for x in v1["rows"] if x[u"v1 の state"] == "VALUE_MISMATCH")
    pnf_rec = v1[u"POINTER_NOT_FOUND(別に数える)"][u"件数"]
    c = lambda label, k: ctrl[(label, k)]
    pred = [
        {u"記号": "E-1", u"予測": u"P の発火(D1 24)= 0", u"実測": len(fired["P"]), u"当たり": len(fired["P"]) == 0},
        {u"記号": "E-2", u"予測": u"U の発火(D1 24)= 0", u"実測": len(fired["U"]), u"当たり": len(fired["U"]) == 0},
        {u"記号": "E-3", u"予測": u"合成の検査通過 24 → 18", u"実測": u"%d → %d" % (len(pass_before), len(pass_after)),
         u"当たり": (len(pass_before), len(pass_after)) == (24, 18)},
        {u"記号": "E-4", u"予測": u"VALUE_MISMATCH 44 → 44・PNF 0 → 0",
         u"実測": u"VM %d → %d / PNF %d → %d" % (before_state["VALUE_MISMATCH"], after_state["VALUE_MISMATCH"],
                                                before_state["POINTER_NOT_FOUND"], after_state["POINTER_NOT_FOUND"]),
         u"当たり": (before_state["VALUE_MISMATCH"], after_state["VALUE_MISMATCH"],
                 before_state["POINTER_NOT_FOUND"], after_state["POINTER_NOT_FOUND"]) == (44, 44, 0, 0)},
        {u"記号": "E-5", u"予測": u"渡した以外の参照先 0", u"実測": pointer_changed, u"当たり": pointer_changed == 0},
        {u"記号": "E-6", u"予測": u"期間(注入): 作れた 18・作れなかった 6・P 18/18・U 0・(d) 0",
         u"実測": u"作れた %d / 作れなかった %d / P %d / U %d / d %d" % (
             c(u"C-期間(注入)", u"作れた"), c(u"C-期間(注入)", u"作れなかった"), c(u"C-期間(注入)", u"**発火 P**"),
             c(u"C-期間(注入)", u"**発火 U**"), c(u"C-期間(注入)", u"**発火 d**")),
         u"当たり": (c(u"C-期間(注入)", u"作れた"), c(u"C-期間(注入)", u"作れなかった"), c(u"C-期間(注入)", u"**発火 P**"),
                 c(u"C-期間(注入)", u"**発火 U**"), c(u"C-期間(注入)", u"**発火 d**")) == (18, 6, 18, 0, 0)},
        {u"記号": "E-7", u"予測": u"単位: 作れた 24・U 24/24・P 0・(d) 0",
         u"実測": u"作れた %d / U %d / P %d / d %d" % (c(u"C-単位", u"作れた"), c(u"C-単位", u"**発火 U**"),
                                                 c(u"C-単位", u"**発火 P**"), c(u"C-単位", u"**発火 d**")),
         u"当たり": (c(u"C-単位", u"作れた"), c(u"C-単位", u"**発火 U**"), c(u"C-単位", u"**発火 P**"),
                 c(u"C-単位", u"**発火 d**")) == (24, 24, 0, 0)},
        {u"記号": "E-8", u"予測": u"次元: 作れた 24・P 0・U 0((d) 24)",
         u"実測": u"作れた %d / P %d / U %d / d %d" % (c(u"C-次元", u"作れた"), c(u"C-次元", u"**発火 P**"),
                                                 c(u"C-次元", u"**発火 U**"), c(u"C-次元", u"**発火 d**")),
         u"当たり": (c(u"C-次元", u"作れた"), c(u"C-次元", u"**発火 P**"), c(u"C-次元", u"**発火 U**")) == (24, 0, 0)},
        {u"記号": "E-9", u"予測": u"D2 85 の P の露出 0〜4", u"実測": d2p, u"当たり": 0 <= d2p <= 4},
        {u"記号": "E-10", u"予測": u"D3 42 の P の露出 0〜2", u"実測": d3p, u"当たり": 0 <= d3p <= 2},
        {u"記号": "E-11", u"予測": u"D4 50 の P の露出 0〜3", u"実測": d4p, u"当たり": 0 <= d4p <= 3},
        {u"記号": "E-12", u"予測": u"D2 85 で単位の種類が違う 0〜8", u"実測": d2u, u"当たり": 0 <= d2u <= 8},
        {u"記号": "E-13", u"予測": u"D4 50 で単位の種類が違う 0", u"実測": d4u, u"当たり": d4u == 0},
        {u"記号": "E-14", u"予測": u"誤拒否の増加 0・危険な通過 0 → 0",
         u"実測": u"VM 増 %d / 危険な通過 %d" % (after_state["VALUE_MISMATCH"] - before_state["VALUE_MISMATCH"],
                                             sum(1 for x in pass_after if x[u"注入か"])),
         u"当たり": after_state["VALUE_MISMATCH"] == before_state["VALUE_MISMATCH"]
         and sum(1 for x in pass_after if x[u"注入か"]) == 0},
    ]
    hit = sum(1 for p in pred if p[u"当たり"] is True)
    rec = {
        "seal": SEAL,
        "step": u"**P・U の限定実装の実測。engine 不変・規則は封じた 2 つ + (d)・0 USD**",
        u"**第 1 部 規則の適用**": {
            u"状態(前)": dict(before_state), u"状態(後)": dict(after_state),
            u"**検査通過**": {u"前": len(pass_before), u"後": len(pass_after)},
            u"**発火(規則ごと)**": {k: [{"doc": d, "id": i} for d, i in v] for k, v in fired.items()},
            u"**(d) の発火が 10-17 の記録と同じ**": d_same_as_record,
            u"記録の VALUE_MISMATCH / PNF": {"VM": vm_rec, "PNF": pnf_rec}},
        u"**対照(故障を作って当てる。GROUNDED の 24 行)**": {k[0] + "/" + k[1]: v for k, v in sorted(ctrl.items())},
        u"**第 2 部 露出の帯(状態は変えない)**": {
            u"D2 席が名指した 85 行/P": rate(d2p, n85),
            u"D2 席が名指した 85 行/U": rate(d2u, n85),
            u"D2 の U の明細": [{"doc": d, "id": i, "claim": cc, "fact": fc}
                             for d, i, cc, fc in expo[u"D2 席が名指した 85 行/U"]],
            u"D3 無改変で名指した 42 行/P": rate(d3p, len(expo[u"D3 分母"])),
            u"D3 無改変で名指した 42 行/U": rate(len(expo[u"D3 無改変で名指した 42 行/U"]), len(expo[u"D3 分母"])),
            u"D4 正解(T5)の参照先 50 件/P": rate(d4p, gold_total),
            u"D4 正解(T5)の参照先 50 件/U": rate(d4u, gold_total),
            u"**参照先が解けなかった件数**": {k: len(v) for k, v in sorted(expo.items()) if k.endswith(u"/解けない")} or {u"0 件": 0}},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit, u"外れ": len(pred) - hit},
        u"rows": rows,
        u"limits": [
            u"**精度は上がらない。**危険な通過は前も後も 0 件",
            u"**P は実データで発火していない(予測どおりなら)。**価値は注入の穴に対してだけ",
            u"**U は単位の種類しか見ない。**百万円と千円の取り違えは値の照合の仕事",
            u"**engine を 1 行も変えていない。**規則は封じた 2 つ + (d)",
            u"**同じ 8 書類である。**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(u"=== P・U の実測。engine 不変・0 USD ===")
    print(u"状態(前) %s" % json.dumps(dict(before_state), ensure_ascii=False))
    print(u"状態(後) %s" % json.dumps(dict(after_state), ensure_ascii=False))
    print(u"**検査通過 %d → %d**  発火 d %d / P %d / U %d  (d) 記録と同じ: %s"
          % (len(pass_before), len(pass_after), len(fired["d"]), len(fired["P"]), len(fired["U"]), d_same_as_record))
    print(u"--- 対照 ---")
    for k, v in sorted(ctrl.items()):
        print(u"  %-14s %-12s %d" % (k[0], k[1], v))
    print(u"--- 露出 ---")
    for k, v in rec[u"**第 2 部 露出の帯(状態は変えない)**"].items():
        print(u"  %-30s %s" % (k, json.dumps(v, ensure_ascii=False)[:200]))
    print(u"--- 予測 ---")
    for p in pred:
        print(u"  %-5s %s  %s  (実測 %s)" % (p[u"記号"], verdict_word(p[u"当たり"]), p[u"予測"], p[u"実測"]))
    print(u"当たり %d / 外れ %d" % (hit, len(pred) - hit))
    print("->", OUT)


if __name__ == "__main__":
    main()
