# -*- coding: utf-8 -*-
u"""**次元で露出した 6 行の診断**(人間の指示 2026-10-17)。

`attr_inject_2026-10-17.json` で「同じ値を別の次元にも持つ」と数えた行について、
**行ごとに、競合する fact・その軸と枠・文が連結か個別かを言っているか**を記録する。

**読むだけ。engine を変えない。規則を増やさない。注入もしない。0 USD・席は呼ばない。**
**どの次元差を不一致にするかは決めない**(それは次の封で人間が決める)。

    python3 measure/xbrl_dim_diag_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
SRC = os.path.join(FX, "attr_inject_2026-10-17.json")
OUT = os.path.join(FX, "dim_diag_2026-10-17.json")

_sp = importlib.util.spec_from_file_location(
    "attr_for_dim", os.path.join(HERE, "xbrl_attr_inject_2026-10-17.py"))
AT = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(AT)
A1, MB, IJ, PR, I, ED, VE = AT.A1, AT.MB, AT.IJ, AT.PR, AT.I, AT.ED, AT.VE

#: 文が「どちらの話か」を言っている字(**字で留める**。増やすときは封で)
WORDS = (u"連結", u"個別", u"単体", u"セグメント", u"株主資本", u"利益剰余金",
         u"剰余金", u"提出会社", u"当事業年度", u"当連結会計年度", u"当期")
#: 軸の local 名 → 人が読む分類(**在る軸だけ書く。無い軸は「その他」に落ちる**)
AXIS_CLASS = {
    "ConsolidatedOrNonConsolidatedAxis": u"連結・個別の区分",
    "SegmentAxis": u"セグメント",
    "BusinessSegmentsAxis": u"セグメント",
    "ReportableSegmentsAxis": u"セグメント",
    "OperatingSegmentsAxis": u"セグメント",
    "ComponentsOfEquityAxis": u"株主資本の内訳",
    "EquityComponentsAxis": u"株主資本の内訳",
}


def axes_of_instance(zbytes):
    u"""枠 → [(軸, 枠の名)]。**instance の XML にそのまま在る**(linkbase は読まない)。"""
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    out = {}
    for n in z.namelist():
        if not (n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")):
            continue
        raw = z.read(n).decode("utf-8")
        for cid, body in re.findall(
                r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', raw,
                re.S):
            out[cid] = re.findall(r'dimension="([^"]+)"[^>]*>([^<]+)<', body)
    return out


def classify(axis):
    u"""軸(QName)を人が読む分類に落とす。**軸が無ければ「軸を読めない」**。"""
    if not axis:
        return u"軸を読めない"
    return AXIS_CLASS.get(axis.split(":")[-1], u"その他の軸")


def words_in(text):
    return [w for w in WORDS if w in (text or u"")]


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    src = json.load(io.open(SRC, encoding="utf-8"))
    target = [(x[u"doc"], x[u"id"]) for x in src["rows"]
              if x[u"露出(注入なし)"][u"別の次元"][u"件数"]]
    base24 = [(x[u"doc"], x[u"id"]) for x in src["rows"]]
    score = json.load(io.open(os.path.join(FX, "score_2026-10-17.json"),
                              encoding="utf-8"))
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    by_doc = collections.defaultdict(list)
    for doc, rid in target:
        by_doc[doc].append(rid)

    detail, tally = [], collections.Counter()
    pointer_dim = {u"基準 24 行": collections.Counter(),
                   u"席が参照先を出した全部の行": collections.Counter(),
                   u"正解(T5)の参照先": collections.Counter()}
    axes_seen = collections.Counter()
    dimmed = collections.defaultdict(list)
    coincident = collections.Counter()
    unresolved = []
    rival_axes = collections.Counter()
    rule_b = collections.Counter()
    rule_b_rows = []
    doc_profile = {}
    # **8 書類すべてを回す。**基準 24 行が在る書類だけ回すと、
    # **母集団の数が静かに 85 → 70 に落ちる**(第 1 便で実際に落ちた)。
    for doc in sorted({x["doc"] for x in score["rows"]}):
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows = {r["id"]: r for r in MB.build_rows(tampered, chosen, pl)[0]}
        zb2, _e, _mm = PR.build_modified_zip(zb, tampered)
        facts = I.load_instance(zb2)["facts"]
        ax = axes_of_instance(zb2)
        #: **書類が連結か個別か**(P20 の落とし込みが見ている数と同じ関数)
        con_count = I.consolidated_element_count(facts)
        doc_profile[doc] = {u"連結の要素数": con_count,
                           u"**個別しか無い書類**": con_count == 0}
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f
                for f in facts}

        #: **参照先に明示次元が付いていた行**を 3 つの母集団で数える
        for grp, picks in (
                (u"基準 24 行",
                 [(d, i) for d, i in base24 if d == doc]),
                (u"席が参照先を出した全部の行",
                 [(x["doc"], x["id"]) for x in score["rows"]
                  if x["doc"] == doc and x[u"席"][u"参照先"]]),
                (u"正解(T5)の参照先",
                 # **key は `正解[正解]`。**`正解[参照先]` は存在せず、
                 # 第 1 便はこれで**静かに 0 件**になった
                 [(x["doc"], x["id"]) for x in score["rows"]
                  if x["doc"] == doc and (x[u"正解"] or {}).get(u"正解")])):
            for d, i in picks:
                row = [x for x in score["rows"]
                       if x["doc"] == d and x["id"] == i][0]
                ptr = ((row[u"正解"] or {}).get(u"正解")
                       if grp == u"正解(T5)の参照先" else row[u"席"][u"参照先"])
                f = keys.get(A1.norm_pointer(ptr or u""))
                if f is None:
                    pointer_dim[grp][u"instance に無い"] += 1
                    continue
                dims = ax.get(f["context"], [])
                pointer_dim[grp][u"明示次元つき" if dims else u"明示次元なし"] += 1
                if dims:
                    dimmed[grp].append({u"doc": d, u"id": i, u"参照先": ptr,
                                        u"軸と枠": dims})
                for a, _mem in dims:
                    axes_seen[a] += 1

        #: **候補規則 (b)「文に『連結』が在り、参照先が個別の枠なら不一致」の帯。**
        #: **規則にはしない。**当たる行と、当たった先が正解だった行を数えるだけ。
        for x in score["rows"]:
            if x["doc"] != doc or not x[u"席"][u"参照先"]:
                continue
            f = keys.get(A1.norm_pointer(x[u"席"][u"参照先"]))
            if f is None:
                continue
            dims = ax.get(f["context"], [])
            if not any(a.endswith("ConsolidatedOrNonConsolidatedAxis")
                       and m.endswith("NonConsolidatedMember")
                       for a, m in dims):
                continue
            rule_b[u"参照先が個別(NonConsolidated)の枠"] += 1
            if con_count == 0:
                rule_b[u"**うち書類に連結の fact が 0 件(個別しか無い)**"] += 1
            if not [g for g in facts
                    if g["name"] == f["name"] and not ax.get(g["context"])]:
                rule_b[u"**うち同じ要素の「次元なし」の枠が無い**"] += 1
            w = words_in(mrows[x["id"]][u"抜粋"])
            if u"連結" in w:
                rule_b[u"**うち文に「連結」が在る(規則 b が当たる)**"] += 1
                gold = (x[u"正解"] or {}).get(u"正解")
                same = bool(gold and A1.norm_pointer(gold)
                            == A1.norm_pointer(x[u"席"][u"参照先"]))
                if same:
                    rule_b[u"**うち正解と同じ参照先(= 誤拒否になる)**"] += 1
                rule_b_rows.append({u"doc": doc, u"id": x["id"],
                                    u"席の参照先": x[u"席"][u"参照先"],
                                    u"正解": gold, u"**正解と同じ**": same,
                                    u"文に在った字": w})
            if [a for a in w if a in (u"個別", u"単体", u"提出会社")]:
                rule_b[u"うち文に「個別・単体・提出会社」が在る"] += 1

        #: **偶然一致する側**(T5 の注入が値を借りた fact)の次元を数える。
        #: **これは要素そのものが違う機構で、次元の兄弟とは別物である。**
        for x in score["rows"]:
            if x["doc"] != doc or not (x[u"正解"] or {}).get(u"偶然一致する側"):
                continue
            f = keys.get(A1.norm_pointer(x[u"正解"][u"偶然一致する側"]))
            if f is None:
                # **数値の fact 一覧は `unitRef` を持つ fact だけ**
                # (`adapters/xbrl/instance.py`)。DEI の文字(証券コード等)は入らない
                coincident[u"数値の fact 一覧に無い(文字・DEI など)"] += 1
                unresolved.append(x[u"正解"][u"偶然一致する側"])
                continue
            dims = ax.get(f["context"], [])
            coincident[classify(dims[0][0]) if dims else u"明示次元なし"] += 1

        for rid in by_doc.get(doc, []):
            row = [x for x in score["rows"]
                   if x["doc"] == doc and x["id"] == rid][0]
            r = mrows[rid]
            ptr = row[u"席"][u"参照先"]
            base = keys[A1.norm_pointer(ptr)]
            tol = abs(VE.V.UNIT_SCALE.get(r[u"単位"], 1)) or 1
            rivals = AT.exposure(facts, base, tol)[u"別の次元"]
            got = []
            for key in rivals:
                ctx = key.split("@", 1)[1]
                dims = ax.get(ctx, [])
                cls = ([classify(a) for a, _m in dims] or [u"軸を読めない"])
                got.append({u"競合する fact": key, u"軸と枠": dims,
                            u"分類": cls[0]})
                for a, _m2 in dims:
                    rival_axes[a] += 1
                tally[cls[0]] += 1
            w = words_in(r[u"抜粋"])
            mine = ax.get(base["context"], [])
            detail.append({
                u"doc": doc, u"id": rid, u"注入か": row[u"注入か"],
                u"正解": row[u"正解"], u"値": r[u"値"], u"単位": r[u"単位"],
                u"文(抜粋)": r[u"抜粋"],
                u"**文に在った字**": w,
                u"席の参照先": ptr,
                u"席の参照先の軸と枠": mine,
                u"席の参照先は明示次元つきか": bool(mine),
                u"**競合**": got,
                u"**値は同じか**": True,
                u"**文だけで連結・個別を区別できるか**": bool(
                    [x for x in w if x in (u"連結", u"個別", u"単体",
                                           u"提出会社")]),
            })

    rec = {
        "step": u"**次元で露出した 6 行の診断。読むだけ・engine 不変・0 USD**",
        u"**偶然一致する側の次元(T5 の注入が借りた fact)**": dict(coincident),
        u"**明示次元つきだった参照先(名指し)**": {k: v for k, v
                                    in dimmed.items()},
        u"入力": "fixtures/xbrl/cd8/attr_inject_2026-10-17.json",
        u"**対象**": {u"行": len(detail),
                  u"選び方": u"`別の次元` の露出が 1 件以上あった行"},
        u"**競合の分類(fact の件数)**": dict(tally),
        u"**行の分類**": dict(collections.Counter(
            x[u"**競合**"][0][u"分類"] for x in detail)),
        u"**文が連結・個別を言っていた行**": sum(
            1 for x in detail if x[u"**文だけで連結・個別を区別できるか**"]),
        u"**参照先に明示次元が付いていたか**": {k: dict(v) for k, v
                                 in pointer_dim.items()},
        u"**instance から読めた軸(参照先の側)**": dict(axes_seen),
        u"**競合する fact の軸**": dict(rival_axes),
        u"**書類ごとの連結・個別**": doc_profile,
        u"**候補規則 (b) の帯(規則にはしない)**": dict(rule_b),
        u"**候補規則 (b) が当たった行**": rule_b_rows,
        u"**偶然一致する側が解けなかった例**": sorted(set(unresolved))[:5],
        u"rows": detail,
        u"limits": [
            u"**この 6 行は contract v1 が通した 24 行の中の露出である。**"
            u"通らなかった行・他の書類の率ではない",
            u"**値が同じ兄弟 fact が在ることは、席がそれを選ぶことではない。**"
            u"選ばれる頻度は測っていない",
            u"**6 行はいずれも無改変の行で、正解(T5)の参照先は無い。**"
            u"どちらが正しいかは文の読みに依る",
            u"**軸は instance の XML から読めたが、Core は今これを読んでいない。**"
            u"読める = 規則が書けるとは限らない",
            u"**どの次元差を不一致にするかは決めない。**次の封で人間が決める",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 次元で露出した %d 行の診断(読むだけ・0 USD)===" % len(detail))
    for x in detail:
        print(u"--- %s %s  %s %s  %s"
              % (x[u"doc"], x[u"id"], x[u"値"], x[u"単位"], x[u"席の参照先"]))
        print(u"    文の字: %s / 連結・個別を言っている: %s"
              % (u"・".join(x[u"**文に在った字**"]) or u"(無し)",
                 u"はい" if x[u"**文だけで連結・個別を区別できるか**"] else u"いいえ"))
        for g in x[u"**競合**"]:
            print(u"    競合 [%s] %s" % (g[u"分類"], g[u"競合する fact"]))
    print(u"--- 競合の分類(fact)---")
    for k, v in sorted(tally.items(), key=lambda a: -a[1]):
        print(u"  %-12s %d" % (k, v))
    print(u"--- 参照先に明示次元が付いていたか ---")
    for k, v in rec[u"**参照先に明示次元が付いていたか**"].items():
        print(u"  %-22s %s" % (k, json.dumps(v, ensure_ascii=False)))
    print(u"--- instance から読めた軸 ---")
    for k, v in sorted(axes_seen.items(), key=lambda a: -a[1]):
        print(u"  %-60s %d" % (k, v))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
