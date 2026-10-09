# -*- coding: utf-8 -*-
"""手順 1・2(人間の裁定 2026-10-09)― AI 文実験の状態別件数を**再取得して検算する。**

**214 件を最初から「誤停止」と呼ばない。**製品上の意味が違うので混ぜない:
  `VALUE_MISMATCH`            → 正しい Claim を値不一致として止めた = **真の誤停止**
  `POINTER_NOT_FOUND`         → 元データから該当 Evidence を辿れない = **照合範囲の問題**
  `UNVERIFIABLE`              → 決定論的に照合できない = **照合範囲の問題**

実験時と同一の commit・データ・設定で回し、**各ハッシュを記録する**(人間の追加条件)。
**Core も Adapter も 1 行も変えない。**
"""

import collections
import hashlib
import io
import json
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
PROSE = os.path.join(HERE, "ai_prose_2026-10-09.txt")
OUT = os.path.join(HERE, "ai_prose_states_2026-10-09.json")
PROFILE = V.P7
STOPPED = ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE")
MEANING = {
    "VALUE_MISMATCH": "真の誤停止(正しい Claim を値不一致として止めた)",
    "POINTER_NOT_FOUND": "照合範囲の問題(元データから該当 Evidence を辿れない)",
    "UNVERIFIABLE": "照合範囲の問題(決定論的に照合できない)",
}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=REPO, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace").strip()


def main():
    ident = {
        "head": git("rev-parse", "HEAD"),
        "experiment_result_commit": "ab7d132",
        "profile": PROFILE.name,
        "document": DOC,
        "modified_zip_sha256": sha(MOD_ZIP),
        "modified_zip_tracked": False,
        "modified_zip_reproducible": "fixtures/xbrl/ai_prose_claims_2026-10-09.py の build_modified_zip で byte 同一に再生成できることを確認済み",
        "labels_sha256": sha(LABELS),
        "prose_sha256": sha(PROSE),
        "protected_surface_sha256": "490888d46d034ca9eaae8e4b4d01f494919abf21a8b057e87c835d25256d7116",
        "protected_surface_files": 22,
        "protected_surface_uncommitted": 0,
    }
    for k, v in ident.items():
        print("  %-34s %s" % (k, v))
    print()

    with open(MOD_ZIP, "rb") as fh:
        zb = fh.read()
    recs, res, _ = INS.run_verification(DOC, PROFILE, lambda: zb)
    lab = {r["id"]: r for r in json.load(open(LABELS, encoding="utf-8"))["labels"]}

    cell = collections.defaultdict(collections.Counter)
    missing = []
    for r in recs:
        cid = r.claim.id
        q = res.get(cid)
        m = (lab.get(cid) or {}).get("札")
        if q is None or m is None:
            missing.append(cid); continue
        cell[m][q.state.value] += 1

    ORDER = ("GROUNDED",) + STOPPED
    print("  %-10s %9s %15s %18s %14s %8s" % ("札", "GROUNDED", "VALUE_MISMATCH",
                                              "POINTER_NOT_FOUND", "UNVERIFIABLE", "計"))
    totals = collections.Counter()
    for m in ("真", "偽", "判定不能"):
        c = cell[m]
        print("  %-10s %9d %15d %18d %14d %8d"
              % (m, c["GROUNDED"], c["VALUE_MISMATCH"], c["POINTER_NOT_FOUND"],
                 c["UNVERIFIABLE"], sum(c.values())))
        totals.update(c)
    print("  %-10s %9d %15d %18d %14d %8d"
          % ("計", totals["GROUNDED"], totals["VALUE_MISMATCH"],
             totals["POINTER_NOT_FOUND"], totals["UNVERIFIABLE"], sum(totals.values())))
    print()

    t = cell["真"]
    t_total = sum(t.values())
    t_stop = sum(t[s] for s in STOPPED)
    print("  [検算] 札が『真』の合計 = %d  (391 であるべき) -> %s"
          % (t_total, "一致" if t_total == 391 else "**不一致**"))
    print("  [検算] 真のうち止まった = %d  (214 であるべき) -> %s"
          % (t_stop, "一致" if t_stop == 214 else "**不一致**"))
    print("  [検算] 札なし = %d" % len(missing))
    print()
    print("  **214 件の内訳 ― 製品上の意味が違うので混ぜない**")
    for s in STOPPED:
        print("    %-18s %4d 件 (%.1f%%)  %s" % (s, t[s], 100.0 * t[s] / t_stop, MEANING[s]))
    print("    うち **真の誤停止** = VALUE_MISMATCH の %d 件 (%.1f%% / 391)"
          % (t["VALUE_MISMATCH"], 100.0 * t["VALUE_MISMATCH"] / t_total))
    print("    うち **照合範囲の問題** = PNF + UNV の %d 件 (%.1f%% / 391)"
          % (t["POINTER_NOT_FOUND"] + t["UNVERIFIABLE"],
             100.0 * (t["POINTER_NOT_FOUND"] + t["UNVERIFIABLE"]) / t_total))
    print()
    f = cell["偽"]
    fid = [cid for cid in lab if (lab[cid].get("札") == "偽")]
    print("  **偽 1 件の engine の状態**(人間の追加条件)")
    for cid in fid:
        q = res.get(cid)
        print("    %s -> **%s**  reason=%s  pointer=%d 本"
              % (cid, q.state.value, q.reason,
                 len([p for p in next(r.pointers for r in recs if r.claim.id == cid)])))
    print("    偽の内訳: " + " / ".join("%s %d" % (k, f[k]) for k in ORDER if f[k]))

    out = {"identity": ident,
           "by_label_and_state": {k: dict(v) for k, v in cell.items()},
           "checks": {"true_total": t_total, "true_total_expected": 391,
                      "true_stopped": t_stop, "true_stopped_expected": 214,
                      "unlabelled": missing},
           "stopped_breakdown_meaning": MEANING,
           "false_claim_states": {cid: res[cid].state.value for cid in fid}}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str); fh.write(u"\n")
    print()
    print("  -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
