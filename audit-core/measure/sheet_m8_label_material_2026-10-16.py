# -*- coding: utf-8 -*-
"""段 8 のラベル材料。**問いは `sheet_label_spec` から生成する**(人間の指示 ①)。

> 規則と問いの対応が一つでも不一致なら、**ラベル材料を生成できない。**

だからこの file は問いの字を 1 文字も持たない。`question_text()` で組み立て、
`check_question()` に通してから書き出す。通らなければ例外で止まる。

    python3 measure/sheet_m8_label_material_2026-10-16.py <出力の親ディレクトリ>
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m8_material_2026-10-16.json")
BINDS = os.path.join(FX, "m8_binds_2026-10-16.json")
OUT = os.path.join(FX, "m8_label_material_2026-10-16.json")

BANNED = ["GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
          "pointer", "R-1", "R-3", "R-4", "range_identified", "value_match",
          "封", "合格", "不合格", "engine", "照合結果", "判定結果", "正解",
          "未確認", "別名", "独立した裏づけ", "誤受理", "agree_", "保留にする"]


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


L = _mod("label_spec", "sheet_label_spec_2026-10-15.py")


def main():
    parent = sys.argv[1]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    question = L.question_text()
    L.check_question(question)          # **ここが門。落ちたら材料は作れない**
    # 封 §5: **問いは段 6 と 1 文字も変えない。**違っていたら材料を作らない
    m6 = json.load(io.open(os.path.join(FX, "m6_label_material_2026-10-15.json"),
                           encoding="utf-8"))
    if question != m6["question"]:
        raise AssertionError("問いが段 6 と違う(封 §5 に反する)")

    extract = (mat["prompt"].split("----- 表(ここから) -----")[1]
               .split("----- 表(ここまで) -----")[0].strip())
    rows = [{"id": c["id"], "金額の表記": c["text"], "文": c["sentence"]}
            for c in claims if not c.get("skipped")]
    made = []
    for seat, order in (("seat1", rows), ("seat2", list(reversed(rows)))):
        body = [question, "", "(A) 表の抜粋", extract, "",
                "(B) 金額の一覧(%d 件)" % len(order)]
        for r in order:
            body.append("- id: %s / 金額: %s / 文: %s"
                        % (r["id"], r["金額の表記"], r["文"]))
        text = "\n".join(body)
        for w in BANNED:
            if w in text:
                raise AssertionError("禁じた語が材料に在る: %s" % w)
        d = os.path.join(parent, "m8_label_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        made.append({"seat": seat, "path": p, "chars": len(text),
                     "first_id": order[0]["id"], "last_id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s"
              % (seat, len(text), order[0]["id"], order[-1]["id"], p))
    rec = {"seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "spec_version": L.SPEC["version"],
           "question_generated_from": "measure/sheet_label_spec_2026-10-15.py",
           "question_checked": True,
           "question_identical_to_m6": True,
           "question": question,
           "spec_rules": sorted(L.SPEC["rules"]),
           "column_alias": L.COLUMN_ALIAS,
           "claims": len(rows),
           "seats": [{"seat": "seat1", "model": "claude-sonnet-4-5", "order": "そのまま"},
                     {"seat": "seat2", "model": "claude-haiku-4-5", "order": "逆順"}],
           "files": made, "banned_checked": BANNED,
           "withheld": ["engine の判定", "pointer", "状態", "ルート", "封", "仕様",
                        "段 3〜段 6 の結果", "親の規則", "旧 engine の結果"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
