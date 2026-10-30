# -*- coding: utf-8 -*-
"""段 9 のラベル材料。**問いは段 9 の spec から生成する**(封 §3-4)。

> 規則と問いの対応が一つでも不一致なら、**ラベル材料を生成できない。**

この file は問いの字を 1 文字も持たない。`question_text()` で組み立て、
`check_question()` に通してから書き出す。通らなければ例外で止まる。

段 8 との違いは**問いの会計の 2 本の規則**だけである(封 §3-4)。
だから「問いが段 6 と同じ」という門は**使えない**。代わりに

  * 段 9 の spec から生成したこと
  * **会計の 2 本以外は段 8 の問いと 1 文字も違わないこと**

を機械で確かめる。

    python3 measure/sheet_m9_label_material_2026-10-16.py <出力の親ディレクトリ>
"""
import difflib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m9_material_2026-10-16.json")
BINDS = os.path.join(FX, "m9_binds_2026-10-16.json")
OUT = os.path.join(FX, "m9_label_material_2026-10-16.json")

BANNED = ["GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
          "pointer", "R-1", "R-3", "R-4", "range_identified", "value_match",
          "封", "合格", "不合格", "engine", "照合結果", "判定結果", "正解",
          "未確認", "別名", "独立した裏づけ", "誤受理", "agree_", "保留にする",
          "③", "発火", "A-1", "A-3", "X-2"]


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


L9 = _mod("spec9_for_label", "sheet_label_spec_m9_2026-10-16.py")


def diff_against_m8(question):
    """**会計の 2 本以外が動いていないこと**を行の差分で確かめる。"""
    old = L9.L.question_text().split("\n")
    new = question.split("\n")
    changed = [l for l in difflib.unified_diff(old, new, lineterm="", n=0)
               if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    bad = [l for l in changed
           if not any(k in l for k in ("R-会計-1", "R-会計-2", "会計 …"))]
    if bad:
        raise AssertionError("会計の 2 本以外が動いた: %s" % bad)
    return changed


def main():
    parent = sys.argv[1]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    question = L9.question_text()
    L9.check_question(question)         # **ここが門。落ちたら材料は作れない**
    changed = diff_against_m8(question)

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
        d = os.path.join(parent, "m9_label_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        made.append({"seat": seat, "path": p, "chars": len(text),
                     "first_id": order[0]["id"], "last_id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s"
              % (seat, len(text), order[0]["id"], order[-1]["id"], p))
    rec = {"seal": "docs/DOMAIN1_M9_SEAL_2026-10-16.md",
           "spec_version": L9.SPEC["version"],
           "question_generated_from": "measure/sheet_label_spec_m9_2026-10-16.py",
           "question_checked": True,
           "question_identical_to_m8": False,
           "question_changed_lines": changed,
           "question_change_reason": ("封 §3-4。旧 R-会計-2 は『`東京都` を外せ』と"
                                      "無条件に指示していたが、正規化は裏づけの在る"
                                      "別名だけを畳む。**席に、道具が拒んでいる推測を"
                                      "させていた。**"),
           "question": question,
           "spec_rules": sorted(L9.SPEC["rules"]),
           "column_alias": L9.COLUMN_ALIAS,
           "claims": len(rows),
           "seats": [{"seat": "seat1", "model": "claude-sonnet-4-5",
                      "order": "そのまま"},
                     {"seat": "seat2", "model": "claude-haiku-4-5",
                      "order": "逆順"}],
           "files": made, "banned_checked": BANNED,
           "withheld": ["engine の判定", "pointer", "状態", "ルート", "封", "仕様",
                        "段 3〜段 8 の結果", "親の規則", "旧 engine の結果",
                        "機会の件数", "裏づけの規則", "③の発火の数"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
