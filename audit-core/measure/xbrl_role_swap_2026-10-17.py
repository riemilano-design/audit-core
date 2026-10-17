# -*- coding: utf-8 -*-
"""封 `docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md` の実測。**A / B / C を同じ行で比べる。**

**engine は 1 行も変えない。0 USD・席は呼ばない**(凍結した答えを読む)。
**contract を足さない。正解で調整しない。**

  A = 席の答えそのまま
  B = 席の参照先を Core の recipe に差し替えて `audit_core.verify`(**上書きしない**)
  C = 封じた注入記録での独立監査

    python3 measure/xbrl_role_swap_2026-10-17.py
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
OUT = os.path.join(FX, "role_swap_2026-10-17.json")
SEAL = "docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md"
UNCHECKED = (u"単位", u"期間", u"次元(連結区分)", u"重複")

import audit_core as core                                   # noqa: E402
from adapters.xbrl import instance as I                     # noqa: E402
from adapters.xbrl import prose as PR                        # noqa: E402
from adapters.xbrl import recipes as R                       # noqa: E402
from adapters.xbrl import registry_setup as RS               # noqa: E402
from adapters.xbrl import resolve as RV                      # noqa: E402
from adapters.xbrl import vocabulary as V                    # noqa: E402
from adapters.xbrl import edinet as ED                       # noqa: E402

_sp = importlib.util.spec_from_file_location(
    "inv_for_swap", os.path.join(HERE, "xbrl_verify_inventory_2026-10-17.py"))
INV = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(INV)
A1, MB, IJ, PROFILE = INV.A1, INV.MB, INV.IJ, INV.PROFILE

PASS, MISMATCH, ERR, UNPROVABLE = (u"検査通過", u"不一致", u"誤りが在る", u"実証不能")


def compose(seat_word, core_state, why):
    """**封 §1 の合成規則。字のとおり 1 か所で。席の申告は上書きしない。**"""
    if seat_word == u"誤りが在る":
        return ERR
    if seat_word == u"判定できない":
        return UNPROVABLE
    if seat_word != u"確認済み":
        return UNPROVABLE                      # 欠け
    if why is not None:
        return UNPROVABLE                      # 検証できない
    if core_state == "GROUNDED":
        return PASS
    if core_state == "VALUE_MISMATCH":
        return MISMATCH
    return UNPROVABLE                          # POINTER_NOT_FOUND 等


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    mat = json.load(io.open(os.path.join(FX, "material_2026-10-17.json"),
                            encoding="utf-8"))
    sc = json.load(io.open(os.path.join(FX, "score_2026-10-17.json"),
                           encoding="utf-8"))
    seat = {(r[u"doc"], r[u"id"]): r[u"席"] for r in sc[u"rows"]}
    pre = {}
    for p in mat[u"書類ごと"]:
        for rid, v in p[u"席の前に出せる分"].items():
            pre[(p["docID"], rid)] = v
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"),
                             encoding="utf-8"))[u"引いた 8 件"]

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
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])):
                (f["name"], f["context"]) for f in inst["facts"]}
        for r in mrows:
            rid = r["id"]
            key = (doc, rid)
            s = seat[key]
            g = pre[key][u"正解"]
            injected = bool(pre[key][u"注入か"])
            core_state, why, cid, comparator = None, None, None, None
            if s[u"参照先"] is None:
                why = u"参照先を名指していない"
            else:
                for rp in recipe_list:
                    c = rp.claim
                    if c.value is None:
                        continue
                    span = (c.provenance or {}).get("span") or ""
                    if (abs(c.value - r[u"値"]) <= A1.TOL
                            and r[u"数の字面"] in span):
                        cid = c.id
                        break
                if cid is None:
                    why = u"主張が無い"
                else:
                    rp = by_claim[cid]
                    if rp.contract is None:
                        why = u"contract が無い"
                    else:
                        ev = [x for x in rp.pointers if x.scheme == "xbrl"]
                        if len(ev) != 1:
                            why = u"参照先が 2 本要る"
                        else:
                            raw = keys.get(s[u"参照先"])
                            loc = ("%s@%s" % raw) if raw else s[u"参照先"]
                            res = core.verify(
                                core.Recipe(claim=rp.claim,
                                            pointers=(core.Pointer("xbrl", loc),),
                                            contract=rp.contract),
                                resolver, registry)
                            core_state = res.state.name
                            comparator = rp.contract.comparator
            rows.append({
                u"doc": doc, u"id": rid, u"注入か": injected,
                u"正解": (g or {}).get(u"正解"),
                u"A(席の判定)": s[u"判定"], u"席の参照先": s[u"参照先"],
                u"Core の結果": core_state, u"検証できない理由": why,
                u"comparator": comparator, u"主張 id": cid,
                u"**B の最終判定**": compose(s[u"判定"], core_state, why),
                u"**未検査属性**": list(UNCHECKED)})

    inj = [x for x in rows if x[u"注入か"]]
    clean = [x for x in rows if not x[u"注入か"]]
    named = [x for x in rows if x[u"席の参照先"] is not None]
    passed = [x for x in rows if x[u"**B の最終判定**"] == PASS]
    mism = [x for x in rows if x[u"**B の最終判定**"] == MISMATCH]
    unprov = [x for x in rows if x[u"**B の最終判定**"] == UNPROVABLE]

    def rate(num, den):
        return {u"分子": num, u"分母": den,
                u"率": (round(100.0 * num / den, 1) if den else None)}

    # R-1 誤った参照先を検査通過にした
    r1_pass_inj = [x for x in passed if x[u"注入か"]]
    r1_pass_wrong = [x for x in passed
                     if x[u"正解"] and x[u"席の参照先"] != x[u"正解"]]
    # R-2 正しい主張を不一致にした(無改変の行)
    r2 = [x for x in mism if not x[u"注入か"]]
    # R-3 実証不能の内訳
    r3 = collections.Counter(
        (x[u"検証できない理由"] or (u"席が %s" % x[u"A(席の判定)"]))
        for x in unprov)
    # R-4 最終判定の正確性
    a_detect = [x for x in inj if x[u"A(席の判定)"] == u"誤りが在る"]
    b_detect = [x for x in inj if x[u"**B の最終判定**"] == ERR]
    a_false = [x for x in clean if x[u"A(席の判定)"] == u"誤りが在る"]
    b_false = [x for x in clean if x[u"**B の最終判定**"] in (ERR, MISMATCH)]
    a_miss = [x for x in inj if x[u"A(席の判定)"] == u"確認済み"]
    b_miss = [x for x in inj if x[u"**B の最終判定**"] == PASS]
    a_ok_clean = [x for x in clean if x[u"A(席の判定)"] == u"確認済み"]
    b_ok_clean = [x for x in clean if x[u"**B の最終判定**"] == PASS]
    # R-5 覆い / R-6 差分・率 / R-7 contract が無い
    base = [x for x in clean
            if x[u"A(席の判定)"] == u"確認済み" and x[u"席の参照先"] is not None]
    r6 = [x for x in rows if x[u"検証できない理由"] == u"参照先が 2 本要る"]
    r7 = [x for x in rows if x[u"検証できない理由"] == u"contract が無い"]

    pred = [
        {u"記号": "P-1", u"予測": u"R-1 = 0 件", u"実測": len(r1_pass_inj),
         u"当たり": len(r1_pass_inj) == 0},
        {u"記号": "P-2", u"予測": u"R-2 = 0 件", u"実測": len(r2),
         u"当たり": len(r2) == 0},
        {u"記号": "P-3", u"予測": u"B の検出 = 51(A と同じ)",
         u"実測": u"B %d / A %d" % (len(b_detect), len(a_detect)),
         u"当たり": len(b_detect) == 51 and len(a_detect) == 51},
        {u"記号": "P-4", u"予測": u"B の偽警報 = 2(A と同じ)",
         u"実測": u"B %d / A %d" % (len(b_false), len(a_false)),
         u"当たり": len(b_false) == 2 and len(a_false) == 2},
        {u"記号": "P-5", u"予測": u"B の実証不能 = 150 行", u"実測": len(unprov),
         u"当たり": len(unprov) == 150},
        {u"記号": "P-6", u"予測": u"検査通過 = 10 行・すべて無改変",
         u"実測": u"%d 行・注入 %d" % (len(passed), len(r1_pass_inj)),
         u"当たり": len(passed) == 10 and not r1_pass_inj},
        {u"記号": "P-7", u"予測": u"覆い = 10/41",
         u"実測": u"%d/%d" % (len(b_ok_clean), len(base)),
         u"当たり": len(b_ok_clean) == 10 and len(base) == 41},
        {u"記号": "P-8", u"予測": u"差分・率 7 行と contract 無し 24 行は全部 実証不能",
         u"実測": u"%d / %d(別判定 %d 件)"
               % (len(r6), len(r7),
                  sum(1 for x in r6 + r7
                      if x[u"**B の最終判定**"] != UNPROVABLE)),
         u"当たり": all(x[u"**B の最終判定**"] == UNPROVABLE for x in r6 + r7)},
    ]
    hit = sum(1 for p in pred if p[u"当たり"])

    rec = {
        "seal": SEAL,
        "step": u"**A / B / C を同じ行で比べた。engine 不変・0 USD・席は呼ばない**",
        u"**`検査通過` の意味**": (
            u"**現行 Core の検査を通過しただけ。「正しい」ではない。**"
            u"未検査属性: %s" % u"・".join(UNCHECKED)),
        u"行": {u"合計": len(rows), u"注入": len(inj), u"無改変": len(clean),
              u"席が名指した": len(named)},
        u"R-1 誤った参照先を検査通過にした": {
            u"(a) 検査通過のうち注入の行": rate(len(r1_pass_inj), len(passed)),
            u"(b) 注入の行のうち検査通過": rate(len(r1_pass_inj), len(inj)),
            u"正解と違う参照先で通した行": rate(len(r1_pass_wrong), len(passed)),
            u"明細": [{k: x[k] for k in (u"doc", u"id", u"席の参照先", u"正解")}
                    for x in r1_pass_inj + r1_pass_wrong]},
        u"R-2 正しい主張を不一致にした(無改変)": {
            u"率": rate(len(r2), len(clean)),
            u"明細": [{k: x[k] for k in (u"doc", u"id", u"席の参照先")}
                    for x in r2]},
        u"R-3 実証不能": {u"件数": rate(len(unprov), len(rows)),
                    u"内訳": dict(r3)},
        u"R-4 最終判定の正確性": {
            u"注入 %d 行" % len(inj): {
                u"検出(誤りが在る)": {"A": rate(len(a_detect), len(inj)),
                               "B": rate(len(b_detect), len(inj))},
                u"**危険な誤通過**": {"A": rate(len(a_miss), len(inj)),
                              "B": rate(len(b_miss), len(inj))}},
            u"無改変 %d 行" % len(clean): {
                u"偽警報": {"A": rate(len(a_false), len(clean)),
                         "B": rate(len(b_false), len(clean))},
                u"正しく通した": {"A": rate(len(a_ok_clean), len(clean)),
                            "B": rate(len(b_ok_clean), len(clean))}},
            u"注": u"**`実証不能` はどちらの正しさにも数えていない**(封 §3)"},
        u"R-5 検査通過の覆い": {
            u"率": rate(len(b_ok_clean), len(base)),
            u"注": u"分母は**無改変で席が `確認済み` と言い、参照先を名指した行**"},
        u"R-6 差分・率の行(別集計)": {
            u"件数": len(r6),
            u"B の判定": dict(collections.Counter(
                x[u"**B の最終判定**"] for x in r6))},
        u"R-7 contract が無い行(別集計)": {
            u"件数": len(r7),
            u"B の判定": dict(collections.Counter(
                x[u"**B の最終判定**"] for x in r7)),
            u"注": u"**その場で contract を足していない**(封 §2 の 2)"},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit,
                      u"外れ": len(pred) - hit},
        u"rows": rows,
        u"limits": [
            u"**A の危険な誤通過は 0 件なので、B が誤通過を減らすことは"
            u"この材料では示せない**(封 §5)",
            u"**`検査通過` は「正しい」ではない。**単位・期間・次元・重複は未検査",
            u"**contract を足していない。**実証不能のまま残した",
            u"**席の答えは A と B で同一である。**LLM の特定能力の差は測っていない"
            u"(替えたのは実証の層だけ)",
            u"**同じ 8 書類である。**新しい標本での再現は測っていない",
            u"**engine は 1 行も変えていない。**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 役割を替える実験(A / B / C)。0 USD・engine 不変 ===")
    print(u"行 %d(注入 %d / 無改変 %d)・席が名指した %d"
          % (len(rows), len(inj), len(clean), len(named)))
    print(u"B の判定: 検査通過 %d / 不一致 %d / 誤りが在る %d / 実証不能 %d"
          % (len(passed), len(mism), len(b_detect) + len(b_false)
             - len([x for x in b_false
                    if x[u"**B の最終判定**"] == MISMATCH]), len(unprov)))
    print(u"R-1 検査通過のうち注入: %d/%d" % (len(r1_pass_inj), len(passed)))
    print(u"R-2 無改変で不一致: %d/%d" % (len(r2), len(clean)))
    print(u"R-3 実証不能 %d/%d 内訳 %s"
          % (len(unprov), len(rows), json.dumps(dict(r3), ensure_ascii=False)))
    print(u"R-4 検出 A %d / B %d(注入 %d)・偽警報 A %d / B %d(無改変 %d)"
          % (len(a_detect), len(b_detect), len(inj),
             len(a_false), len(b_false), len(clean)))
    print(u"   危険な誤通過 A %d / B %d" % (len(a_miss), len(b_miss)))
    print(u"   無改変で正しく通した A %d / B %d" % (len(a_ok_clean), len(b_ok_clean)))
    print(u"R-5 覆い %d/%d" % (len(b_ok_clean), len(base)))
    print(u"R-6 差分・率 %d 行 / R-7 contract 無し %d 行" % (len(r6), len(r7)))
    print(u"--- 予測との照合 ---")
    for p in pred:
        print(u"  %-4s %-40s 実測 %-24s %s"
              % (p[u"記号"], p[u"予測"], p[u"実測"],
                 u"**当たり**" if p[u"当たり"] else u"**外れ**"))
    print(u"  当たり %d / 外れ %d" % (hit, len(pred) - hit))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
