# -*- coding: utf-8 -*-
"""未検査分岐の観察用スクリプト(読み取りのみ)。e2_arm_scorer_2026-10-13.py(封じた本体、
sha256 e9937a5314b206dfe266c2770fdf1e9ce9beeb7d243c72cce12386cd4c491d82)は一切変更していない。
**この観察は「監査対象の固定集合」には含めない**(今回新たに作った分析であり、固定集合は
e2_arm_scorer_audit_scope_draft_2026-10-13.md が宣言した7ファイルのまま変えない)。
目的: 非GROUNDED状態・入力欠落・id衝突・分母境界の4分岐について、現行コードが実際に何をするかを
観察する。修正はしない(修正は監査所見が出た後の別の判断)。
"""
import importlib.util
import copy
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCORER_PATH = os.path.join(HERE, "e2_arm_scorer_2026-10-13.py")
LABEL_PATH = os.path.join(HERE, "e2_labels_P_merged_2026-10-13.json")

_spec = importlib.util.spec_from_file_location("e2_arm_scorer", SCORER_PATH)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def identity_arm(labels):
    out = {}
    for cid, lab in labels.items():
        pointers = ["xbrl:jppfs_cor:%s@%s" % (e, c) for (e, c) in sorted(lab["fact"])]
        out[cid] = {"state": "GROUNDED", "pointers": pointers}
    return out


def main():
    labels = S.load_labels(LABEL_PATH)
    base = identity_arm(labels)
    some_id = sorted(labels)[0]
    results = {}

    arm = copy.deepcopy(base)
    arm[some_id] = {"state": "UNVERIFIABLE", "pointers": []}
    rep = S.score(arm, labels)
    results["case1_unverifiable_empty_pointers"] = {
        "G": rep["G"], "E2_count_strict": rep["E2_count_strict"], "E2_count_v0": rep["E2_count_v0"],
        "row": next(r for r in rep["rows"] if r["id"] == some_id),
    }

    arm2 = copy.deepcopy(base)
    arm2[some_id] = {"state": "VALUE_MISMATCH", "pointers": ["xbrl:jppfs_cor:SomeWrongElement@CurrentYearInstant"]}
    rep2 = S.score(arm2, labels)
    results["case1_value_mismatch_with_pointer"] = {
        "G": rep2["G"], "E2_count_strict": rep2["E2_count_strict"], "E2_count_v0": rep2["E2_count_v0"],
    }

    arm3 = copy.deepcopy(base)
    del arm3[some_id]
    rep3 = S.score(arm3, labels)
    results["case2_missing_claim"] = {
        "L": rep3["L"], "G": rep3["G"],
        "row": next(r for r in rep3["rows"] if r["id"] == some_id),
        "note": "state=None, silently excluded from G/E2, no warning raised by score()",
    }

    layerP_like = {"N030": {"state": "GROUNDED", "pointers": ["xbrl:jppfs_cor:CostOfSales@CurrentYearDuration"]}}
    layerR_like = {"N030": {"state": "GROUNDED", "pointers": ["xbrl:jppfs_cor:ShortTermLoansPayable@CurrentYearDuration"]}}
    merged = dict(layerP_like)
    merged.update(layerR_like)
    results["case3_id_collision_across_layers"] = {
        "survives": merged["N030"],
        "note": "score() has no layer concept; collision happens at dict-merge time before score() is called",
    }

    rep5 = S.score({}, {})
    results["case5_L_zero"] = {k: v for k, v in rep5.items() if k != "rows"}

    arm6 = copy.deepcopy(base)
    for cid in arm6:
        arm6[cid]["state"] = "POINTER_NOT_FOUND"
        arm6[cid]["pointers"] = []
    rep6 = S.score(arm6, labels)
    results["case5_G_zero"] = {k: v for k, v in rep6.items() if k != "rows"}

    import json
    print(json.dumps(results, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
