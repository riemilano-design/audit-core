# -*- coding: utf-8 -*-
"""独立判定と、旧エンジン・新エンジン(規則 4 あり)の束縛を突き合わせる。

**この採点の定義は、独立 3 席の回答を 1 行も見る前に書いてコミットした**
(人間の裁定 2026-10-12 の禁止事項「結果を見てからの候補定義の調整」と同じ理由)。

採点の定義(ここを後から変えない):

* **独立判定が「判定不能」の行** ― エンジンの正誤を判定しない。**別に数える。**
* **独立判定が「独立判定」の行** ― 独立判定の `(要素, context)` を正解とし、
  エンジンの pointer と次のように突き合わせる。

  | エンジンの状態 | pointer の一致 | 分類 |
  |---|---|---|
  | 通過(GROUNDED) | 先頭の fact が一致 | **正答** |
  | 通過(GROUNDED) | 先頭は違うが pointer のどれかが一致 | **一致(緩い)** ― 正答に数えず別に出す |
  | 通過(GROUNDED) | どれも一致しない | **誤った束縛** |
  | 停止 | 先頭の fact が一致 | **誤停止(束縛は当たっていた)** |
  | 停止 | どれも一致しない | **誤停止(束縛も違う)** |

* **エンジンの pointer が対(derived_value)で、独立判定が 1 件の fact を挙げている行**は、
  「形が違う(対 vs 単一)」として**別に数える**。無理に正答・誤りへ寄せない。
* 正答率の分母は **「独立判定が確定した行」**だけとし、判定不能を分母に入れない。

使い方:
    python3 audit-core/fixtures/xbrl/score_blind51_2026-10-12.py <audit-core の道> \
        --answers <回答 JSON を 1 つ以上> --key <blind51_key_2026-10-12.json> \
        --engine <エンジンの出力 JSON> [--label 旧エンジン]

`--engine` の JSON は {"<docID>": {"<claim id>": {"state": ..., "pointers": [...]}}} の形。
"""
import argparse
import json
import os
import sys
from collections import Counter


def load_answers(paths):
    rows = {}
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        for r in d["行"]:
            key = r["行の鍵"]
            if key in rows:
                raise SystemExit("行の鍵が重複している: %s" % (key,))
            rows[key] = {"判定者": d.get("判定者"), **r}
    return rows


def ptr_parts(p):
    """'xbrl:jppfs_cor:X@CurrentYearInstant' -> ('jppfs_cor:X', 'CurrentYearInstant')"""
    if not isinstance(p, str) or "@" not in p:
        return None
    body = p.split(":", 1)[1] if p.startswith("xbrl:") else p
    name, _, ctx = body.rpartition("@")
    return (name, ctx)


def classify(ans, eng):
    """1 行を分類する。返すのは (分類, 補足)。"""
    if ans["判定"] != "独立判定":
        return ("判定不能", None)
    truth = (ans.get("要素"), ans.get("context"))
    if truth[0] is None or truth[1] is None:
        return ("判定不能", "要素か context が null")
    if eng is None:
        return ("エンジンの出力が無い", None)
    facts = [q for q in (ptr_parts(p) for p in (eng.get("pointers") or [])) if q]
    passed = eng.get("state") == "GROUNDED"
    is_pair = len(facts) >= 2
    head_match = bool(facts) and facts[0] == truth
    any_match = truth in facts
    if is_pair:
        return ("形が違う(対 vs 単一)", "先頭一致" if head_match else ("どれか一致" if any_match else "不一致"))
    if passed:
        if head_match:
            return ("正答", None)
        if any_match:
            return ("一致(緩い)", None)
        return ("誤った束縛", "engine=%s@%s" % (facts[0] if facts else ("", "")))
    if head_match:
        return ("誤停止(束縛は当たっていた)", eng.get("reason"))
    return ("誤停止(束縛も違う)", eng.get("reason"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("here")
    ap.add_argument("--answers", nargs="+", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--label", default="エンジン")
    ap.add_argument("--targets-only", action="store_true", help="おとりを除いて 51 件だけで数える")
    a = ap.parse_args()

    answers = load_answers(a.answers)
    key = json.load(open(a.key, encoding="utf-8"))["map"]
    engine = json.load(open(a.engine, encoding="utf-8"))

    counts = Counter()
    detail = []
    for row_key, ans in sorted(answers.items()):
        meta = key.get(row_key)
        if meta is None:
            raise SystemExit("鍵に無い行: %s" % (row_key,))
        if a.targets_only and not meta["対象"]:
            continue
        eng = (engine.get(meta["docID"]) or {}).get(meta["id"])
        kind, extra = classify(ans, eng)
        counts[kind] += 1
        detail.append({"行の鍵": row_key, "docID": meta["docID"], "id": meta["id"],
                       "対象": meta["対象"], "分類": kind, "補足": extra,
                       "独立判定": [ans.get("要素"), ans.get("context")],
                       "エンジン": [eng.get("state"), eng.get("pointers")] if eng else None,
                       "判定者": ans.get("判定者")})

    decided = sum(n for k, n in counts.items() if k not in ("判定不能", "エンジンの出力が無い"))
    print("== %s(%s)" % (a.label, "51 件のみ" if a.targets_only else "98 行すべて"))
    for k, n in counts.most_common():
        print("   %-28s %3d" % (k, n))
    print("   ---")
    print("   独立判定が確定した行(分母)        %3d" % (decided,))
    if decided:
        print("   正答                              %3d  (%.1f%%)" % (counts["正答"], 100.0 * counts["正答"] / decided))
    print("   判定不能(分母に入れない)          %3d" % (counts["判定不能"],))
    out = os.environ.get("AC_OUT")
    if out:
        json.dump({"label": a.label, "targets_only": a.targets_only,
                   "counts": dict(counts), "decided": decided, "detail": detail},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("   written", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
