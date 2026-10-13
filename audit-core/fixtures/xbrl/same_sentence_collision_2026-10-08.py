# -*- coding: utf-8 -*-
"""同じ文の中の 2 件以上の主張が**同じ相手**に結ばれていないかを機械で確かめる。
Core のコードではない。

人間の指示(2026-10-08): 「新しく通った中から、同じ文の別の勘定科目に結んだものが
無いかを機械で確かめる(同じ文の中で 2 つの主張が同じ相手を指していないか)。」

## 何を衝突と数えるか

同じ文(``provenance.sentence``)の中の 2 件以上の主張が、**pointer の集合が完全に同じ**
(順序は無視)で結ばれていたら 1 つの衝突とする。

これは `T007`/`T008`(同じ文の 2 つの「増加」が当期−前期の同じ対に結ばれていた)と
`T021`/`T022` の型である ― 60 件の確認で人間が見つけ、直し 6 で解消した欠陥。

**同じ相手に結ぶこと自体が常に誤りとは限らない**(同じ数を 2 回言う文もある)。
だから**件数と原文を出して、人が読める形にする**。この script は正誤を決めない。

    python3 fixtures/xbrl/same_sentence_collision_2026-10-08.py --doc S100Z4Q1 \
        [--profiles P7 P10 P11] [--json out.json]

通信はしない。API は呼ばない(費用 0 円)。
"""

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

import audit_core as core  # noqa: E402
from adapters.xbrl import edinet as E, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V  # noqa: E402


def rows_for(zb, inst, profile):
    num, txt = R.build_raw_claims(zb, profile)
    recipes = [R.claim_to_recipe(c, "num") for c in num] + [R.claim_to_recipe(c, "text") for c in txt]
    raws = list(num) + list(txt)
    results = core.verify_all(recipes, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))
    out = []
    for raw, rc, rs in zip(raws, recipes, results):
        if not rs.pointers:
            continue
        out.append({
            "id": raw["id"], "kind": rc.claim.provenance["kind"], "sentence": raw["sentence"],
            "state": rs.state.value, "subject": rc.claim.subject, "value": rc.claim.value,
            "unit": rc.claim.unit, "word": raw.get("word"), "span": raw.get("span"),
            "pointers": sorted(rs.pointers), "recomputed": rs.recomputed,
        })
    return out


def collisions(rows):
    """``(文の番号, pointer の集合)`` が同じ束縛済みの主張の群。2 件以上の群だけ返す。"""

    by = collections.defaultdict(list)
    for r in rows:
        by[(r["sentence"], tuple(r["pointers"]))].append(r)
    return [v for v in by.values() if len(v) >= 2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--profiles", nargs="+", default=["P7", "P10", "P11"])
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    zb = open(E.cache_path(a.doc), "rb").read()
    inst = I.load_instance(zb)
    out = {"doc": a.doc, "profiles": {}}
    for name in a.profiles:
        rows = rows_for(zb, inst, V.PROFILES[name])
        groups = collisions(rows)
        same_kind = [g for g in groups if len({r["kind"] for r in g}) == 1]
        # **群の数ではなく、巻き込まれた主張の件数で数える。**
        # 群の数は、1 つの大きな群が小さな群に分裂すると「増えた」と出てしまう
        # (語彙を増やして列挙の各項目が自分の主語を得ると、まさにそうなる)。
        # 指標の向きが逆になるので、主張の件数を正本にする。
        involved = sum(len(g) for g in groups)
        out["profiles"][name] = {
            "bound": len(rows), "collisions": len(groups), "collisions_same_kind": len(same_kind),
            "claims_involved": involved, "largest_group": max([len(g) for g in groups] or [0]),
            "groups": [[{k: r[k] for k in ("id", "kind", "state", "subject", "value", "unit", "word", "span",
                                           "recomputed", "pointers")} for r in g] for g in groups],
        }
        print("=" * 88)
        print("%s  profile=%s  束縛できた主張 %d / 衝突に巻き込まれた主張 %d 件 / %d 群(最大 %d 件・同じ種類だけの群 %d)" % (
            a.doc, name, len(rows), involved, len(groups), max([len(g) for g in groups] or [0]), len(same_kind)))
        for g in groups:
            print("  ---- 同じ文 %d・同じ pointer に %d 件 ----" % (g[0]["sentence"], len(g)))
            print("       ptr=%s" % (g[0]["pointers"],))
            for r in g:
                print("       %-5s %-4s %-16s subj=%s val=%s word=%s recomp=%s" % (
                    r["id"], r["kind"], r["state"], r["subject"], r["value"], r["word"], r["recomputed"]))
                print("             span=%s" % (r["span"] or "")[:72])
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("written:", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
