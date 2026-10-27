# -*- coding: utf-8 -*-
"""P27 段 2 §3-1 ― 調整用の 10 社の文に P27・P27E を当てる再現の測定(U-1〜U-5)。
封 ``docs/XBRL_P27_SEAL_2026-10-27.md`` §3-1・§9-2。段 1 の測定の script ``measure/xbrl_p27_tune_2026-10-27.py`` は **1 行も変えず**、importlib で読んで
``PROFILES`` を 4 つ(P22・P26・P27・P27E)に替えて同じ関数(``inject_doc``・``claim_record``・``inject_summary`` など)を呼ぶ。土台は段 1 と同じ
「P22 と P26 の両方で GROUNDED」なので、注入の site の集合は P27 の規則に依らない。

    cd audit-core
    python3 measure/xbrl_p27_tune_rerun_2026-10-27.py judge  [--out <file>]
    python3 measure/xbrl_p27_tune_rerun_2026-10-27.py inject [--out <file>] [--procs N]

**0 USD・通信なし・鍵は読まない・LLM は呼ばない。** engine は測る側から 1 行も変えない。**評価用の文・DB の応答は開かない**(段 1 の ``Ctx.guard`` が評価用の docID を
どの file も開く前に止める)。調整用の文(``~/.cache/audit-core/edinetdb-p27/reports/``)と ZIP は読むだけ。``~/.cache/audit-core/edinet/`` と
``edinet-fresh-2026-10-21/`` には 1 file も足さない(前後の件数と名前の一覧の sha256 を記録し、変わっていれば記録を書かずに止める)。
repo に置く記録に ``span``・``subject``・``value``・``recomputed`` は入れない(段 1 の ``write_record`` が検査する)。
"""
import argparse
import collections
import importlib.util
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
for _p in (HERE, DEFAULT_ROOT, os.path.join(DEFAULT_ROOT, "core", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("xbrl_p27_tune_2026-10-27.py", "p27_tune_for_rerun")          # 段 1 の測定の script(1 行も変えない)

SEAL = "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md"
JUDGE_REL = os.path.join("fixtures", "xbrl", "p27", "tune_p27_2026-10-27.json")
INJECT_REL = os.path.join("fixtures", "xbrl", "p27", "tune_p27_inject_2026-10-27.json")
PROFILES4 = ("P22", "P26", "P27", "P27E")
STATES = T.STATES
CLAIM_FIELDS = ("id", "kind", "form", "unit", "state", "reason", "pointers")
#: 封 §3-1 の予測の幅(字のまま。結果の門が封の文書の太字と照らす)
BOUNDS = {
    "U-2": {"P27 の無改変 GROUNDED": (271, 275), "P27 の無改変 VALUE_MISMATCH": (14, 18), "P26 → P27 で新しい GROUNDED": 0, "P26 → P27 で VALUE_MISMATCH に入る行": 0},
    "U-3": {"P27E の無改変が P27 と state が同じ行": 534},
    "U-4": {"T8_REL 通した P27・P27E": (0, 1), "T8_REL 名指して原本の値 P27": (15, 24), "T8_REL 名指して原本の値 P27E": (70, 80)},
    "U-5": {"T1_VALUE 通した 4 profile": 0, "T1_VALUE 名指して原本の値 P27E": (6, 8)},
}


def default_outside(cache_root):
    return os.path.join(cache_root, "tune_p27")


def setup(root, docs, outside_dir, work_root, backend=None):
    base = T.DB.default_cache_base()
    zip_dir, cache_root, existing_dir = T.DB.default_zip_dir(), T.DB.default_cache_root(), T.DB.default_existing_cache_dir()
    outside_dir = outside_dir or default_outside(cache_root)
    ctx = T.Ctx(root, zip_dir, cache_root, existing_dir, outside_dir, work_root, docs)            # 評価用はここで止まる
    git = T.git_facts(root)
    return ctx, git, backend or T.RealBackend()


def header(ctx, step, git, backend, before, after):
    with io.open(os.path.abspath(__file__), "rb") as fh:
        script_sha = T.sha256_hex(fh.read())
    if before != after:
        raise T.Stop("**既存の cache か ZIP の folder の件数か名前が変わった。記録を書かずに止める**")
    return {"seal": SEAL, "step": step, "backend": backend.name,
            "HEAD の commit": git["HEAD"], "W の commit": git["W"], "W は HEAD の祖先": git["W は HEAD の祖先"],
            "この script の sha256": script_sha, "段 1 の測定の script(読むだけ・1 行も変えない)の sha256": T.sha256_hex(T.read_bytes(os.path.join(HERE, "xbrl_p27_tune_2026-10-27.py"))),
            "対象の docID": list(ctx.docs), "対象は調整用の全部": list(ctx.docs) == list(ctx.tuning),
            "使った文の sha256": dict((d, ctx.report_sha[d]) for d in ctx.docs),
            "engine の指紋": backend.fingerprint(),
            "cache の前後": {"前": before, "後": after, "変化なし": before == after}}


# ====================================================================================================
def run_judge(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, say=print):
    """4 profile の判定(P22・P26・P27・P27E)。段 1 の記録 ``tune_2026-10-27.json`` の P22・P26 の欄と 1 欄ずつ照らす(U-1)。"""
    T.PROFILES = PROFILES4
    ctx, git, backend = setup(root, docs, outside_dir, None, backend)
    out = out or os.path.join(root, JUDGE_REL)
    before = T.cache_snapshot(ctx)
    prev = T.read_json(os.path.join(root, T.JUDGE_REL))
    prev_rows = dict(((r["docID"], r["id"]), r) for r in prev["claim"])
    per_doc, rows = [], []
    u1_diff = []
    for doc in ctx.docs:
        text, _tb = ctx.read_report(doc)
        zb = ctx.read_zip(doc)
        outs = dict((p, backend.verify(zb, p, text)) for p in PROFILES4)
        ids = [c["id"] for c in outs["P22"]["claims"]]
        for p in PROFILES4:
            if [c["id"] for c in outs[p]["claims"]] != ids:
                raise T.Stop("**claim の id の並びが profile 間で違う: %s。止める**" % doc)
        per = dict((p, dict((c["id"], c) for c in outs[p]["claims"])) for p in PROFILES4)
        differ = dict((p, [i for i in ids if (per["P22"][i]["value"], per["P22"][i]["span"], per["P22"][i]["unit"]) !=
                                         (per[p][i]["value"], per[p][i]["span"], per[p][i]["unit"])]) for p in PROFILES4)
        states = dict((p, collections.Counter(c["state"] for c in outs[p]["claims"])) for p in PROFILES4)
        per_doc.append({"docID": doc, "型": ctx.styles[doc], "文の sha256": ctx.report_sha[doc],
                        "claim の数": dict((p, len(outs[p]["claims"])) for p in PROFILES4),
                        "state の数": dict((p, dict((s, states[p].get(s, 0)) for s in STATES)) for p in PROFILES4),
                        "値・span・単位が P22 と違う id の数": dict((p, len(differ[p])) for p in PROFILES4)})
        for cid in ids:
            rec = {"docID": doc, "id": cid}
            for p in PROFILES4:
                rec[p] = T.claim_record(per[p][cid])
            rows.append(rec)
            old = prev_rows[(doc, cid)]
            for p in ("P22", "P26"):
                if old[p] != rec[p]:
                    u1_diff.append({"docID": doc, "id": cid, "profile": p})
        say("  %s %s claim %d" % (doc, ctx.styles[doc], len(ids)))
    after = T.cache_snapshot(ctx)
    rec = header(ctx, "P27 段 2 §3-1 ― 調整用の判定(P22・P26・P27・P27E。U-1 U-2 U-3)", git, backend, before, after)
    rec["claim の対の付け方"] = "id で対にする。4 profile で id の並びが同じであることを確かめた(違えば止まる)。値・span・単位が P22 と違う id は会社ごとに数えた"
    rec["会社"] = per_doc
    rec["claim"] = rows
    rec["集計"] = judge_summary(rows, per_doc)
    rec["U-1(旗が偽の P22・P26)"] = {"段 1 の記録": os.path.join("fixtures", "xbrl", "p27", "tune_2026-10-27.json"),
                                "段 1 の記録と欄(id・kind・form・unit・state・reason・pointers)が違う行": len(u1_diff), "違う行": u1_diff,
                                "照らした行": 2 * len(rows), "段 1 の記録の行": len(prev_rows), "行の集合が同じ": set(prev_rows) == set((r["docID"], r["id"]) for r in rows)}
    rec["限界"] = ["span・subject・value・recomputed は repo の外にも置かない(この測定は段 1 の全部の欄の記録を作り直さない)",
                 "読む行(2 席の読み)は作らない: 封 §3-2 以降の評価用の測定で P27E の無改変の動いた行を読む"]
    T.write_record(out, rec)
    say("-> %s(claim %d)" % (out, len(rows)))
    return rec


def judge_summary(rows, per_doc):
    st = dict((p, dict((s, sum(1 for r in rows if r[p]["state"] == s)) for s in STATES)) for p in PROFILES4)
    n = len(rows)
    out = {"claim": n, "state の数": st, "VALUE_MISMATCH の率": dict((p, T.frac(st[p]["VALUE_MISMATCH"], n)) for p in PROFILES4)}
    out["P26 → P27 で新しい GROUNDED"] = sum(1 for r in rows if r["P27"]["state"] == "GROUNDED" and r["P26"]["state"] != "GROUNDED")
    out["P26 → P27 で GROUNDED を離れた行"] = sum(1 for r in rows if r["P26"]["state"] == "GROUNDED" and r["P27"]["state"] != "GROUNDED")
    out["P26 → P27 で VALUE_MISMATCH に入る行"] = sum(1 for r in rows if r["P27"]["state"] == "VALUE_MISMATCH" and r["P26"]["state"] != "VALUE_MISMATCH")
    out["P26 → P27 で state が動いた行"] = sum(1 for r in rows if r["P27"]["state"] != r["P26"]["state"])
    out["P27 → P27E で state が動いた行"] = sum(1 for r in rows if r["P27E"]["state"] != r["P27"]["state"])
    out["P27E の無改変が P27 と state が同じ行"] = sum(1 for r in rows if r["P27E"]["state"] == r["P27"]["state"])
    out["P27E の無改変が P27 と state・reason・pointers が同じ行"] = sum(1 for r in rows if all(r["P27E"][k] == r["P27"][k] for k in ("state", "reason", "pointers")))
    return out


# ====================================================================================================
def run_inject(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, work_root=None, procs=1, say=print):
    """4 profile の注入(T1_VALUE・T8_REL)。段 1 の記録 ``tune_inject_2026-10-27.json`` の P22・P26 の分類と 1 行ずつ照らす(U-1)。"""
    T.PROFILES = PROFILES4
    work_root = work_root or tempfile.mkdtemp(prefix="p27_tune_rerun_", dir=os.environ.get("TMPDIR"))
    ctx, git, backend = setup(root, docs, outside_dir, work_root, backend)
    out = out or os.path.join(root, INJECT_REL)
    seed, seed_meta = T.IJ.verify_seed_sealed(T.SEED_FILE)               # git に追跡され内容が一致していなければ止まる
    before = T.cache_snapshot(ctx)
    T._STATE.update(ctx=ctx, backend=backend, seed=seed, work=work_root, cap=T.INJECT_CAP)
    if procs > 1:
        results = T.run_parallel(ctx.docs, procs)
    else:
        results = dict((d, T._inject_worker(d)) for d in ctx.docs)
    rows, full, per_doc = [], [], {}
    for d in ctx.docs:
        r, f, c = results[d]
        rows += r
        full += f
        per_doc[d] = c
        say("  %s 注入 %d 件" % (d, len(r)))
    full_blob = T.dumps({"seed 以外の注入の字": full}).encode("utf-8")
    T.write_text(os.path.join(ctx.outside_dir, "inject_full.json"), full_blob.decode("utf-8"))
    after = T.cache_snapshot(ctx)
    prev = T.read_json(os.path.join(root, T.INJECT_REL))
    prev_rows = dict(((r["docID"], r["id"]), r) for r in prev["行"])
    u1_diff = []
    for r in rows:
        old = prev_rows.get((r["docID"], r["id"]))
        if old is None:
            u1_diff.append({"docID": r["docID"], "id": r["id"], "profile": "(段 1 の記録に無い行)"})
            continue
        for p in ("P22", "P26"):
            if old[p] != r[p]:
                u1_diff.append({"docID": r["docID"], "id": r["id"], "profile": p})
    rec = header(ctx, "P27 段 2 §3-1 ― 調整用の注入(T1_VALUE・T8_REL。4 profile。U-1 U-4 U-5)", git, backend, before, after)
    rec["種"] = {"file": "measure/SEED.json", "sealed_in_commit": seed_meta.get("sealed_in_commit"), "seed_file_sha256": seed_meta.get("seed_file_sha256")}
    rec["型"] = {"T1_VALUE": "inject.select(types=[T1_VALUE]) のまま", "T8_REL": "円の単位族の token・r ∈ %s・%d 回まで" % (list(T.T8_R_VALUES), T.T8_TRIES),
               "上限": "型ごと・1 書類あたり %d 件" % T.INJECT_CAP, "土台": "無改変で P22 と P26 の両方が GROUNDED(段 1 と同じ)。分類の土台は各 profile の同じ id の無改変の claim"}
    rec["書類別の数え"] = per_doc
    rec["注入の行の数"] = len(rows)
    rec["集計"] = T.inject_summary(rows)
    rec["T8_REL の site"] = {"注入の行": sum(1 for r in rows if r["型"] == "T8_REL"), "作れる site(上限の前)": sum(per_doc[d]["T8_REL"].get("作れる site", 0) for d in per_doc)}
    rec["行"] = rows
    rec["U-1(旗が偽の P22・P26)"] = {"段 1 の記録": os.path.join("fixtures", "xbrl", "p27", "tune_inject_2026-10-27.json"),
                                "段 1 の記録と分類(対応・結果・state・reason)が違う行": len(u1_diff), "違う行": u1_diff,
                                "照らした行": len(rows), "段 1 の記録の行": len(prev_rows),
                                "行の集合が同じ": set(prev_rows) == set((r["docID"], r["id"]) for r in rows)}
    rec["repo の外に置いたもの"] = {"folder": T.DB.display_path(ctx.outside_dir),
                              "注入の字・新しい値": {"file": "inject_full.json", "sha256": T.sha256_hex(full_blob), "bytes": len(full_blob)}}
    rec["限界"] = ["注入は 2 型だけ。DB と原本の差の実際の分布ではない(T8_REL の r の 4 値は 3 本の差の大きさに寄せた決め打ち)",
                 "ρ = 0.15 は T8_REL の変え幅(±10%)を包むように決めたので、同じ T8_REL で測る P27E の『名指す率』は作りから当たりやすい(封 §10-2)"]
    T.write_record(out, rec)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "inject"))
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--outside-dir", default=None, help="既定: ~/.cache/audit-core/edinetdb-p27/tune_p27/")
    ap.add_argument("--work-dir", default=None)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--docs", default=None, help="コンマ区切り(既定: 調整用の全部)。評価用は止める")
    a = ap.parse_args(argv)
    docs = a.docs.split(",") if a.docs else None
    if a.cmd == "judge":
        run_judge(root=a.root, docs=docs, out=a.out, outside_dir=a.outside_dir)
    else:
        run_inject(root=a.root, docs=docs, out=a.out, outside_dir=a.outside_dir, work_root=a.work_dir, procs=a.procs)


if __name__ == "__main__":
    main()
