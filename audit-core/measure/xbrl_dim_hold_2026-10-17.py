# -*- coding: utf-8 -*-
u"""封 `docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md`(commit `407dbcd`)の実測。

**(d) を当てて、曖昧な参照先を検査通過にせず保留にできるかを測る。**
**精度の改善を測るものではない**(危険な通過は既に 0/24。封 §6)。

**engine は 1 行も変えない。規則は封じた 1 つだけ。0 USD・席は呼ばない。**

    python3 measure/xbrl_dim_hold_2026-10-17.py
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
OUT = os.path.join(FX, "dim_hold_2026-10-17.json")
SEAL = "docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md"


def _load(name, mod):
    sp = importlib.util.spec_from_file_location(mod, os.path.join(HERE, name))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


H = _load("xbrl_dim_hold_rule_2026-10-17.py", "hold_rule")
AT = _load("xbrl_attr_inject_2026-10-17.py", "attr_for_hold")
DM = _load("xbrl_dim_diag_2026-10-17.py", "diag_for_hold")
VE, A1, MB, IJ, PR, I, ED = AT.VE, AT.A1, AT.MB, AT.IJ, AT.PR, AT.I, AT.ED
RSW = _load("xbrl_role_swap_2026-10-17.py", "swap_for_hold")
compose = RSW.compose
PASS = RSW.PASS


def tol_of(unit):
    u"""比較器が梯子に渡す幅(`claim_scale` = `UNIT_SCALE[単位]`)。

    **新しい閾値を作らない**(封 §9)。`attr_inject` の露出と同じ数。
    """
    return abs(VE.V.UNIT_SCALE.get(unit, 1)) or 1


def comparator_accepts(g, claim_value, unit):
    u"""**別の数え方**(封との食い違い 2): 比較器が `g` も受けるか。

    主役の欄ではない。`measure/` の中でだけ使い、**別の欄として記録する。**
    """
    scale = VE.V.UNIT_SCALE.get(unit)
    if scale is None or g.get("value") is None:
        return False
    from adapters.xbrl import comparators as C
    return C._match_value(g["value"], claim_value * scale, scale) is not None


def verdict_word(v):
    u"""判定の語を**1 か所で決める**(`True` / `None` / `False`)。

    **`None` は未測定である。偽として外れに数えない** ―
    2026-10-19 の再実行の印字でこれを踏んだ(記録と文書は正しく、印字だけが
    `None` を偽として「外れ」と書いていた)。語を 2 か所に書いたのが原因なので、
    **所有する 1 か所に寄せる**(記憶 `pin-each-property-in-one-owner`)。
    """
    if v is True:
        return u"**当たり**"
    if v is None:
        return u"**未測定**"
    if v is False:
        return u"**外れ**"
    # **三値以外は受けない。**真偽値として緩めると、`1` や `"x"` が
    # 静かに「当たり」になる(変異がそれで黙った。2026-10-19)
    raise ValueError(u"判定は True / False / None のどれかである: %r" % (v,))


def rate(num, den):
    return {u"分子": num, u"分母": den,
            u"率": (round(100.0 * num / den, 1) if den else None)}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    swap = json.load(io.open(os.path.join(FX, "role_swap_2026-10-17.json"),
                             encoding="utf-8"))
    b_by = {(x[u"doc"], x[u"id"]): x for x in swap["rows"]}
    score = {(x["doc"], x["id"]): x for x in json.load(
        io.open(os.path.join(FX, "score_2026-10-17.json"),
                encoding="utf-8"))["rows"]}
    v1 = json.load(io.open(os.path.join(FX, "contract_v1_2026-10-17.json"),
                           encoding="utf-8"))
    v1_by = {(x[u"doc"], x[u"id"]): x for x in v1["rows"]}
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"),
                             encoding="utf-8"))[u"引いた 8 件"]

    rows, ctrl, expo = [], collections.Counter(), collections.defaultdict(list)
    gold_axes = collections.Counter()
    before_state, after_state = collections.Counter(), collections.Counter()
    pointer_changed = 0
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
        ax = DM.axes_of_instance(zb2)
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f
                for f in facts}
        for r in mrows:
            b = b_by[(doc, r["id"])]
            sc = score[(doc, r["id"])]
            seat_word, ptr = b[u"A(席の判定)"], b[u"席の参照先"]
            unit, val = r[u"単位"], r[u"値"]
            tol = tol_of(unit)
            rec = {u"doc": doc, u"id": r["id"], u"注入か": b[u"注入か"],
                   u"単位": unit, u"値": val, u"席の参照先": ptr}

            # --- 第 2 部 露出の帯(**状態を変えない**。参照先の fact 自身の値で)
            for name, p in ((u"D2 席が名指した 85 行", ptr),
                            (u"D4 正解(T5)の参照先 50 件",
                             (sc[u"正解"] or {}).get(u"正解"))):
                if not p:
                    continue
                f = keys.get(A1.norm_pointer(p))
                if f is None:
                    expo[name + u"/解けない"].append((doc, r["id"]))
                    continue
                sibs = H.siblings(facts, f, tol)
                if sibs:
                    expo[name].append((doc, r["id"]))
                    if name.startswith("D4"):
                        for a, _mm2 in ax.get(sibs[0]["context"], []):
                            gold_axes[a] += 1
                if name.startswith("D2") and not b[u"注入か"]:
                    (expo[u"D3 無改変で名指した 42 行"].append((doc, r["id"]))
                     if sibs else None)
                    expo[u"D3 分母"].append((doc, r["id"]))

            # --- 第 1 部 規則の適用(**状態が変わりうるのは GROUNDED だけ**)
            if ptr is None:
                rec.update({u"v1 の state": None,
                            u"**(d) の後**": None,
                            u"**B′ の最終判定(前)**": v1_by[(doc, r["id"])]
                            [u"**B′ の最終判定**"]})
                rec[u"**最終判定(後)**"] = rec[u"**B′ の最終判定(前)**"]
                rows.append(rec)
                continue
            f = keys.get(A1.norm_pointer(ptr))
            loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
            out = VE.verify_external({"kind": "single_value", "value": val,
                                      "unit": unit, "pointers": [loc]}, facts)
            before_state[out["state"]] += 1
            new, sibs = H.apply_hold(out, f, facts, tol)
            after_state[new["state"]] += 1
            if tuple(new["pointers"]) != tuple(out["pointers"]):
                pointer_changed += 1
            why = new["reason"] if new["state"] == VE.UNPROVABLE else None
            final = (compose(seat_word, None, why) if why
                     else compose(seat_word, new["state"], None))
            rec.update({
                u"v1 の state": out["state"],
                u"**(d) の後**": new["state"],
                u"**発火**": bool(sibs),
                u"兄弟の件数": len(sibs),
                u"理由": new.get("reason"),
                u"**B′ の最終判定(前)**": v1_by[(doc, r["id"])]
                [u"**B′ の最終判定**"],
                u"**最終判定(後)**": final})
            if sibs:
                rec[u"**比較器も受ける兄弟(別の数え方)**"] = sum(
                    1 for g in sibs if comparator_accepts(g, val, unit))

            # --- 対照(**故障を作って当てる**。封 §7 の D-10・D-11)
            if out["state"] == H.GROUNDED and not sibs:
                for branch, label in ((u"期間(注入)", u"C-期間"),
                                      (u"単位", u"C-単位"),
                                      (u"次元", u"C-次元(陽性対照)")):
                    fs, key, bad = AT.inject(facts, f, branch)
                    if key is None:
                        ctrl[(label, u"作れなかった")] += 1
                        continue
                    o2 = VE.verify_external(
                        {"kind": "single_value", "value": val, "unit": unit,
                         "pointers": [loc]}, fs)
                    _n2, s2 = H.apply_hold(o2, f, fs, tol)
                    ctrl[(label, u"試せた")] += 1
                    ctrl[(label, u"**発火**")] += bool(s2)
            rows.append(rec)

    fired = [x for x in rows if x.get(u"**発火**")]
    pass_before = [x for x in rows if x[u"**B′ の最終判定(前)**"] == PASS]
    pass_after = [x for x in rows if x[u"**最終判定(後)**"] == PASS]
    d = json.load(io.open(os.path.join(FX, "dim_diag_2026-10-17.json"),
                          encoding="utf-8"))
    diag6 = [(x[u"doc"], x[u"id"]) for x in d["rows"]]
    nc18 = [(x[u"doc"], x[u"id"]) for x in d[u"**候補規則 (b) が当たった行**"]]
    #: 個別の枠を指した 18 行(診断の帯)。名指しが無いので doc/id は
    #: **その場で引き直す**(診断の記録は件数だけを持つ)
    nc_fired = [x for x in fired
                if u"nonconsolidatedmember" in (x[u"席の参照先"] or u"")]
    d2 = len(expo[u"D2 席が名指した 85 行"])
    d3 = len(expo[u"D3 無改変で名指した 42 行"])
    d4 = len(expo[u"D4 正解(T5)の参照先 50 件"])
    gold_total = sum(1 for k in score.values()
                     if (k[u"正解"] or {}).get(u"正解"))
    eq_axes = sum(v for k, v in gold_axes.items()
                  if k.split(":")[-1] in ("ComponentsOfEquityAxis",
                                          "OperatingSegmentsAxis"))
    pred = [
        {u"記号": "D-1", u"予測": u"D1 24 行での発火 = 6 行",
         u"実測": len(fired), u"当たり": len(fired) == 6},
        {u"記号": "D-2", u"予測": u"発火した行が診断の 6 行と字で一致",
         u"実測": u"一致" if sorted((x[u"doc"], x[u"id"]) for x in fired)
         == sorted(diag6) else u"不一致",
         u"当たり": sorted((x[u"doc"], x[u"id"]) for x in fired)
         == sorted(diag6)},
        {u"記号": "D-3", u"予測": u"検査通過 24 → 18",
         u"実測": u"%d → %d" % (len(pass_before), len(pass_after)),
         u"当たり": (len(pass_before), len(pass_after)) == (24, 18)},
        {u"記号": "D-4", u"予測": u"個別の枠を指した 18 行は 0 件発火",
         u"実測": len(nc_fired), u"当たり": len(nc_fired) == 0},
        {u"記号": "D-5", u"予測": u"D2 85 行の露出 = 10〜30(点 18)",
         u"実測": d2, u"当たり": 10 <= d2 <= 30},
        {u"記号": "D-6", u"予測": u"D3 42 行の露出 = 6〜16(点 8)",
         u"実測": d3, u"当たり": 6 <= d3 <= 16},
        {u"記号": "D-7", u"予測": u"D4 50 件の露出 = 4〜16(点 9)",
         u"実測": d4, u"当たり": 4 <= d4 <= 16},
        {u"記号": "D-8", u"予測": u"誤拒否(不一致)の増加 = 0 件",
         u"実測": after_state["VALUE_MISMATCH"] - before_state["VALUE_MISMATCH"],
         u"当たり": (after_state["VALUE_MISMATCH"]
                 == before_state["VALUE_MISMATCH"])},
        {u"記号": "D-9", u"予測": u"危険な通過 R-1 = 0 → 0(精度の改善 0 件)",
         u"実測": sum(1 for x in pass_after if x[u"注入か"]),
         u"当たり": sum(1 for x in pass_after if x[u"注入か"]) == 0},
        {u"記号": "D-10", u"予測": u"期間だけ違う同額の兄弟で発火 0 件",
         u"実測": ctrl[(u"C-期間", u"**発火**")],
         u"当たり": ctrl[(u"C-期間", u"**発火**")] == 0},
        {u"記号": "D-11", u"予測": u"単位だけ違う同額の兄弟で発火 0 件",
         u"実測": ctrl[(u"C-単位", u"**発火**")],
         u"当たり": ctrl[(u"C-単位", u"**発火**")] == 0},
        {u"記号": "D-12", u"予測": u"VALUE_MISMATCH と POINTER_NOT_FOUND は記録と同じ",
         u"実測": u"不一致 %d(記録 %d)/ PNF %d(記録 %d)"
         % (after_state["VALUE_MISMATCH"],
            sum(1 for x in v1["rows"] if x[u"v1 の state"] == "VALUE_MISMATCH"),
            after_state["POINTER_NOT_FOUND"],
            v1[u"POINTER_NOT_FOUND(別に数える)"][u"件数"]),
         u"当たり": (after_state["VALUE_MISMATCH"]
                 == sum(1 for x in v1["rows"]
                        if x[u"v1 の state"] == "VALUE_MISMATCH")
                 and after_state["POINTER_NOT_FOUND"]
                 == v1[u"POINTER_NOT_FOUND(別に数える)"][u"件数"])},
        {u"記号": "D-13", u"予測": u"渡した以外の参照先が現れた件数 = 0 件",
         u"実測": pointer_changed, u"当たり": pointer_changed == 0},
        #: **D-14 は D-7 が 1 件以上であることを前提にした予測である。**
        #: D-7 が 0 件なら**予測の対象が存在しない** ― 当たりにも外れにも数えず
        #: **未測定**として残す(記憶 `zero-needs-a-measured-cause`)。
        {u"記号": "D-14", u"予測": u"D-7 で露出した正解の軸は過半が株主資本かセグメント",
         u"実測": u"%d / %d" % (eq_axes, sum(gold_axes.values())),
         u"当たり": (None if sum(gold_axes.values()) == 0
                 else eq_axes * 2 > sum(gold_axes.values())),
         u"注": u"**未測定**(D-7 が 0 件で、予測の対象が存在しない)"
         if sum(gold_axes.values()) == 0 else None},
    ]
    hit = sum(1 for p in pred if p[u"当たり"] is True)
    unmeasured = sum(1 for p in pred if p[u"当たり"] is None)
    rec = {
        "seal": SEAL,
        "step": u"**(d) の限定実装の実測。engine 不変・規則は封じた 1 つ・0 USD**",
        u"**第 1 部 規則の適用**": {
            u"状態(前)": dict(before_state), u"状態(後)": dict(after_state),
            u"**発火**": rate(len(fired), len(pass_before)),
            u"**検査通過**": {u"前": len(pass_before), u"後": len(pass_after)},
            u"**発火した行**": [{u"doc": x[u"doc"], u"id": x[u"id"],
                           u"兄弟の件数": x[u"兄弟の件数"],
                           u"理由": x[u"理由"],
                           u"**比較器も受ける兄弟(別の数え方)**":
                               x.get(u"**比較器も受ける兄弟(別の数え方)**")}
                          for x in fired]},
        u"**対照(故障を作って当てる)**": {
            k[0] + "/" + k[1]: v for k, v in sorted(ctrl.items())},
        u"**第 2 部 露出の帯(状態は変えない)**": {
            u"D2 席が名指した 85 行": rate(d2, sum(
                1 for k in b_by.values() if k[u"席の参照先"])),
            u"D3 無改変で名指した 42 行": rate(d3, len(expo[u"D3 分母"])),
            u"D4 正解(T5)の参照先 50 件": rate(d4, gold_total),
            u"**D4 で露出した正解の軸**": dict(gold_axes),
            u"**参照先が解けなかった件数**": {
                k: len(v) for k, v in sorted(expo.items())
                if k.endswith(u"/解けない")} or {u"0 件": 0}},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit,
                      u"外れ": len(pred) - hit - unmeasured,
                      u"**未測定**": unmeasured},
        u"rows": rows,
        u"limits": [
            u"**発火した行が誤った参照先だったとは言えない**(封 §8 の 1)。"
            u"無改変の行で、機械で固定された正解が無い",
            u"**この規則は精度を上げない。**危険な通過は前も後も 0 件",
            u"**保留は誤りの指摘ではない。**検査通過が減ったことを改善に数えない",
            u"**要素そのものを取り違える問題(T5)は残る。**この規則は要素が同一の"
            u"曖昧さしか見ない",
            u"**軸情報の保持((e))は入っていない。**別の変更として切り分けた",
            u"**engine を 1 行も変えていない。**規則は封じた 1 つだけ",
            u"**同じ 8 書類である。**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== (d) の実測。engine 不変・0 USD ===")
    print(u"状態(前) %s" % json.dumps(dict(before_state), ensure_ascii=False))
    print(u"状態(後) %s" % json.dumps(dict(after_state), ensure_ascii=False))
    print(u"**検査通過 %d → %d**(発火 %d 行)"
          % (len(pass_before), len(pass_after), len(fired)))
    print(u"--- 対照 ---")
    for k, v in sorted(ctrl.items()):
        print(u"  %-16s %-10s %d" % (k[0], k[1], v))
    print(u"--- 第 2 部 露出の帯 ---")
    for k, v in rec[u"**第 2 部 露出の帯(状態は変えない)**"].items():
        print(u"  %-26s %s" % (k, json.dumps(v, ensure_ascii=False)))
    print(u"--- 予測との照合 ---")
    for p in pred:
        print(u"  %-5s %-42s 実測 %-26s %s"
              % (p[u"記号"], p[u"予測"], p[u"実測"],
                 verdict_word(p[u"当たり"])))
    print(u"  当たり %d / 外れ %d / 未測定 %d"
          % (hit, len(pred) - hit - unmeasured, unmeasured))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
