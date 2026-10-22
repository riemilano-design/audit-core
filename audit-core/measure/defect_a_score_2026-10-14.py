# -*- coding: utf-8 -*-
"""欠陥 A の評価を採点する(封 docs/DEFECT_A_EVAL_SEAL_2026-10-14.md §5・§7)。

採点は**封じたとおり**:
  F-1 動いた行のうち 2 席が `差` で一致した割合(分母は L_A)  合格線 >= 90%
  F-2 動いた行のうち 2 席が `水準` で一致した件数              合格線 = 0
  F-3 「VALUE_MISMATCH -> GROUNDED」以外の向きに動いた行        合格線 = 0
  F-4 母数 L_A                                              合格線 >= 20
**2 席が食い違った行・判定不能の行は F-1 の分子に入らない(分母には入る)。**

§7 の「合否に入れないが必ず報告する」6 項目も出す。通信しない。
"""
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

BASE = os.path.join(ROOT, "fixtures", "xbrl", "defect_a")
BA = os.path.join(BASE, "before_after_2026-10-14.json")
KEY = os.path.join(BASE, "commander_only", "key_2026-10-14.json")
S1 = os.path.join(BASE, "answers_seat1", "answer_2026-10-14.json")
S2 = os.path.join(BASE, "answers_seat2", "answer_2026-10-14.json")
OUT = os.path.join(BASE, "score_2026-10-14.json")
PROFILE = "P20"
MONEY = ("百万円", "千円", "円", "億円")
VERDICTS = ("差", "水準", "判定不能")


def _structure():
    p = os.path.join(ROOT, "measure", "defect_a_structure_2026-10-14.py")
    spec = importlib.util.spec_from_file_location("defect_a_structure", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ST = _structure()


def seat_rows(path, who):
    d = json.load(io.open(path, encoding="utf-8"))
    out = {}
    for r in d["行"]:
        v = r["判定"]
        if v not in VERDICTS:
            raise AssertionError("%s: %s の判定が enum 外 %r" % (who, r["行の鍵"], v))
        out[r["行の鍵"]] = {"判定": v, "項目名": r.get("項目名(文から読める範囲)"), "理由": r.get("理由")}
    return d, out


def report_items():
    """§7 の報告項目。8 書類の金額の主張を数え直す。"""
    from adapters.xbrl import recipes as R, vocabulary as V, edinet, instance as I, extract as E
    ba = json.load(io.open(BA, encoding="utf-8"))
    moved = {m["id"] for m in ba["result"][PROFILE]["moved"]}
    cond = collections.Counter()
    offsets = collections.Counter()
    for d in ba["docs"]:
        zb = io.open(edinet.cache_path(d), "rb").read()
        num, _ = R.build_raw_claims(zb, V.PROFILES[PROFILE])
        inst = I.load_instance(zb)
        ctxs = inst["contexts"]
        vals, units = {}, {}
        for f in inst["facts"]:
            k = (f["name"].split(":")[-1], f["context"])
            vals[k], units[k] = f["value"], f.get("unit")
        for c in num:
            if c.get("unit") not in MONEY:
                continue
            ps = [q for q in ([c["pointer"]] if isinstance(c.get("pointer"), str) else (c.get("pointer") or []))
                  if q.startswith("xbrl:")]
            if len(ps) != 1:
                continue
            elem = ps[0].split("@")[0].split(":")[-1]
            ctx = ps[0].split("@", 1)[1]
            period = "CurrentYear" if "CurrentYear" in ctx else ("Prior1Year" if "Prior1Year" in ctx else "?")
            other = (ctx.replace("CurrentYear", "Prior1Year") if period == "CurrentYear"
                     else ctx.replace("Prior1Year", "CurrentYear") if period == "Prior1Year" else ctx)
            if c.get("result") == "VALUE_MISMATCH":
                mem_a = frozenset(m.split(":")[-1] for m in (ctxs.get(ctx) or {}).get("members") or [])
                mem_b = frozenset(m.split(":")[-1] for m in (ctxs.get(other) or {}).get("members") or [])
                if period == "?":
                    cond["期間が隣接でない"] += 1
                elif mem_a != mem_b:
                    cond["集計範囲(member)が違う"] += 1
                elif units.get((elem, ctx)) != units.get((elem, other)):
                    cond["単位が違う"] += 1
                else:
                    cond["4 つの条件はすべて満たす"] += 1
    # ずれは **engine が実際に使った差**(after の recomputed)から出す。
    # context の対を文字置換で推測すると別の対を拾う(2026-10-14 に 1 件で -4227 単位という
    # 自分のバグの値を出した)。
    for m in ba["result"][PROFILE]["moved"]:
        stated = m["value"] * {"百万円": 10 ** 6, "千円": 10 ** 3, "円": 1, "億円": 10 ** 8}[m["unit"]]
        w, rc = m["claim_scale"], m["after"]["recomputed"]
        if w and rc is not None:
            offsets[round((abs(rc) - abs(stated)) / float(w), 3)] += 1
        else:
            offsets["測れない"] += 1
    return cond, offsets


def main():
    ba = json.load(io.open(BA, encoding="utf-8"))
    key = json.load(io.open(KEY, encoding="utf-8"))
    scored = {r["行の鍵"]: r["claim_id"] for r in key["rows_map"] if r["採点対象"]}
    moved = {m["id"] for m in ba["result"][PROFILE]["moved"]}
    if set(scored.values()) != moved:
        raise AssertionError("採点対象が動いた行と一致しない")
    raw1, a1 = seat_rows(S1, "席1")
    raw2, a2 = seat_rows(S2, "席2")
    for who, a in (("席1", a1), ("席2", a2)):
        if set(a) != {r["行の鍵"] for r in key["rows_map"]}:
            raise AssertionError("%s の行が材料と合わない(%d 行)" % (who, len(a)))

    agree = collections.Counter()
    pairs = collections.Counter()
    rows = []
    for k in sorted(scored):
        v1, v2 = a1[k]["判定"], a2[k]["判定"]
        pairs[(v1, v2)] += 1
        state = v1 if v1 == v2 else "食い違い"
        agree[state] += 1
        rows.append({"行の鍵": k, "claim_id": scored[k], "席1": v1, "席2": v2, "確定": state,
                     "席1の項目名": a1[k]["項目名"], "席2の項目名": a2[k]["項目名"]})
    L_A = len(scored)
    F1 = agree["差"] / float(L_A)
    F2 = agree["水準"]
    F3 = ba["result"][PROFILE]["F3"]
    verdict = []
    verdict.append(("F-1 >= 90%", F1 >= 0.90, "%.1f%% (%d/%d)" % (F1 * 100, agree["差"], L_A)))
    verdict.append(("F-2 = 0", F2 == 0, "%d 件" % F2))
    verdict.append(("F-3 = 0", F3 == 0, "%d 件" % F3))
    verdict.append(("F-4 >= 20", L_A >= 20, "%d 件" % L_A))

    # 混ぜた行(採点しない)の一致も報告する
    mixed = [r["行の鍵"] for r in key["rows_map"] if not r["採点対象"]]
    mixed_agree = collections.Counter()
    for k in mixed:
        v1, v2 = a1[k]["判定"], a2[k]["判定"]
        mixed_agree[v1 if v1 == v2 else "食い違い"] += 1

    cond, offsets = report_items()
    print("== 採点(封 §5)==")
    for name, ok, got in verdict:
        print("  %-12s %-4s %s" % (name, "合格" if ok else "不合格", got))
    print("\n  2 席の確定の内訳(採点対象 %d 件):" % L_A)
    for k, n in sorted(agree.items(), key=lambda kv: -kv[1]):
        print("    %-8s %d" % (k, n))
    print("\n  混ぜた行 %d 件(採点しない)の内訳:" % len(mixed))
    for k, n in sorted(mixed_agree.items(), key=lambda kv: -kv[1]):
        print("    %-8s %d" % (k, n))
    print("\n== 報告のみ(封 §7)==")
    print("  [金額の VALUE_MISMATCH の 4 条件]")
    for k, n in sorted(cond.items(), key=lambda kv: -kv[1]):
        print("    %-26s %d" % (k, n))
    print("  [動いた行のずれ(書かれた桁で割った値)]")
    for k, n in sorted(offsets.items(), key=lambda kv: str(kv[0])):
        print("    %-10s %d" % (k, n))
    print("  [profile 差] P20 L_A=%d / P16 L_A=%d"
          % (ba["result"]["P20"]["L_A"], ba["result"]["P16"]["L_A"]))
    print("  [奪われた件数(F-3 の内訳)] %d" % F3)

    out = {"purpose": "欠陥 A の評価の採点(封 docs/DEFECT_A_EVAL_SEAL_2026-10-14.md)",
           "profile": PROFILE, "L_A": L_A,
           "F1": F1, "F1_num": agree["差"], "F2": F2, "F3": F3,
           "verdict": {name: {"合否": "合格" if ok else "不合格", "値": got} for name, ok, got in verdict},
           "overall": "合格" if all(ok for _, ok, _ in verdict) else "不合格",
           "agree_counts": dict(agree), "pair_counts": {" / ".join(k): v for k, v in sorted(pairs.items())},
           "mixed_agree_counts": dict(mixed_agree), "mixed_n": len(mixed),
           "condition_counts": dict(cond),
           "offset_units": {str(k): v for k, v in sorted(offsets.items(), key=lambda kv: str(kv[0]))},
           "profile_L_A": {"P20": ba["result"]["P20"]["L_A"], "P16": ba["result"]["P16"]["L_A"]},
           "seats": {"席1": raw1.get("判定者"), "席2": raw2.get("判定者"),
                     "読んだファイル": {"席1": raw1.get("読んだファイル"), "席2": raw2.get("読んだファイル")}},
           "rows": rows}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n総合: %s" % out["overall"])
    print("->", OUT)


if __name__ == "__main__":
    main()
