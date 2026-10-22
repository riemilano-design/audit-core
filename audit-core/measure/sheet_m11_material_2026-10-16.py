# -*- coding: utf-8 -*-
"""段 11 本実験の材料(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §2)。

**報告文を生成する前に commit する。**

**選び方の規則は段 9 の script をそのまま呼ぶ**(封 §2-1)。
この file が変えるのは**除外する標本の範囲だけ**である:

  * 値の除外に **段 9** を足す → 段 4〜段 9 で主張された値(0 を除く)の行は入らない
  * 既出の行の数えに **段 9 の材料**を足す → 重複は**落とさずに数えて開示する**

**材料は旧 engine(`sheet_m5_engine`)の別名表で作る**(封 §2-2)。
歳入側の engine で作ると 18 会計が正本に直って印字され、
**抜粋に別名の形が 1 行も載らず、試験の歯がそこで消える。**
`check_alias_forms_are_printed()` がその歯である。

**封 §2-3 の停止条件をここで判定する**(生成より先):
  * 表 3b が 0 行 / 表 3b の会計が 0 件 / 値のセルが 20 未満 → **生成しない**

    python3 measure/sheet_m11_material_2026-10-16.py
"""
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "m11_material_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"
# **段 9 を足す。これがこの file の唯一の変更点である**(封 §2-1)
ADD_BINDS = "m9_binds_2026-10-16.json"
ADD_MAT = "m9_material_2026-10-16.json"
MIN_CELLS = 20                   # 封 §2-3。**G-5 の線(20 件)と同じ数**
ALIAS_FORM = re.compile(r"東京都.+?会計")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


M9 = _mod("m9mat_for_m11", "sheet_m9_material_2026-10-16.py")
OPP = _mod("opp9_for_m11", "sheet_m9_opportunity_2026-10-16.py")


def widened():
    """段 9 を足した除外の範囲を返す。**規則は足さない。範囲だけ広げる。**"""
    return (tuple(M9.PREV) + (ADD_BINDS,), tuple(M9.PREV_MAT) + (ADD_MAT,))


def build():
    """段 9 の `build()` を**そのまま呼ぶ。**入力の範囲だけ差し替える。"""
    prev, prev_mat = widened()
    old = (M9.PREV, M9.PREV_MAT)
    M9.PREV, M9.PREV_MAT = prev, prev_mat
    try:
        return M9.build()
    finally:
        M9.PREV, M9.PREV_MAT = old          # **凍結した module を汚さない**


def check_alias_forms_are_printed(extract):
    """**歯**: 抜粋に `東京都○○会計` の形が載っていること(封 §2-2)。

    歳入側の engine で材料を作ると全部正本に直るので、ここが 0 件になる。
    **0 件なら③の発火機会が無い ― 材料の作り方を間違えている。**
    """
    forms = sorted(set(ALIAS_FORM.findall(extract)))
    if not forms:
        raise AssertionError(
            "**抜粋に別名の形が 1 件も無い。**歳入側の engine で材料を作った疑いが在る"
            "(封 §2-2)。③の発火機会が消えている")
    return forms


def _printed_rows(extract):
    """抜粋に**印字された行**の鍵を表ごとに返す(**開示のための別計算**)。

    段 9 の `rows_in_previous_extracts()` は 表 3 を **5 欄か 7 欄**で読む。
    **段 9 の表 3 は 6 欄で印字されている**ので、あの数え方には当たらない
    ― つまり「過去の抜粋と重複した行」は**段 9 の表 3 を数えられていない。**
    規則は凍結した側の字なので**変えない。**代わりに**正しい数を別に測って開示する。**
    (重複した行は落とさずに数えるだけなので、**標本の選び方には影響しない。**)
    """
    out = {"表2": set(), "表3": set()}
    for line in extract.split("\n"):
        if "\t" not in line:
            continue
        c = [x.strip() for x in line.split("\t")]
        if c[0] == "会計":
            continue
        if len(c) == 7 and c[1] in ("款", "項"):
            out["表2"].add((M9.norm(c[0]), M9.norm(c[1]), M9.norm(c[2]),
                            M9.norm(c[3])))
        elif len(c) == 6 and c[1] and c[2] and c[3]:
            out["表3"].add((M9.norm(c[0]), M9.norm("目"),
                            M9.norm("%s > %s" % (c[1], c[2])), M9.norm(c[3])))
    return out


def overlap_disclosure(extract):
    """段 9 の抜粋と**実際に**重複した行を表ごとに数える(**開示だけ**)。"""
    mat = json.load(io.open(os.path.join(FX, ADD_MAT), encoding="utf-8"))
    m9x = (mat["prompt"].split("----- 表(ここから) -----")[1]
           .split("----- 表(ここまで) -----")[0])
    a, b = _printed_rows(extract), _printed_rows(m9x)
    return {"表2": len(a["表2"] & b["表2"]), "表3": len(a["表3"] & b["表3"]),
            "段 9 の抜粋の行": {k: len(v) for k, v in b.items()},
            "注": ("**段 9 の script の数え方は 6 欄の表 3 に当たらない**ので、"
                   "記録の『過去の抜粋と重複した行』は段 9 の表 3 を含まない。"
                   "**規則は凍結した側の字なので変えず、正しい数をここに開示する。**"
                   "重複した行は**落とさずに数えるだけ**なので、"
                   "**標本の選び方には影響しない**")}


def stop_check(counts, cells):
    """封 §2-3 の 3 つの条件。**判定を 1 か所に置く**(字で書くと変異が黙る)。"""
    fail = []
    if counts["表3b_行"] < 1:
        fail.append("表 3b が 0 行(③の機会が無い)")
    if len(counts["表3b_の会計"]) < 1:
        fail.append("表 3b に載る会計が 0 件")
    if cells < MIN_CELLS:
        fail.append("値のセルが %d 件(G-5 の線 %d を満たせない)" % (cells, MIN_CELLS))
    return {"生成してよいか": not fail, "止める理由": fail,
            "規則": ("表 3b ≥ 1 行・表 3b の会計 ≥ 1 件・値のセル ≥ %d。"
                     "満たさなければ生成しない。**規則を緩めて機会を作り直さない**"
                     % MIN_CELLS)}


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    b = build()
    extract, counts = b["extract"], b["counts"]
    forms = check_alias_forms_are_printed(extract)
    cells = OPP.cells_of(extract)
    stop = stop_check(counts, len(cells))
    prev, prev_mat = widened()
    rec = {"seal": SEAL,
           "step": "封 §11 の 2。**生成より先に commit する**",
           "model": M9.MODEL, "runs": 1,
           "limits": {"extract_chars": M9.MAX_EXTRACT,
                      "report_chars": M9.MAX_REPORT},
           "rule_source": "measure/sheet_m9_material_2026-10-16.py の build()",
           "rule": ("**段 9 の規則をそのまま呼んだ。**変えたのは除外する標本の範囲だけ"
                    "(段 4〜段 8 → 段 4〜**段 9**)"),
           "excluded_stages": list(prev),
           "excluded_extracts": list(prev_mat),
           "alias_table_from": ("**旧 engine(measure/sheet_m5_engine_2026-10-15.py)**。"
                                "歳入側の engine では作らない(封 §2-2。"
                                "作ると抜粋に別名の形が 1 行も載らず歯が消える)"),
           "alias_forms_in_extract": forms,
           "value_columns": {"表2": list(M9.COLS_KESSAN), "表3": list(M9.COLS_MEISAI)},
           "change_from_m9": [
               "**除外する値に段 9 の主張を足した**(標本が新しくなる)",
               "**既出の行の数えに段 9 の抜粋を足した**(落とさずに数えて開示する)",
               "**規則・表の形・列・上限・指示文は 1 文字も変えていない。**",
           ],
           "prompt_identical_to_stage4": True,
           "excluded_values": b["excluded_values"],
           "excluded_rows_from_previous_extracts":
               b["excluded_rows_from_previous_extracts"],
           "counts": counts, "chosen": b["chosen"],
           "過去の抜粋と重複した行(正しい数。開示)": overlap_disclosure(extract),
           "value_cells": len(cells),
           "stop_check": stop,
           "kou_backing_dropped": b["kou_backing_dropped"],
           "moku_backing_dropped": b["moku_backing_dropped"],
           "alias": {"通った": b["alias_passed"],
                     "未確認の別名": b["unconfirmed_alias"],
                     "未確認の正本": b["unconfirmed_canonical"],
                     "注": ("**抜粋の会計の欄は旧 engine の canonicalize 後の字。**"
                            "裏づけの在る別名だけが直り、無い別名は "
                            "`東京都○○会計` のまま載る。**この差が③の発火機会であり、"
                            "新 engine が正本に直す対象である。**")},
           "extract_chars": len(extract),
           "prompt": M9.PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3 の結果",
                        "段 4〜段 9 の報告文と採点結果", "診断(P-5)の結果",
                        "機会の数(O-1〜O-8)", "歳入側の裏づけの規則", "③の存在"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋 %d 字 / 値のセル %d / 除いた値 %d / 既出の行 %d"
          % (len(extract), len(cells), b["excluded_values"],
             b["excluded_rows_from_previous_extracts"]))
    print("別名の形: %s" % "・".join(forms[:6]))
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    print("**停止条件: %s**%s"
          % ("生成してよい" if stop["生成してよいか"] else "生成しない",
             "" if stop["生成してよいか"] else " / " + "・".join(stop["止める理由"])))
    print("->", OUT)


if __name__ == "__main__":
    main()
