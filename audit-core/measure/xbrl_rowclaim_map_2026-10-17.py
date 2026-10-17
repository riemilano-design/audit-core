# -*- coding: utf-8 -*-
"""**私の器の欠陥を数える: 行 -> Core の主張 の対応は 1 対 1 ではなかった。**

仮説 A の分岐を追う途中で見つけた(`measure/xbrl_branch_a_2026-10-17.py` の
`sys.settrace` が、S100YZ7E の **4 行を 1 つの主張 `N022`** として記録した)。

材料の行は `(値が許容差の内側) かつ (数の字面が span に在る)` で Core の主張に
対応付けている(`measure/xbrl_cd_material_2026-10-17.py` の `pre` を作る所)。
**同じ値が同じ文に何度も出る書類では、先に当たった 1 つの主張に複数の行が張り付く。**

**封の記録は書き換えない。**ここで数えるのは「どの行の Core 欄が他の行と同じ主張
から来ているか」で、**分母を分けて率を併記する**ためである
(記憶 `zero-count-may-be-my-own-bug`・`compare-rates-need-same-base`)。

**engine は触らない。0 USD・席は呼ばない。**

    python3 measure/xbrl_rowclaim_map_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
OUT = os.path.join(FX, "rowclaim_map_2026-10-17.json")

_sp = importlib.util.spec_from_file_location(
    "pnf_diag_for_map", os.path.join(HERE, "xbrl_pnf_diag_2026-10-17.py"))
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)
A1, MB, IJ, ED, VD = D.A1, D.MB, D.IJ, D.ED, D.VD


def claim_of(row, claims):
    """**材料の作り手と同じ対応付けをそのまま使う**(直さない。数えるだけ)。"""
    for c in claims:
        if c.get("value") is None:
            continue
        if (abs(c["value"] - row[u"値"]) <= A1.TOL
                and row[u"数の字面"] in (c.get("span") or "")):
            return c["id"]
    return None


def rate(num, den):
    return {u"分子": num, u"分母": den,
            u"率": (round(100.0 * num / den, 1) if den else None)}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    docs = json.load(io.open(os.path.join(FX, "draw_2026-10-17.json"),
                             encoding="utf-8"))[u"引いた 8 件"]
    mat = json.load(io.open(os.path.join(FX, "material_2026-10-17.json"),
                            encoding="utf-8"))
    sc = json.load(io.open(os.path.join(FX, "score_2026-10-17.json"),
                           encoding="utf-8"))
    seat = {(r[u"doc"], r[u"id"]): r[u"席"] for r in sc[u"rows"]}
    pre = {}
    for p in mat[u"書類ごと"]:
        for rid, v in p[u"席の前に出せる分"].items():
            pre[(p["docID"], rid)] = v
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)

    t = collections.Counter()
    per_doc, shared_detail, wrong = {}, {}, []
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        rows, _n = MB.build_rows(tampered, chosen, pl)
        claims = VD.verify_document(zb, MB.PROFILE, tampered)["claims"]
        m = {r["id"]: claim_of(r, claims) for r in rows}
        mult = collections.Counter(v for v in m.values() if v is not None)
        sh = {cid: sorted(rid for rid, v in m.items() if v == cid)
              for cid, n in mult.items() if n > 1}
        if sh:
            shared_detail[doc] = sh
        per_doc[doc] = {u"行": len(rows),
                        u"対応が付かない行": sum(1 for v in m.values() if v is None),
                        u"異なる主張": len(mult),
                        u"**複数の行が張り付いた主張**": len(sh),
                        u"**その主張に張り付いた行**": sum(len(v) for v in sh.values())}
        t[u"行"] += len(rows)
        t[u"対応が付かない行"] += per_doc[doc][u"対応が付かない行"]
        t[u"共有された行"] += per_doc[doc][u"**その主張に張り付いた行**"]
        t[u"共有された主張"] += len(sh)
        for rid, cid in m.items():
            g = pre[(doc, rid)][u"正解"]
            if not (g and g.get(u"種類") == u"参照先が在る"):
                continue
            one = cid is not None and mult[cid] == 1
            hit = pre[(doc, rid)]["Core"][u"参照先"] == g[u"正解"]
            t[u"T5"] += 1
            t[u"T5 のうち 1 対 1"] += one
            t[u"T5 のうち対応が付かない"] += cid is None
            t[u"T5 のうち共有"] += (cid is not None and mult[cid] > 1)
            t[u"特定(全部の行)"] += hit
            if one:
                t[u"特定(1 対 1 の行だけ)"] += hit
            s = seat[(doc, rid)][u"参照先"]
            if s is not None and s != g[u"正解"]:
                wrong.append({u"doc": doc, u"id": rid, u"主張 id": cid,
                              u"その主張に張り付いた行": mult[cid] if cid else 0})

    rec = {
        "step": u"**器の欠陥を数える。封の記録は書き換えない。engine 不変・0 USD**",
        u"**何が起きていたか**": (
            u"材料の行は `(値が許容差の内側) かつ (数の字面が span に在る)` で "
            u"Core の主張に対応付けている。**同じ値が同じ文に複数回出る書類では、"
            u"先に当たった 1 つの主張に複数の行が張り付く。**"
            u"その行の Core 欄は**他の行の判断を写したもの**になる"),
        u"見つけ方": u"仮説 A の `sys.settrace` が S100YZ7E の 4 行を 1 つの主張"
                 u"(`N022`)として記録した",
        u"合計": dict(t),
        u"書類ごと": per_doc,
        u"**複数の行が張り付いた主張**": shared_detail,
        u"**Core 自身の特定率を分母で分ける**": {
            u"全部の T5 行(封の記録と同じ数)": rate(t[u"特定(全部の行)"], t[u"T5"]),
            u"**1 対 1 の行だけ**": rate(t[u"特定(1 対 1 の行だけ)"],
                                 t[u"T5 のうち 1 対 1"]),
            u"注": u"**どちらも書く。**封の記録の数(全部の行)は残し、"
                  u"**器の欠陥を除いた分母の数を併記する**"},
        u"席が外した行(α の天井の分母)": {
            u"行": len(wrong),
            u"**異なる主張の数**": len({(w[u"doc"], w[u"主張 id"]) for w in wrong}),
            u"明細": wrong,
            u"注": u"**7 行は独立した 7 件ではない。**`N022` に 4 行が張り付いている"},
        u"limits": [
            u"**これは私の器の欠陥であり、Core の欠陥ではない。**"
            u"Core は 1 つの主張について 1 回判断している",
            u"**封の記録は書き換えていない。**率は 2 つ並べた",
            u"**席の答え・D′・D″ はこの欠陥の影響を受けない**"
            u"(席は行ごとに答え、D′・D″ は行の値から直に引く)。"
            u"**影響するのは Core 欄だけ**である",
            u"**A 対 C′ の判定は変わらない。**C′ が Core を使ったのは席が保留した行で、"
            u"T5 に保留は 0 件だった",
            u"**対応付けを直していない。**直すのは別便(どの行がどの主張かを"
            u"span の位置で決める等)。**直したら必ず測る**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 行 -> 主張 の対応(私の器の欠陥。0 USD)===")
    print(json.dumps(dict(t), ensure_ascii=False, indent=1))
    for d, v in sorted(per_doc.items()):
        print(u"  %s %s" % (d, json.dumps(v, ensure_ascii=False)))
    r = rec[u"**Core 自身の特定率を分母で分ける**"]
    for k in (u"全部の T5 行(封の記録と同じ数)", u"**1 対 1 の行だけ**"):
        print(u"  %-28s %s%% (%s/%s)" % (k, r[k][u"率"], r[k][u"分子"], r[k][u"分母"]))
    print(u"  席が外した %d 行 = **異なる主張 %d 件**"
          % (len(wrong), len({(w[u"doc"], w[u"主張 id"]) for w in wrong})))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
