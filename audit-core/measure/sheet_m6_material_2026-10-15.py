# -*- coding: utf-8 -*-
"""段 6 の材料を**機械で**作る(人間の指示 2026-10-15 の ③)。

> 次の標本では、以下の 3 条件をすべて満たすようにしてください。
>   未確認の会計を含む / 親が効く行を含む / 新規主張 10 件以上
> 対象を増やすこと自体が目的ではありません。
> **前回の標本では一度も発火しなかった条件を、実際に評価できる標本にすることが目的です。**

選び方(**内容で選ばない。全部機械の規則**):
  0. **段 4・段 5 で主張された値を持つ行を 1 行も入れない** → 新規性を構造で保証する
  1. 表 1 = 総括の会計の行のうち、**3 列とも値が新しい**会計すべて
  2. 表 2 = **未確認の会計**(別名の裏づけが 3 本に届かない)の款・項の行、文書の順で先頭から
  3. 表 3 = **親が無ければ 4 欄で一意にならない**目の行(一般会計)、文書の順で先頭から

**指示文の字は段 4・段 5 と同じものを使う**(抜粋だけが変わる)。
出力は**報告文を生成する前に commit する**。
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "m6_material_2026-10-15.json")
PREV = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json")
MAX_EXTRACT = 24000
MAX_REPORT = 1200
KAN_HEAD = 40
MOKU_HEAD = 40
MODEL = "claude-sonnet-4-5"


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_m6", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm

# 指示文は段 4・段 5 と同じ字(抜粋だけ差し替える)
M4 = _mod("m4mat", "sheet_m4_material_2026-10-15.py")
PROMPT = M4.PROMPT


def yen(v):
    return "" if v is None else "{:,}".format(v)


def used_values():
    """段 4・段 5 で主張された値。**0 は除く。**

    段 5 の報告文が「差額は 0 円」と書いたので 0 は「既出の値」になるが、
    **0 は行を特定しない**(不用額などに何千行も現れる)。これで行を落とすと
    抜粋がほとんど空になる。だから**行を選ぶ規則からは 0 を外す。**
    ただし**主張の新規・再出の印は変えない** ― 報告文が「0 円」と書けば
    その主張は `再出` のままである(封 追記 2 の D の数え方を変えない)。
    """
    out = set()
    for f in PREV:
        for c in json.load(io.open(os.path.join(FX, f), encoding="utf-8"))["claims"]:
            v = c.get("value")
            if v is not None and v != 0:
                out.add(v)
    return out


def build():
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        p = os.path.join(M2.CACHE, f)
        if not os.path.exists(p):
            raise SystemExit("材料が無い: %s" % f)
        books[f], _ = M2.M1.read(p)
    sk = M2.parse_soukatu(books[M2.SOUKATU])
    ks = M2.parse_kessan(books[M2.KESSAN])
    ms = M2.parse_meisai(books[M2.MEISAI])
    raw = E.fix_total_level(E.build_index(sk, ks, ms))
    alias = E.alias_table(raw)
    ents = E.canonicalize(raw, alias)
    used = used_values()

    unconfirmed = {u["name"] for u in alias["unconfirmed"]}
    canon_of_unconfirmed = {u.get("canonical") for u in alias["unconfirmed"]
                            if u.get("canonical")}
    k4 = collections.defaultdict(set)
    for e in ents:
        k4[(norm(e["scope"]), norm(e["level"]), norm(e["name"]),
            norm(e["column"]))].add(e["value"])
    dup4 = {k for k, v in k4.items() if len(v) > 1}

    lines, counts, cond = [], {}, {}

    # ---- 表 1: 値が全部新しい会計だけ
    lines.append("【表 1】会計別の決算額(単位: 円)")
    lines.append("会計別\t歳入決算額\t歳出決算額\t差額")
    n, accounts1 = 0, []
    for a in sk["accounts"]:
        v = a["values"]
        vals = [v.get("歳入決算額"), v.get("歳出決算額"), v.get("差額")]
        if any(x in used for x in vals if x is not None):
            continue
        lines.append("%s\t%s\t%s\t%s" % (a["name"], yen(vals[0]), yen(vals[1]),
                                         yen(vals[2])))
        n += 1
        accounts1.append(a["name"])
    counts["表1_行"] = n
    counts["表1_の会計"] = accounts1

    # ---- 表 2: 未確認の会計の款・項(= 明細の双子が同じ会計だと証明できない会計)
    lines.append("")
    lines.append("【表 2】款・項別の歳出(単位: 円)")
    lines.append("会計\t階層\t科目名\t予算現額\t支出済額\t不用額")
    n, acc2 = 0, []
    for e in ents:
        if n >= KAN_HEAD:
            break
        if e["file"] != "決算書 歳出" or e["level"] not in ("款", "項"):
            continue
        if e["scope"] not in canon_of_unconfirmed:
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        row = {}
        for o in ents:
            if (o["scope"] == e["scope"] and o["level"] == e["level"]
                    and o["name"] == e["name"] and o["file"] == e["file"]):
                row[norm(o["column"])] = o["value"]
        lines.append("%s\t%s\t%s\t%s\t%s\t%s" % (
            e["scope"], e["level"], e["name"], yen(row.get(norm("予算現額"))),
            yen(row.get(norm("支出済額"))), yen(row.get(norm("不用額")))))
        n += 1
        if e["scope"] not in acc2:
            acc2.append(e["scope"])
    counts["表2_行"] = n
    counts["表2_の会計"] = acc2

    # ---- 表 3: 親が無ければ一意にならない目の行
    lines.append("")
    lines.append("【表 3】目別の歳出(単位: 円)")
    lines.append("会計\t款名\t項名\t目名\t支出済額")
    n, names3, parents3 = 0, [], set()
    for e in ents:
        if n >= MOKU_HEAD:
            break
        if e["level"] != "目" or e.get("scope_unconfirmed"):
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        key = (norm(e["scope"]), norm(e["level"]), norm(e["name"]),
               norm(e["column"]))
        if key not in dup4 or not e["parent"]:
            continue
        kan, _, ko = e["parent"].partition(" > ")
        lines.append("%s\t%s\t%s\t%s\t%s" % (e["scope"], kan, ko, e["name"],
                                             yen(e["value"])))
        n += 1
        names3.append(e["name"])
        parents3.add(e["parent"])
    counts["表3_行"] = n
    counts["表3_の目名"] = sorted(set(names3))
    counts["表3_の親の種類"] = len(parents3)
    counts["表3_同名で親が違う目"] = {k: v for k, v in
                                     collections.Counter(names3).items() if v > 1}

    extract = "\n".join(lines)
    if len(extract) > MAX_EXTRACT:
        raise AssertionError("抜粋が上限を超えた: %d > %d" % (len(extract), MAX_EXTRACT))

    cond["条件1 未確認の会計を含む"] = {
        "満たす": bool(acc2),
        "どう満たすか": "表 2 の会計は、明細側の `東京都○○会計` が別名として未確認なので、"
                        "款・項の主張は 6 欄が 2 通りに割れて保留になるはず",
        "会計": acc2}
    cond["条件2 親が効く行を含む"] = {
        "満たす": bool(counts["表3_同名で親が違う目"]),
        "どう満たすか": "表 3 は、親を外すと 4 欄で一意にならない目の行だけ",
        "同名で親が違う目": counts["表3_同名で親が違う目"]}
    cond["条件3 新規主張 10 件以上"] = {
        "満たす(構造として)": True,
        "どう満たすか": "**抜粋に、段 4・段 5 で主張された値(0 を除く)を持つ行を"
                        "1 行も入れていない**。0 は行を特定しないので行の選別から外した"
                        "(主張の新規・再出の印は変えない)",
        "ただし": "報告文が実際に 10 件以上の数を挙げるかは生成するまで分からない。"
                  "**10 件未満なら、そのまま報告して作り直さない**",
        "除いた値の数": len(used)}
    return extract, counts, cond, sorted(unconfirmed)


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    extract, counts, cond, unconfirmed = build()
    rec = {"seal": "docs/DOMAIN1_M6_SEAL_2026-10-15.md",
           "model": MODEL, "runs": 1,
           "limits": {"extract_chars": MAX_EXTRACT, "report_chars": MAX_REPORT},
           "rule": ("段 4・段 5 で主張された値(0 を除く)を持つ行を 1 行も入れない / "
                    "表 1 = 3 列とも値が新しい会計すべて / "
                    "表 2 = 未確認の会計の款・項を文書の順で先頭から %d 行 / "
                    "表 3 = 親が無ければ 4 欄で一意にならない目を先頭から %d 行"
                    % (KAN_HEAD, MOKU_HEAD)),
           "prompt_identical_to_stage4": True,
           "counts": counts, "conditions": cond,
           "unconfirmed_accounts": unconfirmed,
           "extract_chars": len(extract),
           "prompt": PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3 の結果",
                        "段 4・段 5 の報告文と採点結果", "診断の結果"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋 %d 字" % len(extract))
    print("counts:", json.dumps(counts, ensure_ascii=False))
    for k, v in cond.items():
        print("%s -> %s" % (k, json.dumps(v, ensure_ascii=False)[:220]))
    print("->", OUT)


if __name__ == "__main__":
    main()
