# -*- coding: utf-8 -*-
"""P20(連結・単体の落とし込み)の測定。封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md §3。

通信しない(ZIP はキャッシュから読む)。測るのは**直し用 8 書類**だけ。
最終評価用の 8 書類は開かない(封 `431f436`)。使用済み 6 書類は C-1〜C-4 に入れない。

対にするのは **id ではなく中身の鍵**。P20 は語彙(``_label_subjects``)も動かしうるので
行が増減し、id は揃わない(2026-10-14 の記録「分母は集合として揃える」)。
全行の分母と共通行の分母を**別々に**出す。

使い方::  python3 -B measure/consolidation_p20_measure_2026-10-14.py
出力: fixtures/xbrl/p20/result_2026-10-14.json
"""

import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "tests", "golden"))

from adapters.xbrl import instance as I, recipes as R, vocabulary as V  # noqa: E402
from tests.golden import _instrument as H  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "p20", "result_2026-10-14.json")
BASE, NEW = "P16", "P20"


def key_of(claim):
    """中身の鍵(id を**含めない**。封 §3 の対の付け方)。"""

    return (claim.get("kind"), claim.get("form"), claim.get("subject"),
            claim.get("value"), claim.get("unit"), claim.get("word"), claim.get("span"))


def key_without_form(claim):
    """``form`` を外した鍵。

    P20 は同じ主張の ``form`` を ``direct_value`` → ``derived_value`` に変えうる
    (当期と前期の 2 つの fact が引けるようになり、差の式になる)。中身の鍵に
    ``form`` が入っているので、その行は「片方にしか無い」に落ちる ― **実際には
    同じ主張**なので、形を外した鍵でも対を作り、落ちた行が本当に消えたのか
    形が変わっただけなのかを機械で分ける。
    """

    k = list(key_of(claim))
    k[1] = None
    return tuple(k)


def zip_bytes(doc):
    path = os.path.join(CACHE, doc + ".zip")
    with io.open(path, "rb") as fh:
        return fh.read()


def states(zb, doc, profile):
    """``{中身の鍵: 状態}`` と、鍵が重なった件数。

    状態は検証の結果(``run_verification``)から、鍵は生の主張の辞書から取る。
    **両者の id の集合が完全に一致することを確かめる**(片方だけが先に動いたら
    対の付け方そのものが壊れるので、黙って進めない)。
    """

    prof = V.PROFILES[profile]
    num_claims, text_claims = R.build_raw_claims(zb, prof)
    keys, loose = {}, {}
    for kind, claims in (("num", num_claims), ("text", text_claims)):
        for claim in claims:
            keys[claim["id"]] = key_of(dict(claim, kind=kind))
            loose[claim["id"]] = key_without_form(dict(claim, kind=kind))
    recipe_list, results, _ = H.run_verification(doc, prof, lambda: zb)
    ids = {recipe.claim.id for recipe in recipe_list}
    if ids != set(keys):
        raise SystemExit("id の集合が一致しない (%s/%s): 検証 %d 件 / 生の主張 %d 件"
                         % (doc, profile, len(ids), len(keys)))
    rows, dup, rows_loose = {}, 0, {}
    for recipe in recipe_list:
        key = keys[recipe.claim.id]
        if key in rows:
            dup += 1
        rows[key] = results[recipe.claim.id].state.name
        rows_loose[loose[recipe.claim.id]] = results[recipe.claim.id].state.name
    return rows, dup, rows_loose


def rate(n, d):
    return None if not d else round(100.0 * n / d, 1)


def main():
    split = json.load(io.open(SPLIT, encoding="utf-8"))
    docs = list(split["development"])
    per, totals = [], collections.Counter()
    for doc in docs:
        zb = zip_bytes(doc)
        elems = I.consolidated_element_count(I.load_instance(zb)["facts"])
        base_rows, base_dup, base_loose = states(zb, doc, BASE)
        new_rows, new_dup, new_loose = states(zb, doc, NEW)
        common = set(base_rows) & set(new_rows)
        # 鍵には None が混ざる(word・kind が無い行)ので、字にしてから並べる。
        changed = sorted((k for k in common if base_rows[k] != new_rows[k]), key=repr)
        row = {
            "doc": doc,
            "consolidated_elements": elems,
            "consolidated": elems > 0,
            "claims_base": len(base_rows), "claims_new": len(new_rows),
            "dup_keys_base": base_dup, "dup_keys_new": new_dup,
            "common_rows": len(common),
            "grounded_base": sum(1 for v in base_rows.values() if v == "GROUNDED"),
            "grounded_new": sum(1 for v in new_rows.values() if v == "GROUNDED"),
            "changed_rows": len(changed),
            "changed_detail": [{"key": list(k), "from": base_rows[k], "to": new_rows[k]}
                               for k in changed[:40]],
            "only_base": len(set(base_rows) - set(new_rows)),
            "only_new": len(set(new_rows) - set(base_rows)),
            # form を外した鍵では対になるか(= 消えたのではなく形が変わっただけか)。
            "only_base_without_form": len(set(base_loose) - set(new_loose)),
            "only_new_without_form": len(set(new_loose) - set(base_loose)),
            "changed_rows_without_form": sum(
                1 for k in (set(base_loose) & set(new_loose)) if base_loose[k] != new_loose[k]),
        }
        per.append(row)
        print("%-10s 連結枠 %3d  主張 %3d→%3d  一致 %3d→%3d  状態が変わった行 %d"
              % (doc, elems, row["claims_base"], row["claims_new"],
                 row["grounded_base"], row["grounded_new"], row["changed_rows"]))
        for k in ("claims_base", "claims_new", "grounded_base", "grounded_new",
                  "changed_rows", "common_rows"):
            totals[k] += row[k]

    cons = [r for r in per if r["consolidated"]]
    nons = [r for r in per if not r["consolidated"]]
    c1 = sum(r["changed_rows"] for r in cons)
    c1_loose = sum(r["changed_rows_without_form"] for r in cons)
    c1_unpaired = sum(r["only_base"] + r["only_new"] for r in cons)
    c2 = sum(r["grounded_new"] for r in nons)
    c2_claims = sum(r["claims_new"] for r in nons)
    c3 = [{"doc": r["doc"], "grounded_new": r["grounded_new"],
           "lifted": r["grounded_new"] > 0} for r in nons]
    out = {
        "seal": "docs/CONSOLIDATION_P20_PLAN_2026-10-14.md",
        "base": BASE, "new": NEW, "docs": docs,
        "per_document": per,
        "consolidated_docs": len(cons), "nonconsolidated_docs": len(nons),
        "C1_changed_rows_on_consolidated": c1,
        # C-1 は「対になった行で状態が変わった件数」。対にならなかった行が在れば
        # C-1 の 0 は意味を失うので、**その件数も同じ所に出す**。
        "C1_unpaired_rows_on_consolidated": c1_unpaired,
        "C1_changed_rows_without_form_on_consolidated": c1_loose,
        "C1_pass": c1 == 0 and c1_unpaired == 0 and c1_loose == 0,
        "C2_grounded_on_nonconsolidated": c2,
        "C2_claims_on_nonconsolidated": c2_claims,
        "C2_rate": rate(c2, c2_claims),
        "C2_pass": c2 >= 71,
        "C3": c3, "C3_pass": all(x["lifted"] for x in c3) and len(c3) == 2,
        "C4_grounded_base": totals["grounded_base"], "C4_grounded_new": totals["grounded_new"],
        "C4_claims_base": totals["claims_base"], "C4_claims_new": totals["claims_new"],
        "C4_rate_base": rate(totals["grounded_base"], totals["claims_base"]),
        "C4_rate_new": rate(totals["grounded_new"], totals["claims_new"]),
        "C4_pass": (rate(totals["grounded_new"], totals["claims_new"]) or 0) >= 46.0,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("")
    print("C-1 連結 %d 書類: 状態が変わった行 %d 件 / 対にならなかった行 %d 件 / "
          "形を外した鍵でも %d 件 (合格線 すべて 0) -> %s"
          % (len(cons), c1, c1_unpaired, c1_loose, "合格" if out["C1_pass"] else "不合格"))
    print("C-2 連結なし %d 書類で一致: %d / %d 件 = %s%% (合格線 71 件) -> %s"
          % (len(nons), c2, c2_claims, out["C2_rate"], "合格" if out["C2_pass"] else "不合格"))
    print("C-3 書類レベルの沈黙が外れたか: %s -> %s"
          % (c3, "合格" if out["C3_pass"] else "不合格"))
    print("C-4 8 書類全体の一致率: %s%% -> %s%% (合格線 46%%) -> %s"
          % (out["C4_rate_base"], out["C4_rate_new"], "合格" if out["C4_pass"] else "不合格"))
    print("\n->", OUT)


if __name__ == "__main__":
    main()
