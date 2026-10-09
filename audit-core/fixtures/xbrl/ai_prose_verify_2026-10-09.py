# -*- coding: utf-8 -*-
"""封 AI_PROSE_SEAL_2026-10-09 §2.4 の 4 段目 ― verify を回し、札と突き合わせる。

**門⑧ 札が先。** 独立監査の札の file が git に追跡され HEAD と一致していなければ
**1 行も verify しない。**「札が判定より先」を規律ではなく機械で守る
(7186ffc の失敗を踏まえた歯止め)。

出すもの:
  - 両腕の 4 状態の件数(人間の文 / AI の文、同じ実行・P7)
  - **2×2**(札 真/偽 × 判定 GROUNDED/止めた)
  - 予測 AI-3〜AI-7 と AI-4m の判定
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
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
MOD_ZIP = os.path.join(HERE, "ai_prose_instance_2026-10-09.zip")
LABELS = os.path.join(HERE, "ai_prose_labels_2026-10-09.json")
COUNTS = os.path.join(HERE, "ai_prose_counts_2026-10-09.json")
OUT = os.path.join(HERE, "ai_prose_result_2026-10-09.json")
PROFILE = V.P7

# 人間の文の誤停止の参照値。**この実験では人間の文の札を作っていない。**
# 既存の記録(CONFIRMATION_RESULT_XBRL_2026-10-08.md §2。人間の読み・**盲検ではない**):
# 止まった 19 件のうち、止まるのが正しいのは 4 件、こちら側の欠陥は 15 件。
HUMAN_MISSTOP_RECORDED = 15
HUMAN_CLAIMS_RECORDED = 91


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def gate8():
    """札の file が追跡され HEAD と一致しているか。"""
    rel = os.path.relpath(LABELS, REPO)
    if not os.path.exists(LABELS):
        return ["%s が無い ― 札がまだ付いていない" % rel]
    if git("ls-files", "--error-unmatch", "--", rel).returncode != 0:
        return ["%s が git に追跡されていない ― **札をコミットしてから verify する**" % rel]
    if git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        return ["%s が HEAD と違う ― 札が後から書き換えられている" % rel]
    return []


def states(results_by_id):
    return collections.Counter(r.state for r in results_by_id.values())


def main():
    bad = gate8()
    if bad:
        print("止まる 門⑧:")
        for b in bad:
            print("  " + b)
        print("  **verify は 1 行も走らせていない。**")
        return 3
    print("門⑧ 通過 ― 札は追跡済みで HEAD と一致(**札が判定より先**)")

    with open(os.path.join(CACHE, "%s.zip" % DOC), "rb") as fh:
        human_zb = fh.read()
    with open(MOD_ZIP, "rb") as fh:
        ai_zb = fh.read()

    # **同じ実行で両腕。**
    h_recipes, h_res, _ = INS.run_verification(DOC, PROFILE, lambda: human_zb)
    a_recipes, a_res, _ = INS.run_verification(DOC, PROFILE, lambda: ai_zb)
    h_st, a_st = states(h_res), states(a_res)
    ORDER = ("GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE")

    print()
    print("  %-10s %5s %9s %6s %6s %6s %6s" % ("腕", "主張", "GROUNDED", "VM", "PNF", "UNV", "束縛"))
    arms = {}
    for name, recs, st, res in (("人間の文", h_recipes, h_st, h_res), ("AI の文", a_recipes, a_st, a_res)):
        bound = sum(1 for r in recs if r.claim.subject is not None)
        arms[name] = {"claims": len(recs), "bound": bound,
                      **{k: st[k] for k in ORDER}}
        print("  %-10s %5d %9d %6d %6d %6d %6d"
              % (name, len(recs), st["GROUNDED"], st["VALUE_MISMATCH"],
                 st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], bound))

    # 札と突き合わせ
    lab = json.load(open(LABELS, encoding="utf-8"))
    by_id = {r["id"]: r for r in lab["labels"]}
    cell = collections.Counter()
    false_grounded, miss_stop = [], []
    unlabelled = []
    for r in a_recipes:
        cid = r.claim.id
        res = a_res.get(cid)
        if res is None:
            continue
        mark = (by_id.get(cid) or {}).get("札")
        if mark is None:
            unlabelled.append(cid); continue
        passed = res.state == "GROUNDED"
        if mark == "判定不能":
            cell["判定不能・通過" if passed else "判定不能・停止"] += 1
            continue
        key = ("%s・%s" % (mark, "通過" if passed else "停止"))
        cell[key] += 1
        if mark == "偽" and passed:
            contract = r.contract
            false_grounded.append({
                "id": cid, "subject": r.claim.subject, "value": r.claim.value,
                "unit": r.claim.unit, "form": r.claim.form.value,
                "comparator": None if contract is None else contract.comparator,
                "pointers": [str(p) for p in r.pointers],
                "recomputed": res.recomputed,
                "誤りの型": (by_id.get(cid) or {}).get("誤りの型"),
                "根拠": (by_id.get(cid) or {}).get("根拠"),
            })
        if mark == "真" and not passed:
            miss_stop.append({"id": cid, "state": res.state, "reason": res.reason})

    n_true = cell["真・通過"] + cell["真・停止"]
    n_false = cell["偽・通過"] + cell["偽・停止"]
    print()
    print("  2×2(札 × 判定)― 判定不能は別立て")
    print("  %-14s %10s %10s" % ("", "GROUNDED", "止めた"))
    print("  %-14s %10d %10d" % ("主張が真", cell["真・通過"], cell["真・停止"]))
    print("  %-14s %10d %10d" % ("主張が偽", cell["偽・通過"], cell["偽・停止"]))
    print("  %-14s %10d %10d" % ("判定不能", cell["判定不能・通過"], cell["判定不能・停止"]))
    print("  真 %d / 偽 %d / 判定不能 %d / 札なし %d"
          % (n_true, n_false, cell["判定不能・通過"] + cell["判定不能・停止"], len(unlabelled)))

    # 予測の判定
    def num_bound_grounded(recs, res):
        nb = [r for r in recs if r.claim.id.startswith("N") and r.claim.subject is not None]
        g = sum(1 for r in nb if res[r.claim.id].state == "GROUNDED")
        return g, len(nb), (g / float(len(nb)) if nb else 0.0)
    hg, hn, hr = num_bound_grounded(h_recipes, h_res)
    ag, an_, ar = num_bound_grounded(a_recipes, a_res)

    v = {}
    v["AI-3"] = {"予測": "束縛できた数の主張のうち GROUNDED の割合は AI ≥ 人間",
                 "人間": "%d/%d = %.1f%%" % (hg, hn, hr * 100),
                 "AI": "%d/%d = %.1f%%" % (ag, an_, ar * 100),
                 "判定": "当たり" if ar >= hr else "外れ"}
    nfg = cell["偽・通過"]
    v["AI-4"] = {"予測": "誤って GROUNDED が 1〜6 件", "実測": nfg,
                 "判定": "当たり" if 1 <= nfg <= 6 else "外れ",
                 "注": "0 件なら予測の外れであり、同時に製品にとって最良の結果"}
    v["AI-5"] = {"予測": "偽の主張が 2〜12 件", "実測": n_false,
                 "判定": "当たり" if 2 <= n_false <= 12 else "外れ"}
    if n_false:
        rec = cell["偽・停止"] / float(n_false)
        v["AI-6"] = {"予測": "正しい停止 ÷ 偽 が 0.5 以上 1.0 未満",
                     "実測": "%d/%d = %.3f" % (cell["偽・停止"], n_false, rec),
                     "判定": "当たり" if 0.5 <= rec < 1.0 else "外れ"}
    else:
        v["AI-6"] = {"予測": "同上", "実測": "偽 0 件", "判定": "評価不能(AI-5 が外れたため。封に先に書いた扱い)"}
    ai_missrate = len(miss_stop) / float(len(a_recipes))
    human_missrate = HUMAN_MISSTOP_RECORDED / float(HUMAN_CLAIMS_RECORDED)
    v["AI-7"] = {"予測": "誤停止率は AI < 人間",
                 "AI": "%d/%d = %.1f%%(札で測った)" % (len(miss_stop), len(a_recipes), ai_missrate * 100),
                 "人間": "%d/%d = %.1f%%(**この実験の札ではない。**2026-10-08 の記録・人間の読み・盲検ではない)"
                          % (HUMAN_MISSTOP_RECORDED, HUMAN_CLAIMS_RECORDED, human_missrate * 100),
                 "判定": "当たり" if ai_missrate < human_missrate else "外れ",
                 "注": "両腕で札の作り方が違う(AI は盲検の札・人間は過去の非盲検の読み)。この非対称は結論の強さを下げる"}
    v["AI-4m"] = {"予測": "誤った通過の経路は総当たり探索(recipes.py:212)か abs 枝",
                  "件数": len(false_grounded),
                  "判定": "誤った通過が 0 件なので評価不能" if not false_grounded else "下の一覧で経路を人が見る"}

    print()
    for k in ("AI-3", "AI-4", "AI-5", "AI-6", "AI-7", "AI-4m"):
        print("  %-6s %s" % (k, v[k].get("判定")))

    out = {"seal": "docs/AI_PROSE_SEAL_2026-10-09.md", "profile": PROFILE.name,
           "same_execution": True, "gate8_labels_committed_first": True,
           "arms": arms, "two_by_two": dict(cell),
           "labels_summary": collections.Counter(r["札"] for r in lab["labels"]),
           "false_grounded": false_grounded, "miss_stop_count": len(miss_stop),
           "unlabelled_ids": unlabelled, "predictions": v}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str); fh.write(u"\n")
    print()
    print("誤った通過 %d 件 / 誤停止 %d 件 -> %s" % (len(false_grounded), len(miss_stop), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
