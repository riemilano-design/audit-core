# -*- coding: utf-8 -*-
"""便 RD0: 実物の公開データ(有報と決算短信の zip)から、会社の folder(素材)と正解を機械で作る(封 explore/rd0/SEAL.md §1)。

使い方: python3 -I build_rd0.py <audit-core の folder> <RD0 の根>
<RD0 の根>/co{21..26}/期1/(CSV・txt)と co{n}/正解/(正解.json・罠.json・期.json・使わない.json・文の中.json・他の読み.json)を書く。
zip は信頼しない data: 読むだけで、中の物は走らせない。engine は load_instance を読むだけに使う。
"""
import csv
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser

AC, ROOT = sys.argv[1], sys.argv[2]
sys.path.insert(0, AC)
from adapters.xbrl.instance import load_instance  # noqa: E402

CACHE = os.path.expanduser("~/.cache/audit-core")
ROWS = ["1", "2", "3", "4", "5", "6"]
ITEMS = [  # (項目, 要素, 枠の時)
    ("売上高_当期", "NetSales", "CurrentYearDuration"),
    ("売上高_前期", "NetSales", "Prior1YearDuration"),
    ("営業利益_当期", "OperatingIncome", "CurrentYearDuration"),
    ("営業利益_前期", "OperatingIncome", "Prior1YearDuration"),
    ("経常利益_当期", "OrdinaryIncome", "CurrentYearDuration"),
    ("当期純利益_当期", None, "CurrentYearDuration"),
    ("減価償却費_当期", "DepreciationAndAmortizationOpeCF", "CurrentYearDuration"),
    ("現金及び預金_当期末", "CashAndDeposits", "CurrentYearInstant"),
    ("流動資産合計_当期末", "CurrentAssets", "CurrentYearInstant"),
    ("資産合計_当期末", "Assets", "CurrentYearInstant"),
    ("短期借入金_当期末", "ShortTermLoansPayable", "CurrentYearInstant"),
    ("長期借入金_当期末", "LongTermLoansPayable", "CurrentYearInstant"),
    ("負債合計_当期末", "Liabilities", "CurrentYearInstant"),
    ("純資産合計_当期末", "NetAssets", "CurrentYearInstant"),
    ("純資産合計_前期末", "NetAssets", "Prior1YearInstant"),
    ("期末の従業員数_当期末", "NumberOfEmployees", "CurrentYearInstant"),
]
PRIOR = {"CurrentYearDuration": "Prior1YearDuration", "CurrentYearInstant": "Prior1YearInstant",
         "Prior1YearDuration": "Prior2YearDuration", "Prior1YearInstant": "Prior2YearInstant"}
NONCON = "_NonConsolidatedMember"


class Doc(HTMLParser):
    """htm を、表(行の並び)と表の外の字に分ける。"""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.blocks = []  # ("text", 字) か ("table", 行の並び)
        self.depth = 0
        self.row = None
        self.cell = None
        self.span = 1
        self.text = []
        self.skip = 0

    def flush_text(self):
        t = re.sub(r"\s+", " ", "".join(self.text)).strip()
        if t:
            self.blocks.append(("text", t))
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style") or (tag == "ix:header"):
            self.skip += 1
        elif tag == "table":
            if self.depth == 0:
                self.flush_text()
                self.blocks.append(("table", []))
            self.depth += 1
        elif tag == "tr" and self.depth:
            self.row = []
        elif tag in ("td", "th") and self.depth and self.row is not None:
            self.cell = []
            try:
                self.span = max(1, int(a.get("colspan") or 1))
            except ValueError:
                self.span = 1
        elif tag in ("br", "p", "div") and not self.depth:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") or tag == "ix:header":
            self.skip = max(0, self.skip - 1)
        elif tag == "table" and self.depth:
            self.depth -= 1
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.row.extend([""] * (self.span - 1))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.depth:
            if any(c for c in self.row):
                self.blocks[-1][1].append(self.row)
            self.row = None
        elif tag in ("p", "div") and not self.depth:
            self.text.append("\n")

    def handle_data(self, d):
        if self.skip:
            return
        if self.depth:
            if self.cell is not None:
                self.cell.append(d)
        else:
            self.text.append(d)


def convert(raw, out_csv, out_txt):
    doc = Doc()
    doc.feed(raw)
    doc.flush_text()
    rows, texts, recent = [], [], []
    for kind, body in doc.blocks:
        if kind == "text":
            for line in [x.strip() for x in body.split("\n") if x.strip()]:
                texts.append(line)
                if len(line) < 60:
                    recent = (recent + [line])[-2:]
        elif body:
            for line in recent:
                rows.append([line])
            rows.extend(body)
            rows.append([])
            recent = []
    wrote = []
    if rows:
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
        wrote.append(out_csv)
    body = "\n".join(texts)
    if len(body) >= 200:
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(body + "\n")
        wrote.append(out_txt)
    return wrote


def value(facts, contexts, local, ctx):
    hit = [f["value"] for f in facts if f["name"].split(":")[-1] == local and f["context"] == ctx]
    return int(round(hit[0])) if hit else None


def main():
    d = json.load(open(os.path.join(AC, "fixtures/xbrl/tanshin/fetched_2026-11-09.json"), encoding="utf-8"))
    sha2path = {}
    for sub in ("edinet", "edinet-fresh-2026-10-21", "edinet-prior-2026-11-02"):
        for f in os.listdir(os.path.join(CACHE, sub)):
            p = os.path.join(CACHE, sub, f)
            sha2path[hashlib.sha256(open(p, "rb").read()).hexdigest()] = p
    rows = {r["#"] if isinstance(r["#"], str) else str(r["#"]): r for r in d["行"]}
    for i, key in enumerate(ROWS):
        r = rows[key]
        num = str(21 + i)
        co = os.path.join(ROOT, "co" + num)
        src, gold_dir = os.path.join(co, "期1"), os.path.join(co, "正解")
        os.makedirs(src, exist_ok=True)
        os.makedirs(gold_dir, exist_ok=True)
        yb = open(sha2path[r["有報の ZIP の sha256"]], "rb").read()
        tb = open(os.path.join(CACHE, "tanshin-2026-11-09", r["証券コード"], r["番号"] + ".zip"), "rb").read()
        files = 0
        for tag, zb, keep in (("有報", yb, lambda n: n.startswith("XBRL/PublicDoc/")),
                              ("短信", tb, lambda n: "/Summary/" in n or "/Attachment/" in n or n.startswith("Summary/") or n.startswith("Attachment/"))):
            z = zipfile.ZipFile(io.BytesIO(zb))
            k = 0
            for n in sorted(z.namelist()):
                if not (n.endswith(".htm") and keep(n)):
                    continue
                k += 1
                base = os.path.join(src, "%s_%02d" % (tag, k))
                files += len(convert(z.read(n).decode("utf-8", "ignore"), base + ".csv", base + ".txt"))
        inst = load_instance(yb)
        facts, contexts = inst["facts"], inst["contexts"]
        cons = any(f["context"] == "CurrentYearDuration" and f["name"].split(":")[-1] == "NetSales" for f in facts) \
            or any(f["context"] == "CurrentYearInstant" and f["name"].split(":")[-1] == "Assets" for f in facts)
        suf = "" if cons else NONCON
        gold, other, decide = {}, {}, []
        for item, local, ctx in ITEMS:
            if local is None:
                local = "ProfitLossAttributableToOwnersOfParent" if cons else "ProfitLoss"
                if cons:
                    a, b = value(facts, contexts, local, ctx), value(facts, contexts, "ProfitLoss", ctx)
                    if a is not None and b is not None and a != b:
                        decide.append({"項目": item, "読み": [{"値": a, "説明": "親会社株主に帰属する当期純利益"},
                                                              {"値": b, "説明": "当期純利益"}]})
            c = ctx + suf
            if local == "NumberOfEmployees" and not cons:
                c = ctx if value(facts, contexts, local, ctx) is not None else ctx + NONCON
            gold[item] = value(facts, contexts, local, c)
            alts = []
            if cons:
                v = value(facts, contexts, local, ctx + NONCON)
                if v is not None:
                    alts.append(v)
            v = value(facts, contexts, local, PRIOR[ctx] + suf)
            if v is not None:
                alts.append(v)
            other[item] = sorted({x for x in alts if x != gold[item]})
        gold.update({"売上総利益_当期": None, "借入の残高の合計_当期末": None, "人件費_当期": None, "月次の売上高_当期": None})
        dur = contexts.get("CurrentYearDuration") or contexts.get("CurrentYearDuration" + NONCON) or {}
        w = lambda name, obj: json.dump(obj, open(os.path.join(gold_dir, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        w("正解.json", {"期1": gold})
        w("期.json", {"当期の始まり": dur.get("start"), "当期の終わり": dur.get("end")})
        w("罠.json", {"無い": [k for k, _, _ in ITEMS if gold[k] is None], "罠": [], "決め": decide})
        w("使わない.json", [])
        w("文の中.json", [])
        w("他の読み.json", other)
        print(num, "file", files, "連結" if cons else "単体", "無い", sum(gold[k] is None for k, _, _ in ITEMS), "決め", len(decide))


if __name__ == "__main__":
    main()
