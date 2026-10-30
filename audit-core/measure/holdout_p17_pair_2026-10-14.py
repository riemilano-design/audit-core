# -*- coding: utf-8 -*-
"""封 §4(第 1 段)― 同じ書類に P16 と P17 を当てて、**ラベルの要らない数**を出す。

A-1  P17 が P16 で GROUNDED だった行を壊した件数
A-2  GROUNDED 件数の差
A-3  止めた割合(POINTER_NOT_FOUND + UNVERIFIABLE)の下がり幅

**行の対応づけは id でやらない。** P17 は主語の行を足す規則(``augment_subject_rows``)を
持つので主張の件数が変わり、id(並び順で付く番号)はずれる。中身の鍵
``(kind, form, subject, value, unit, word, span)`` で対応させ、**鍵が重複する行の件数も
出す**(重複があると対応づけが後勝ちになるので、数を見る前に知る必要がある)。

**分母**: P17 は主張の件数そのものが増えるので、率を単純に並べると比べられない
(2026-10-15 の「分母を揃える」)。だから次の 3 つを**全部**出す。

1. それぞれの profile の全部の行での率(分母が違うことを明記して並べる)
2. **共通の鍵だけ**に揃えた率(対で比べられる数)
3. P17 だけに在る行(増えた行)の状態の内訳(増えた行で稼いでいないかを見る)

通信しない(ZIP はキャッシュから読む)。
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import verify_document as VD  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17")
DRAWN = os.path.join(OUT, "drawn2_2026-10-14.json")
STOPPED = ("POINTER_NOT_FOUND", "UNVERIFIABLE")


def key_of(claim):
    return (claim.get("kind"), claim.get("form"), claim.get("subject"),
            claim.get("value"), claim.get("unit"), claim.get("word"), claim.get("span"))


def index_claims(claims):
    """鍵 -> 行。**重複した鍵の件数も返す**(後勝ちで潰れる分を隠さない)。"""

    out, dup = {}, 0
    for c in claims:
        k = key_of(c)
        if k in out:
            dup += 1
        out[k] = c
    return out, dup


def rate(counts, total):
    return None if not total else 100.0 * counts / total


def run_doc(doc_id):
    with open(os.path.join(CACHE, doc_id + ".zip"), "rb") as fh:
        zb = fh.read()
    a = VD.verify_document(zb, "P16", None)
    b = VD.verify_document(zb, "P17", None)
    ia, dup_a = index_claims(a["claims"])
    ib, dup_b = index_claims(b["claims"])
    common = set(ia) & set(ib)
    only_b = set(ib) - set(ia)
    only_a = set(ia) - set(ib)

    broke = [k for k in common if ia[k]["state"] == "GROUNDED" and ib[k]["state"] != "GROUNDED"]
    gained = [k for k in common if ia[k]["state"] != "GROUNDED" and ib[k]["state"] == "GROUNDED"]

    def tally(idx, keys):
        c = {}
        for k in keys:
            s = idx[k]["state"]
            c[s] = c.get(s, 0) + 1
        return c

    return {
        "doc": doc_id,
        "claims_P16": len(a["claims"]), "claims_P17": len(b["claims"]),
        "dup_key_P16": dup_a, "dup_key_P17": dup_b,
        "states_P16_all": a["document"]["states"], "states_P17_all": b["document"]["states"],
        "common": len(common), "only_P16": len(only_a), "only_P17": len(only_b),
        "common_states_P16": tally(ia, common), "common_states_P17": tally(ib, common),
        "only_P17_states": tally(ib, only_b), "only_P16_states": tally(ia, only_a),
        "broke": len(broke), "gained": len(gained),
        "broke_rows": [{"subject": ia[k]["subject"], "value": ia[k]["value"], "unit": ia[k]["unit"],
                        "span": (ia[k]["span"] or "")[:70],
                        "P16_pointer": (ia[k]["pointers"] or [None])[0],
                        "P17_state": ib[k]["state"],
                        "P17_pointer": (ib[k]["pointers"] or [None])[0]} for k in broke],
    }


def main():
    with io.open(DRAWN, encoding="utf-8") as fh:
        drawn = json.load(fh)
    docs = [d["docID"] for d in drawn["drawn"]]
    rows = [run_doc(d) for d in docs]

    tot = {"claims_P16": 0, "claims_P17": 0, "common": 0, "only_P17": 0, "only_P16": 0,
           "broke": 0, "gained": 0, "dup_key_P16": 0, "dup_key_P17": 0}
    g16 = g17 = s16 = s17 = cg16 = cg17 = cs16 = cs17 = 0
    for r in rows:
        for k in tot:
            tot[k] += r[k]
        g16 += r["states_P16_all"].get("GROUNDED", 0)
        g17 += r["states_P17_all"].get("GROUNDED", 0)
        s16 += sum(r["states_P16_all"].get(s, 0) for s in STOPPED)
        s17 += sum(r["states_P17_all"].get(s, 0) for s in STOPPED)
        cg16 += r["common_states_P16"].get("GROUNDED", 0)
        cg17 += r["common_states_P17"].get("GROUNDED", 0)
        cs16 += sum(r["common_states_P16"].get(s, 0) for s in STOPPED)
        cs17 += sum(r["common_states_P17"].get(s, 0) for s in STOPPED)

    summary = {
        "docs": docs, "totals": tot,
        "all_rows": {"P16": {"claims": tot["claims_P16"], "grounded": g16, "stopped": s16,
                             "grounded_pct": rate(g16, tot["claims_P16"]),
                             "stopped_pct": rate(s16, tot["claims_P16"])},
                     "P17": {"claims": tot["claims_P17"], "grounded": g17, "stopped": s17,
                             "grounded_pct": rate(g17, tot["claims_P17"]),
                             "stopped_pct": rate(s17, tot["claims_P17"])}},
        "common_rows": {"n": tot["common"],
                        "P16": {"grounded": cg16, "stopped": cs16,
                                "grounded_pct": rate(cg16, tot["common"]),
                                "stopped_pct": rate(cs16, tot["common"])},
                        "P17": {"grounded": cg17, "stopped": cs17,
                                "grounded_pct": rate(cg17, tot["common"]),
                                "stopped_pct": rate(cs17, tot["common"])}},
        "A1_broke": tot["broke"], "A1_gained_for_reference": tot["gained"],
        "A2_grounded_diff_all": g17 - g16, "A2_grounded_diff_common": cg17 - cg16,
        "A3_stopped_pct_drop_all": (rate(s16, tot["claims_P16"]) - rate(s17, tot["claims_P17"]))
        if tot["claims_P16"] and tot["claims_P17"] else None,
        "A3_stopped_pct_drop_common": (rate(cs16, tot["common"]) - rate(cs17, tot["common"]))
        if tot["common"] else None,
        "per_doc": rows,
    }
    p = os.path.join(OUT, "pair_P16_P17_2026-10-14.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)

    print("書類 %d 件: %s" % (len(docs), ", ".join(docs)))
    print("\n【それぞれの全部の行(分母が違う)】")
    for pn in ("P16", "P17"):
        a = summary["all_rows"][pn]
        print("  %s  主張 %4d / 一致 %4d (%.1f%%) / 止めた %4d (%.1f%%)"
              % (pn, a["claims"], a["grounded"], a["grounded_pct"], a["stopped"], a["stopped_pct"]))
    print("\n【共通の鍵だけ(分母を揃えた %d 行)】" % tot["common"])
    for pn in ("P16", "P17"):
        a = summary["common_rows"][pn]
        print("  %s  一致 %4d (%.1f%%) / 止めた %4d (%.1f%%)"
              % (pn, a["grounded"], a["grounded_pct"], a["stopped"], a["stopped_pct"]))
    print("\n  P17 だけに在る行 %d(状態 %s)" % (tot["only_P17"], summary["per_doc"] and
                                              json.dumps({k: sum(r["only_P17_states"].get(k, 0) for r in rows)
                                                          for k in ("GROUNDED", "VALUE_MISMATCH",
                                                                    "POINTER_NOT_FOUND", "UNVERIFIABLE")},
                                                         ensure_ascii=False)))
    print("  P16 だけに在る行 %d" % tot["only_P16"])
    print("  鍵の重複 P16 %d / P17 %d" % (tot["dup_key_P16"], tot["dup_key_P17"]))
    print("\n【封の合格線】")
    print("  A-1 壊した件数: %d(予測 0〜3 / 合格線 5 以下)" % tot["broke"])
    print("  A-2 一致の増減: 全部の行 %+d / 共通の行 %+d(合格線 1 件も減らない)"
          % (g17 - g16, cg17 - cg16))
    print("  A-3 止めた割合の下がり幅: 全部 %+.1f pt / 共通 %+.1f pt(予測 3〜12 / 合格線 2 以上)"
          % (summary["A3_stopped_pct_drop_all"], summary["A3_stopped_pct_drop_common"]))
    print("\n->", p)


if __name__ == "__main__":
    main()
