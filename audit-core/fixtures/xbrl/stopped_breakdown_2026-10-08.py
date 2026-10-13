# -*- coding: utf-8 -*-
"""「直す前」(profile P7)に止まった主張を、理由コード別に出し、
`no_element` の群については**元データに在るかどうかの証拠**を一緒に印字する計測 script。
Core のコードではない。

人間の指示(2026-10-08): 「2 社目・3 社目の『直す前』の止まった件数を理由コード別に出す。
1 社目と同じく『元データに無いので止まるのが正しい』と『こちらの漏れ』に分ける。」

## 分けるための証拠(判定ではなく証拠を出す)

ZIP の label linkbase は**会社拡張の 15 件だけ**で、標準タクソノミ(jppfs_cor/jpcrp_cor)の
日本語ラベルは入っていない(1 社目: 249 要素のうち label で引けるのは 8 件)。
**だから「その勘定科目が書類に在るか」をラベルでは判定できない。** 代わりに次の 2 つを出す。

1. **`facts_any`** ― 語彙が割り当てた要素名(`elems`)に、**context を問わず** fact が 1 件でも
   在るか(`instance.facts_for` と同じ完全一致・部分一致の規則を、context の選別だけ外して当てる)。
2. **`stem_siblings`** ― 要素名を CamelCase で区切り、**4 文字以上のトークンを 1 つ以上共有する**
   書類の中の要素名。これが在れば「同じ系統の勘定科目は書類に在るが、語彙が別の名前を指している」
   = **こちらの漏れ**の証拠になる。無ければ「元データに無い」の証拠になる。

**どちらも証拠であって判定ではない。** 最後の振り分けは人が読む。この script は
**振り分けの列を作らない**(作ると証拠を見ずに列だけ読まれる)。

    python3 fixtures/xbrl/stopped_breakdown_2026-10-08.py --doc S100Z4Q1 [--profile P7] [--json out.json]

通信はしない。API は呼ばない(費用 0 円)。
"""

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

import audit_core as core  # noqa: E402
from adapters.xbrl import edinet as E, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V  # noqa: E402

CAMEL = re.compile(r"[A-Z][a-z0-9]*|[a-z0-9]+")
MIN_TOKEN = 4  # 語幹として数えるトークンの最短の長さ。字で書く。


def tokens(name):
    return [t for t in CAMEL.findall(name.split(":")[-1]) if len(t) >= MIN_TOKEN]


def facts_anywhere(elems, facts):
    """``instance.facts_for`` の要素の選び方(完全一致 → 部分一致)を、context の
    選別だけ外して当てる。「その要素名の fact が書類のどこかに在るか」を見るため。
    """

    if not elems:
        return []
    exact, loose = [], []
    for f in facts:
        local = f["name"].split(":")[-1]
        if any(local == e or local == e + "SummaryOfBusinessResults"
               or local == e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults" for e in elems):
            exact.append(f)
        elif any(e.lower() in local.lower() for e in elems):
            loose.append(f)
    return exact or loose


def stem_siblings(elems, doc_names, limit=6):
    """``elems`` のどれかと 4 文字以上のトークンを共有する、書類の中の要素名。
    共有したトークン数の多い順。
    """

    want = set()
    for e in elems or []:
        want |= set(t.lower() for t in tokens(e))
    if not want:
        return []
    rows = []
    for n in doc_names:
        shared = want & set(t.lower() for t in tokens(n))
        if shared:
            rows.append((len(shared), sorted(shared), n))
    rows.sort(key=lambda r: (-r[0], r[2]))
    return [{"element": n, "shared": sh} for _k, sh, n in rows[:limit]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--profile", default="P7")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    zb = open(E.cache_path(a.doc), "rb").read()
    inst = I.load_instance(zb)
    profile = V.PROFILES[a.profile]
    num, txt = R.build_raw_claims(zb, profile)
    raws = list(num) + list(txt)
    recipes = [R.claim_to_recipe(c, "num") for c in num] + [R.claim_to_recipe(c, "text") for c in txt]
    results = core.verify_all(recipes, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))

    doc_names = sorted({f["name"] for f in inst["facts"]})
    rows = []
    for raw, rc, rs in zip(raws, recipes, results):
        if rs.state.value == "GROUNDED":
            continue
        kind = rc.claim.provenance["kind"]
        subj = rc.claim.subject
        elems = None
        if subj:
            from adapters.xbrl import extract as X
            # 語彙が割り当てた要素名。主語の引き方は本体と同じ 1 か所を通す。
            _w, elems = X.subject_of("%s " % subj, len(subj) + 1, profile.subjects)
        fa = facts_anywhere(elems, inst["facts"])
        rows.append({
            "id": raw["id"], "kind": kind, "state": rs.state.value,
            "reason_core": rs.reason, "reason_raw": raw.get("reason"),
            "subject": subj, "elems": elems, "value": rc.claim.value, "unit": rc.claim.unit,
            "word": raw.get("word"), "span": raw.get("span"),
            "pointers": list(rs.pointers), "recomputed": rs.recomputed,
            "facts_any": len(fa),
            "facts_any_contexts": sorted({f["context"] for f in fa})[:8],
            "facts_any_names": sorted({f["name"] for f in fa})[:4],
            "stem_siblings": stem_siblings(elems, doc_names),
        })

    C = collections.Counter
    key = lambda r: "%s / %s" % (r["state"], r["reason_core"] or r["reason_raw"] or "(なし)")
    tally = C(key(r) for r in rows)
    print("=" * 84)
    print("%s  profile=%s  主張 %d 件 / 止まった %d 件 (%.1f%%)" % (
        a.doc, a.profile, len(raws), len(rows), 100.0 * len(rows) / len(raws)))
    print("-" * 84)
    for k, v in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])):
        print("  %3d  %s" % (v, k))
    print("-" * 84)
    print("内訳の証拠(facts_any = context を問わず要素の fact が在る件数)")
    for r in sorted(rows, key=lambda r: (r["state"], r["reason_core"] or "", r["id"])):
        print("  %-5s %-4s %-18s %-42s subj=%s elems=%s" % (
            r["id"], r["kind"], r["state"], r["reason_core"] or r["reason_raw"] or "-", r["subject"], r["elems"]))
        print("        facts_any=%d %s" % (r["facts_any"], r["facts_any_names"] if r["facts_any"] else ""))
        if r["facts_any"]:
            print("        ctx=%s" % (r["facts_any_contexts"],))
        if not r["facts_any"]:
            sib = r["stem_siblings"]
            print("        stem_siblings=%s" % ([s["element"] for s in sib] if sib else "(無し)"))
        print("        span=%s" % (r["span"] or "")[:72])
    if a.json:
        json.dump({"doc": a.doc, "profile": a.profile, "claims": len(raws), "stopped": len(rows),
                   "tally": dict(tally), "rows": rows},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("written:", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
