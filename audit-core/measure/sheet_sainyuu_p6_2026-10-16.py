# -*- coding: utf-8 -*-
"""P-6 誤った別名の対照(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md §4)。

> 誤った別名を受理するケースを別途診断する。**人工材料での診断結果は、実データでの
> 安全性の証明とは分けて記録する。**(人間の判断 2026-10-16)

**P-5 より先に測る。**通る別名が 1 件から 18 件に増えるので、
「増えたか」より「誤って通していないか」を先に出す。

  D-1 正しい対を受理した数(18 のうち何件)
  D-2 **誤った対**を受理した数(18 × 誤った正本 19 通り = 342 組)
  D-3 **対照に歯が在るか** ― 規則を緩めたら誤った対が通るか

段 10 の負の対照は **D-2 = 0 だが歯が無かった**(値が全部異なるので、
規則を 1 列に緩めても 0 件のままだった)。**今回はそこを測る。**

通信しない。`MIN_INDEPENDENT` は触らない。
  usage: python3 measure/sheet_sainyuu_p6_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p6_2026-10-16.json")
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
P1 = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P2 = _mod("p2_for_p6", "sheet_sainyuu_p2_2026-10-16.py")
E = P2.E
norm = P2.norm
MIN = E.MIN_INDEPENDENT


def build():
    p1 = json.load(io.open(P1, encoding="utf-8"))
    sk, _ = P2.P1M.read(P2.P1M.SAINYUU)
    sm, _ = P2.P1M.read(P2.P1M.MEISAI_SAINYUU)
    kk, _kn = P2.kessan_kan(sk)
    mk, mn = P2.meisai_kan(sm, p1["meisai_sainyuu"]["toc"])
    raw, al, out_vals = P2.saisyutu_values()
    det, _ = P2.determined_keys(kk)
    holders = P2.value_holders(kk)
    existing = P2.existing_backing(raw, al)
    unconf = [u for u in al["unconfirmed"] if u.get("canonical")]
    return kk, mk, mn, al, out_vals, det, holders, existing, unconf


def accept(x, c, kk, mk, det, holders, out_vals, existing,
           *, min_independent=MIN, use_value_check=True,
           use_6a=True, use_6b=True, use_6d=True, use_existing=True):
    """**全部の規則を当てて**その対を受理するか決める。

    緩める旗(`use_*`)は**対照に歯が在るかを測るためだけ**に使う。
    本番の判定は既定値(全部 True・`min_independent` は engine の字)である。
    """
    mine, theirs = mk.get(x, {}), kk.get(c, {})
    hits, why = [], collections.Counter()
    for (nm, col), v in sorted(mine.items()):
        w = theirs.get((nm, col))
        if w is None:
            why["決算書に同じ行が無い"] += 1
            continue
        if use_value_check and v != w:
            why["値が食い違う"] += 1
            continue
        if use_6b and (nm, col) in det.get(c, set()):
            why["6b"] += 1
            continue
        if use_6a and (v in out_vals.get(c, set()) or v in out_vals.get(x, set())):
            why["6a"] += 1
            continue
        if use_6d and len(holders.get((col, v), ())) > 1:
            why["6d"] += 1
            continue
        hits.append({"level": "款", "name": nm, "column": col, "value": v,
                     "parent": None, "files": ["決算書 歳入", "事項別明細 歳入"]})
    ind, _ = E._independent(hits)
    vals = {h["value"] for h in ind}
    if use_existing:
        vals |= set(existing.get(x, {}).get("values", []))
    return len(vals) >= min_independent, len(vals), dict(why)


def wrong_pairs(unconf, kk):
    """**誤った対**を作る。`main` の中に書くと、ここを壊す変異が黙る
    (記録は変異のたびに作り直されないため。2026-10-16 の変異 R6 で実測)。"""
    canon = sorted({norm(c) for c in kk})
    return [(norm(u["name"]), c) for u in unconf for c in canon
            if c != norm(u["canonical"])]


def correct_pairs(unconf):
    return [(norm(u["name"]), norm(u["canonical"])) for u in unconf]


def main():
    kk, mk, mn, al, out_vals, det, holders, existing, unconf = build()
    args = (kk, mk, det, holders, out_vals, existing)

    d1 = []
    for u in unconf:
        ok, n, _ = accept(norm(u["name"]), norm(u["canonical"]), *args)
        d1.append({"alias": u["name"], "canonical": u["canonical"],
                   "accepted": ok, "independent": n})

    pairs = wrong_pairs(unconf, kk)
    d2 = []
    for x, c in pairs:
        ok, n, why = accept(x, c, *args)
        if ok:
            d2.append({"alias": x, "wrong_canonical": c, "independent": n,
                       "why": why})

    # **歯の測定。**規則を 1 つずつ緩めたら誤った対が何件通るか
    teeth = {}
    for label, kw in (
            ("値の食い違いを無視する", {"use_value_check": False}),
            ("6a を外す", {"use_6a": False}),
            ("6b を外す", {"use_6b": False}),
            ("6d を外す", {"use_6d": False}),
            ("MIN_INDEPENDENT を 1 にする", {"min_independent": 1}),
            ("歳出側の既存の裏づけも数える(既定)", {"use_existing": True}),
            ("全部緩める", {"use_value_check": False, "use_6a": False,
                        "use_6b": False, "use_6d": False,
                        "min_independent": 1})):
        n = sum(1 for x, c in pairs if accept(x, c, *args, **kw)[0])
        teeth[label] = n

    rec = {"seal": SEAL, "step": "P-6 誤った別名の対照",
           "min_independent": MIN,
           "D-1 正しい対の受理": {"accepted": sum(1 for r in d1 if r["accepted"]),
                          "of": len(d1), "detail": d1},
           "D-2 誤った対の受理": {"accepted": len(d2), "of": len(pairs),
                          "detail": d2[:20]},
           "D-3 歯の測定(規則を緩めたら誤った対が何件通るか)": teeth,
           "has_teeth": any(n > 0 for lbl, n in teeth.items()
                            if lbl != "歳出側の既存の裏づけも数える(既定)"),
           "limits": [
               "**これは実データの数字で作った対照であり、実物の報告文の中に"
               "誤った別名が現れたわけではない。**",
               "**人工材料での診断結果は実データでの安全性の証明と分けて記録する**"
               "(人間の指示)。",
               "**「別名規則の安全性が改善した」とは書かない。**",
           ]}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)

    print("=== P-6 誤った別名の対照(MIN_INDEPENDENT = %d)===" % MIN)
    print("**D-1 正しい対の受理: %d / %d**"
          % (rec["D-1 正しい対の受理"]["accepted"], len(d1)))
    print("**D-2 誤った対の受理: %d / %d**" % (len(d2), len(pairs)))
    for r in d2[:5]:
        print("   通った誤った対: %s -> %s(%d 本)"
              % (r["alias"], r["wrong_canonical"], r["independent"]))
    print("**D-3 歯の測定 ― 規則を緩めたら誤った対が通るか**")
    for lbl, n in teeth.items():
        print("   %-34s %d / %d %s" % (lbl, n, len(pairs),
                                       "**通る**" if n else ""))
    print("対照に歯が在るか: %s" % rec["has_teeth"])
    print("->", OUT)


if __name__ == "__main__":
    main()
