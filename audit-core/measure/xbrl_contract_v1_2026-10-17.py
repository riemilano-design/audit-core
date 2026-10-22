# -*- coding: utf-8 -*-
"""封 `docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md` の実測。**A / B / B′ を同じ行で比べる。**

  A  = 席の答えそのまま(LLM 単独)
  B  = 席の参照先を **Core 自身の recipe** に差し替えて verify(役割実験の腕)
  B′ = 席の参照先を **contract v1 の入口**
       (`measure/xbrl_verify_external_v1_2026-10-17.py`)に渡す

**合成規則は役割実験の封と同じ字を使う**(`measure/xbrl_role_swap_2026-10-17.py` の
`compose` を import する。字を写さない)。
**engine の既存経路は 1 行も変えていない。0 USD・席は呼ばない。**

    python3 measure/xbrl_contract_v1_2026-10-17.py
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
OUT = os.path.join(FX, "contract_v1_2026-10-17.json")
SEAL = "docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md"

from adapters.xbrl import instance as I                     # noqa: E402
from adapters.xbrl import prose as PR                        # noqa: E402
from adapters.xbrl import edinet as ED                       # noqa: E402

_vp = importlib.util.spec_from_file_location(
    "verify_external_v1_for_measure",
    os.path.join(HERE, "xbrl_verify_external_v1_2026-10-17.py"))
VE = importlib.util.module_from_spec(_vp)
_vp.loader.exec_module(VE)

_sp = importlib.util.spec_from_file_location(
    "role_swap_for_v1", os.path.join(HERE, "xbrl_role_swap_2026-10-17.py"))
RSW = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(RSW)
A1, MB, IJ = RSW.A1, RSW.MB, RSW.IJ
compose = RSW.compose                      # **同じ合成規則(写さない)**
PASS, MISMATCH, ERR, UNPROVABLE = RSW.PASS, RSW.MISMATCH, RSW.ERR, RSW.UNPROVABLE


def kind_of(unit):
    """v1 で渡す主張の種類。**1 本しか無いので単一の値だけ**(封 §4)。"""
    return "single_value"


def rate(num, den):
    return {u"分子": num, u"分母": den,
            u"率": (round(100.0 * num / den, 1) if den else None)}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    swap = json.load(io.open(os.path.join(FX, "role_swap_2026-10-17.json"),
                             encoding="utf-8"))
    b_by = {(x[u"doc"], x[u"id"]): x for x in swap["rows"]}
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
        facts = I.load_instance(zb2)["facts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])):
                (f["name"], f["context"]) for f in facts}
        for r in mrows:
            b = b_by[(doc, r["id"])]
            seat_word, ptr = b[u"A(席の判定)"], b[u"席の参照先"]
            out = None
            if ptr is None:
                final = compose(seat_word, None, u"参照先を名指していない")
                why = u"参照先を名指していない"
            else:
                raw = keys.get(ptr)
                loc = ("%s@%s" % raw) if raw else ptr
                out = VE.verify_external(
                    {"kind": kind_of(r[u"単位"]), "value": r[u"値"],
                     "unit": r[u"単位"], "pointers": [loc]}, facts)
                if out["state"] == VE.UNPROVABLE:
                    why = out["reason"]
                    final = compose(seat_word, None, why)
                else:
                    why = None
                    final = compose(seat_word, out["state"], None)
            rows.append({
                u"doc": doc, u"id": r["id"], u"注入か": b[u"注入か"],
                u"正解": b[u"正解"], u"単位": r[u"単位"], u"値": r[u"値"],
                u"A(席の判定)": seat_word, u"席の参照先": ptr,
                u"v1 の state": (out or {}).get("state"),
                u"v1 の規則": (out or {}).get("rule"),
                u"v1 の理由": (out or {}).get("reason"),
                u"未検査属性": list(VE.UNCHECKED),
                u"検証できない理由": why,
                u"**B の最終判定**": b[u"**B の最終判定**"],
                u"**B′ の最終判定**": final})

    inj = [x for x in rows if x[u"注入か"]]
    clean = [x for x in rows if not x[u"注入か"]]
    named = [x for x in rows if x[u"席の参照先"] is not None]
    tried = [x for x in named if x[u"v1 の state"] != VE.UNPROVABLE]
    passed = [x for x in rows if x[u"**B′ の最終判定**"] == PASS]
    mism = [x for x in rows if x[u"**B′ の最終判定**"] == MISMATCH]
    unprov = [x for x in rows if x[u"**B′ の最終判定**"] == UNPROVABLE]
    pnf = [x for x in named if x[u"v1 の state"] == "POINTER_NOT_FOUND"]
    r1 = [x for x in passed if x[u"注入か"]]
    r2 = [x for x in mism if not x[u"注入か"]]
    b_pass = [x for x in rows if x[u"**B の最終判定**"] == PASS]
    b_unprov = [x for x in rows if x[u"**B の最終判定**"] == UNPROVABLE]
    detect = {k: len([x for x in inj if x[k] == ERR])
              for k in (u"**B の最終判定**", u"**B′ の最終判定**")}
    detect["A"] = len([x for x in inj if x[u"A(席の判定)"] == u"誤りが在る"])
    false = {k: len([x for x in clean if x[k] in (ERR, MISMATCH)])
             for k in (u"**B の最終判定**", u"**B′ の最終判定**")}
    false["A"] = len([x for x in clean if x[u"A(席の判定)"] == u"誤りが在る"])
    base = [x for x in clean
            if x[u"A(席の判定)"] == u"確認済み" and x[u"席の参照先"] is not None]
    two_pointer_rules = [x for x in rows
                         if x[u"v1 の規則"] in (u"差分", u"変化率")]
    reasons = collections.Counter(
        (x[u"検証できない理由"] or u"―") for x in unprov)

    pred = [
        {u"記号": "P-1", u"予測": u"検証を試みられた行 = 68", u"実測": len(tried),
         u"当たり": len(tried) == 68},
        {u"記号": "P-2", u"予測": u"R-1(注入が検査通過)= 0 件", u"実測": len(r1),
         u"当たり": len(r1) == 0},
        {u"記号": "P-3", u"予測": u"R-2(無改変で不一致)= 1〜15 件", u"実測": len(r2),
         u"当たり": 1 <= len(r2) <= 15},
        {u"記号": "P-4", u"予測": u"検査通過は 10 行から増える",
         u"実測": u"%d(B は %d)" % (len(passed), len(b_pass)),
         u"当たり": len(passed) > 10},
        {u"記号": "P-5", u"予測": u"検出 51・偽警報 2(A・B と同じ)",
         u"実測": u"検出 %d / 偽警報 %d"
               % (detect[u"**B′ の最終判定**"], false[u"**B′ の最終判定**"]),
         u"当たり": (detect[u"**B′ の最終判定**"] == 51
                 and false[u"**B′ の最終判定**"] == 2)},
        {u"記号": "P-6", u"予測": u"2 本要る規則の発火 = 0 件(実物)",
         u"実測": len(two_pointer_rules),
         u"当たり": len(two_pointer_rules) == 0,
         # **この `注` の字は凍結した記録(contract_v1_2026-10-17.json)に
         # そのまま入っている。**入口は監査の REVISE で `measure/` へ移したが、
         # **字を直すと script が自分の記録を再現しなくなる**ので直さない
         # (旧い道を指しているのは承知の上。新しい道は上の docstring と
         # `tests/measure/test_verify_external_v1.py`)。
         u"注": u"**凍結した答えは参照先を 1 本しか持たないので、"
               u"2 本の規則はこの実測では呼んでいない。"
               u"人工の入力での発火は `tests/adapters/xbrl/test_verify_external.py` "
               u"の 9〜11 番が確かめる**"},
        {u"記号": "P-7", u"予測": u"実証不能は 129 行から減る",
         u"実測": u"%d(B は %d)" % (len(unprov), len(b_unprov)),
         u"当たり": len(unprov) < len(b_unprov)},
        {u"記号": "P-8", u"予測": u"POINTER_NOT_FOUND が 1 件以上",
         u"実測": len(pnf), u"当たり": len(pnf) >= 1},
    ]
    hit = sum(1 for p in pred if p[u"当たり"])

    rec = {
        "seal": SEAL,
        "step": u"**contract v1 の実測。A / B / B′。engine の既存経路は不変・0 USD**",
        u"**`検査通過` の意味**": (
            u"**現行 Core の検査を通過しただけ。「正しい」ではない。**未検査属性: %s"
            % u"・".join(VE.UNCHECKED)),
        u"**合成規則**": u"役割実験の封と同じ(`xbrl_role_swap_2026-10-17.compose` を import)",
        u"行": {u"合計": len(rows), u"注入": len(inj), u"無改変": len(clean),
              u"席が名指した": len(named)},
        u"R-5 覆い(検証を試みられた行)": {
            u"B(Core 自身の recipe)": rate(
                len([x for x in named
                     if b_by[(x[u"doc"], x[u"id"])][u"Core の結果"] is not None]),
                len(named)),
            u"**B′(contract v1)**": rate(len(tried), len(named)),
            u"単位ごと": dict(collections.Counter(
                (x[u"単位"] or u"(無し)") for x in tried))},
        u"R-1 誤った参照先を検査通過にした": {
            u"(a) 検査通過のうち注入": rate(len(r1), len(passed)),
            u"(b) 注入のうち検査通過": rate(len(r1), len(inj)),
            u"明細": [{k: x[k] for k in (u"doc", u"id", u"席の参照先", u"正解")}
                    for x in r1]},
        u"R-2 正しい主張を不一致にした(無改変)": {
            u"率": rate(len(r2), len(clean)),
            u"明細": [{k: x[k] for k in
                     (u"doc", u"id", u"席の参照先", u"単位", u"値")}
                    for x in r2]},
        u"R-3 実証不能": {u"B": rate(len(b_unprov), len(rows)),
                    u"**B′**": rate(len(unprov), len(rows)),
                    u"B′ の内訳": dict(reasons)},
        u"R-4 最終判定": {
            u"検出(注入 %d)" % len(inj): {"A": detect["A"],
                                     "B": detect[u"**B の最終判定**"],
                                     u"B′": detect[u"**B′ の最終判定**"]},
            u"偽警報(無改変 %d)" % len(clean): {"A": false["A"],
                                        "B": false[u"**B の最終判定**"],
                                        u"B′": false[u"**B′ の最終判定**"]},
            u"注": u"**`実証不能` はどちらの正しさにも数えていない**"},
        u"検査通過": {u"B": len(b_pass), u"**B′**": len(passed),
                 u"分母(無改変で席が確認済み・名指した)": len(base)},
        u"POINTER_NOT_FOUND(別に数える)": {
            u"件数": len(pnf),
            u"明細": [{k: x[k] for k in (u"doc", u"id", u"席の参照先")}
                    for x in pnf]},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit,
                      u"外れ": len(pred) - hit},
        u"rows": rows,
        u"limits": [
            u"**検出と偽警報は定義上 A と同じになる**(封 §5)。改善の根拠にしない",
            u"**`検査通過` は「正しい」ではない。**単位・期間・次元・重複は未検査",
            u"**2 本要る規則はこの実測では呼んでいない**"
            u"(凍結した答えが参照先を 1 本しか持たない)。人工の試験で確かめた",
            u"**規則は v1 の 3 つだけ。**増やしていない",
            u"**既存の経路を変えていない。**新しい file は入口 1 つ",
            u"**同じ 8 書類である。**新しい標本での再現は測っていない",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== contract v1 の実測(A / B / B′)。0 USD ===")
    print(u"覆い: B %s → **B′ %s**"
          % (json.dumps(rec[u"R-5 覆い(検証を試みられた行)"][u"B(Core 自身の recipe)"],
                        ensure_ascii=False),
             json.dumps(rec[u"R-5 覆い(検証を試みられた行)"][u"**B′(contract v1)**"],
                        ensure_ascii=False)))
    print(u"検査通過: B %d → **B′ %d**(分母 %d)"
          % (len(b_pass), len(passed), len(base)))
    print(u"**R-1 誤通過: %d/%d** / **R-2 誤拒否: %d/%d**"
          % (len(r1), len(passed), len(r2), len(clean)))
    print(u"実証不能: B %d → B′ %d / 内訳 %s"
          % (len(b_unprov), len(unprov),
             json.dumps(dict(reasons), ensure_ascii=False)))
    print(u"検出 A %d / B %d / B′ %d(注入 %d)"
          % (detect["A"], detect[u"**B の最終判定**"],
             detect[u"**B′ の最終判定**"], len(inj)))
    print(u"偽警報 A %d / B %d / B′ %d(無改変 %d)"
          % (false["A"], false[u"**B の最終判定**"],
             false[u"**B′ の最終判定**"], len(clean)))
    print(u"POINTER_NOT_FOUND %d 件" % len(pnf))
    print(u"--- 予測との照合 ---")
    for p in pred:
        print(u"  %-4s %-34s 実測 %-18s %s"
              % (p[u"記号"], p[u"予測"], p[u"実測"],
                 u"**当たり**" if p[u"当たり"] else u"**外れ**"))
    print(u"  当たり %d / 外れ %d" % (hit, len(pred) - hit))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
