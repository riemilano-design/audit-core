# -*- coding: utf-8 -*-
"""**M-3 の追記**(封 docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md §4 の後)。

**封の採点条件は変えない。**封の M-3 の数はそのまま残し、**別の数をここに足す。**

## なぜ要るのか(測って分かった私の器の欠陥)

封の M-3 は「**一意のセル**が見つかり、その値が主張の金額と一致」と書いた。
実測すると A の 35 件中 **28 件**が「一意に定まらない(2 セル)」で落ちた。
理由を 1 件読んだら、**同じ行が 2 つの原資料に在る**からだった ―
例: `一般会計 / 項 / 総務費 / 子供政策連携費 / 支出済額` は
**決算書 歳出 `E25`** と **事項別明細 `R684`** の両方に在り、**値は同じ**。
**評価者はどちらでも辿れる。**つまりこれは**方式の出力の質ではなく、
原資料の構成(決算書と明細が同じ項を両方印字する)の性質である。**

**だから封の定義を書き換えず、2 つ目の定義を足して両方を出す**
(記憶 `evidence-file-must-be-the-completed-run`・`zero-count-may-be-my-own-bug`)。

| 記号 | 定義 |
|---|---|
| **M-3(封の字)** | 一意のセルが見つかり、値が主張と一致 |
| **M-3′(追記)** | 当たったセルが**すべて同じ値**で、**その値が主張と一致**(file をまたぐ重複は許す) |

**A・B のどちらにも同じ関数を当てる。**
**順位が変わるかどうかを必ず書く** ― 変わらなければ、この欠陥は結論に効いていない。

## 併せて測るもの ― **別枠での「根拠のない確認」**

別枠(正解不明 11 件)で、**方式が答えた行の値が主張の金額と違う**件を数える。
これは「**原資料に無い数を、在るかのように確認した**」件である。
**正解不明でも、これは機械で分かる。**

    python3 measure/sheet_poc_m3_addendum_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
SEAT1 = os.path.join(FX, "m11_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m11_answers_seat2_2026-10-16.json")
OUT = os.path.join(FX, "poc_m3_addendum_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


S = _mod("abscore_for_m3", "sheet_poc_ab_score_2026-10-17.py")


def cells_of(ans):
    """6 欄に当たる原資料のセルを全部返す(**A にも B にも同じ関数**)。"""
    out = []
    for e in S.index():
        if not S.scope_match(ans.get("会計"), e["scope"]):
            continue
        if S._s(ans.get("階層")) != S._s(e["level"]):
            continue
        if S._parent(ans.get("親")) != S._parent(e["parent"]):
            continue
        if S._s(ans.get("科目名")) != S._s(e["name"]):
            continue
        if not S.col_match(ans.get("列"), e["column"]):
            continue
        out.append({"file": e["file"],
                    "cell": (e.get("evidence") or {}).get("value_ref"),
                    "value": e["value"]})
    return out


def reach(ans, want):
    """**M-3′**: (到達できたか, 理由, 当たった file の数)。**判定を 1 か所に置く。**"""
    if ans is None:
        return False, "答えが住所になっていない", 0
    hits = cells_of(ans)
    if not hits:
        return False, "原資料に当たる行が無い", 0
    vals = {h["value"] for h in hits}
    if len(vals) > 1:
        return False, "当たった行の値が揺れる(%d 通り)" % len(vals), len(hits)
    if vals.pop() != want:
        return False, "到達した行の値が主張と違う", len(hits)
    return True, None, len(hits)


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    gold = json.load(io.open(GOLD, encoding="utf-8"))
    rec_in = json.load(io.open(BINDS, encoding="utf-8"))
    claims = {c["id"]: c for c in rec_in["claims"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}
    arms = {"A1 一般 LLM(sonnet)": {r["id"]: S.answer_of_seat(s1.get(r["id"]))
                                 for r in gold["rows"]},
            "A2 一般 LLM(haiku)": {r["id"]: S.answer_of_seat(s2.get(r["id"]))
                                for r in gold["rows"]},
            "B Audit Core": {r["id"]: S.answer_of_core(bn[r["id"]])
                             for r in gold["rows"]}}
    out, unfounded = {}, {}
    for name, ans in arms.items():
        n = ok = 0
        why = collections.Counter()
        files = collections.Counter()
        bad = []
        for r in gold["rows"]:
            kind, a, _ = ans[r["id"]]
            if kind != "接続":
                continue
            n += 1
            hit, w, nf = reach(a, claims[r["id"]]["value"])
            files[nf] += 1
            if hit:
                ok += 1
            else:
                why[w] += 1
            # **別枠での「根拠のない確認」**
            if not r["正解"] and not hit and w == "到達した行の値が主張と違う":
                bad.append({"id": r["id"], "主張": claims[r["id"]]["value"],
                            "答えた行": a})
        out[name] = {"接続した件": n, "到達できた(M-3′)": ok,
                     "rate": (float(ok) / n) if n else None,
                     "到達できない理由": dict(why),
                     "当たった file の数ごと": dict(files)}
        unfounded[name] = {"件数": len(bad), "明細": bad}

    封 = {k: v["M-3 根拠の再現性"] for k, v in
         json.load(io.open(os.path.join(FX, "poc_ab_score_2026-10-17.json"),
                           encoding="utf-8"))["arms"].items()} \
        if os.path.exists(os.path.join(FX, "poc_ab_score_2026-10-17.json")) else {}
    order_sealed = sorted(封, key=lambda k: -(封[k]["rate"] or 0)) if 封 else []
    order_new = sorted(out, key=lambda k: -(out[k]["rate"] or 0))
    rec = {"seal": SEAL, "step": "**封の採点条件は変えない。数を足すだけ**",
           "**なぜ追記が要るのか**": (
               "封の M-3 は「一意のセル」を求めたが、**同じ行が決算書 歳出と事項別明細の"
               "両方に在り、値は同じ**(例 `E25` と `R684`)。"
               "**評価者はどちらでも辿れるので、これは方式の出力の質ではなく"
               "原資料の構成の性質である。**"
               "**封の数は残し、2 つ目の定義の数をここに足す。**"),
           "M-3(封の字。残す)": 封,
           "M-3′(追記。file をまたぐ重複を許す)": out,
           "順位は変わったか": {
               "封の順": order_sealed, "追記の順": order_new,
               "変わった": order_sealed != order_new,
               "注": ("**変わらなければ、この器の欠陥は A と B の比較の結論に"
                      "効いていない。**変わったなら結論を追記の側で書き直す")},
           "別枠での根拠のない確認(**原資料に無い数を在るかのように答えた**)":
               unfounded,
           "limits": [
               "**これは追記であって、封の採点条件の変更ではない。**"
               "封の M-3 の数はそのまま残してある",
               "**M-3′ も「同じ値のセルが複数在る」ことを許すだけで、"
               "どのセルを指したかの正しさは測っていない。**"
               "正しさは M-1 / M-2(正解集合)の側で測る",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== M-3 の追記(封の数は変えない)===")
    for name, v in out.items():
        print("%-22s M-3′ %5.1f%% (%2d/%2d) / 理由 %s"
              % (name, 100 * (v["rate"] or 0), v["到達できた(M-3′)"],
                 v["接続した件"], json.dumps(v["到達できない理由"],
                                        ensure_ascii=False)))
    print("封の順:", order_sealed)
    print("追記の順:", order_new)
    print("**順位は変わったか: %s**" % (order_sealed != order_new))
    print("--- 別枠での根拠のない確認 ---")
    for name, v in unfounded.items():
        print("%-22s %d 件 %s" % (name, v["件数"],
                                 [x["id"] for x in v["明細"]]))
    print("->", OUT)


if __name__ == "__main__":
    main()
