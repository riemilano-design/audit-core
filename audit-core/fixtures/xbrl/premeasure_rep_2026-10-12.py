# -*- coding: utf-8 -*-
"""代表選択の封の下ごしらえ: 畳んだ群の構成を数える(実装はしない)。"""
import json, sys, os
from collections import Counter
HERE=sys.argv[1]; sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R, vocabulary as V, instance as I
from tests.adapters.xbrl import _material as M
S="SummaryOfBusinessResults"
def kind(name):
    pre, local = name.split(":")[0], name.split(":")[-1]
    if local.endswith(S): return "5年表(Summary)"
    if pre=="jppfs_cor": return "財務諸表本体(jppfs)"
    if pre=="jpcrp_cor": return "jpcrp(非Summary)"
    return "会社拡張"
rec={}
_o=R._direct_value_claim
def spy(claim,s,a,b,sign,num,unit,prec,subj,elems,member,facts,contexts):
    out=_o(claim,s,a,b,sign,num,unit,prec,subj,elems,member,facts,contexts)
    if subj:
        is_diff = bool(R._MONEY_UNIT_RE_AFTER.search(s[b:b+4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(s[max(0,a-25):a]))
        want = "CurrentYear"
        pool=[f for f in I.facts_for(elems,facts,contexts,member,want_ctx=want) if f["unit"] and f["unit"].upper().startswith("JPY")]
        groups={}
        for f in pool: groups.setdefault((f["context"],f["value"],f["unit"]),[]).append(f)
        rec[claim["id"]]={"is_diff":is_diff,"n_groups":len(groups),
            "groups":[sorted({kind(f["name"]) for f in g}) for g in groups.values()],
            "names":[sorted({f["name"].split(":")[-1] for f in g}) for g in groups.values()]}
    return out
R._direct_value_claim=spy
tot=Counter()
for tag,doc,prof in (("1B",M.DOC_1,V.P1),("5F",M.DOC_5,V.P5F)):
    rec.clear(); R.build_raw_claims(M.load_zip_bytes(doc["docID"],doc["sha256"]),prof)
    c=Counter()
    for cid,e in rec.items():
        if e["n_groups"]!=1: continue
        g=e["groups"][0]; names=e["names"][0]
        if len(names)==1: c["群が 1 要素(代表の選択なし)"]+=1
        elif "財務諸表本体(jppfs)" in g and "5年表(Summary)" in g:
            # jppfs が 2 種以上なら jppfs 優先でも決まらない
            jp=[n for n in names if not n.endswith(S)]
            c["jppfs + Summary、jppfs が 1 種(優先で決まる)" if len(jp)==1 else "jppfs + Summary、jppfs が 2 種以上(優先でも決まらない)"]+=1
        elif "5年表(Summary)" in g and "財務諸表本体(jppfs)" not in g: c["Summary だけ(本体が無い)"]+=1
        else: c["その他(本体が 2 種以上 / 会社拡張)"]+=1
    print("== %s: 候補が 1 群に畳まれる数の Claim %d" % (tag, sum(c.values())))
    for k,n in c.most_common(): print("   %-44s %d" % (k,n))
    tot+=c
print("== 合計"); [print("   %-44s %d" % (k,n)) for k,n in tot.most_common()]
