# -*- coding: utf-8 -*-
"""**仮説 A の分岐を特定する。engine は 1 行も変えない。0 USD・席は呼ばない。**

人間の指示(2026-10-17)の 1〜3 番。**修正には入らない。**
やることは 3 つだけ。

  1. `no_element` に至る**実行された行**を `sys.settrace` で特定する(コードは触らない)
  2. **最小の再現入力**を関数の層で作る(member だけが違う 2 つの context)
  3. **修正前の予測**を固定する(行ごと・書類ごと。結果を見てから変えない)

出力は `fixtures/xbrl/cd8/branch_a_2026-10-17.json`。

    python3 measure/xbrl_branch_a_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DIAG = os.path.join(FX, "pnf_diag_2026-10-17.json")
DRAW = os.path.join(FX, "draw_2026-10-17.json")
OUT = os.path.join(FX, "branch_a_2026-10-17.json")

_sp = importlib.util.spec_from_file_location(
    "pnf_diag_for_branch", os.path.join(HERE, "xbrl_pnf_diag_2026-10-17.py"))
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)
I, R, V, PR, ED = D.I, D.R, D.V, D.PR, D.ED
A1, MB, IJ = D.A1, D.MB, D.IJ

# `no_element` を代入している行(`git grep -n '"no_element"' adapters/xbrl/recipes.py`)
NO_ELEMENT_LINES = (214, 330, 332, 433, 458, 502, 519, 726, 729, 827)


def trace_no_element(doc, claim_ids):
    """**実行された行**を記録する。`sys.settrace` は engine を書き換えない。"""
    zb = io.open(ED.cache_path(doc), "rb").read()
    old, A1.TMP = A1.TMP, MB.TMP
    try:
        text, refs = A1.material(doc)
    finally:
        A1.TMP = old
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    chosen, _c = MB.pick_injections(text, refs, seed, doc)
    tampered, _p = IJ.apply_edits(text, chosen)
    zb2, _e, _m = PR.build_modified_zip(zb, tampered)
    recipes_file = os.path.abspath(R.__file__)
    hits = []

    def tracer(frame, event, arg):
        if event != "line":
            return tracer
        if (frame.f_lineno in NO_ELEMENT_LINES
                and os.path.abspath(frame.f_code.co_filename) == recipes_file):
            lv = frame.f_locals
            cl = lv.get("claim") if isinstance(lv.get("claim"), dict) else {}
            if cl.get("id") in claim_ids:
                hits.append({u"行": frame.f_lineno, u"関数": frame.f_code.co_name,
                             u"主張 id": cl.get("id"),
                             u"subject": cl.get("subject"),
                             u"選ばれた要素": [str(x) for x in (lv.get("elems") or [])],
                             u"member": str(lv.get("member")),
                             u"**候補 fact の数 fs**":
                                 len(lv.get("fs")) if isinstance(lv.get("fs"), list) else None,
                             u"当期の候補 cur":
                                 len(lv.get("cur")) if isinstance(lv.get("cur"), list) else None})
        return tracer

    sys.settrace(tracer)
    try:
        R.build_recipes(zb2, V.PROFILES[D.PROFILE])
    finally:
        sys.settrace(None)
    out, seen = [], set()
    for h in hits:                      # 同じ行が 2 度通る(1 文 2 回の走査)
        k = (h[u"主張 id"], h[u"行"])
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def minimal_repro():
    """**最小の再現入力。**member だけが違う 2 つの枠。engine の関数をそのまま呼ぶ。"""
    ctx_plain = {"CurrentYearInstant": {"members": []}}
    ctx_nc = {"CurrentYearInstant_NonConsolidatedMember":
              {"members": ["jppfs_cor:NonConsolidatedMember"]}}
    fact_plain = {"name": "jppfs_cor:CurrentAssets", "context": "CurrentYearInstant",
                  "value": 771000.0, "unit": "JPY", "decimals": "-3"}
    fact_nc = {"name": "jppfs_cor:CurrentAssets",
               "context": "CurrentYearInstant_NonConsolidatedMember",
               "value": 771000.0, "unit": "JPY", "decimals": "-3"}
    elems = ("CurrentAssets",)
    cases = []
    for name, ctxs, facts, enabled in (
            (u"素の枠(次元なし)", ctx_plain, [fact_plain], False),
            (u"**単体 member だけの枠**・fallback 無効(P16)", ctx_nc, [fact_nc], False),
            (u"**単体 member だけの枠**・fallback 有効(P20)", ctx_nc, [fact_nc], True),
            (u"単体 member だけの枠・fallback 有効・**連結の要素が在る**",
             dict(ctx_nc, **ctx_plain),
             [fact_nc, dict(fact_plain, name="jppfs_cor:Assets")], True)):
        wrapped = I.with_nonconsolidated_fallback(ctxs, facts, enabled)
        cid = list(ctx_nc)[0] if ctxs is not ctx_plain else list(ctx_plain)[0]
        cases.append({
            u"場合": name,
            u"連結の財務要素の数": I.consolidated_element_count(facts),
            u"nonconsolidated_ok": bool(getattr(wrapped, "nonconsolidated_ok", False)),
            u"ctx_ok(member=None)": I.ctx_ok(cid, wrapped, None),
            u"**facts_for の件数**": len(I.facts_for(elems, facts, wrapped, None))})
    return {u"入れた枠と fact": {u"素": ctx_plain, u"単体 member だけ": ctx_nc},
            u"場合ごと": cases,
            u"**この再現入力が示すこと**": (
                u"**member を指定しない引き(`member=None`)で、単体 member だけの枠は "
                u"`nonconsolidated_ok` が立っていないと候補に入らない。**"
                u"立つ条件は `with_nonconsolidated_fallback(…, enabled)` の "
                u"`enabled`(profile の `nonconsolidated_fallback`)と "
                u"**連結の財務要素が 0 件**の 2 つ")}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    diag = json.load(io.open(DIAG, encoding="utf-8"))
    after = [r for r in diag["rows"]
             if r[u"**候補 0 の内訳**"][u"どこで落ちたか"].startswith(u"語彙は正解")]
    traced = {}
    for doc in sorted({r[u"doc"] for r in diag["rows"]}):
        ids = {r[u"Core の主張 id"] for r in diag["rows"] if r[u"doc"] == doc}
        traced[doc] = trace_no_element(doc, ids)

    docs = json.load(io.open(DRAW, encoding="utf-8"))[u"引いた 8 件"]
    material = {}
    for d in docs:
        inst = I.load_instance(io.open(ED.cache_path(d), "rb").read())
        material[d] = {
            u"連結の財務要素の数": I.consolidated_element_count(inst["facts"]),
            u"単体 member だけの context": sum(
                1 for cid, c in inst["contexts"].items()
                if [m.split(":")[-1] for m in (c.get("members") or [])]
                == [I.NONCONSOLIDATED_MEMBER]),
            u"fact": len(inst["facts"]),
            u"**fallback の条件を満たす**":
                I.consolidated_element_count(inst["facts"]) == 0}

    rec = {
        "step": u"**仮説 A の分岐の特定・再現入力・修正前の予測。engine 不変・0 USD**",
        u"人間の指示": u"2026-10-17(分岐を特定する / 予測を固定する / 証拠が揃ったら止める)",
        u"**実行された行**": traced,
        u"**分岐の場所**": {
            u"file": "adapters/xbrl/recipes.py",
            u"行": 330,
            u"関数": "_direct_value_claim",
            u"直前の条件": u"`fs = I.facts_for(elems, facts, contexts, member)` が空 "
                      u"→ `cur` も空 → `claim[\"reason\"] = \"no_element\"`",
            u"落とす関数": {"file": "adapters/xbrl/instance.py",
                      u"関数": "ctx_ok / plain_context",
                      u"行": u"216-224(ctx_ok)・208-213(plain_context)",
                      u"規則": u"`member is None` のときは `plain_context` ― "
                             u"**members が空で、cid に NonConsolidated を含まない枠だけ**。"
                             u"例外は `nonconsolidated_ok` が立っているときだけ"},
            u"条件を立てる場所": {"file": "adapters/xbrl/instance.py",
                        u"関数": "with_nonconsolidated_fallback",
                        u"行": "178-188",
                        u"2 つの条件": [u"profile の `nonconsolidated_fallback` が真",
                                   u"`consolidated_element_count(facts) == 0`"]},
            u"**profile**": {u"今回の測定で使った": D.PROFILE,
                         u"`P16.nonconsolidated_fallback`":
                             V.PROFILES["P16"].nonconsolidated_fallback,
                         u"`P20.nonconsolidated_fallback`":
                             V.PROFILES["P20"].nonconsolidated_fallback,
                         # 2026-10-17 に測った時点のコードの既定(記録の事実)。2026-10-20(段 2)に
                         # vocabulary.DEFAULT_PROFILE は P21 になったので、字で留めて記録を再現できるようにする。
                         u"**Core の既定**": "P20",
                         u"**注意**": (
                             u"**(ア) の封は P16 を「既定」と書いたが、"
                             u"コードの既定は P20 である**"
                             u"(`vocabulary.DEFAULT_PROFILE`)。"
                             u"**封の字は直さない。この食い違いを記録に残す**")}},
        u"**最小の再現入力**": minimal_repro(),
        u"材料の性質(8 書類)": material,
        u"rows": [{u"doc": r[u"doc"], u"id": r[u"id"],
                   u"主張 id": r[u"Core の主張 id"],
                   u"subject": r[u"Core が決めた subject"],
                   u"選ばれた要素": r[u"**候補 0 の内訳**"][u"その語に当たった要素"],
                   u"正解の要素": r[u"正解の key"].split("@")[0],
                   u"どこで落ちたか": r[u"**候補 0 の内訳**"][u"どこで落ちたか"]}
                  for r in diag["rows"]],
        u"limits": [
            u"**分岐の特定であって、原因の修正ではない。**engine は 1 行も変えていない",
            u"**`sys.settrace` で観測した。**実行された行は記録したが、"
            u"**実行されなかった行が通らない理由までは観測していない**",
            u"**2 書類 10 行の観測である。**他の 6 書類では `fallback の条件` を"
            u"満たさないので、同じ分岐には入らない",
            u"**仮説 B(語彙・主語)には触っていない。**7 行はそちらが先に効いている",
            u"**予測は profile の切り替えについてである。**"
            u"コードの修正についての予測ではない",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 仮説 A の分岐(engine 不変・0 USD)===")
    for doc, hs in sorted(traced.items()):
        print(u"%s: 実行された行 %s"
              % (doc, dict(collections.Counter(h[u"行"] for h in hs))))
    for h in sorted(traced.get("S100YZEV", []), key=lambda x: x[u"主張 id"]):
        print(u"   %s %s 要素 %s / member %s / fs %s / cur %s -> 行 %d"
              % (h[u"主張 id"], h[u"subject"], h[u"選ばれた要素"], h[u"member"],
                 h[u"**候補 fact の数 fs**"], h[u"当期の候補 cur"], h[u"行"]))
    print(u"--- 最小の再現入力 ---")
    for c in rec[u"**最小の再現入力**"][u"場合ごと"]:
        print(u"   %-52s ctx_ok %-5s facts_for %d(連結の要素 %d / ok %s)"
              % (c[u"場合"], c[u"ctx_ok(member=None)"],
                 c[u"**facts_for の件数**"], c[u"連結の財務要素の数"],
                 c[u"nonconsolidated_ok"]))
    print(u"--- 材料(8 書類)---")
    for d, v in sorted(material.items()):
        print(u"   %s 連結の財務要素 %4d / **fallback の条件 %s**"
              % (d, v[u"連結の財務要素の数"], v[u"**fallback の条件を満たす**"]))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
