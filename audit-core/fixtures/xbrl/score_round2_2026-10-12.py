# -*- coding: utf-8 -*-
"""2 巡目(対の形)の独立判定と、エンジンの束縛を突き合わせる。
**この定義は 2 巡目の回答を 1 行も見る前にコミットした。** 1 巡目の採点(score_blind51)は変えない。

採点の定義:
* 独立判定が「判定不能」 → 別に数える(分母に入れない)。
* 独立判定の 形 が「差(当期−前期)」:
    エンジンの pointer が対(xbrl: が 2 本) → 2 本とも独立判定の {当期側, 前期側} と一致 = **正答**、
      1 本だけ一致 = **部分一致**、どちらも違う = 通過なら **誤った束縛** / 停止なら **誤停止(束縛も違う)**。
      2 本とも一致していて停止 = **誤停止(束縛は当たっていた)**。
    エンジンの pointer が単一 → **形が違う(単一 vs 差)**。pointer 空で停止 → **誤停止(束縛も違う)**。
* 独立判定の 形 が「単一」または「差額そのものの fact」:
    1 巡目と同じ(先頭一致 = 正答 / どれか一致 = 一致(緩い) / 不一致 = 誤った束縛 or 誤停止)。
    エンジンが対 → **形が違う(対 vs 単一)**。
* 1 巡目で独立判定が確定している行は、**1 巡目の判定を正本とする**(2 巡目は上書きしない)。
  その行の 2 巡目の判定は「席間の一致」として別に記録するだけで、証拠には数えない。
"""
import argparse, json, os, sys
from collections import Counter


def ptr_parts(p):
    if not isinstance(p, str) or "@" not in p:
        return None
    body = p.split(":", 1)[1] if p.startswith("xbrl:") else p
    name, _, ctx = body.rpartition("@")
    return (name, ctx)


def side(d):
    if not d or not d.get("要素") or not d.get("context"):
        return None
    return (d["要素"], d["context"])


def classify(ans, eng):
    if ans["判定"] != "独立判定":
        return ("判定不能", None)
    cur, pri = side(ans.get("当期側")), side(ans.get("前期側"))
    if eng is None:
        return ("エンジンの出力が無い", None)
    facts = [q for q in (ptr_parts(p) for p in (eng.get("pointers") or [])) if q]
    passed = eng.get("state") == "GROUNDED"
    form = ans.get("形")
    if form == "差(当期−前期)":
        if cur is None or pri is None:
            return ("判定不能", "差なのに片側が null")
        if not facts:
            return ("誤停止(束縛も違う)", eng.get("reason"))
        if len(facts) == 1:
            return ("形が違う(単一 vs 差)", None)
        hit = sum(1 for f in facts if f in (cur, pri))
        if hit == 2:
            return ("正答", None) if passed else ("誤停止(束縛は当たっていた)", eng.get("reason"))
        if hit == 1:
            return ("部分一致", None)
        return ("誤った束縛", None) if passed else ("誤停止(束縛も違う)", eng.get("reason"))
    # 単一 / 差額そのもの
    if cur is None:
        return ("判定不能", "当期側が null")
    if len(facts) >= 2:
        return ("形が違う(対 vs 単一)", None)
    if not facts:
        return ("誤停止(束縛も違う)", eng.get("reason"))
    if facts[0] == cur:
        return ("正答", None) if passed else ("誤停止(束縛は当たっていた)", eng.get("reason"))
    return ("誤った束縛", None) if passed else ("誤停止(束縛も違う)", eng.get("reason"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("here")
    ap.add_argument("--answers", nargs="+", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--round1-truth", required=True, help="independent_truth_2026-10-12.json")
    ap.add_argument("--label", default="エンジン")
    a = ap.parse_args()
    key = json.load(open(a.key, encoding="utf-8"))["map"]
    engine = json.load(open(a.engine, encoding="utf-8"))
    r1 = json.load(open(a.round1_truth, encoding="utf-8"))
    r1_decided = {(r["docID"], r["id"]) for r in r1["決定済み"]}
    rows = {}
    for p in a.answers:
        d = json.load(open(p, encoding="utf-8"))
        for r in d["行"]:
            if r["行の鍵"] in rows:
                raise SystemExit("行の鍵が重複: %s" % r["行の鍵"])
            rows[r["行の鍵"]] = {"判定者": d.get("判定者"), **r}
    counts, counts_target, detail, overlap = Counter(), Counter(), [], []
    for k, ans in sorted(rows.items()):
        m = key[k]
        eng = (engine.get(m["docID"]) or {}).get(m["id"])
        kind, extra = classify(ans, eng)
        rec = {"行の鍵": k, "docID": m["docID"], "id": m["id"], "対象": m["対象"], "形": ans.get("形"),
               "分類": kind, "補足": extra, "独立判定": [side(ans.get("当期側")), side(ans.get("前期側"))],
               "エンジン": [eng.get("state"), eng.get("pointers")] if eng else None, "判定者": ans.get("判定者")}
        if (m["docID"], m["id"]) in r1_decided:
            rec["1巡目で確定済み"] = True
            overlap.append(rec)
            continue
        detail.append(rec)
        counts[kind] += 1
        if m["対象"]:
            counts_target[kind] += 1
    for title, c in (("2 巡目で新たに測った行(1 巡目で未確定だった行)", counts), ("  うち対象", counts_target)):
        dec = sum(n for kk, n in c.items() if kk not in ("判定不能", "エンジンの出力が無い"))
        print("== %s — %s" % (a.label, title))
        for kk, n in c.most_common():
            print("   %-26s %3d" % (kk, n))
        print("   分母(確定した行) %d / 正答 %d / 判定不能 %d" % (dec, c["正答"], c["判定不能"]))
    print("   1 巡目で確定済みの行(席間の一致の記録のみ): %d" % len(overlap))
    out = os.environ.get("AC_OUT")
    if out:
        json.dump({"label": a.label, "counts": dict(counts), "counts_target": dict(counts_target),
                   "detail": detail, "overlap_round1": overlap}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("   written", out)


if __name__ == "__main__":
    sys.exit(main())
