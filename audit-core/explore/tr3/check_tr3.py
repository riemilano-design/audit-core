# -*- coding: utf-8 -*-
"""便 TR3: 言い回しを変えた資料を、TR1 の拾い方と照合(1 字も変えない)で点検し、拾わなかった字を数える(封 §2)。

使い方: python3 -I check_tr3.py <audit-core の folder> <TR0 の根> <TR1 の根> <TR3 の根>
読むもの: <TR3>/doc/{n}.md(書く席の資料。信頼しない data として字で読むだけ)・<TR1>/A/{n}.json(基準 A)
          比べに <TR1>/doc/{n}.md(TR1 の新しい資料)
書くもの: <TR3>/check/{n}.json・<TR3>/report/{n}.html・<TR3>/miss/{n}.json(拾わなかった字)・<TR3>/miss_tr1/{n}.json
拾い方は check_tr1.extract、照合は check_tr1.verify(基準 A)、点検レポートは TR2 の report_tr1_v2.report をそのまま使う。
"""
import json
import os
import re
import sys

AC, TR0, TR1, OUT = sys.argv[1:5]
sys.argv = [sys.argv[0], AC, TR0, TR1, OUT]
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
import report_tr1_v2 as R  # noqa: E402  (中で check_tr1 を読み込む)

C = R.C
UNIT_NEAR = re.compile(r"[△▲\-−+＋]?\d[\d,]*(?:\.\d+)?(?=\s{0,2}(?:百万円|千円|億円|円|％|%|人|名|ポイント|pt))")


def tokens(md):
    """数える字: 表の第 1 列以外の、数字を含む升(見出しの行と区切りの行を除く)と、表でない行の単位の近い数。"""
    out = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            first = True
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw = lines[i]
                if first or re.match(r"^\s*\|[\s\-:|]+\|\s*$", raw):
                    first = False
                    i += 1
                    continue
                cells = raw.strip().strip("|").split("|")
                pos = raw.index("|") + 1
                for j, c in enumerate(cells):
                    a = pos
                    pos += len(c) + 1
                    if j == 0 or not re.search(r"\d", c):
                        continue
                    out.append({"行": i, "始め": a, "終わり": a + len(c), "字": c.strip(), "場所": "表"})
                i += 1
            continue
        if not lines[i].startswith("#"):
            for m in UNIT_NEAR.finditer(lines[i]):
                out.append({"行": i, "始め": m.start(), "終わり": m.end() + 1, "字": m.group(0), "場所": "文"})
        i += 1
    return out


def missed(md, recs):
    at = {}
    for r in recs:
        at.setdefault(r["行"], []).append(r["始め"])
    out = []
    for t in tokens(md):
        if not any(t["始め"] <= s < t["終わり"] for s in at.get(t["行"], [])):
            out.append(t)
    return out


def dump(obj, *parts):
    p = os.path.join(*parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1, default=str)


def main():
    for n in C.NUMS:
        A = C.load(os.path.join(TR1, "A", n + ".json"))
        with open(os.path.join(OUT, "doc", n + ".md"), encoding="utf-8") as f:
            md = f.read()
        recs = C.extract(md)
        for r in recs:
            r["区分"], r["info"] = C.verify(r, A, "A")
        title = next((l.lstrip("#").strip() for l in md.split("\n") if l.startswith("#")), "資料")
        html, cnt = R.report(n, recs, A, title)
        dump(recs, OUT, "check", n + ".json")
        dump(html, OUT, "report", n + ".html")
        ms = missed(md, recs)
        dump({"数えた字": len(tokens(md)), "拾わなかった": ms}, OUT, "miss", n + ".json")
        with open(os.path.join(TR1, "doc", n + ".md"), encoding="utf-8") as f:
            md1 = f.read()
        ms1 = missed(md1, C.extract(md1))
        dump({"数えた字": len(tokens(md1)), "拾わなかった": ms1}, OUT, "miss_tr1", n + ".json")
        print(n, "拾った", len(recs), cnt, "| 拾わなかった字", len(ms), "/", len(tokens(md)), "| TR1 の資料", len(ms1), "/", len(tokens(md1)))


if __name__ == "__main__":
    main()
