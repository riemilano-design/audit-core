# -*- coding: utf-8 -*-
"""core_expectation_1B_v2.json(profile P6)を作る。C-1g の結果 §8(人間の委任 2026-10-06「君に任せる」)。

規則(C-1g の予測 §2): v1 は 1 byte も変えない。v2 は **v1 を土台に**、司令塔の 1 回目の計測
``c1g_first_run_1B_P6.json`` の値で、封じた ID 集合(N030・N048・N050・T026・T028)だけを更新する。
生成の最後に 91 件すべてを 1 回目の JSON と 4 欄(state・pointers・recomputed・normalization)で照合し、
1 件でも違えば書かない。2 社目(5F)は差 0 なので v2 を作らない(v1 がそのまま P6 の門)。
3 社目は予測と実測の差の集合が一致しなかったので、この段では期待値を作らない(規則どおり止める)。

  python3 fixtures/xbrl/make_expectation_1B_v2.py
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.join(HERE, "core_expectation_1B.json")
RUN = os.path.join(HERE, "c1g_first_run_1B_P6.json")
OUT = os.path.join(HERE, "core_expectation_1B_v2.json")
SEALED_IDS = ("N030", "N048", "N050", "T026", "T028")
V1_SHA = "f8a45ecce18a3d98181061a6943449c75a0fbb850e09ec0b71808a45a70fd820"
RUN_SHA = "e4b3795204dc0c18"  # 先頭 16 桁(C-1g の結果 §3)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pairs(time_range):
    # run の "CurrentYear/Duration" → v1 の [["CurrentYear","Duration"]]
    return [list(t.split("/", 1)) for t in time_range] or None


def main():
    if sha(V1) != V1_SHA:
        print("v1 の sha が違う"); return 2
    if not sha(RUN).startswith(RUN_SHA):
        print("1 回目の JSON の sha が違う"); return 2
    v1 = json.load(open(V1, encoding="utf-8"))
    run = {r["id"]: r for r in json.load(open(RUN, encoding="utf-8"))["claims"]}
    out = {"source": "core_expectation_1B.json + c1g_first_run_1B_P6.json", "source_sha256": {"core_expectation_1B.json": sha(V1), "c1g_first_run_1B_P6.json": sha(RUN)},
           "document": v1["document"], "profile": "P6", "derived_from_v1_ids_changed": list(SEALED_IDS), "claims": []}
    changed = []
    for row in v1["claims"]:
        row = json.loads(json.dumps(row))  # deep copy
        r = run[row["id"]]
        if row["id"] in SEALED_IDS:
            row["modifiers"]["normalization"] = r["modifiers"]["normalization"]
            row["modifiers"]["time_range"] = pairs(r["modifiers"]["time_range"])
            row["evidence"]["pointers"] = list(r["pointers"])
            row["evidence"]["schemes"] = sorted({p.split(":", 1)[0] for p in r["pointers"]})
            row["contract"]["comparator"] = r["comparator"]
            if r["comparator"] == "builtin:flow_sign(cur)==direction":
                row["contract"]["tolerance"] = None
            row["result"]["state"] = r["state"]
            row["result"]["recomputed"] = r["recomputed"]
            row["result"]["script_reason"] = r["reason"]
            changed.append(row["id"])
        # 4 欄の照合(91 件すべて)
        bad = []
        if row["result"]["state"] != r["state"]: bad.append("state")
        if list(row["evidence"]["pointers"]) != list(r["pointers"]): bad.append("pointers")
        if row["result"]["recomputed"] != r["recomputed"]: bad.append("recomputed")
        if row["modifiers"]["normalization"] != r["modifiers"]["normalization"]: bad.append("normalization")
        if bad:
            print("1 回目の JSON と違う:", row["id"], bad); return 3
        out["claims"].append(row)
    if changed != list(SEALED_IDS):
        print("更新した ID が封じた集合と違う:", changed); return 3
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1); f.write("\n")
    print("written", OUT, sha(OUT)[:16], "claims", len(out["claims"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
