# -*- coding: utf-8 -*-
"""手順 ①〜⑦ の材料を**1 回の実行で**切り出す(人間の決定 R-2026-10-12-03・R-2026-10-09-10)。

出すもの(すべて fixtures/xbrl/ に書く。既に在れば**上書きしない**):
  stop_cause_main_material_2026-10-12.json   真 × 停止 214 件。id/文/数/単位/札/確信 + engine の state/reason/comparator/recomputed/pointers/provenance の抜粋
                                              → 本線 A 実装席と独立 分類席の**同じ入力**(分類席には本線の分類結果を渡さない)
                                              → 末尾 reaudit_B_strata に再監査 B の層別の鍵(再監査 A/B の席は**このファイルを読まない**)
  reaudit_A_material_2026-10-12.json         真 × VALUE_MISMATCH 33 件全件。**id/文/数/単位だけ**
  reaudit_B_material_2026-10-12.json         真 × GROUNDED 60 + PNF 13 + UNV 27 = 100 件。**id/文/数/単位だけ**。id 順(層を隠す)
  stop_cause_material_meta_2026-10-12.json   同一性(HEAD・ZIP・札・保護面の sha)・種・件数・各 sheet の sha256

**Core も Adapter も 1 行も変えない。** 実験時と同じ ZIP(sha で照合)・同じ profile P7・同じ札で engine を 1 回回す。
判定不能 23 件は分母に入れない(R-2026-10-09-09 条件 5)。偽 1 件(T087)は真でないので再監査の母集団に入らない。
"""
import collections, hashlib, io, json, os, random, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
for p in (ROOT, os.path.join(ROOT, "core", "py"), os.path.join(ROOT, "tests", "golden")):
    sys.path.insert(0, p)
from adapters.xbrl import vocabulary as V      # noqa: E402
import _instrument as INS                      # noqa: E402

DOC = "S100Z4Q1"
MOD_ZIP = os.path.join(HERE, "ai_prose_instance_2026-10-09.zip")
LABELS = os.path.join(HERE, "ai_prose_labels_2026-10-09.json")
CLAIMS = os.path.join(HERE, "ai_prose_claims_unlabelled_2026-10-09.json")
STATES = os.path.join(HERE, "ai_prose_states_2026-10-09.json")
OUT_MAIN = os.path.join(HERE, "stop_cause_main_material_2026-10-12.json")
OUT_A = os.path.join(HERE, "reaudit_A_material_2026-10-12.json")
OUT_B = os.path.join(HERE, "reaudit_B_material_2026-10-12.json")
OUT_META = os.path.join(HERE, "stop_cause_material_meta_2026-10-12.json")
PROFILE = V.P7
PROTECTED = "490888d46d034ca9eaae8e4b4d01f494919abf21a8b057e87c835d25256d7116"
# 種: 2026-10-12 の決定ログのコミット sha。この抽出のために私が作った値ではない。
SEED = "e7dbf93"
STRATA = (("GROUNDED", 60), ("POINTER_NOT_FOUND", 13), ("UNVERIFIABLE", 27))   # R-2026-10-09-10
EXPECT = {"真": 391, "真_stopped": 214, "GROUNDED": 177, "VALUE_MISMATCH": 33,
          "POINTER_NOT_FOUND": 57, "UNVERIFIABLE": 124}
PROV_KEYS = ("kind", "sentence", "span", "word", "value_only", "sign_token", "ambiguous_count",
             "member_source", "schemes", "modifiers", "comparison")


def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p):
    with open(p, "rb") as fh: return sha_bytes(fh.read())
def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace").strip()


def jsonable(x):
    if isinstance(x, dict): return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [jsonable(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None: return x
    return str(x)


def main():
    for p in (OUT_MAIN, OUT_A, OUT_B, OUT_META):
        if os.path.exists(p):
            print("既に在る。上書きしない:", p); return 2
    # 門 1: 札は追跡済みで HEAD と一致(ai_prose_verify の門 ⑧ と同じ)
    rel = os.path.relpath(LABELS, REPO)
    if git("ls-files", "--", rel) != rel: print("札が追跡されていない"); return 2
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=REPO).returncode != 0:
        print("札が HEAD と違う"); return 2
    # 門 2: ZIP・札は実験時(手順 1・2 の記録)と同じ sha
    st = json.load(open(STATES, encoding="utf-8"))["identity"]
    ident = {"head": git("rev-parse", "HEAD"), "profile": PROFILE.name, "document": DOC,
             "modified_zip_sha256": sha_file(MOD_ZIP), "labels_sha256": sha_file(LABELS),
             "claims_sha256": sha_file(CLAIMS), "seed": SEED, "strata": dict(STRATA)}
    for k in ("modified_zip_sha256", "labels_sha256"):
        if ident[k] != st[k]: print("実験時と違う:", k); return 2
    # 門 3: 保護面
    bund = subprocess.run("git ls-files audit-core/core/py audit-core/adapters | sort | xargs shasum -a 256 | shasum -a 256",
                          shell=True, cwd=REPO, stdout=subprocess.PIPE).stdout.decode().split()[0]
    if bund != PROTECTED: print("保護面の sha が違う:", bund); return 2
    ident["protected_surface_sha256"] = bund

    zb = open(MOD_ZIP, "rb").read()
    recs, res, _ = INS.run_verification(DOC, PROFILE, lambda: zb)
    lab = {r["id"]: r for r in json.load(open(LABELS, encoding="utf-8"))["labels"]}
    txt = {c["id"]: c for c in json.load(open(CLAIMS, encoding="utf-8"))["claims"]}
    by_id = {r.claim.id: r for r in recs}

    true_ids = sorted(cid for cid in lab if lab[cid]["札"] == "真")
    cnt = collections.Counter(res[cid].state.value for cid in true_ids)
    stopped = [cid for cid in true_ids if res[cid].state.value != "GROUNDED"]
    got = {"真": len(true_ids), "真_stopped": len(stopped), **cnt}
    for k, v in EXPECT.items():
        if got.get(k) != v: print("検算 不一致:", k, got.get(k), "expected", v); return 3
    print("検算:", json.dumps(got, ensure_ascii=False))

    def row_text(cid):
        t = txt[cid]; return {"id": cid, "文": t["文"], "数": t["数"], "単位": t["単位"]}

    main_rows = []
    for cid in stopped:
        r, q, l = by_id[cid], res[cid], lab[cid]
        prov = {k: jsonable(q.provenance.get(k)) for k in PROV_KEYS if k in q.provenance}
        prov["resolved_pointers_count"] = len(q.provenance.get("resolved_pointers", ()))
        main_rows.append({**row_text(cid), "札": l["札"], "確信": l.get("確信"),
                          "engine": {"state": q.state.value, "reason": q.reason, "comparator": q.comparator,
                                     "recomputed": q.recomputed, "achieved_depth": q.achieved_depth,
                                     "pointers": list(q.pointers),
                                     "subject": r.claim.subject, "form": r.claim.form.value if hasattr(r.claim.form, "value") else str(r.claim.form),
                                     "unverifiable_reason": r.unverifiable_reason, "not_found_reason": r.not_found_reason,
                                     "contract": {"comparator": r.contract.comparator, "params": jsonable(r.contract.params)} if r.contract else None,
                                     "provenance": prov}})
    # 再監査 A: 真 × VM 全件
    a_rows = [row_text(cid) for cid in stopped if res[cid].state.value == "VALUE_MISMATCH"]
    # 再監査 B: 層化抽出。層ごとに id 順の母集団から sample。出力は id 順で層を隠す
    b_ids, strata_key = [], {}
    for state, n in STRATA:
        pool = sorted(cid for cid in true_ids if res[cid].state.value == state)
        picked = sorted(random.Random("%s|reaudit-B-2026-10-12|%s" % (SEED, state)).sample(pool, n))
        strata_key[state] = {"population": len(pool), "n": n, "ids": picked}
        b_ids += picked
    b_rows = [row_text(cid) for cid in sorted(b_ids)]
    assert len(b_rows) == 100 and len(set(b_ids)) == 100

    note_main = ("真 × 停止 214 件(判定不能 23 件と偽 1 件は含まない)。本線 A 実装席と独立 分類席の同じ入力。"
                 "分類は docs/STOP_CAUSE_CRITERIA_2026-10-09.md の項目だけで行う。D1(札の誤り)は候補として書けるが確定は ⑥ でのみ。"
                 "reaudit_B_strata は再監査 B の層の鍵 ― 再監査 A/B の席はこのファイルを開かない。")
    main_out = {"note": note_main, "identity": ident, "counts": got, "rows": main_rows,
                "reaudit_B_strata": strata_key}
    a_out = {"note": "真 × VALUE_MISMATCH 33 件全件の再監査。id/文/数/単位だけ。engine の状態・本線の札・reason・pointer は渡さない。"
                     "札の定義は ai_prose_labels_2026-10-09.json と同じ(真/偽/判定不能・確信 高/中/低)。根拠は S100Z4Q1 の XBRL の fact。",
             "document": DOC, "rows": len(a_rows), "claims": a_rows}
    b_out = {"note": "層化抽出 100 件の再監査(層は明かさない。id 順)。id/文/数/単位だけ。札の定義は同上。偽を見つけたら根拠に fact の要素名・context・値を書く。",
             "document": DOC, "rows": len(b_rows), "claims": b_rows}
    for p, o in ((OUT_MAIN, main_out), (OUT_A, a_out), (OUT_B, b_out)):
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump(o, fh, ensure_ascii=False, indent=1, default=str); fh.write(u"\n")
    meta = {"identity": ident, "counts": got, "python": sys.version.split()[0],
            "sheets": {os.path.basename(p): {"sha256": sha_file(p), "rows": n}
                       for p, n in ((OUT_MAIN, len(main_rows)), (OUT_A, len(a_rows)), (OUT_B, len(b_rows)))},
            "reaudit_B_strata_counts": {k: v["n"] for k, v in strata_key.items()},
            "excluded": {"判定不能": 23, "偽": 1, "note": "分母は真 391。再監査の母集団も真 391"}}
    with io.open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1); fh.write(u"\n")
    print(json.dumps(meta["sheets"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
