# -*- coding: utf-8 -*-
"""E2 ラベル(層 P・無作為 120 件)の採点。**席の回答を 1 行も読む前に書いた**(sha256 を report に記録)。

定義(後から変えない):
* 席 A・B とも「独立判定」で、当期側/前期側の (要素, context) の集合が一致 → **確定(厳密)**。
  要素名の末尾 SummaryOfBusinessResults を除いた名前(TotalAssets→Assets の別名込み)で一致 → **確定(同値類 v0)**。
  厳密一致は同値類一致に含まれる。ラベルに採るのは同値類 v0 の一致(規則は人間の承認待ち。厳密の件数も併記)。
* 片方が判定不能 → **判定不能(片側)**。両方が判定不能 → **判定不能(両側)**。
* 両方が独立判定で fact が違う → **不一致**。多数決・第 3 席の裁定はしない。不一致の行は id と両席の答えを全部出す。
* 「形」の一致は別に数える(fact が一致していて形が違う行は確定に数え、形の欄に両方を残す)。
* 分母は 120。確定・判定不能(片側/両側)・不一致の 4 つで 120 になる。
* 再監査 B(100 行、独立)と重なる id については、B が同定した要素との一致を**記録だけ**する(ラベルには使わない)。
予測(読む前に書く): 確定(同値類 v0) 70〜95 / 120、判定不能(両側) 8〜25、不一致 ≤ 15。外れ方: 確定 < 70 なら材料(文の切り方・率の欄)の欠陥を疑い、不一致 > 15 なら同値類規則の穴を疑う。
"""
import json, sys, re, collections, os
D = os.path.dirname(os.path.abspath(__file__))
def canon(e):
    e = e.split(':')[-1]
    if e.endswith('SummaryOfBusinessResults'): e = e[:-len('SummaryOfBusinessResults')]
    return {'TotalAssets': 'Assets'}.get(e, e)
def facts(row, strict):
    out = set()
    for side in ('当期側', '前期側'):
        f = row.get(side)
        if f and f.get('要素'):
            e = f['要素'].split(':')[-1] if strict else canon(f['要素'])
            out.add((e, f.get('context')))
    return out
def main(a_path, b_path, key_path, b_struct_path, out_path):
    A = {r['行の鍵']: r for r in json.load(open(a_path))['行']}
    B = {r['行の鍵']: r for r in json.load(open(b_path))['行']}
    key = json.load(open(key_path))['map']
    bs = {r['id']: r for r in json.load(open(b_struct_path))['rows']}
    assert set(A) == set(key) == set(B), (len(A), len(B), len(key))
    cnt = collections.Counter(); shape = collections.Counter(); labels = []; mism = []; bcmp = collections.Counter()
    for k in sorted(key):
        a, b = A[k], B[k]; cid = key[k]['id']
        da, db = a['判定'] == '独立判定', b['判定'] == '独立判定'
        if da and db:
            if facts(a, False) == facts(b, False) and facts(a, False):
                cls = '確定(同値類v0)'; strict = facts(a, True) == facts(b, True)
                cnt['確定(厳密)'] += strict
            else:
                cls = '不一致'; mism.append({'鍵': k, 'id': cid, '席1': a, '席2': b})
        elif da or db: cls = '判定不能(片側)'
        else: cls = '判定不能(両側)'
        cnt[cls] += 1
        if cls.startswith('確定'): shape['形が一致' if a.get('形') == b.get('形') else '形が違う'] += 1
        lab = {'id': cid, '鍵': k, '分類': cls, '形': [a.get('形'), b.get('形')],
               'fact(席1)': sorted(facts(a, True)), 'fact(席2)': sorted(facts(b, True)),
               '同値の他の候補(和集合)': sorted({(c.get('要素'), c.get('context')) for r in (a, b) for c in (r.get('同値の他の候補') or []) if c.get('要素')})}
        if cid in bs:
            bf = set(tuple(x) for x in bs[cid]['B が同定した fact [(要素, context)]'])
            bfc = set((canon(e), c) for e, c in bf)
            ref = facts(a, False) if cls.startswith('確定') else None
            r = '未比較(未確定)' if ref is None else ('B と同じ(同値類v0)' if ref <= bfc else 'B と違う')
            bcmp[r] += 1; lab['再監査Bとの比較(記録のみ)'] = r
        labels.append(lab)
    rep = {'definition_sha256_note': 'この採点器の sha256 は report に別記', 'counts': dict(cnt), '形': dict(shape), '再監査B との重なり': dict(bcmp), 'labels': labels, '不一致の行': mism}
    json.dump(rep, open(out_path, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({'counts': dict(cnt), '形': dict(shape), 'B': dict(bcmp)}, ensure_ascii=False))
if __name__ == '__main__':
    main(*sys.argv[1:6])
