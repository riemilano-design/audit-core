# -*- coding: utf-8 -*-
"""候補の定義の封の下ごしらえ: 3 形態が材料の中に何件あるかを数える。
実装はしない。候補集合の構造だけを測る。"""
import json, os, sys
from collections import Counter, defaultdict
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V
from adapters.xbrl import instance as I
from tests.adapters.xbrl import _material as M

def classify(group):
    """同じ (context, 値, 単位) を持つ fact 群の、要素名の関係を分類する。"""
    names = [f["name"] for f in group]
    locals_ = [n.split(":")[-1] for n in names]
    if len(set(names)) == 1:
        return "(イ) 同じ要素の重複"
    base = set()
    for l in locals_:
        base.add(l[:-len("SummaryOfBusinessResults")] if l.endswith("SummaryOfBusinessResults") else l)
    if len(base) == 1:
        return "(ア) 別名対(SummaryOfBusinessResults)"
    # Income/IncomeLoss の読み替えも facts_for が同一視している
    base2 = set(b.replace("IncomeLoss", "Income") for b in base)
    if len(base2) == 1:
        return "(ア) 別名対(Income/IncomeLoss)"
    return "(ウ) 異なる要素名"

def report(tag, zb, profile):
    inst = None
    # facts/contexts は build_raw_claims の中で作られるので、同じ関数を使って取り出す
    import adapters.xbrl.recipes as RR
    facts_holder = {}
    orig = I.facts_for
    def spy(elems, facts, contexts, member=None, want_ctx=None):
        facts_holder["facts"] = facts; facts_holder["contexts"] = contexts
        return orig(elems, facts, contexts, member, want_ctx)
    I.facts_for = spy
    RR.I.facts_for = spy
    num, text = RR.build_raw_claims(zb, profile)
    I.facts_for = orig; RR.I.facts_for = orig
    facts = facts_holder["facts"]
    groups = defaultdict(list)
    for f in facts:
        if not (f["unit"] and f["unit"].upper().startswith("JPY")):
            continue
        groups[(f["context"], f["value"], f["unit"])].append(f)
    multi = {k: v for k, v in groups.items() if len(v) >= 2}
    cc = Counter(classify(v) for v in multi.values())
    print("%s: JPY fact %d 件 / (context,値,単位) の組 %d / **2 件以上の組 %d**" % (tag, sum(len(v) for v in groups.values()), len(groups), len(multi)))
    for k, n in cc.most_common():
        print("    %-38s %d 組" % (k, n))
    # 要素名が 2 種類以上の組だけ
    diff_names = {k: v for k, v in multi.items() if len({f["name"] for f in v}) >= 2}
    print("    うち要素名が 2 種類以上: %d 組" % len(diff_names,))
    ex = sorted(diff_names.items(), key=lambda kv: -len(kv[1]))[:4]
    for k, v in ex:
        print("      ctx=%-22s 値=%-18s %s" % (k[0], format(int(k[1]), ",d"), [f["name"] for f in v]))
    return {"tag": tag, "groups": len(groups), "multi": len(multi), "by_class": dict(cc), "diff_names": len(diff_names)}

out = []
ZIP = os.environ["AC_ZIP"]
with open(ZIP, "rb") as f:
    out.append(report("S100Z4Q1(P7)", f.read(), V.P7))
out.append(report("1B(P1)", M.load_zip_bytes(M.DOC_1["docID"], M.DOC_1["sha256"]), V.P1))
out.append(report("5F(P5F)", M.load_zip_bytes(M.DOC_5["docID"], M.DOC_5["sha256"]), V.P5F))
json.dump(out, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1)
