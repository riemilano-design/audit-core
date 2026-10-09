# -*- coding: utf-8 -*-
"""封 AI_PROSE_SEAL_2026-10-09 §2.1/§2.4 の 2 段目。

やること:
  1. 元の ZIP の **MD&A の textBlock だけ**を AI の本文に差し替えた複製を作る。
     **fact は 1 件も触らない。**接続部も核も 1 行も変えない。
  2. ``recipes.build_raw_claims`` **だけ**を走らせる。**verify は走らせない。**
  3. 人間の文と AI の文を**同じ実行で** P7 で回し、件数を出す。
  4. **判定の付いていない**主張一覧を書き出す ― 封の指定どおり
     **id・文・数・単位だけ。** ``subject``・``bound``・``reason``・``pointer`` は
     engine の判断なので**札を付ける監査に見せない。**

機械の門:
  門① 複製の **fact と context が元と完全一致**(1 件でも違えば止まる)
  門② 差し替えたのは MD&A の textBlock **1 つだけ**(他の 121 本は一致)
  門⑦ **差し込んだ本文が往復する** ― 複製から strip_html で取り出した文に
       AI の本文が入っていること(入っていなければ配線が違う)
"""

import hashlib
import io
import json
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape as xml_escape

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (ROOT, os.path.join(ROOT, "core", "py")):
    sys.path.insert(0, p)
from adapters.xbrl import instance as I        # noqa: E402
from adapters.xbrl import recipes as R         # noqa: E402
from adapters.xbrl import vocabulary as V      # noqa: E402

DOC = "S100Z4Q1"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
PROSE = os.path.join(HERE, "ai_prose_2026-10-09.txt")
OUT_ZIP = os.path.join(HERE, "ai_prose_instance_2026-10-09.zip")
OUT_SHEET = os.path.join(HERE, "ai_prose_claims_unlabelled_2026-10-09.json")
OUT_COUNTS = os.path.join(HERE, "ai_prose_counts_2026-10-09.json")
PROFILE = V.P7


def sha(b):
    return hashlib.sha256(b).hexdigest()


def prose_to_html(text):
    """1 行 = 1 段落。**本文の文字は変えない**(HTML の特殊文字だけ逃がす)。"""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        out.append("<p>%s</p>" % xml_escape(line))
    return "\n".join(out)


def build_modified_zip(zb, prose):
    inst = I.load_instance(zb)
    mdna = I.select_mdna(inst["textblocks"])
    if mdna is None:
        raise SystemExit("MD&A の textBlock が見つからない")
    src = inst["source"]
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        raw = z.read(src).decode("utf-8")
        members = [(i, z.read(i.filename)) for i in z.infolist()]
    # 要素を 1 つだけ差し替える
    pat = re.compile(
        r"(<%s\b[^>]*>)(.*?)(</%s>)" % (re.escape(mdna), re.escape(mdna)), re.S)
    hits = pat.findall(raw)
    if len(hits) != 1:
        raise SystemExit("MD&A の要素が %d 個 ― 1 個でないので止まる" % len(hits))
    new_inner = xml_escape(prose_to_html(prose))
    new_raw = pat.sub(lambda m: m.group(1) + new_inner + m.group(3), raw, count=1)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in members:
            out.writestr(info, new_raw.encode("utf-8") if info.filename == src else data)
    return buf.getvalue(), mdna, src


def main():
    with open(os.path.join(CACHE, "%s.zip" % DOC), "rb") as fh:
        zb = fh.read()
    with io.open(PROSE, encoding="utf-8") as fh:
        prose = fh.read()
    print("元 ZIP sha %s… / AI の本文 %d 字 sha %s…"
          % (sha(zb)[:12], len(prose), sha(prose.encode("utf-8"))[:12]))

    zb2, mdna, src = build_modified_zip(zb, prose)
    a, b = I.load_instance(zb), I.load_instance(zb2)

    # 門① fact と context が完全一致
    fa = [(f["name"], f["context"], f["unit"], f["decimals"], f["value"]) for f in a["facts"]]
    fb = [(f["name"], f["context"], f["unit"], f["decimals"], f["value"]) for f in b["facts"]]
    if fa != fb or a["contexts"] != b["contexts"]:
        print("止まる 門①: fact か context が元と違う(%d vs %d 件)" % (len(fa), len(fb)))
        return 3
    print("門① 通過 ― fact %d 件・context %d 件が元と完全一致" % (len(fa), len(a["contexts"])))

    # 門② 差し替えたのは MD&A の 1 本だけ
    diff = [n for n in set(a["textblocks"]) | set(b["textblocks"])
            if a["textblocks"].get(n) != b["textblocks"].get(n)]
    if diff != [mdna]:
        print("止まる 門②: 変わった textBlock が %d 本(%s)" % (len(diff), diff[:3]))
        return 3
    print("門② 通過 ― textBlock %d 本のうち変わったのは MD&A の 1 本だけ" % len(a["textblocks"]))

    # 門⑦ 往復
    got = I.strip_html(b["textblocks"][mdna])
    probe = [ln.strip() for ln in prose.split("\n") if len(ln.strip()) > 20][:5]
    missing = [p for p in probe if p not in got]
    if missing:
        print("止まる 門⑦: 差し込んだ本文が往復しない(%d 件が見つからない)" % len(missing))
        print("  例:", repr(missing[0][:60]))
        return 3
    print("門⑦ 通過 ― 差し込んだ本文が複製から取り出せる(標本 %d 件)" % len(probe))

    with open(OUT_ZIP, "wb") as fh:
        fh.write(zb2)

    # **同じ実行で両腕**。verify は走らせない。
    hn, ht = R.build_raw_claims(zb, PROFILE)
    an, at = R.build_raw_claims(zb2, PROFILE)
    human_text = I.strip_html(a["textblocks"][mdna])

    def arm(name, nn, tt, chars):
        bound = sum(1 for r in list(nn) + list(tt) if r["subject"] is not None)
        return {
            "arm": name, "chars": chars,
            "claims": len(nn) + len(tt), "num_claims": len(nn), "text_claims": len(tt),
            "bound_subject_not_none": bound,
            "bound_rate": round(bound / float(len(nn) + len(tt)), 4),
            "num_claims_per_1000_chars": round(len(nn) * 1000.0 / chars, 2),
        }

    counts = {
        "seal": "docs/AI_PROSE_SEAL_2026-10-09.md",
        "profile": PROFILE.name,
        "same_execution": True,
        "verify_run": False,
        "document": DOC,
        "mdna_element": mdna, "instance": src,
        "modified_zip_sha256": sha(zb2),
        "prose_sha256": sha(prose.encode("utf-8")),
        "gate1_facts_identical": True, "gate2_only_mdna_changed": True,
        "gate7_roundtrip": True,
        "arms": [arm("人間の文", hn, ht, len(human_text)),
                 arm("AI の文", an, at, len(got))],
    }
    with io.open(OUT_COUNTS, "w", encoding="utf-8") as fh:
        json.dump(counts, fh, ensure_ascii=False, indent=1); fh.write(u"\n")

    # 札付け用 ― **id・文・数・単位だけ**
    sheet = []
    for r in an:
        sheet.append({"id": r["id"], "文": r["span"], "数": r["value"], "単位": r["unit"]})
    for r in at:
        sheet.append({"id": r["id"], "文": r["span"], "数": None, "単位": None})
    with io.open(OUT_SHEET, "w", encoding="utf-8") as fh:
        json.dump({
            "seal": "docs/AI_PROSE_SEAL_2026-10-09.md §2.4",
            "note": "**engine の判定は入っていない。** subject・bound・reason・pointer も入れていない(engine の判断なので札に影響させない)。",
            "task": "各行に 真 / 偽 / 判定不能 の札を付ける。根拠は S100Z4Q1 の XBRL の fact。",
            "document": DOC, "rows": len(sheet), "claims": sheet,
        }, fh, ensure_ascii=False, indent=1); fh.write(u"\n")

    print()
    for x in counts["arms"]:
        print("  %-8s %5d 字  主張 %3d(数 %3d / 文字 %3d)  束縛 %3d(%.1f%%)  数の主張/1000字 %.2f"
              % (x["arm"], x["chars"], x["claims"], x["num_claims"], x["text_claims"],
                 x["bound_subject_not_none"], x["bound_rate"] * 100,
                 x["num_claims_per_1000_chars"]))
    print()
    print("札付け用 %d 行 -> %s" % (len(sheet), OUT_SHEET))
    print("**verify は走らせていない。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
