# -*- coding: utf-8 -*-
"""段 4 の材料(報告文を書かせる抜粋と指示文)を**機械で**作る(封 §2)。

**司令塔が行を選ばない。**選ぶと分母が歪む。規則は封に固定済み:
  総括 19 会計すべて / 決算書の款 37 件すべて / 明細の目は**先頭から 60 件**。
上限は封 §1 の字(抜粋 24,000 字以内・報告文 1,200 字以内)。

    python3 measure/sheet_m4_material_2026-10-15.py

出力 `fixtures/sheet/m4_material_2026-10-15.json` は**報告文を生成する前に commit する**。
出典: 東京都会計管理局「令和６年度東京都各会計歳入歳出決算書…」CC BY 4.0。
"""
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "m4_material_2026-10-15.json")
MAX_EXTRACT = 24000
MAX_REPORT = 1200
MOKU_HEAD = 60
MODEL = "claude-sonnet-4-5"

_spec = importlib.util.spec_from_file_location(
    "m2", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M2)

PROMPT = u"""次の表は、ある自治体の令和６年度の歳入歳出決算の抜粋です。
この表だけを根拠に、決算の要点を説明する報告文を日本語で %d 字以内で書いてください。
条件: (1) 金額を少なくとも 15 か所挙げ、どの会計・どの科目の数かが読者に分かるように書く。
(2) 表に無い数は書かない。(3) 見出しや箇条書きを使ってよい。
(4) 注記や出典、計算過程の説明は不要。本文だけを書いてください。

----- 表(ここから) -----
%s
----- 表(ここまで) -----""" % (MAX_REPORT, u"%s")


def yen(v):
    return "" if v is None else "{:,}".format(v)


def build():
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        p = os.path.join(M2.CACHE, f)
        if not os.path.exists(p):
            raise SystemExit("材料が無い: %s" % f)
        books[f], _ = M2.M1.read(p)
    soukatu = M2.parse_soukatu(books[M2.SOUKATU])
    kessan = M2.parse_kessan(books[M2.KESSAN])
    meisai = M2.parse_meisai(books[M2.MEISAI])

    lines, counts = [], {}
    lines.append("【表 1】会計別の決算額(単位: 円)")
    lines.append("会計別\t歳入決算額\t歳出決算額\t差額")
    n = 0
    for a in soukatu["accounts"]:
        v = a["values"]
        lines.append("%s\t%s\t%s\t%s" % (a["name"], yen(v.get("歳入決算額")),
                                         yen(v.get("歳出決算額")), yen(v.get("差額"))))
        n += 1
    counts["表1_行"] = n

    lines.append("")
    lines.append("【表 2】款別の歳出(単位: 円)")
    lines.append("会計\t款\t款名\t予算現額\t支出済額\t翌年度繰越額\t不用額")
    n = 0
    for b in kessan["blocks"]:
        for k in b["kan"]:
            v = k["values"]
            lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                b["account"], k.get("code"), k.get("name"),
                yen(v.get(M2.norm("予算現額"))), yen(v.get(M2.norm("支出済額"))),
                yen(v.get(M2.norm("翌年度繰越額"))), yen(v.get(M2.norm("不用額")))))
            n += 1
    counts["表2_行"] = n

    lines.append("")
    lines.append("【表 3】目別の歳出(先頭から %d 件。単位: 円)" % MOKU_HEAD)
    lines.append("会計\t款名\t項名\t目名\t予算現額の計\t支出済額\t不用額")
    n = 0
    for s in meisai["sheets"]:
        kan_rows = sorted(k["row"] for k in s["kan"])
        item_rows = sorted(i["row"] for i in s["items"])
        for mo in s["moku"]:
            if n >= MOKU_HEAD:
                break
            parent_item = [i for i in s["items"] if i["row"] < mo["row"]]
            parent_kan = [k for k in s["kan"] if k["row"] < mo["row"]]
            v = mo["values"]
            lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                s["account"],
                (parent_kan[-1].get("name") if parent_kan else ""),
                (parent_item[-1].get("name") if parent_item else ""),
                mo.get("name"), yen(v.get("計")), yen(v.get("支出済額")), yen(v.get("不用額"))))
            n += 1
        if n >= MOKU_HEAD:
            break
    counts["表3_行"] = n

    extract = "\n".join(lines)
    if len(extract) > MAX_EXTRACT:
        raise AssertionError("抜粋が封の上限を超えた: %d 字 > %d 字" % (len(extract), MAX_EXTRACT))
    return extract, counts


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    extract, counts = build()
    rec = {"seal": "docs/DOMAIN1_M4_SEAL_2026-10-15.md",
           "model": MODEL, "runs": 1,
           "limits": {"extract_chars": MAX_EXTRACT, "report_chars": MAX_REPORT},
           "rule": "総括 19 会計すべて / 款 37 件すべて / 目は先頭から %d 件(内容で選ばない)" % MOKU_HEAD,
           "counts": counts, "extract_chars": len(extract),
           "prompt": PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3 の結果"]}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("抜粋 %d 字 / %s -> %s" % (len(extract), counts, OUT))


if __name__ == "__main__":
    main()
