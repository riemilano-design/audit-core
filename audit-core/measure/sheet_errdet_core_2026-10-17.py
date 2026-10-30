# -*- coding: utf-8 -*-
"""**Core 単体**を誤り入りの報告文で測る(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §3)。

**費用 0 USD。生成しない。**

  **検出 / 保留 / 見落としは排他**(封 §3-1)。**保留は検出に数えない。**
  誤りの 1 件につき **検出-1 / 検出-2 / 検出-3** を別々に採点する(封 §3-2)。
  無改変の主張では **偽警報 / 保留 / 確認済み**を分ける(封 §3-3)。罠 `R035` は**別記**。

**Core 単体(B)は参考群である。**(封 §5-1。**勝っても製品の結論にしない。**)

行の照合は `sheet_poc_ab_score_2026-10-17.py` の `same_row()` を**そのまま使う**
(片側だけの正規化を作らない)。

    python3 measure/sheet_errdet_core_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
REPORT = os.path.join(FX, "m11_report_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
OUT = os.path.join(FX, "errdet_core_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"
TRAP_ID = "R035"
# 封 §3-2 の固定語彙(**6 語。字で留める**)
VOCAB = ("値が原資料に無い", "列の取り違え", "別の科目の値", "親階層の取り違え",
         "単位・符号の表記", "不明")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RUN = _mod("run11_for_errcore", "sheet_m11_run_2026-10-16.py")
SE = RUN.NEW
M7 = SE.M7
M2 = RUN.M2
S = _mod("abscore_for_errcore", "sheet_poc_ab_score_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


_IDX = {}


def index():
    if "e" in _IDX:
        return _IDX["e"]
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    raw = M7.fix_total_level(M7.build_index(*args))
    al = SE.alias_table(raw)
    entries = M7.canonicalize(raw, al)
    _IDX["e"] = (entries, M7.column_cues(entries), M7.vocabulary(entries))
    return _IDX["e"]


def run_core(text):
    """段 11 の B と**同じ呼び出し順**。索引・別名表は使い回す(同じもの)。"""
    entries, cues, vocab = index()
    claims = M7.extract_claims(text, vocab, cues)
    return claims, [M7.bind(c, entries) for c in claims]


def check_variant(cv, c0, changed):
    """**変種が有効か**(封 §6)。(有効か, 理由) を返す。**判定を 1 か所に置く。**"""
    if len(cv) != len(c0):
        return False, "主張の数が違う: %d != %d" % (len(cv), len(c0))
    for a, b in zip(cv, c0):
        if a["id"] != b["id"]:
            return False, "id の並びが違う: %s != %s" % (a["id"], b["id"])
        if a["sentence_index"] != b["sentence_index"]:
            return False, "%s の文が違う" % a["id"]
        if a["id"] in changed:
            if a["value"] == b["value"]:
                return False, "%s の値が変わっていない" % a["id"]
        elif a["value"] != b["value"]:
            return False, "**変えていない %s の値が動いた**" % a["id"]
    return True, None


def classify(b):
    """封 §3-1。**検出 / 保留 / 確認済みは排他。**"""
    if b["state"] == "GROUNDED":
        return "確認済み"
    if b["state"] == "VALUE_MISMATCH":
        return "検出"
    return "保留"


def kind_of_core(b):
    """Core の**種類の申告**を固定語彙に写す(封 §3-2)。

    Core は「値が合わない」としか言えない。**列の取り違えや別の科目は区別できない。**
    """
    return "値が原資料に無い" if b["state"] == "VALUE_MISMATCH" else "不明"


def ref_of(claim, b):
    """Core が**指した行**の 6 欄を返す(無ければ None)。

    `GROUNDED` は `evidence` が 6 欄を持つ。`VALUE_MISMATCH` は持たないので、
    **候補の鍵から取る**(鍵は 1 通りに決まっている ― それが `VALUE_MISMATCH` の条件)。
    """
    if b["state"] == "GROUNDED":
        ev = b["evidence"]
        return {"会計": ev["scope"], "階層": ev["level"], "親": ev["parent"],
                "科目名": ev["name"], "列": ev["column"], "値": ev["value"]}
    if b["state"] != "VALUE_MISMATCH":
        return None
    entries, _c, _v = index()
    cands, _k, blocked, _i = M7.candidates(claim, entries)
    if blocked:
        return None
    groups = collections.OrderedDict()
    for e in cands:
        groups.setdefault(M7.field_key(e), []).append(e)
    if len(groups) != 1:
        return None
    e = list(groups.values())[0][0]
    return {"会計": e["scope"], "階層": e["level"], "親": e["parent"],
            "科目名": e["name"], "列": e["column"], "値": e["value"]}


def score_variant(name, text, changed, planted, c0, gold):
    """1 つの変種を採点する。**封 §3 の分け方のまま。**"""
    cv, bv = run_core(text)
    ok, why = check_variant(cv, c0, set(changed))
    out = {"変種": name, "誤りの id": sorted(changed), "有効": ok, "無効の理由": why,
           "誤りの採点": [], "無改変": {"偽警報": 0, "保留": 0, "確認済み": 0,
                              "偽警報の id": []},
           "罠(%s)" % TRAP_ID: None, "件ごと": []}
    if not ok:
        return out
    cm = {c["id"]: c for c in cv}
    bm = {b["claim_id"]: b for b in bv}
    for cid in sorted(cm):
        b, c = bm[cid], cm[cid]
        kind = classify(b)
        row = {"id": cid, "答え": kind, "状態": b["state"]}
        if cid in changed:
            p = [x for x in planted if x["id"] == cid][0]
            ref = ref_of(c, b)
            row.update({
                "誤りの型": p["型"], "群": p["群"],
                "検出-1 誤りだと言えた": kind == "検出",
                "見落とし": kind == "確認済み",
                "保留": kind == "保留",
                "検出-2 正しい根拠": (S.same_row(ref, p["正しい参照先(改変前)"])
                              if ref else None),
                "示した参照先": ref,
                "検出-3 種類": kind_of_core(b),
                "検出-3 正解ラベル": p["誤りの種類(正解ラベル)"],
                "検出-3 一致": (kind_of_core(b)
                           == p["誤りの種類(正解ラベル)"]) and kind == "検出"})
            out["誤りの採点"].append(row)
        elif cid == TRAP_ID:
            out["罠(%s)" % TRAP_ID] = {
                "答え": kind, "状態": b["state"],
                "**文書は正しいのに一致しないと言ったか**": kind == "検出"}
        else:
            key = {"検出": "偽警報", "保留": "保留", "確認済み": "確認済み"}[kind]
            out["無改変"][key] += 1
            if kind == "検出":
                out["無改変"]["偽警報の id"].append(cid)
        out["件ごと"].append(row)
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    shas = RUN.check_shas()
    mk = load(MAKE)
    planted = mk["植えた誤り"]
    report = load(REPORT)["report"]
    gold = {r["id"]: r for r in load(GOLD)["rows"]}
    c0, b0 = run_core(report)
    frozen = {b["claim_id"]: b for b in load(BINDS)["binds_new"]}
    drift = [b["claim_id"] for b in b0
             if b["state"] != frozen[b["claim_id"]]["state"]]
    if drift:
        raise SystemExit("**対照が段 11 の記録と違う: %s**" % drift)

    singles = [score_variant(v["名前"], v["本文"], v["誤りの id"], planted, c0, gold)
               for v in mk["1 件ずつの変種"]]
    bundle = score_variant("束ねた変種(8 件)", mk["束ねた変種"]["本文"],
                           mk["束ねた変種"]["誤りの id"], planted, c0, gold)

    # **束ねた変種と 1 件ずつで、件ごとの結果が一致するか**(封 §1-1・F-6)
    bmap = {r["id"]: r["答え"] for r in bundle["件ごと"]}
    cross = []
    for s in singles:
        for r in s["件ごと"]:
            if r["id"] in s["誤りの id"] and bmap.get(r["id"]) != r["答え"]:
                cross.append({"id": r["id"], "1 件ずつ": r["答え"],
                              "束ねた": bmap.get(r["id"])})
    err = [r for s in singles for r in s["誤りの採点"]]
    by_type = collections.defaultdict(lambda: collections.Counter())
    for r in err:
        by_type[r["誤りの型"]][r["答え"]] += 1
    by_group = collections.defaultdict(lambda: collections.Counter())
    for r in err:
        by_group[r["群"]][r["答え"]] += 1
    by_strat = collections.defaultdict(lambda: collections.Counter())
    for r in err:
        p = [x for x in planted if x["id"] == r["id"]][0]
        by_strat["結べた" if p["Core が結べた主張か"] else "結べなかった"][r["答え"]] += 1

    miss = [r["id"] for r in err if r["見落とし"]]
    det = [r["id"] for r in err if r["検出-1 誤りだと言えた"]]
    held = [r["id"] for r in err if r["保留"]]
    fa = sorted({i for s in singles for i in s["無改変"]["偽警報の id"]})
    d2 = [r["id"] for r in err if r["検出-2 正しい根拠"] is True]
    d3 = [r["id"] for r in err if r["検出-3 一致"]]
    bound_ids = [p["id"] for p in planted if p["Core が結べた主張か"]]
    unbound_ids = [p["id"] for p in planted if not p["Core が結べた主張か"]]

    ver = {
        "E-1 見落とし = 0 件": {"実測": len(miss), "ids": miss,
                         "満たした": len(miss) == 0},
        "E-2 偽警報 ≦ 1 件": {"実測": len(fa), "ids": fa,
                        "満たした": len(fa) <= 1,
                        "分母": "無改変の主張(1 件ずつの変種では 1 件につき 33 件。"
                              "罠 %s は別記)" % TRAP_ID},
        "E-3 結べた 4 件の誤りは全部検出": {
            "結べた ids": bound_ids, "検出した ids": det,
            "満たした": sorted(det) == sorted(bound_ids)},
        "E-4 結べなかった 4 件は検出 0・保留 4(**合否ではない**)": {
            "結べなかった ids": unbound_ids, "保留した ids": held,
            "そのとおりか": sorted(held) == sorted(unbound_ids)},
    }
    pass_all = all(ver[k]["満たした"] for k in
                   ("E-1 見落とし = 0 件", "E-2 偽警報 ≦ 1 件",
                    "E-3 結べた 4 件の誤りは全部検出"))

    rec = {"seal": SEAL, "step": "封 §8 の 3。**Core 単体。費用 0 USD**",
           "engine_sha": shas,
           "**B は参考群である**": ("封 §5-1。**勝っても製品の結論にしない。**"
                          "測るのは検証器の価値であって Core の優位性ではない"),
           "対照が段 11 の記録と一致": not drift,
           "植えた誤り": len(planted),
           "**判定(封 §3-4)**": ver,
           "合否": "**合格**" if pass_all else "**不合格**",
           "検出 / 保留 / 見落とし(誤り 8 件)": {
               "検出": {"件数": len(det), "ids": det},
               "保留": {"件数": len(held), "ids": held},
               "見落とし": {"件数": len(miss), "ids": miss}},
           "検出-2 正しい根拠を提示": {"件数": len(d2), "ids": d2,
                            "分母": "誤り 8 件"},
           "検出-3 種類を特定": {"件数": len(d3), "ids": d3,
                         "分母": "誤り 8 件",
                         "注": ("Core は「値が合わない」としか言えない。"
                               "**群 I の正解ラベルと一致した分だけ当たる**")},
           "型ごと": {k: dict(v) for k, v in by_type.items()},
           "群ごと": {k: dict(v) for k, v in by_group.items()},
           "層ごと(結べた / 結べなかった)": {k: dict(v) for k, v in by_strat.items()},
           "偽警報(無改変。罠は別記)": {"件数": len(fa), "ids": fa},
           "罠(%s)" % TRAP_ID: {
               "1 件ずつの変種での答え": sorted({
                   s["罠(%s)" % TRAP_ID]["答え"] for s in singles
                   if s["罠(%s)" % TRAP_ID]}),
               "束ねた変種での答え": (bundle["罠(%s)" % TRAP_ID] or {}).get("答え"),
               "注": ("**文書は正しい。`extract_claims` の符号落ち。**"
                     "**検出率の分母に入れない**(封 §2-4)")},
           "束ねた変種": {"無改変": bundle["無改変"],
                    "誤りの採点": [{k: r[k] for k in
                                ("id", "答え", "誤りの型", "群")}
                               for r in bundle["誤りの採点"]]},
           "**束ねた変種と 1 件ずつの食い違い**": {"件数": len(cross),
                                   "明細": cross,
                                   "判定": ("一致(交絡なし)" if not cross
                                         else "**食い違った。束ねた変種を "
                                              "LLM 側に使わない**")},
           "1 件ずつの変種": singles,
           "limits": [
               "**人工的な誤りである。**実際の文書で起きる誤りの分布は測っていない"
               "(封 §7 の 1)。",
               "**誤りは正解集合の 24 件にしか植えていない。**"
               "別枠 11 件での検出能力は測れない。",
               "**B は参考群である。**この数で製品の結論を書かない。",
               "**罠(%s)は私の欠陥であって文書の誤りではない。**"
               "「検出できた」と書かない。" % TRAP_ID,
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== Core 単体 × 誤り入りの報告文(費用 0)===")
    print("対照は段 11 の記録と一致: %s / 植えた誤り %d 件"
          % (not drift, len(planted)))
    print("**検出 %d / 保留 %d / 見落とし %d**(誤り 8 件)"
          % (len(det), len(held), len(miss)))
    print("   検出: %s" % det)
    print("   保留: %s" % held)
    print("検出-2 正しい根拠 %d/8: %s" % (len(d2), d2))
    print("検出-3 種類の特定 %d/8: %s" % (len(d3), d3))
    print("型ごと: %s" % json.dumps({k: dict(v) for k, v in by_type.items()},
                                 ensure_ascii=False))
    print("層ごと: %s" % json.dumps({k: dict(v) for k, v in by_strat.items()},
                                 ensure_ascii=False))
    print("偽警報(無改変): %d 件 %s" % (len(fa), fa))
    print("罠 %s: 1 件ずつ %s / 束ね %s"
          % (TRAP_ID, rec["罠(%s)" % TRAP_ID]["1 件ずつの変種での答え"],
             rec["罠(%s)" % TRAP_ID]["束ねた変種での答え"]))
    print("束ねた変種との食い違い: %s"
          % rec["**束ねた変種と 1 件ずつの食い違い**"]["判定"])
    for k, v in ver.items():
        print("%-40s %s" % (k, json.dumps(v, ensure_ascii=False)))
    print("**合否: %s**" % rec["合否"])
    print("->", OUT)


if __name__ == "__main__":
    main()
