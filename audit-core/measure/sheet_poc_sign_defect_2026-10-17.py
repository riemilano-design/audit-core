# -*- coding: utf-8 -*-
"""**符号の落ちを診断する**(方式 C の採点の後に見つけた私の欠陥)。

**この診断は C の結果を見た後に書いた。だから予測は無い。測るのは事実だけである。**

## 何を見つけたか

報告文の 18 文目は「**補正予算額はマイナス48,327,000円**」と書いている。
`extract_claims` が切り出した `R035` は `text = "48,327,000円"` ・`value = 48327000` ―
**「マイナス」を落としている。**その結果

  * 正本の行(と場会計 / 目 / 運営費 / 補正予算額)の値は **-48,327,000**
  * だから **値が一致せず**、Core は「値の食い違いを検出」として保留した
  * 第 1 便の封の第 1 段は、同じ値で数えたので「**値が不一致**」に分類した
  * 席(A・C)は **値の欄に -48327000 と書いた** ― **文の「マイナス」を読んでいる**

**つまり「原資料に無い数を在るかのように答えた」という私の数え方は、この 1 件では
報告文の誤りを指していない。報告文は正しい。**落ちているのは**切り出しの符号**である。

**封の正解基準・正解集合・採点の数は 1 つも書き換えない**
(記憶 `evidence-file-must-be-the-completed-run`)。**数え直した結果をここに別に書く。**

    python3 measure/sheet_poc_sign_defect_2026-10-17.py
"""
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
OUT = os.path.join(FX, "poc_sign_defect_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"
ARMS = (("A1 一般 LLM(sonnet)", "m11_answers_seat1_2026-10-16.json"),
        ("A2 一般 LLM(haiku)", "m11_answers_seat2_2026-10-16.json"),
        ("C1 一般 LLM + 証拠(sonnet)", "poc_c_answers_seat1_2026-10-17.json"),
        ("C2 一般 LLM + 証拠(haiku)", "poc_c_answers_seat2_2026-10-17.json"))
# **負の印。字で留める**(日本語の決算書で使われる形)
MINUS_MARKS = ("マイナス", "△", "▲", "−", "-", "▲")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


G = _mod("gold_for_sign", "sheet_poc_gold_2026-10-17.py")
OPP = _mod("opp9_for_sign", "sheet_m9_opportunity_2026-10-16.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def minus_before(sentence, text):
    """`text` の**直前**に負の印が在るか。(在るか, 印, 直前の字) を返す。

    **判定を 1 か所に置く。**同じ字が文に 2 回出る場合は**どれかの出現**で見る。
    """
    i, found = 0, []
    while True:
        j = sentence.find(text, i)
        if j < 0:
            break
        before = sentence[max(0, j - 6):j]
        hit = [m for m in MINUS_MARKS if before.endswith(m)]
        found.append({"直前の字": before, "印": hit[0] if hit else None})
        i = j + 1
    marks = [f["印"] for f in found if f["印"]]
    return bool(marks), (marks[0] if marks else None), found


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    mat = load(MAT)
    cells = OPP.cells_of(OPP.extract_of(mat))
    rec_in = load(BINDS)
    claims = {c["id"]: c for c in rec_in["claims"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    gold = {r["id"]: r for r in load(GOLD)["rows"]}
    answers = {name: {a["id"]: a for a in load(os.path.join(FX, f))["answers"]}
               for name, f in ARMS}

    rows, affected = [], []
    for cid in sorted(claims):
        c = claims[cid]
        if c.get("skipped"):
            continue
        has, mark, found = minus_before(c["sentence"], c["text"])
        row = {"id": cid, "切り出した字": c["text"], "切り出した値": c["value"],
               "直前に負の印": has, "印": mark, "出現ごと": found}
        if has:
            fixed = -c["value"]
            kind, hits = G.classify_value(fixed, cells)
            row["符号を直した値"] = fixed
            row["符号を直したときの第 1 段"] = kind
            row["封の第 1 段(変えない)"] = gold[cid]["第 1 段"]
            if len(hits) == 1:
                ok, miss = G.independent_check(hits[0], c["sentence"])
                row["符号を直したときの第 2 段"] = {"通った条件": ok,
                                        "欠けた条件": miss}
                row["符号を直したら正解集合に入るか"] = not miss
            row["道具の状態"] = bn[cid]["state"]
            row["道具が出した行の値"] = bn[cid].get("recomputed")
            row["席が書いた値"] = {name: answers[name][cid].get("値")
                            for name, _f in ARMS}
            row["席の値が正本の行と一致"] = {
                name: answers[name][cid].get("値") == bn[cid].get("recomputed")
                for name, _f in ARMS}
            affected.append(row)
        rows.append(row)

    neg_cells = [c for c in cells if c["value"] < 0]
    rec = {
        "seal": SEAL,
        "step": "**C の採点の後に見つけた私の欠陥の診断。予測は無い**",
        "**封の正解基準・正解集合・採点の数は書き換えていない**": True,
        "主張の数": len(rows),
        "直前に負の印が在る主張": {"件数": len(affected),
                       "ids": [r["id"] for r in affected]},
        "抜粋の値のセル": len(cells),
        "そのうち負の値のセル": len(neg_cells),
        "明細": affected,
        "分かったこと": [
            "**`extract_claims` は金額の直前の「マイナス」を落とす。**"
            "切り出した値は正で、正本の行は負である。",
            "**報告文はこの件では正しい。**誤っているのは切り出しの符号である。",
            "**だから「原資料に無い数を在るかのように答えた」という数え方は、"
            "この件では報告文の誤りを指していない。**",
            "**席(A・C)は値の欄に正本の行と同じ負の値を書いた。**"
            "**文の「マイナス」を読んでいる。**",
            "**Core の「値の食い違いを検出」は、文書の層では空振りである** ― "
            "照合しているのは**自分の切り出した値**と正本だからである。",
        ],
        "limits": [
            "**これは 1 件の診断である。**規則を直していない。直しは別の封で切る。",
            "**封の第 1 段・正解集合・A / B / C の採点の数は 1 つも動かしていない。**"
            "動かすと凍結した記録が再現できなくなる。",
            "**「席が正しかった」と書けるのは値の欄の符号についてだけである。**"
            "席は食い違いを述べていない(保留していない)。",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 符号の落ちの診断(C の採点の後に見つけた)===")
    print("主張 %d 件 / 直前に負の印が在る主張 %d 件: %s"
          % (len(rows), len(affected), [r["id"] for r in affected]))
    print("抜粋の値のセル %d / そのうち負の値 %d" % (len(cells), len(neg_cells)))
    for r in affected:
        print("** %s: 切り出し %s(%d)/ 印 %s / 符号を直すと %d → 第 1 段 %s"
              % (r["id"], r["切り出した字"], r["切り出した値"], r["印"],
                 r["符号を直した値"], r["符号を直したときの第 1 段"]))
        print("   封の第 1 段(変えない): %s / 道具の状態 %s / 道具の行の値 %s"
              % (r["封の第 1 段(変えない)"], r["道具の状態"], r["道具が出した行の値"]))
        print("   符号を直したら正解集合に入るか: %s"
              % r.get("符号を直したら正解集合に入るか"))
        print("   席が書いた値: %s" % json.dumps(r["席が書いた値"],
                                           ensure_ascii=False))
        print("   席の値が正本の行と一致: %s"
              % json.dumps(r["席の値が正本の行と一致"], ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
