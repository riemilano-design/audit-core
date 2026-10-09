# -*- coding: utf-8 -*-
"""封 AI_PROSE_SEAL_2026-10-09 §2.3 の規則どおりに、指示文を組み立てる。

**網に触れない。LLM も呼ばない。** 作るのは「送る文」だけ。

§2.3 の規則(封じた通り。ここで変えない):
  - 元の ZIP の instance から **member を持たない素の context の fact を全件**
  - **(要素名, context id) の昇順**
  - **ラベル・値・単位・期間**の 4 欄
  - **選別・間引き・並べ替えをしない**

門③(封 §2.5): **指示文の全文に、人間の MD&A の 20 字以上の部分列が 1 つも
含まれないこと。** 含まれたら書かずに止まる ― 写しになっていたら実験の意味が消える。
"""

import hashlib
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))      # audit-core/
for p in (ROOT, os.path.join(ROOT, "core", "py")):
    sys.path.insert(0, p)
from adapters.xbrl import instance as I            # noqa: E402

DOC = "S100Z4Q1"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
TEMPLATE = os.path.join(HERE, "ai_prose_prompt_2026-10-09.txt")
TEMPLATE_SHA = "eeca4a1474f427538ff76ce536a84ab6c1e9a245fd5b8a8a73df916dd58b23d4"
HUMAN_MDNA = os.path.join(ROOT, "measure", "material", "xbrl", "%s.original.txt" % DOC)
OUT_PROMPT = os.path.join(HERE, "ai_prose_prompt_filled_2026-10-09.txt")
OUT_META = os.path.join(HERE, "ai_prose_prompt_meta_2026-10-09.json")
GATE3_N = 20


def sha(b):
    return hashlib.sha256(b).hexdigest()


def period_of(ctx):
    if ctx is None:
        return "?"
    if ctx.get("instant"):
        return "%s 時点" % ctx["instant"]
    if ctx.get("start") and ctx.get("end"):
        return "%s〜%s" % (ctx["start"], ctx["end"])
    return "?"


def build_facts_table(zb):
    inst = I.load_instance(zb)
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        id2label = I.labels_from_zip(z, inst["names"])
    contexts = inst["contexts"]
    rows = []
    for f in inst["facts"]:
        if not I.plain_context(f["context"], contexts):
            continue
        rows.append(f)
    # **(要素名, context id) の昇順。間引かない。**
    rows.sort(key=lambda f: (f["name"], f["context"]))
    lines = ["| 項目 | 値 | 単位 | 期間 |", "|---|---|---|---|"]
    for f in rows:
        label = id2label.get(f["name"].replace(":", "_")) or f["name"]
        v = f["value"]
        vs = ("%d" % v) if float(v).is_integer() else ("%s" % v)
        lines.append("| %s | %s | %s | %s |"
                     % (label, vs, f["unit"], period_of(contexts.get(f["context"]))))
    return "\n".join(lines), len(rows), len(inst["facts"]), inst["source"]


def gate3(prompt_text):
    """人間の MD&A の 20 字以上の部分列が指示文に無いこと。"""
    with io.open(HUMAN_MDNA, encoding="utf-8") as fh:
        human = fh.read()
    hits = []
    for i in range(0, len(human) - GATE3_N + 1):
        piece = human[i:i + GATE3_N]
        if piece in prompt_text:
            hits.append((i, piece))
            if len(hits) >= 5:
                break
    return human, hits


def main():
    with io.open(TEMPLATE, encoding="utf-8") as fh:
        raw = fh.read()
    if sha(raw.encode("utf-8")) != TEMPLATE_SHA:
        print("止まる: 指示文の雛形の sha が封と違う"); return 3
    body = raw.split("---\n", 1)[1]        # 先頭の # の説明は送らない
    if "{FACTS}" not in body:
        print("止まる: 雛形に {FACTS} が無い"); return 3

    zpath = os.path.join(CACHE, "%s.zip" % DOC)
    with open(zpath, "rb") as fh:
        zb = fh.read()
    table, used, total, src = build_facts_table(zb)
    prompt = body.replace("{FACTS}", table)

    human, hits = gate3(prompt)
    if hits:
        print("止まる 門③: 人間の MD&A の %d 字以上の部分列が指示文に含まれている" % GATE3_N)
        for i, piece in hits:
            print("  原文 %d 文字目: %r" % (i, piece))
        print("  指示文を書かずに終わる。")
        return 3

    with io.open(OUT_PROMPT, "w", encoding="utf-8") as fh:
        fh.write(prompt)
    meta = {
        "seal": "docs/AI_PROSE_SEAL_2026-10-09.md",
        "document": DOC,
        "instance_source": src,
        "template_sha256": TEMPLATE_SHA,
        "facts_total_in_instance": total,
        "facts_used_plain_context": used,
        "facts_rule": "member を持たない素の context の fact を全件・(要素名, context id) の昇順・ラベル/値/単位/期間の 4 欄・間引きなし",
        "prompt_chars": len(prompt),
        "prompt_sha256": sha(prompt.encode("utf-8")),
        "human_mdna_chars": len(human),
        "human_mdna_sha256": sha(human.encode("utf-8")),
        "gate3_substring_length": GATE3_N,
        "gate3_hits": 0,
        "llm_called": False,
    }
    with io.open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1); fh.write(u"\n")
    print("門③ 通過 ― 人間の MD&A の %d 字以上の部分列は 0 件" % GATE3_N)
    print("fact: instance 全体 %d 件 → 素の context %d 件を全部使った" % (total, used))
    print("指示文 %d 字  sha256 %s" % (len(prompt), meta["prompt_sha256"]))
    print("  -> %s" % OUT_PROMPT)
    print("**LLM は呼んでいない。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
