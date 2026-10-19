# -*- coding: utf-8 -*-
"""e2_arm_scorer_2026-10-13.py の恒等・変異検査(保全用)。この検査スクリプト自体はラベルを読むが、
ラベルの中身・採点器の定義を1文字も書き換えない。入力はe2_labels_P_merged_2026-10-13.json(既存・不変)
と、ラベルのfactから合成した腕の出力(本スクリプトが構成する。engineは使わない)のみ。
出力は e2_arm_scorer_identity_report_2026-10-13.json と e2_arm_scorer_mutation{1,2,3}_report_2026-10-13.json。
各ファイルのsha256は本スクリプトの実行後にshasumで別途記録する(本スクリプトは出力しない)。
"""
import importlib.util
import json
import os
import copy

HERE = os.path.dirname(os.path.abspath(__file__))
SCORER_PATH = os.path.join(HERE, "e2_arm_scorer_2026-10-13.py")
LABEL_PATH = os.path.join(HERE, "e2_labels_P_merged_2026-10-13.json")

_spec = importlib.util.spec_from_file_location("e2_arm_scorer", SCORER_PATH)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def dump(obj, name):
    path = os.path.join(HERE, name)
    json.dump(obj, open(path, "w"), ensure_ascii=False, indent=1)
    return path


def main():
    labels = S.load_labels(LABEL_PATH)
    L = len(labels)

    def build_identity():
        out = {}
        for cid, lab in labels.items():
            pointers = ["xbrl:jppfs_cor:%s@%s" % (e, c) for (e, c) in sorted(lab["fact"])]
            out[cid] = {"state": "GROUNDED", "pointers": pointers}
        return out

    arm0 = build_identity()
    rep0 = S.score(arm0, labels)
    assert rep0["E2_count_strict"] == 0 and rep0["E2_count_v0"] == 0
    assert rep0["G"] == L and rep0["E1prime_strict"] == L
    dump(rep0, "e2_arm_scorer_identity_report_2026-10-13.json")

    cid1 = sorted(labels)[0]
    arm1 = copy.deepcopy(arm0)
    old = arm1[cid1]["pointers"][0]
    elem_ctx = old[len("xbrl:jppfs_cor:"):]
    elem, ctx = elem_ctx.split("@")
    new_ctx = "Prior1YearInstant" if ctx != "Prior1YearInstant" else "CurrentYearInstant"
    arm1[cid1]["pointers"][0] = "xbrl:jppfs_cor:%s@%s" % (elem, new_ctx)
    rep1 = S.score(arm1, labels)
    assert rep1["E2_count_strict"] == rep0["E2_count_strict"] + 1
    assert rep1["E2_count_v0"] == rep0["E2_count_v0"] + 1
    rep1["_mutation"] = {"kind": "context_shift", "claim_id": cid1, "old": old, "new": arm1[cid1]["pointers"][0]}
    dump(rep1, "e2_arm_scorer_mutation1_report_2026-10-13.json")

    pair_id = next(cid for cid, lab in labels.items() if len(lab["fact"]) >= 2)
    arm2 = copy.deepcopy(arm0)
    dropped = arm2[pair_id]["pointers"].pop()
    rep2 = S.score(arm2, labels)
    assert rep2["E2_count_strict"] == rep0["E2_count_strict"] + 1
    assert rep2["E2_count_v0"] == rep0["E2_count_v0"] + 1
    rep2["_mutation"] = {"kind": "drop_one_pointer", "claim_id": pair_id, "dropped": dropped}
    dump(rep2, "e2_arm_scorer_mutation2_report_2026-10-13.json")

    single_id = next(cid for cid, lab in labels.items() if len(lab["fact"]) == 1)
    arm3 = copy.deepcopy(arm0)
    old3 = arm3[single_id]["pointers"][0]
    body = old3[len("xbrl:jppfs_cor:"):]
    elem3, ctx3 = body.split("@")
    arm3[single_id]["pointers"][0] = "xbrl:jpcrp_cor:%sSummaryOfBusinessResults@%s" % (elem3, ctx3)
    rep3 = S.score(arm3, labels)
    assert rep3["E2_count_strict"] == rep0["E2_count_strict"] + 1
    assert rep3["E2_count_v0"] == rep0["E2_count_v0"]
    rep3["_mutation"] = {"kind": "canon_equivalent_suffix", "claim_id": single_id, "old": old3, "new": arm3[single_id]["pointers"][0]}
    dump(rep3, "e2_arm_scorer_mutation3_report_2026-10-13.json")

    print(json.dumps({
        "L": L,
        "identity": {k: v for k, v in rep0.items() if k != "rows"},
        "mutation1": {k: v for k, v in rep1.items() if k != "rows"},
        "mutation2": {k: v for k, v in rep2.items() if k != "rows"},
        "mutation3": {k: v for k, v in rep3.items() if k != "rows"},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
