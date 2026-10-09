# -*- coding: utf-8 -*-
"""封A の計器 ― 梯子が実際に比べた**符号つき残差**を測る。

残差 = (梯子に渡った fact − 梯子に渡った target) ÷ claim_scale

梯子 ``_match_value(fact_value, target, unit)``(comparators.py:40)は
  round    : |fact - target| <= unit/2
  truncate : 0 <= fact - target < unit
を、符号そのまま → ``abs`` の 2 順で試す。有効な許容は **[-unit/2, +unit)**。

符号の扱いは 3 通りに分かれ、**梯子に渡る値が違う**ので別に数える:
  (1) 符号そのまま          … target = claim.value * unit_scale
  (2) 向きを別に検査(flow 枝) … comparators.py:93。**常に abs(fact)**・向きは sign_ok で別途
  (3) 符号を落とし向きの検査なし … 梯子の 2 順目が当たった(印が "abs+..." )

**自己試験**: 既存 3 書類は封A §2-2 に内訳が記録されている。
``--self-test`` でその数を再現できるか確かめる(再現しなければ計器を疑う)。
"""

import argparse
import collections
import io
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (ROOT, os.path.join(ROOT, "core", "py"), os.path.join(ROOT, "tests", "golden")):
    sys.path.insert(0, p)
from adapters.xbrl import vocabulary as V      # noqa: E402
import _instrument as INS                      # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

ORDER = ("負", "0", "(0,0.5]", "(0.5,1)", ">=1")

# **合否はこちら** ― 封A §2-2 の集計表(符号の扱い × 帯)。封の本表。
SEALED_AGG = {
    "符号そのまま": (0, 17, 20, 29, 0),          # 計 66
    "向きを別に検査": (0, 1, 3, 1, 0),            # 計 5
    "符号を落とし検査なし": (0, 12, 15, 7, 0),     # 計 34
}                                                # 合計 105

# 封A §2-2 の **per-document の脚注**。合否には使わない。
# **S100Z4Q1 の行は封の転記の誤り**(docs/NORMALIZATION_SEAL_A_ADDENDUM_2026-10-09.md)。
# 脚注 3 行の合計は 102 で、封自身の集計表 105 と 3 件ずれる。実測は (0,1,23,19,0)。
# **封の本文は書き換えない。期待値もここで黙って直さない**(ずれを印字し続ける)。
SEALED_PER_DOC_AS_WRITTEN = {
    "S100YMFV": (0, 1, 15, 18, 0),
    "S100Z4B6": (0, 28, 0, 0, 0),
    "S100Z4Q1": (0, 1, 21, 18, 0),      # ← 転記の誤り。実測 (0,1,23,19,0)
}
# 梯子を呼ぶ比較子だけが残差を持つ。それ以外は「値比較をしていない」として別に数える。
LADDER_COMPARATORS = {
    "equals_within": 1.0,
    "diff(a-b) equals_within": 1.0,
    "equals_within(pure*100)": 100.0,
    "diff(a-b)(pure*100)": 100.0,
}


def band(x):
    if x < 0:
        return "負"
    if x == 0:
        return "0"
    if x <= 0.5:
        return "(0,0.5]"
    if x < 1:
        return "(0.5,1)"
    return ">=1"


def measure(doc):
    with open(os.path.join(CACHE, "%s.zip" % doc), "rb") as fh:
        zb = fh.read()
    recs, res, _ = INS.run_verification(doc, V.P7, lambda: zb)
    rows, skipped = [], collections.Counter()
    for r in recs:
        q = res[r.claim.id]
        if q.state.value != "GROUNDED":
            continue
        c = r.contract
        if c is None or c.comparator not in LADDER_COMPARATORS:
            skipped["比較子が梯子を呼ばない:%s" % (None if c is None else c.comparator)] += 1
            continue
        p = c.params or {}
        if "claim_scale" not in p or "unit_scale" not in p or q.recomputed is None:
            skipped["幅か実測値が無い:%s" % c.comparator] += 1
            continue
        pure = LADDER_COMPARATORS[c.comparator]
        cs = p["claim_scale"]
        comp = q.provenance.get("comparison") or {}
        how = comp.get("normalization")
        target = r.claim.value * p["unit_scale"] * pure
        fact = q.recomputed
        if comp.get("flow_convention") is not None:
            mode = "向きを別に検査"
            fv, tv = abs(fact), abs(target)
        elif (how or "").startswith("abs"):
            mode = "符号を落とし検査なし"
            fv, tv = abs(fact), abs(target)
        else:
            mode = "符号そのまま"
            fv, tv = fact, target
        resid = (fv - tv) / cs
        rows.append({"id": r.claim.id, "how": how, "mode": mode,
                     "comparator": c.comparator, "residual": resid,
                     "band": band(resid), "claim_scale": cs,
                     "decimals": (q.provenance.get("resolved_pointers") or ({},))[0]
                                 .get("meta", {}).get("decimals")})
    return rows, skipped, len(recs)


def report(doc, rows, skipped, total):
    b = collections.Counter(r["band"] for r in rows)
    order = ORDER
    print("  %-10s 主張 %3d / 値比較した GROUNDED %3d  ->  " % (doc, total, len(rows)), end="")
    print("  ".join("%s:%d" % (k, b[k]) for k in order))
    m = collections.Counter(r["mode"] for r in rows)
    print("    符号の扱い: " + " / ".join("%s %d" % (k, v) for k, v in sorted(m.items())))
    h = collections.Counter(r["how"] for r in rows)
    print("    印: " + " / ".join("%s %d" % (k, v) for k, v in sorted(h.items(), key=lambda x: str(x))))
    d = collections.Counter(r["decimals"] for r in rows)
    print("    decimals: " + " / ".join("%s %d" % (k, v) for k, v in sorted(d.items(), key=lambda x: str(x))))
    if skipped:
        print("    値比較をしていない GROUNDED: " + " / ".join("%s=%d" % kv for kv in skipped.items()))
    return tuple(b[k] for k in order)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="*")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.self_test:
        print("自己試験 ― 封A §2-2 を再現するか(**合否は集計表**)")
        allrows = []
        per = {}
        for doc in SEALED_PER_DOC_AS_WRITTEN:
            rows, sk, total = measure(doc)
            per[doc] = report(doc, rows, sk, total)
            allrows += rows
        print()
        print("  [合否] 封の集計表(符号の扱い × 帯)")
        ok = True
        for mode, want in SEALED_AGG.items():
            rs = [r for r in allrows if r["mode"] == mode]
            got = tuple(collections.Counter(r["band"] for r in rs)[k] for k in ORDER)
            print("    %-22s 封 %s / 実測 %s  計 %d  -> %s"
                  % (mode, want, got, sum(got), "一致" if got == want else "**不一致**"))
            ok = ok and got == want
        print("    合計 封 105 / 実測 %d" % len(allrows))
        print()
        print("  [参考・合否に使わない] 封の per-document の脚注")
        for doc, want in SEALED_PER_DOC_AS_WRITTEN.items():
            print("    %-10s 封 %s / 実測 %s -> %s"
                  % (doc, want, per[doc], "一致" if per[doc] == want else "**不一致(封の転記の誤り)**"))
        wsum = sum(sum(v) for v in SEALED_PER_DOC_AS_WRITTEN.values())
        print("    脚注の合計 %d / 封の集計表 105 -> 脚注どおりだと %d 件ずれる"
              % (wsum, 105 - wsum))
        print()
        print("自己試験: %s" % ("集計表を完全に再現 ― 計器は封の本表を再現する" if ok
                              else "**集計表が不一致。計器を疑う。封A の測定に進まない。**"))
        return 0 if ok else 3

    out = {}
    for doc in a.docs:
        rows, sk, total = measure(doc)
        report(doc, rows, sk, total)
        out[doc] = {"claims": total, "rows": rows,
                    "skipped": dict(sk),
                    "bands": dict(collections.Counter(r["band"] for r in rows)),
                    "modes": dict(collections.Counter(r["mode"] for r in rows)),
                    "hows": dict(collections.Counter(r["how"] for r in rows)),
                    "decimals": dict(collections.Counter(r["decimals"] for r in rows))}
    if a.out:
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=str); fh.write(u"\n")
        print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
