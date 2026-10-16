# -*- coding: utf-8 -*-
"""段 7 の材料を**機械で**作る(封 §8 の 5)。**報告文を生成する前に commit する。**

選び方(**内容で選ばない。全部機械の規則。先に決めて、出力を見て選び直さない**):
  0. **段 4・段 5・段 6 で主張された値(0 を除く)を持つ行を 1 行も入れない**
  1. **段 6 の抜粋に現れた行を 1 行も入れない**(会計・階層・親・科目名が同じ行を外す)
  2. 表 1 = 総括の**会計名の一覧**(値を載せない)
  3. 表 2 = **一般会計**の款・項の行、文書の順で先頭から 40 行(列 = 予算現額・支出済額・不用額)
  4. 表 3 = **親が無ければ 4 欄で一意にならない**目の行(一般会計)、先頭から 40 行
     (列 = **計**・支出済額・不用額。明細の見出しは `予算現額` ではなく `計` である)

**指示文の字は段 4 から 1 文字も変えない。**

**開示(材料の形を段 6 から変えた点が 3 つ在る):**

1. 段 6 の表 3 は値の列が `支出済額` の 1 列だけだった。段 7 は**3 列**にする。
   ただしこの変更は、**診断で「列の手がかりが無いと親が取れても接続にならない」と
   分かった後**に決めたものである。**材料を engine の都合に合わせた変更として開示する。**
   報告文の書き方は誘導しない(指示文は不変)。
2. **表 1 は会計名の一覧にして、値を載せない。**最初に書いた規則
   (「3 列とも値が新しい会計すべて」+「段 6 の抜粋の行を外す」)では**表 1 が 0 行**になり、
   問いの `R-会計-1`(会計名は表 1 に書かれている名前)が**答えられなくなった**。
   値を載せれば既出の値が戻るので、**名前だけ載せる。**
   **その代わり、会計の層の主張はこの標本では作れない。**段 6 では接続 13 件のうち
   11 件が会計の層だったので、**この標本は G-1 がさらに下がる方向である。**
   **下がっても標本を作り直さない。**
3. 表 3 の 1 列目の見出しは `予算現額` ではなく **`計`** である(明細の見出しがそれ)。
   問いの `R-列-2` が既に「表 2 の `予算現額` と表 3 の `計` は同じ列として採点する」と
   決めているので、**問いは 1 文字も変えない。**

    python3 measure/sheet_m7_material_2026-10-15.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "m7_material_2026-10-15.json")
PREV = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json")
M6MAT = os.path.join(FX, "m6_material_2026-10-15.json")
MAX_EXTRACT = 24000
MAX_REPORT = 1200
KAN_HEAD = 40
MOKU_HEAD = 40
COLS_KESSAN = ("予算現額", "支出済額", "不用額")     # 決算書(款・項)の見出し
COLS_MEISAI = ("計", "支出済額", "不用額")            # 明細(目)の見出し
MODEL = "claude-sonnet-4-5"


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_m7mat", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm
M4 = _mod("m4mat_for_m7", "sheet_m4_material_2026-10-15.py")
PROMPT = M4.PROMPT          # **段 4 と同じ字**


def yen(v):
    return "" if v is None else "{:,}".format(v)


def used_values():
    """段 4・段 5・段 6 で主張された値。**0 は除く**(段 6 と同じ理由・同じ扱い)。"""
    out = set()
    for f in PREV:
        for c in json.load(io.open(os.path.join(FX, f), encoding="utf-8"))["claims"]:
            v = c.get("value")
            if v is not None and v != 0:
                out.add(v)
    return out


def rows_in_m6_extract():
    """段 6 の抜粋に現れた行の鍵(会計・階層・親・科目名)。**同じ行を出さない。**"""
    mat = json.load(io.open(M6MAT, encoding="utf-8"))
    body = (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0])
    keys = set()
    for line in body.split("\n"):
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) == 6 and cells[1] in ("款", "項"):
            keys.add((norm(cells[0]), norm(cells[1]), "", norm(cells[2])))
        elif len(cells) == 5 and cells[1] and cells[2] and cells[3]:
            keys.add((norm(cells[0]), norm("目"),
                      norm("%s > %s" % (cells[1], cells[2])), norm(cells[3])))
        elif len(cells) == 4 and cells[0] and cells[1]:
            keys.add((norm(cells[0]), norm("会計"), "", norm(cells[0])))
    return keys


def row_key(e):
    return (norm(e["scope"]), norm(e["level"]), norm(e["parent"]), norm(e["name"]))


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
    seen6 = rows_in_m6_extract()

    k4 = collections.defaultdict(set)
    for e in ents:
        k4[(norm(e["scope"]), norm(e["level"]), norm(e["name"]),
            norm(e["column"]))].add(e["value"])
    dup4 = {k for k, v in k4.items() if len(v) > 1}

    def cols_of(e):
        out = {}
        for o in ents:
            if row_key(o) == row_key(e) and o["file"] == e["file"]:
                out[norm(o["column"])] = o["value"]
        return out

    lines, counts, chosen = [], {}, {"表2": [], "表3": []}

    # 表 1 は**会計名の一覧**。値を載せない(開示 2)
    lines.append("【表 1】会計の一覧")
    lines.append("会計別")
    acc1 = []
    for a in sk["accounts"]:
        lines.append(a["name"])
        acc1.append(a["name"])
    counts["表1_行"] = len(acc1)
    counts["表1_の会計"] = acc1
    counts["表1_に値を載せたか"] = False

    lines.append("")
    lines.append("【表 2】款・項別の歳出(単位: 円)")
    lines.append("会計\t階層\t科目名\t%s" % "\t".join(COLS_KESSAN))
    n = 0
    for e in ents:
        if n >= KAN_HEAD:
            break
        if e["file"] != "決算書 歳出" or e["level"] not in ("款", "項"):
            continue
        if norm(e["scope"]) != norm("一般会計"):
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        if row_key(e) in seen6:
            continue
        row = cols_of(e)
        if any(row.get(norm(c)) in used for c in COLS_KESSAN
               if row.get(norm(c)) is not None):
            continue
        if any(row.get(norm(c)) is None for c in COLS_KESSAN):
            continue
        lines.append("%s\t%s\t%s\t%s" % (
            e["scope"], e["level"], e["name"],
            "\t".join(yen(row.get(norm(c))) for c in COLS_KESSAN)))
        n += 1
        chosen["表2"].append({"階層": e["level"], "科目名": e["name"],
                              "親": e["parent"],
                              "4欄で一意でない": (norm(e["scope"]), norm(e["level"]),
                                                  norm(e["name"]),
                                                  norm("支出済額")) in dup4})
    counts["表2_行"] = n

    lines.append("")
    lines.append("【表 3】目別の歳出(単位: 円)")
    lines.append("会計\t款名\t項名\t目名\t%s" % "\t".join(COLS_MEISAI))
    n, names3, parents3 = 0, [], set()
    for e in ents:
        if n >= MOKU_HEAD:
            break
        if e["level"] != "目" or e.get("scope_unconfirmed"):
            continue
        if norm(e["scope"]) != norm("一般会計"):
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        key = (norm(e["scope"]), norm(e["level"]), norm(e["name"]), norm("支出済額"))
        if key not in dup4 or not e["parent"]:
            continue
        if row_key(e) in seen6:
            continue
        row = cols_of(e)
        if any(row.get(norm(c)) in used for c in COLS_MEISAI
               if row.get(norm(c)) is not None):
            continue
        if any(row.get(norm(c)) is None for c in COLS_MEISAI):
            continue
        kan, _, ko = e["parent"].partition(" > ")
        lines.append("%s\t%s\t%s\t%s\t%s" % (
            e["scope"], kan, ko, e["name"],
            "\t".join(yen(row.get(norm(c))) for c in COLS_MEISAI)))
        n += 1
        names3.append(e["name"])
        parents3.add(e["parent"])
        chosen["表3"].append({"科目名": e["name"], "親": e["parent"]})
    counts["表3_行"] = n
    counts["表3_の目名"] = sorted(set(names3))
    counts["表3_の親の種類"] = len(parents3)
    counts["表3_同名で親が違う目"] = {k: v for k, v in
                                     collections.Counter(names3).items() if v > 1}

    extract = "\n".join(lines)
    if len(extract) > MAX_EXTRACT:
        raise AssertionError("抜粋が上限を超えた: %d > %d" % (len(extract), MAX_EXTRACT))
    return extract, counts, chosen, len(used), len(seen6)


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    extract, counts, chosen, nused, nseen = build()
    rec = {"seal": "docs/DOMAIN1_M7_SEAL_2026-10-15.md",
           "model": MODEL, "runs": 1,
           "limits": {"extract_chars": MAX_EXTRACT, "report_chars": MAX_REPORT},
           "rule": ("段 4・段 5・段 6 で主張された値(0 を除く)を持つ行を入れない / "
                    "段 6 の抜粋に現れた行を入れない / "
                    "表 1 = 会計名の一覧(値を載せない) / "
                    "表 2 = 一般会計の款・項を文書の順で先頭から %d 行 / "
                    "表 3 = 親が無ければ 4 欄で一意にならない目を先頭から %d 行"
                    % (KAN_HEAD, MOKU_HEAD)),
           "value_columns": {"表2": list(COLS_KESSAN), "表3": list(COLS_MEISAI)},
           "shape_change_from_m6": [
               ("表 3 を 1 列から 3 列にした。**診断で「列の手がかりが無いと親が取れても"
                "接続にならない」と分かった後に決めた変更**であり、材料を engine の都合に"
                "合わせた変更として開示する。指示文は段 4 から 1 文字も変えていない"),
               ("**表 1 を会計名の一覧にし、値を載せない。**最初の規則では表 1 が 0 行になり、"
                "問いの `R-会計-1` が答えられなくなった。値を載せれば既出の値が戻るので"
                "名前だけ載せる。**その代わり会計の層の主張が作れないので、"
                "この標本は G-1 がさらに下がる方向である。下がっても作り直さない**"),
               ("表 3 の 1 列目の見出しは `計`(明細の見出し)。問いの `R-列-2` が既に"
                "「表 2 の `予算現額` と表 3 の `計` は同じ列」と決めているので問いは不変"),
           ],
           "prompt_identical_to_stage4": True,
           "excluded_values": nused, "excluded_rows_from_m6_extract": nseen,
           "counts": counts, "chosen": chosen,
           "extract_chars": len(extract),
           "prompt": PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3〜段 6 の結果", "診断の結果",
                        "親の規則"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋 %d 字 / 除いた値 %d 個 / 段 6 の抜粋の行 %d 件を除外"
          % (len(extract), nused, nseen))
    print("counts:", json.dumps(counts, ensure_ascii=False)[:600])
    print("->", OUT)


if __name__ == "__main__":
    main()
