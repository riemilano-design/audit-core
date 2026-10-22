# -*- coding: utf-8 -*-
"""段 11 のラベル材料(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §1・§11 の 7)。

**問いは段 9 の spec から生成し、段 9 の問いと 1 文字も違わないことを機械で確かめる。**
段 9 は会計の 2 本を直したので「段 8 と同じ」門が使えなかったが、
**段 11 は 1 文字も変えない**ので、**段 9 の記録の問いと直接突き合わせる。**

この file は問いの字を 1 文字も持たない。`L9.question_text()` で組み立て、
`L9.check_question()` に通し、**段 9 の記録と照合**してから書き出す。

    python3 measure/sheet_m11_label_material_2026-10-16.py <出力の親ディレクトリ>
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
M9LAB = os.path.join(FX, "m9_label_material_2026-10-16.json")
OUT = os.path.join(FX, "m11_label_material_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"

# 段 9 と同じ禁じ語(1 語も減らさない)
BANNED = ["GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
          "pointer", "R-1", "R-3", "R-4", "range_identified", "value_match",
          "封", "合格", "不合格", "engine", "照合結果", "判定結果", "正解",
          "未確認", "別名", "独立した裏づけ", "誤受理", "agree_", "保留にする",
          "③", "発火", "A-1", "A-3", "X-2"]
# **「歳入」は禁じ語に足せない。**段 9 の問い(凍結)の例文に `歳入決算額` が在る
# (`R003` の例)。足すと**問いを変えることになる**ので、段 9 の一覧をそのまま使う。
# 席は段 4 からずっとこの語を見ており、**今回の経路の存在が漏れる語ではない。**


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


L9 = _mod("spec9_for_m11label", "sheet_label_spec_m9_2026-10-16.py")


def check_identical_to_m9(question):
    """**段 9 の問いと 1 文字も違わないこと。**違えば材料を作れない。"""
    want = json.load(io.open(M9LAB, encoding="utf-8"))["question"]
    if question != want:
        import difflib
        d = [l for l in difflib.unified_diff(want.split("\n"), question.split("\n"),
                                             lineterm="", n=0)
             if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        raise AssertionError("**問いが段 9 と違う。採点基準を変えてはいけない**: %s" % d)
    return True


def main():
    parent = sys.argv[1]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    question = L9.question_text()
    L9.check_question(question)         # **ここが門。落ちたら材料は作れない**
    check_identical_to_m9(question)     # **段 9 と 1 文字も違わない**

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
        d = os.path.join(parent, "m11_label_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        made.append({"seat": seat, "path": p, "chars": len(text),
                     "first_id": order[0]["id"], "last_id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s"
              % (seat, len(text), order[0]["id"], order[-1]["id"], p))
    rec = {"seal": SEAL,
           "spec_version": L9.SPEC["version"],
           "question_generated_from": "measure/sheet_label_spec_m9_2026-10-16.py",
           "question_checked": True,
           "question_identical_to_m9": True,
           "question_changed_lines": [],
           "question": question,
           "spec_rules": sorted(L9.SPEC["rules"]),
           "column_alias": L9.COLUMN_ALIAS,
           "claims": len(rows),
           "seats": [{"seat": "seat1", "model": "claude-sonnet-4-5",
                      "order": "そのまま"},
                     {"seat": "seat2", "model": "claude-haiku-4-5",
                      "order": "逆順"}],
           "retry": "**しない。**機械検査に落ちた答えは「判定不能」として数える(封 §7)",
           "files": made, "banned_checked": BANNED,
           "withheld": ["engine の判定", "pointer", "状態", "ルート", "封", "仕様",
                        "段 3〜段 9 の結果", "親の規則", "旧 engine の結果",
                        "機会の件数", "裏づけの規則", "③の発火の数",
                        "歳入側の資料の存在"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
