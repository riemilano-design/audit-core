# -*- coding: utf-8 -*-
"""**追記**(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md の採点の後に足す数)。

**封の採点基準・合否は 1 つも変えない。合否にこの数を使わない。**
足すのは、採点してから分かった**私の指標の穴**を埋める観測である。

## 穴

封の **検出-2「正しい根拠を提示できたか」**は、
**「改変前の正しい行」を指したか**だけを見ていた。
ところが席は、群 II(値は原資料に在るが参照先が違う)で
**「その数が実際に載っている行」**を指して「列の取り違え / 別の科目の値」と述べた。
**これは誤りの説明としては正しい振る舞い**だが、封の 検出-2 では 0 点になる。

**だから「どちらの行を指したか」を 2 つに分けて数え直す**(**合否には使わない**)。

  **追-1** 改変前の**正しい行**を指した(= 封の 検出-2)
  **追-2** 植えた値が**実際に載っている行**を指した(= 誤りの出どころを指した)

併せて、**無改変 26 件での「確認済み / 保留」**を方式ごとに並べる
(**要確認の件数**は顧客にとっての重さだが、封の合否には入っていない)。

    python3 measure/sheet_errdet_addendum_2026-10-17.py
"""
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
SCORE = os.path.join(FX, "errdet_score_2026-10-17.json")
COREREC = os.path.join(FX, "errdet_core_2026-10-17.json")
OUT = os.path.join(FX, "errdet_addendum_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


A3 = _mod("m3add_for_errdet_add", "sheet_poc_m3_addendum_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def points_at_source(ans, planted_value):
    """**追-2**: 指した行が実在し、その値が**植えた値**と同じか。

    引き当ては追記の `reach()`(M-3′)を**そのまま使う** ―
    片側だけ別の正規化を当てない。
    """
    if ans is None:
        return False, "住所が無い"
    ok, why, _n = A3.reach(ans, planted_value)
    return ok, why


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    mk = {p["id"]: p for p in load(MAKE)["植えた誤り"]}
    sc = load(SCORE)
    core = load(COREREC)

    out = {}
    for arm, rows in sc["件ごとの記録(35 件)"].items():
        by = {r["id"]: r for r in rows}
        a1, a2, detail = [], [], []
        for cid, p in sorted(mk.items()):
            r = by[cid]
            e = [x for x in sc["誤りの件ごと"][arm] if x["id"] == cid][0]
            src_ok, why = points_at_source(r["住所"], p["植えた値"])
            if e["検出-2 正しい根拠"] is True:
                a1.append(cid)
            if src_ok:
                a2.append(cid)
            detail.append({"id": cid, "型": p["型"], "群": p["群"],
                           "追-1 改変前の正しい行": e["検出-2 正しい根拠"],
                           "追-2 植えた値の出どころの行": src_ok,
                           "落ちた理由": None if src_ok else why,
                           "指した住所": r["住所"]})
        out[arm] = {"追-1 改変前の正しい行を指した": {"件数": len(a1), "ids": a1},
                    "追-2 植えた値の出どころを指した": {"件数": len(a2), "ids": a2},
                    "無改変 26 件": sc["A / C の内訳"][arm][
                        "無改変(26 件。罠は別記)"],
                    "明細": detail}
    out["B(参考群)"] = {
        "追-1 改変前の正しい行を指した": {"件数": len(core["検出-2 正しい根拠を提示"]["ids"]),
                            "ids": core["検出-2 正しい根拠を提示"]["ids"]},
        "追-2 植えた値の出どころを指した": {
            "件数": 0,
            "注": "**Core は鍵を文から作るので、出どころの行は出さない**"},
        "無改変 26 件": core["束ねた変種"]["無改変"]}

    rec = {"seal": SEAL,
           "step": "**追記。封の採点基準・合否は変えない。合否にこの数を使わない**",
           "**なぜ追記が要るのか**": (
               "封の 検出-2 は「改変前の正しい行を指したか」だけを見ていた。"
               "**席は群 II で「その数が実際に載っている行」を指して"
               "「列の取り違え / 別の科目の値」と述べた** ― "
               "**誤りの説明としては正しい振る舞いだが、封の 検出-2 では 0 点になる。**"
               "だから 2 つに分けて数え直した"),
           "方式ごと": out,
           "limits": [
               "**これは追記であって、封の採点基準の変更ではない。**"
               "**合否(G-1・G-2)にこの数を使っていない。**",
               "**追-2 は「出どころを指した」だけで、"
               "顧客にとっての有用性を測ったものではない。**",
               "**無改変 26 件の「保留」の実務的な重さは測っていない。**",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 追記(合否には使わない)===")
    print("%-14s %-28s %-28s %s" % ("方式", "追-1 正しい行", "追-2 出どころの行",
                                    "無改変 26 件"))
    for arm in sorted(out):
        v = out[arm]
        print("%-14s %-28s %-28s %s"
              % (arm,
                 "%d %s" % (v["追-1 改変前の正しい行を指した"]["件数"],
                            v["追-1 改変前の正しい行を指した"]["ids"]),
                 "%d %s" % (v["追-2 植えた値の出どころを指した"]["件数"],
                            v["追-2 植えた値の出どころを指した"].get("ids", "")),
                 json.dumps(v["無改変 26 件"], ensure_ascii=False)))
    print("->", OUT)


if __name__ == "__main__":
    main()
