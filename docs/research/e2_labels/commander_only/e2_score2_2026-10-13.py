# -*- coding: utf-8 -*-
"""E2 ラベル 第 2 便(不一致 6 件の再判定 + 再監査 B の残り 72 行 = 78 行)の採点。**回答を 1 行も読む前に書く。**
回答の形(第 2 便): 各行に "fact" 配列 [{"役割": 当期側/前期側/分子/分母/加算項, "要素", "context", "期間", "値", "単位"}] を持つ。
定義(後から変えない):
* 両席が独立判定で、fact 配列の {(役割, 要素, context)} の集合が一致 → 確定(厳密)。
  役割を無視した {(要素, context)} の集合が一致 → 確定(役割違い)(確定に数え、別欄に件数)。
  要素名の末尾 SummaryOfBusinessResults を外した名前(TotalAssets→Assets 込み)で一致 → 確定(同値類v0)(別欄)。ラベルに採るのは同値類v0。
* 片方が判定不能 → 判定不能(片側)。両方 → 判定不能(両側)。両方独立判定で違う → 不一致(多数決・第 3 席なし。全部列挙)。
* 再判定 6 件は第 1 便のラベルを**上書きしない**。別の欄 "第2便" として記録する(両便の結果を並べて人間が読む)。
* 再監査 B の残り 72 行は、B の同定との一致を記録だけする。
予測(読む前): 78 行のうち 確定(同値類v0) 62〜74、判定不能(両側) 2〜8、不一致 ≤ 6。再判定 6 件は 5 件が確定・T025 が判定不能か不一致。
外れ方: 確定 < 62 なら欄の設計の穴(3 回目)。不一致 > 6 なら同値類規則の穴。
"""
import json, sys, collections, os
def canon(e):
    e = e.split(':')[-1]
    if e.endswith('SummaryOfBusinessResults'): e = e[:-len('SummaryOfBusinessResults')]
    return {'TotalAssets': 'Assets'}.get(e, e)
def fs(row, mode):
    out=set()
    for f in row.get('fact') or []:
        if not f.get('要素'): continue
        e=f['要素'].split(':')[-1]
        if mode=='strict': out.add((f.get('役割'), e, f.get('context')))
        elif mode=='norole': out.add((e, f.get('context')))
        else: out.add((canon(e), f.get('context')))
    return out
def main(a_path,b_path,key_path,bstruct_path,prev_labels_path,out_path):
    A={r['行の鍵']:r for r in json.load(open(a_path))['行']}; B={r['行の鍵']:r for r in json.load(open(b_path))['行']}
    key=json.load(open(key_path))['map']; assert set(A)==set(B)==set(key),(len(A),len(B),len(key))
    bs={r['id']:r for r in json.load(open(bstruct_path))['rows']}
    cnt=collections.Counter(); sub=collections.Counter(); labels=[]; mism=[]; bcmp=collections.Counter(); redo=[]
    for k in sorted(key):
        a,b=A[k],B[k]; cid=key[k]['id']; da,db=a['判定']=='独立判定',b['判定']=='独立判定'
        if da and db:
            if fs(a,'canon')==fs(b,'canon') and fs(a,'canon'):
                cls='確定(同値類v0)'; sub['厳密']+=fs(a,'strict')==fs(b,'strict'); sub['役割違い']+= (fs(a,'strict')!=fs(b,'strict') and fs(a,'norole')==fs(b,'norole'))
            else: cls='不一致'; mism.append({'鍵':k,'id':cid,'席1':a,'席2':b})
        elif da or db: cls='判定不能(片側)'
        else: cls='判定不能(両側)'
        cnt[cls]+=1
        lab={'id':cid,'鍵':k,'由来':key[k]['由来'],'分類':cls,'形':[a.get('形'),b.get('形')],'fact(席1)':sorted(fs(a,'strict')),'fact(席2)':sorted(fs(b,'strict'))}
        if cid in bs:
            bf=set((canon(e),c) for e,c in (tuple(x) for x in bs[cid]['B が同定した fact [(要素, context)]']))
            r='未比較(未確定)' if not cls.startswith('確定') else ('B と同じ(同値類v0)' if fs(a,'canon')<=bf else 'B と違う')
            bcmp[r]+=1; lab['再監査Bとの比較(記録のみ)']=r
        if key[k]['由来'].startswith('再判定'): redo.append(lab)
        labels.append(lab)
    json.dump({'counts':dict(cnt),'確定の内訳':dict(sub),'再監査B との比較':dict(bcmp),'再判定6件(第1便は上書きしない)':redo,'labels':labels,'不一致の行':mism},open(out_path,'w'),ensure_ascii=False,indent=1)
    print(json.dumps({'counts':dict(cnt),'内訳':dict(sub),'B':dict(bcmp)},ensure_ascii=False))
if __name__=='__main__': main(*sys.argv[1:7])
