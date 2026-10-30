# -*- coding: utf-8 -*-
"""段 4 のラベル材料を作る(封 §4-1)。**2 席に渡すものは engine の出力を含まない。**

渡すのは: 表の抜粋(生成に使ったものと同じ)+ 主張 1 件ずつ(文・金額の表記)+ 問い。
渡さないのは: engine の判定・pointer・状態・ルート・切り出した主語や列の手がかり・
封・仕様・段 3 の結果。**席 2 は主張の並びを逆順にする。**

材料のファイル全体に禁じた語が無いかを機械で確かめる(前例: note 欄から漏れた)。

    python3 measure/sheet_m4_label_material_2026-10-15.py <出力の親ディレクトリ>
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(ROOT, "fixtures", "sheet", "m4_material_2026-10-15.json")
BINDS = os.path.join(ROOT, "fixtures", "sheet", "m4_binds_2026-10-15.json")
OUT = os.path.join(ROOT, "fixtures", "sheet", "m4_label_material_2026-10-15.json")

BANNED = ["GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
          "pointer", "R-1", "R-3", "R-4", "range_identified", "value_match",
          "封", "合格", "不合格", "engine", "照合結果", "判定結果", "正解"]

QUESTION = u"""以下に (A) 自治体の令和６年度決算の表の抜粋と、(B) ある報告文から抜き出した金額の一覧があります。
(B) の各行について、その金額が (A) の表のどこの数かを答えてください。

答える欄は 4 つです。
  会計   … 表 1 の「会計別」、表 2・表 3 の「会計」に在る名前(例: 一般会計)
  階層   … 会計 / 款 / 項 / 目 / 合計 のどれか
  科目名 … 款名・項名・目名(会計そのものの数なら空欄)
  列     … 歳入決算額 / 歳出決算額 / 差額 / 予算現額 / 支出済額 / 翌年度繰越額 / 不用額 / 計 のどれか

表のどこの数とも決められない場合は、次のどちらかを書いてください。
  根拠なし   … その金額が表に見当たらない
  判定不能   … 文からはどれを指すか決められない(複数に当たる など)

出力は JSON の配列だけにしてください。説明や前置きは書かないこと。各要素は次の形です。
  {"id": "R001", "会計": "一般会計", "階層": "会計", "科目名": "", "列": "歳出決算額"}
  {"id": "R002", "verdict": "根拠なし"}
"""


def main():
    parent = sys.argv[1]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    extract = mat["prompt"].split("----- 表(ここから) -----")[1].split("----- 表(ここまで) -----")[0].strip()
    rows = [{"id": c["id"], "金額の表記": c["text"], "文": c["sentence"]} for c in claims]
    made = []
    for seat, order in (("seat1", rows), ("seat2", list(reversed(rows)))):
        body = [QUESTION, "", "(A) 表の抜粋", extract, "", "(B) 金額の一覧(%d 件)" % len(order)]
        for r in order:
            body.append("- id: %s / 金額: %s / 文: %s" % (r["id"], r["金額の表記"], r["文"]))
        text = "\n".join(body)
        for w in BANNED:
            if w in text:
                raise AssertionError("禁じた語が材料に在る: %s" % w)
        d = os.path.join(parent, "m4_label_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        made.append({"seat": seat, "path": p, "chars": len(text),
                     "first_id": order[0]["id"], "last_id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s" % (seat, len(text), order[0]["id"],
                                                      order[-1]["id"], p))
    rec = {"seal": "docs/DOMAIN1_M4_SEAL_2026-10-15.md",
           "claims": len(rows), "question": QUESTION, "banned_checked": BANNED,
           "seats": [{"seat": "seat1", "model": "claude-sonnet-4-5", "order": "そのまま"},
                     {"seat": "seat2", "model": "claude-haiku-4-5", "order": "逆順"}],
           "files": made,
           "withheld": ["engine の判定", "pointer", "状態", "ルート",
                        "切り出した主語・列の手がかり", "封", "仕様", "段 3 の結果"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
