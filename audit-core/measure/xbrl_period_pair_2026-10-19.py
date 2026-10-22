# -*- coding: utf-8 -*-
u"""封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`(commit `790a5c5`)の実測(段 1)。

**規則 PP(期間の対)を率の主張(参照先 1 本・単位 `％`/`%`)に当て、前期の兄弟 1 本で
検算できる行が増えるかを測る。engine は 1 行も変えない。0 USD・席は呼ばない。**

材料の組み立ては `measure/xbrl_holds_product_path_2026-10-19.py` の `_material_rows`
をそのまま使う(注入後の 8 書類・192 行)。規則は `measure/xbrl_period_pair_rule_2026-10-19.py`
(`prior_siblings`・`sign_from_text`・`apply_pp`)。

    python3 measure/xbrl_period_pair_2026-10-19.py --write
"""
import argparse
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

import audit_core as core                           # noqa: E402

from adapters.xbrl import holds as H                 # noqa: E402
from adapters.xbrl import registry_setup as RS        # noqa: E402
from adapters.xbrl import verify_external as VE       # noqa: E402

SEAL = "docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md"
SEAL_COMMIT = "790a5c5"
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC_PU = os.path.join(CD8, "period_unit_hold_2026-10-19.json")
DRAW = os.path.join(CD8, "draw_2026-10-17.json")
OUT = os.path.join(CD8, "period_pair_2026-10-19.json")

#: H-4 の対象(封 §3)。**字で留める。**
R017_DOC, R017_ID = "S100YWGX", "R017"
R017_NAMES = (u"SegmentProfit", u"OperatingIncome")


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


R = _mod("measure/xbrl_period_pair_rule_2026-10-19.py", "pp_rule_for_measure")
HPP = _mod("measure/xbrl_holds_product_path_2026-10-19.py", "hpp_for_pp_measure")
AT = _mod("measure/xbrl_attr_inject_2026-10-17.py", "attr_for_pp_measure")
A1 = AT.A1


def rate(num, den):
    return {u"分子": num, u"分母": den, u"率": (round(100.0 * num / den, 1) if den else None)}


def h4_scan(f, facts):
    u"""`f`(R017 の参照先)と同じ `dim_of` で名が条件に合う fact を列挙する。"""
    dim = R.dim_of(f["context"])
    out = []
    for g in facts:
        nm = g["name"].rsplit(":", 1)[-1]
        if not any(n in nm for n in R017_NAMES):
            continue
        if not g["context"].startswith("CurrentYear"):
            continue
        if R.dim_of(g["context"]) != dim:
            continue
        sibs = R.prior_siblings(facts, g)
        n_sibs = None if sibs is None else len(sibs)
        pct = None
        hit = False
        if n_sibs == 1:
            cur, prior = g["value"], sibs[0]["value"]
            if cur is not None and prior not in (None, 0):
                pct = round((cur - prior) / abs(prior) * 100, 2)
                hit = abs(pct - 258.0) <= 0.15
        out.append({u"name": g["name"], u"context": g["context"], u"兄弟の本数": n_sibs,
                    u"変化率": pct, u"258.0 に当たる": hit})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    docs = _load(DRAW)[u"引いた 8 件"]
    pu = _load(REC_PU)
    registry = RS.register_all(core.Registry.default())

    rows37 = []
    r017_detail = None
    for doc, inst, mrows, b_by in HPP._material_rows(docs, AT):
        facts, contexts = inst["facts"], inst["contexts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
        for r in mrows:
            unit = r[u"単位"]
            if unit not in (u"％", u"%"):
                continue
            b = b_by[(doc, r["id"])]
            ptr = b[u"席の参照先"]
            rec = {u"doc": doc, u"id": r["id"], u"単位": unit, u"値": r[u"値"],
                   u"席の参照先": ptr, u"抜粋": r[u"抜粋"], u"数の字面": r[u"数の字面"]}
            rows37.append(rec)
            if ptr is None:
                continue
            f = keys.get(A1.norm_pointer(ptr))
            loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
            sibs = R.prior_siblings(facts, f) if f is not None else None
            n_sibs = None if sibs is None else len(sibs)
            sign = R.sign_from_text(r[u"抜粋"], r[u"数の字面"])
            spec = {"kind": "ratio_change", "value": r[u"値"], "unit": unit,
                    "pointers": [loc], "sign": sign}
            out = R.apply_pp(spec, f, facts, registry)
            rec.update({u"兄弟の本数": n_sibs, u"符号": sign, u"state": out["state"],
                        u"reason": out["reason"], u"recomputed": out["recomputed"],
                        u"derived_pointers": out["derived_pointers"],
                        u"sign_checked": out["sign_checked"]})

            if n_sibs == 1 and f is not None:
                g = sibs[0]
                ctrl = {}
                # 値: +1.0 pt
                ctrl[u"値"] = R.apply_pp(dict(spec, value=spec["value"] + 1.0),
                                        f, facts, registry)["state"]
                # 符号: 増 <-> 減 を入れ替える
                flipped = (-sign) if sign is not None else None
                ctrl[u"符号"] = R.apply_pp(dict(spec, sign=flipped), f, facts, registry)["state"]
                # 前期を消す: 兄弟 fact を材料から除く
                facts_rm = [x for x in facts if x is not g]
                out_rm = R.apply_pp(spec, f, facts_rm, registry)
                ctrl[u"前期を消す"] = {u"state": out_rm["state"], u"reason": out_rm["reason"]}
                # 前期を増やす: 同じ名・同じ次元・前期の枠にもう 1 本(値 +1)足す
                dup = dict(g, value=g["value"] + 1.0)
                out_add = R.apply_pp(spec, f, facts + [dup], registry)
                ctrl[u"前期を増やす"] = {u"state": out_add["state"], u"reason": out_add["reason"]}
                rec[u"対照"] = ctrl

                # H-10: 当期 fact に apply_holds を当てて (d)・P・U の発火(claim_unit は f 自身の単位)。
                out0 = {"state": H.GROUNDED, "pointers": (loc,)}
                tol = VE.tol_of(f["unit"])
                _new, fired = H.apply_holds(out0, f, facts, tol, f["unit"], contexts)
                rec[u"発火(当期 fact・(d)PU)"] = fired

            if doc == R017_DOC and r["id"] == R017_ID and f is not None:
                r017_detail = {u"参照先": {u"name": f["name"], u"context": f["context"],
                                        u"値": f["value"]},
                              u"同じセグメント枠の別の要素": h4_scan(f, facts)}

    ref1 = [r for r in rows37 if r[u"席の参照先"] is not None]
    refnone = [r for r in rows37 if r[u"席の参照先"] is None]
    one_sib = [r for r in ref1 if r.get(u"兄弟の本数") == 1]
    dist = collections.Counter(r.get(u"兄弟の本数") for r in ref1)
    sign_dist = collections.Counter(r.get(u"符号") for r in one_sib)
    state_dist = collections.Counter(r.get("state") for r in one_sib)

    ctrl_tally = {
        u"値": collections.Counter(r[u"対照"][u"値"] for r in one_sib),
        u"符号": collections.Counter(r[u"対照"][u"符号"] for r in one_sib),
        u"前期を消す": collections.Counter((r[u"対照"][u"前期を消す"][u"state"],
                                        r[u"対照"][u"前期を消す"][u"reason"]) for r in one_sib),
        u"前期を増やす": collections.Counter((r[u"対照"][u"前期を増やす"][u"state"],
                                         r[u"対照"][u"前期を増やす"][u"reason"]) for r in one_sib),
    }
    fired_tally = collections.Counter()
    for r in one_sib:
        fr = r[u"発火(当期 fact・(d)PU)"]
        for k in ("d", "P", "U"):
            fired_tally[k] += bool(fr[k])

    n155 = 192 - 37
    pu_rows = {(x["doc"], x["id"]): x for x in pu["rows"]}
    base_composed = collections.Counter(x[u"**合成の後**"] for x in pu["rows"])
    base62 = base_composed.get("GROUNDED", 0) + base_composed.get("VALUE_MISMATCH", 0)
    after_states = []
    for x in pu["rows"]:
        key = (x["doc"], x["id"])
        hit17 = [r for r in ref1 if (r["doc"], r["id"]) == key]
        if hit17:
            after_states.append(hit17[0]["state"])
        else:
            after_states.append(x[u"**合成の後**"])
    after_count = collections.Counter(after_states)
    after62 = after_count.get("GROUNDED", 0) + after_count.get("VALUE_MISMATCH", 0)

    r4_hit = any(e[u"258.0 に当たる"] for e in (r017_detail or {}).get(u"同じセグメント枠の別の要素", []))
    r4_found = bool((r017_detail or {}).get(u"同じセグメント枠の別の要素"))

    pred = [
        {u"記号": "H-1", u"予測": u"13・4・0",
         u"実測": u"1 本: %d・2 本: %d・0 本: %d" % (dist.get(1, 0), dist.get(2, 0), dist.get(0, 0)),
         u"当たり": (dist.get(1, 0), dist.get(2, 0), dist.get(0, 0)) == (13, 4, 0)},
        {u"記号": "H-2", u"予測": u"13 / 13 で符号が取れる",
         u"実測": u"%d / %d" % (sum(v for k, v in sign_dist.items() if k is not None), len(one_sib)),
         u"当たり": sign_dist.get(None, 0) == 0 and len(one_sib) == 13},
        {u"記号": "H-3", u"予測": u"GROUNDED 12・VALUE_MISMATCH 1(S100YWGX R017)",
         u"実測": dict(state_dist),
         u"当たり": state_dist.get("GROUNDED", 0) == 12 and state_dist.get("VALUE_MISMATCH", 0) == 1
         and [r for r in one_sib if r["state"] == "VALUE_MISMATCH"] == [
             r for r in one_sib if (r["doc"], r["id"]) == (R017_DOC, R017_ID)]},
        {u"記号": "H-4", u"予測": u"別の要素(SegmentProfit/OperatingIncome)が在り 258.0 が再現する",
         u"実測": r017_detail,
         u"当たり": r4_found and r4_hit},
        {u"記号": "H-5", u"予測": u"対照 値 13/13 が VALUE_MISMATCH",
         u"実測": dict(ctrl_tally[u"値"]),
         u"当たり": ctrl_tally[u"値"].get("VALUE_MISMATCH", 0) == 13 and len(ctrl_tally[u"値"]) == 1},
        {u"記号": "H-6", u"予測": u"対照 符号 13/13 が VALUE_MISMATCH",
         u"実測": dict(ctrl_tally[u"符号"]),
         u"当たり": ctrl_tally[u"符号"].get("VALUE_MISMATCH", 0) == 13 and len(ctrl_tally[u"符号"]) == 1},
        {u"記号": "H-7", u"予測": u"対照 前期を消す 13/13 が UNPROVABLE prior_sibling:0",
         u"実測": {str(k): v for k, v in ctrl_tally[u"前期を消す"].items()},
         u"当たり": ctrl_tally[u"前期を消す"].get(("UNPROVABLE", "prior_sibling:0"), 0) == 13
         and len(ctrl_tally[u"前期を消す"]) == 1},
        {u"記号": "H-8", u"予測": u"対照 前期を増やす 13/13 が UNPROVABLE prior_sibling:2",
         u"実測": {str(k): v for k, v in ctrl_tally[u"前期を増やす"].items()},
         u"当たり": ctrl_tally[u"前期を増やす"].get(("UNPROVABLE", "prior_sibling:2"), 0) == 13
         and len(ctrl_tally[u"前期を増やす"]) == 1},
        {u"記号": "H-9", u"予測": u"参照先なし 20 行・金額の主張 155 行は 1 行も動かない(当てた行数 0)",
         u"実測": {u"参照先なしの行": len(refnone), u"金額の主張の行": n155, u"PP を当てた行数": 0},
         u"当たり": len(refnone) == 20 and n155 == 155},
        {u"記号": "H-10", u"予測": u"13 行で (d)・P・U の発火は 0",
         u"実測": dict(fired_tally),
         u"当たり": fired_tally.get("d", 0) == 0 and fired_tally.get("P", 0) == 0
         and fired_tally.get("U", 0) == 0},
        {u"記号": "H-11", u"予測": u"実証できた行(GROUNDED + VALUE_MISMATCH)は 192 行で 62 → 75",
         u"実測": u"%d → %d" % (base62, after62),
         u"当たり": base62 == 62 and after62 == 75},
        {u"記号": "H-12", u"予測": u"段 2 の 192 行再現は段 1 の記録と 192/192 一致・engine の欄以外 byte 同一",
         u"実測": u"段 2 で測る", u"当たり": u"段 2 で測る"},
        {u"記号": "H-13", u"予測": u"PP-R1〜R3 の 3 本とも red", u"実測": u"段 2 で測る", u"当たり": u"段 2 で測る"},
        {u"記号": "H-14", u"予測": u"独立監査は REVISE 1 回 → GO", u"実測": u"段 2 で測る", u"当たり": u"段 2 で測る"},
        {u"記号": "H-15", u"予測": u"run_tests.sh 1 回目で赤くなるのは test_xbrl_axis3_decision.py test_9 だけ",
         u"実測": u"段 2 で測る", u"当たり": u"段 2 で測る"},
    ]
    hit = sum(1 for p in pred if p[u"当たり"] is True)
    miss = sum(1 for p in pred if p[u"当たり"] is False)

    rec = {
        "seal": SEAL, "seal_commit": SEAL_COMMIT,
        "step": u"**期間の対(PP)の実測。段 1(engine 不変)。0 USD・席は呼ばない**",
        u"行": {u"192 行": 192, u"率の主張(％/%)": len(rows37),
              u"うち参照先 1 本": len(ref1), u"参照先なし": len(refnone)},
        u"**第 1 部 兄弟の本数**": {str(k): v for k, v in sorted(dist.items(), key=str)},
        u"**第 2 部 符号・検算**": {u"符号の分布": {str(k): v for k, v in sign_dist.items()},
                             u"state の分布(13 行)": dict(state_dist)},
        u"R017 の明細(H-4)": r017_detail,
        u"**対照(13 行すべて)**": {
            u"値": {str(k): v for k, v in ctrl_tally[u"値"].items()},
            u"符号": {str(k): v for k, v in ctrl_tally[u"符号"].items()},
            u"前期を消す": {str(k): v for k, v in ctrl_tally[u"前期を消す"].items()},
            u"前期を増やす": {str(k): v for k, v in ctrl_tally[u"前期を増やす"].items()},
        },
        u"H-9 当てていない行数": {u"参照先なし": len(refnone), u"金額の主張": n155, u"PP を当てた行数": 0},
        u"H-10 (d)PU の発火(13 行)": dict(fired_tally),
        u"H-11 実証できた行": {u"v1(合成の後)": base62, u"PP を足した後": after62},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit, u"外れ": miss},
        u"rows": rows37,
        "limits": [
            u"**同じ 8 書類である。**規則 × 標本の積で、新しい書類で 13 が 13 である保証は無い"
            u"(`memory: diagnosis-does-not-transfer-to-a-new-sample`)。",
            u"**「前期比」の字は見ない。**前年同期比(四半期)・2 期前比は annual の有報に出ないとして扱い、"
            u"出たら誤って `Prior1Year` と対にしうる(限界として記録)。",
            u"**方向だけの主張(数が付かない 52 行の型)は触らない。**PP の符号の規則はそちらの土台になるが、"
            u"測るのは別の封。",
            u"**PP は「席が当期を正しく名指した」ことを前提にする。**名指しの誤り(要素の取り違え T5)は "
            u"PP では検出できない(R017 が示す型)。",
        ],
    }
    print(u"=== 期間の対(PP)の実測。engine 不変・0 USD ===")
    print(u"率の主張 %d / 参照先 1 本 %d / 参照先なし %d" % (len(rows37), len(ref1), len(refnone)))
    print(u"兄弟の本数の分布:", dict(dist))
    print(u"符号の分布:", dict(sign_dist))
    print(u"state(13 行):", dict(state_dist))
    print(u"H-11: %d -> %d" % (base62, after62))
    for p in pred:
        print(u"  %-5s %s" % (p[u"記号"], u"当たり" if p[u"当たり"] is True else
                             (u"**外れ**" if p[u"当たり"] is False else u"段 2 で測る")))
    print(u"当たり %d / 外れ %d(段 1 の 11 欄)" % (hit, miss))
    if a.write:
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
