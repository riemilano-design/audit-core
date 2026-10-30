# -*- coding: utf-8 -*-
"""段 5 のラベル材料を作る(封 §1-1・§1-2・§1-5)。**2 席に渡すものは engine の出力を含まない。**

渡すのは: 表の抜粋(生成に使ったものと同じ)+ 主張 1 件ずつ(文・金額の表記)+ 問い。
渡さないのは: engine の判定・pointer・状態・ルート・切り出した主語や列の手がかり・
封・仕様・段 3 の結果。**席 2 は主張の並びを逆順にする。**

材料のファイル全体に禁じた語が無いかを機械で確かめる(前例: note 欄から漏れた)。

    python3 measure/sheet_m5_label_material_2026-10-15.py <出力の親ディレクトリ>
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(ROOT, "fixtures", "sheet", "m5_material_2026-10-15.json")
BINDS = os.path.join(ROOT, "fixtures", "sheet", "m5_binds_2026-10-15.json")
OUT = os.path.join(ROOT, "fixtures", "sheet", "m5_label_material_2026-10-15.json")

BANNED = ["GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
          "pointer", "R-1", "R-3", "R-4", "range_identified", "value_match",
          "封", "合格", "不合格", "engine", "照合結果", "判定結果", "正解",
          "未確認", "別名", "独立した裏づけ", "誤受理", "agree_"]

QUESTION = u"""以下に (A) 自治体の令和６年度決算の表の抜粋と、(B) ある報告文から抜き出した金額の一覧があります。
(B) の各行について、その金額が (A) の表のどこの数かを答えてください。

答える欄は 6 つです。
  会計   … 表 1 の「会計別」、表 2・表 3 の「会計」に在る名前(例: 一般会計)
  階層   … 会計 / 款 / 項 / 目 / 合計 のどれか
  親     … その行の親の科目名。**項なら款名、目なら「款名 > 項名」**(間は半角の > と空白)
           会計・合計・款 の行は**空欄**
  科目名 … 款名・項名・目名(会計そのものの数、および合計の行は**空欄**)
  列     … 歳入決算額 / 歳出決算額 / 差額 / 予算現額 / 支出済額 / 翌年度繰越額 / 不用額 / 計 のどれか
  値     … 表に書かれているその数(カンマ無しの整数)

**全会計を足し合わせた数(表 1 の「合計」の行)はこう書きます。**
  会計 = 合計 / 階層 = 合計 / 親 = 空欄 / 科目名 = 空欄 / 列 = その列
  例: 「全会計の合計では、歳入決算額15,769,405,199,513円」
      -> {"id": "...", "会計": "合計", "階層": "合計", "親": "", "科目名": "",
          "列": "歳入決算額", "値": 15769405199513}

**親の欄を埋められないときは、推測で埋めないでください。**
その場合は下の「判定不能」を選んでください。

表のどこの数とも決められない場合は、次のどちらかを書いてください。
  根拠なし   … その金額が表に見当たらない
  判定不能   … 文からはどれを指すか決められない(複数に当たる / 親が決まらない など)

出力は JSON の配列だけにしてください。説明や前置きは書かないこと。各要素は次の形です。
  {"id": "R001", "会計": "一般会計", "階層": "款", "親": "", "科目名": "福祉費",
   "列": "支出済額", "値": 1066495914576}
  {"id": "R002", "会計": "一般会計", "階層": "目", "親": "福祉費 > 子供家庭福祉費",
   "科目名": "児童福祉施設費", "列": "支出済額", "値": 219337467055}
  {"id": "R003", "verdict": "判定不能"}
"""


def main():
    parent = sys.argv[1]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    extract = mat["prompt"].split("----- 表(ここから) -----")[1].split("----- 表(ここまで) -----")[0].strip()
    rows = [{"id": c["id"], "金額の表記": c["text"], "文": c["sentence"]}
            for c in claims if not c.get("skipped")]
    made = []
    for seat, order in (("seat1", rows), ("seat2", list(reversed(rows)))):
        body = [QUESTION, "", "(A) 表の抜粋", extract, "", "(B) 金額の一覧(%d 件)" % len(order)]
        for r in order:
            body.append("- id: %s / 金額: %s / 文: %s" % (r["id"], r["金額の表記"], r["文"]))
        text = "\n".join(body)
        for w in BANNED:
            if w in text:
                raise AssertionError("禁じた語が材料に在る: %s" % w)
        d = os.path.join(parent, "m5_label_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        made.append({"seat": seat, "path": p, "chars": len(text),
                     "first_id": order[0]["id"], "last_id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s" % (seat, len(text), order[0]["id"],
                                                      order[-1]["id"], p))
    rec = {"seal": "docs/DOMAIN1_M5_SEAL_2026-10-15.md",
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
