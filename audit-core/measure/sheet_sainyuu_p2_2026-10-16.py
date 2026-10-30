# -*- coding: utf-8 -*-
"""P-2・P-3・P-4(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md §4)。

P-1(出どころの確認)は `docs/DOMAIN1_SAIIRU_P1_2026-10-16.md` で済んでいる。
ここで初めて**数**を出す。

  P-2 値の重複 ― 歳入側の候補の値が、同じ会計の**歳出側のどれかの値**と一致する件数
  P-3 歳入側の款の数(歳出側は 17/18 が 1 つだった)
  P-4 **R-独立-6 を当てたあとに 3 本に達する会計の数**(`MIN_INDEPENDENT = 3` のまま)

**R-独立-6**(封 §3)
  6a 歳出側の値と一致 -> 数えない   6b 代数的に決まる列 -> 数えない
  6c 親子 -> 数えない(I-2)        6d 値を持つ正本が 2 つ以上 -> 数えない
  6e 歳出の再掲 -> 数えない(P-1 で 0 件)  6f 別 file だから独立とは書かない

**款の行だけを数える。**項・目・節は 6b(代数的に決まる)で落ちる ―
`款 = Σ項` が成り立つことを**この段で測って**確かめる(測らずに落とさない)。

通信しない。材料は `~/.cache/audit-core/sheet/`。
  usage: python3 measure/sheet_sainyuu_p2_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p2_2026-10-16.json")
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
P1 = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P1M = _mod("p1_for_p2", "sheet_sainyuu_p1_2026-10-16.py")
E = _mod("m5_for_p2", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm
CACHE = M2.CACHE
CODE = re.compile(r"^\d{2}$")

# 明細の `計` と決算書の `予算現額` は同じ列(歳出側と同じ構造の別名)
COL_ALIAS = {"計": "予算現額"}
# **見出しの列と値の列がずれる列。**実測: `予算現額と収入済額との比較` は
# 見出しが I 列・値が J 列に載る。写さないとこの列は索引に入らず、
# 6b の検査が**分母 0**になって「落としたのでも数えたのでもない」状態になる。
VALUE_COL_OFFSET = {"予算現額と収入済額との比較": {"I": "J"}}


def _canon_col(t):
    t = norm(t)
    return norm(COL_ALIAS.get(t, t))


def kessan_kan(sheets):
    """決算書 歳入: 会計ごとの **款** の行(符号・名前・列・値)。

    版面は「符号と名前の行」の**次の行に値**が載る(実測。行 9 が `01 都税`、
    行 10 が値)。括弧内の還付未済金は**さらに次の行**に出るので値として採らない。
    """
    cells = sheets["歳入"]["cells"]
    rows = P1M.cells_by_row(cells)
    head, cols = P1M.header_cols(rows)
    colmap = {}
    for c in cols:
        if c["row"] == head and c["col"] not in ("A", "B", "C"):
            src = VALUE_COL_OFFSET.get(c["text"], {}).get(c["col"], c["col"])
            colmap[src] = _canon_col(c["text"])
    titles = []
    for r in sorted(rows):
        a = rows[r].get("A")
        if isinstance(a, str) and re.sub(r"\s+", "", a).endswith("歳入歳出決算書"):
            flat = re.sub(r"\s+", "", a)
            m = P1M.TITLE_RE.match(flat)
            if not m:
                prev = re.sub(r"\s+", "", rows.get(r - 1, {}).get("A") or "")
                m = P1M.TITLE_RE.match(prev + flat)
            if m:
                titles.append((r, m.group(1)))
    out = collections.defaultdict(dict)
    nkan = collections.defaultdict(set)
    rs = sorted(rows)
    for n, (start, acct) in enumerate(titles):
        end = titles[n + 1][0] - 1 if n + 1 < len(titles) else rs[-1]
        for r in [x for x in rs if start <= x <= end]:
            code, name = rows[r].get("A"), rows[r].get("B")
            if not (isinstance(code, str) and CODE.match(code.strip())):
                continue
            if not isinstance(name, str) or not name.strip():
                continue
            vals = rows.get(r + 1) or {}
            nkan[norm(acct)].add(norm(name))
            for col, cname in colmap.items():
                v = vals.get(col)
                if isinstance(v, (int, float)):
                    out[norm(acct)][(norm(name), cname)] = int(v)
    return dict(out), {k: sorted(v) for k, v in nkan.items()}


def meisai_kan(sheets, toc):
    """明細 歳入: 会計ごとの **款** の行。符号・名前・値は**同じ行**に載る(実測)。"""
    acct_of = {norm(t["sheet"]): t["account"] for t in toc}
    out = collections.defaultdict(dict)
    nkan = collections.defaultdict(set)
    for sname in sheets:
        if sname == "目次":
            continue
        acct = acct_of.get(norm(sname))
        if not acct:
            continue
        rows = P1M.cells_by_row(sheets[sname]["cells"])
        head, cols = P1M.header_cols(rows)
        if head is None:
            continue
        colmap = {}
        for c in cols:
            if c["col"] in ("A", "B", "C", "D"):
                continue
            colmap.setdefault(c["col"], _canon_col(c["text"]))
        for r in sorted(rows):
            code, name = rows[r].get("A"), rows[r].get("B")
            if not (isinstance(code, str) and CODE.match(code.strip())):
                continue
            if not isinstance(name, str) or not name.strip():
                continue
            nkan[norm(acct)].add(norm(name))
            for col, cname in colmap.items():
                v = rows[r].get(col)
                if isinstance(v, (int, float)):
                    out[norm(acct)][(norm(name), cname)] = int(v)
    return dict(out), {k: sorted(v) for k, v in nkan.items()}


def saisyutu_values():
    """歳出側(総括・決算書 歳出・明細 歳出)の**会計ごとの値の集合**。6a に使う。"""
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    by = collections.defaultdict(set)
    for e in raw:
        by[norm(e["scope"])].add(e["value"])
    al = E.alias_table(raw)
    return raw, al, dict(by)


def existing_backing(raw, al):
    """歳出側でいま数えている独立した裏づけの**値**(会計ごと)。"""
    rows = {}
    for e in raw:
        if e["name"] and e["level"] in ("款", "項"):
            k = (e["scope"], e["level"], norm(e["name"]), norm(e["column"]))
            rows.setdefault(k, {"files": {}, "parent": e["parent"]})
            rows[k]["files"][e["file"]] = e["value"]
    out = {}
    for u in al["unconfirmed"]:
        if not u.get("canonical"):
            continue
        x, c = u["name"], norm(u["canonical"])
        hits = []
        for (sc, lv, nm, col), rec in rows.items():
            if sc != x:
                continue
            other = rows.get((c, lv, nm, col))
            if not other:
                continue
            v = sorted(rec["files"].values())[0]
            w = sorted(other["files"].values())[0]
            if v == w and len(set(rec["files"]) | set(other["files"])) >= 2:
                hits.append({"level": lv, "name": nm, "column": col, "value": v,
                             "parent": norm(rec["parent"]) or None,
                             "files": sorted(set(rec["files"]) | set(other["files"]))})
        ind, _ = E._independent(hits)
        out[norm(x)] = {"count": len(ind), "values": sorted({h["value"] for h in ind})}
    return out


def determined_keys(kk):
    """**6b を行ごとに当てる。**その行で関係が成り立つ `(科目名, 列)` を返す。

    列ごとに「全部の行で成り立つ」を要求すると**緩い** ―
    実測で `調定額 = 収入済額+不納欠損額+収入未済額` は 96 行のうち 91 行で成立する。
    列ごとに落とすと 5 行の例外のせいで 91 行も数えてしまう。**だから行ごとに落とす。**
    """
    out = collections.defaultdict(set)
    counted = collections.Counter()
    for acct, rows in kk.items():
        names = {nm for nm, col in rows}
        for nm in names:
            t = rows.get((nm, norm("調定額")))
            vs = [rows.get((nm, norm(x)))
                  for x in ("収入済額", "不納欠損額", "収入未済額")]
            if t is not None and all(v is not None for v in vs):
                counted["調定額 を検査"] += 1
                if t == sum(vs):
                    out[acct].add((nm, norm("調定額")))
                    counted["調定額 を落とした"] += 1
            cmp_ = rows.get((nm, norm("予算現額と収入済額との比較")))
            a = rows.get((nm, norm("予算現額")))
            b = rows.get((nm, norm("収入済額")))
            if cmp_ is not None and a is not None and b is not None:
                counted["比較 を検査"] += 1
                if cmp_ == a - b:
                    out[acct].add((nm, norm("予算現額と収入済額との比較")))
                    counted["比較 を落とした"] += 1
    return {k: v for k, v in out.items()}, dict(counted)


def algebraic_columns(kk):
    """**6b を測る。**列が他の列から決まるなら数えない。

    決算書 歳入で次が成り立つかを会計ごとに数える。
      (1) 調定額 = 収入済額 + 不納欠損額 + 収入未済額
      (2) 予算現額と収入済額との比較 = 予算現額 − 収入済額
    **成り立った会計の数と分母を返す。**全部で成り立った列だけを落とす。
    """
    rel = {"調定額": ("収入済額", "不納欠損額", "収入未済額"),
           "予算現額と収入済額との比較": None}
    out = {}
    for target, parts in rel.items():
        ok = tot = 0
        for acct, rows in kk.items():
            names = {nm for nm, col in rows}
            for nm in names:
                t = rows.get((nm, norm(target)))
                if t is None:
                    continue
                if parts:
                    vs = [rows.get((nm, norm(p))) for p in parts]
                    if any(v is None for v in vs):
                        continue
                    tot += 1
                    ok += 1 if t == sum(vs) else 0
                else:
                    a = rows.get((nm, norm("予算現額")))
                    b = rows.get((nm, norm("収入済額")))
                    if a is None or b is None:
                        continue
                    tot += 1
                    ok += 1 if t == a - b else 0
        out[target] = {"holds": ok, "checked": tot,
                       "drop": bool(tot) and ok == tot}
    return out


def kan_is_sum_of_ko(sheets_k):
    """**6b の根拠を測る。**決算書 歳入で `款 = Σ項` が成り立つか。

    成り立つなら項の行は款から決まる(= 独立した事実ではない)。
    **測らずに落とさない**ので、成り立った数と分母を返す。
    """
    cells = sheets_k["歳入"]["cells"]
    rows = P1M.cells_by_row(cells)
    head, cols = P1M.header_cols(rows)
    colmap = {c["col"]: _canon_col(c["text"]) for c in cols
              if c["row"] == head and c["col"] not in ("A", "B", "C")}
    rs = sorted(rows)
    cur_kan, acc = None, collections.defaultdict(lambda: collections.defaultdict(int))
    kan_val = {}
    for r in rs:
        a, b, c = rows[r].get("A"), rows[r].get("B"), rows[r].get("C")
        if isinstance(a, str) and CODE.match(str(a).strip()) and isinstance(b, str):
            cur_kan = (r, norm(b))
            vals = rows.get(r + 1) or {}
            for col, cname in colmap.items():
                v = vals.get(col)
                if isinstance(v, (int, float)):
                    kan_val[(cur_kan, cname)] = int(v)
        elif isinstance(b, str) and CODE.match(str(b).strip()) and isinstance(c, str) \
                and cur_kan:
            vals = rows.get(r + 1) or {}
            for col, cname in colmap.items():
                v = vals.get(col)
                if isinstance(v, (int, float)):
                    acc[cur_kan][cname] += int(v)
    ok = tot = 0
    for kan, by in acc.items():
        for cname, s in by.items():
            if (kan, cname) not in kan_val:
                continue
            tot += 1
            ok += 1 if kan_val[(kan, cname)] == s else 0
    return {"holds": ok, "checked": tot, "all": bool(tot) and ok == tot}


def judge_account(x, c, mine, theirs, det, holders, out_vals):
    """別名 `x` と正本 `c` について、**R-独立-6 を 1 行ずつ当てる。**

    **main の中に書かないこと。**判定が main の中だけに在ると、門は記録を
    読むだけになり、6a・6b・6d・値の食い違いを外す変異が**全部黙る**
    (2026-10-16 の変異 Q1〜Q4 で実測した)。
    返すのは (採った行, 落ちた理由の数え)。
    """
    hits, why = [], collections.Counter()
    for (nm, col), v in sorted(mine.items()):
        w = theirs.get((nm, col))
        if w is None:
            why["決算書に同じ行が無い"] += 1
            continue
        if v != w:
            why["値が食い違う"] += 1
            continue
        if (nm, col) in det.get(c, set()):
            why["6b 代数的に決まる(行ごと)"] += 1
            continue
        if v in out_vals.get(c, set()) or v in out_vals.get(x, set()):
            why["6a 歳出側の値と一致"] += 1
            continue
        if len(holders.get((col, v), ())) > 1:
            why["6d 値を持つ正本が 2 つ以上"] += 1
            continue
        hits.append({"level": "款", "name": nm, "column": col, "value": v,
                     "parent": None, "files": ["決算書 歳入", "事項別明細 歳入"]})
    return hits, dict(why)


def value_holders(kk):
    """6d の下ごしらえ: `(列, 値)` -> その値を持つ正本の集合。"""
    holders = collections.defaultdict(set)
    for acct, rows in kk.items():
        for (nm, col), v in rows.items():
            holders[(col, v)].add(acct)
    return holders


def main():
    sk, _ = P1M.read(P1M.SAINYUU)
    sm, _ = P1M.read(P1M.MEISAI_SAINYUU)
    p1 = json.load(io.open(P1, encoding="utf-8"))
    kk, kk_names = kessan_kan(sk)
    mk, mk_names = meisai_kan(sm, p1["meisai_sainyuu"]["toc"])
    raw, al, out_vals = saisyutu_values()
    existing = existing_backing(raw, al)
    unconf = [u for u in al["unconfirmed"] if u.get("canonical")]

    alg = algebraic_columns(kk)
    kansum = kan_is_sum_of_ko(sk)
    det, det_counts = determined_keys(kk)

    holders = value_holders(kk)

    per, p2_total = {}, 0
    for u in unconf:
        x, c = norm(u["name"]), norm(u["canonical"])
        mine, theirs = mk.get(x, {}), kk.get(c, {})
        hits, why = judge_account(x, c, mine, theirs, det, holders, out_vals)
        p2_total += why.get("6a 歳出側の値と一致", 0)
        ind, dropped = E._independent(hits)
        ex = existing.get(x, {"count": 0, "values": []})
        merged = sorted(set(ex["values"]) | {h["value"] for h in ind})
        per[u["name"]] = {
            "canonical": u["canonical"],
            "kan_count_sainyuu": len(mk_names.get(x, [])),
            "kan_count_saisyutu_side_existing": ex["count"],
            "sainyuu_hits_before_6": len([1 for k in mine if k in theirs]),
            "sainyuu_kan_names": sorted({nm for nm, col in mine}),
            "sainyuu_independent_new": len(ind),
            "new_columns": sorted({h["column"] for h in ind}),
            "dropped_why": why,
            "i_dedup_dropped": dropped,
            "existing_values": ex["values"],
            "merged_independent_total": len(merged),
            "reaches_min": len(merged) >= al["min_independent"],
        }

    reaches = [k for k, v in per.items() if v["reaches_min"]]
    kan_hist = collections.Counter(v["kan_count_sainyuu"] for v in per.values())
    tot_hist = collections.Counter(v["merged_independent_total"] for v in per.values())

    rec = {"seal": SEAL, "step": "P-2・P-3・P-4",
           "min_independent": al["min_independent"],
           "rule": ("款の行だけを数える。項・目・節は 6b(代数的に決まる)で落ちる ― "
                    "その根拠の `款 = Σ項` を**この段で測った**"),
           "P-2 値の重複(6a で落ちた件数の合計)": p2_total,
           "P-3 歳入側の款の数の分布": dict(kan_hist),
           "P-4 3 本に達する会計": {"count": len(reaches), "of": len(per),
                                "accounts": sorted(reaches)},
           "本数の分布(6 を当てたあと)": dict(tot_hist),
           "6b 列ごとの参考": alg,
           "6b 行ごとに落とした件数": det_counts,
           "6b 款 = Σ項": kansum,
           "per_account": per,
           "limits": [
               "**款の行だけを数えた。**項・目・節は 6b で落ちる(`款 = Σ項` を測った)",
               "**6e は P-1 で 0 件**(書類の表題 19+19 を除いた上での 0)",
               "**これは独立した証拠経路が成立するかの判定であり、"
               "別名規則の安全性が改善したという主張ではない**",
           ]}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)

    print("=== P-2・P-3・P-4(MIN_INDEPENDENT = %d のまま)===" % al["min_independent"])
    print("6b `款 = Σ項`: 成立 %d / 検査 %d / 全部成立 %s"
          % (kansum["holds"], kansum["checked"], kansum["all"]))
    for col, d in sorted(alg.items()):
        print("6b(列ごとの参考)%-20s 成立 %d / 検査 %d"
              % (col, d["holds"], d["checked"]))
    print("**6b 行ごとに落とした: %s**" % det_counts)
    print("**P-2 6a(歳出側の値と一致)で落ちた件数: %d**" % p2_total)
    print("**P-3 歳入側の款の数の分布: %s**" % dict(kan_hist))
    print("**P-4 3 本に達する会計: %d / %d**" % (len(reaches), len(per)))
    print("   本数の分布: %s" % dict(tot_hist))
    why = collections.Counter()
    for v in per.values():
        for k, n in v["dropped_why"].items():
            why[k] += n
    print("   落ちた理由の合計: %s" % dict(why))
    for name, v in sorted(per.items(), key=lambda kv: -kv[1]["merged_independent_total"])[:4]:
        print("   %-28s 款 %d / 既存 %d 本 + 新 %d 本 -> %d 本 %s"
              % (name, v["kan_count_sainyuu"], v["kan_count_saisyutu_side_existing"],
                 v["sainyuu_independent_new"], v["merged_independent_total"],
                 "**達する**" if v["reaches_min"] else ""))
    print("->", OUT)


if __name__ == "__main__":
    main()
