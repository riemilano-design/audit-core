# -*- coding: utf-8 -*-
"""段 8 の材料を**機械で**作る(封 docs/DOMAIN1_M8_SEAL_2026-10-16.md §3)。

**報告文を生成する前に commit する。**

選び方(**内容で選ばない。先に封に書いた規則のまま。出力を見て選び直さない**):
  0. 段 4・段 5・段 6・段 7 で主張された値(0 を除く)を持つ行を 1 行も入れない
  1. 段 6・段 7 の抜粋に現れた行を 1 行も入れない
  2. 表 1 = 総括の会計名の一覧(値を載せない)
  3. 表 2 = 一般会計の款の行と、**裏づけ B-1〜B-3 が 3 本そろった項の行**、先頭から 40 行。
     列は `款名`(項の行だけ。**款の行は空**)・予算現額・支出済額・不用額
  4. 表 3 = 親が無ければ 4 欄で一意にならない目の行(一般会計)、先頭から 40 行。
     列は `款名`・`項名`・計・支出済額・不用額

**指示文の字は段 4 から 1 文字も変えない。**

段 7 からの変更は**表 2 に `款名` の欄が増えたことだけ**である(封 §2-1)。

    python3 measure/sheet_m8_material_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "m8_material_2026-10-16.json")
PREV = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json")
PREV_MAT = ("m6_material_2026-10-15.json", "m7_material_2026-10-15.json")
MAX_EXTRACT = 24000
MAX_REPORT = 1200
KAN_HEAD = 40
MOKU_HEAD = 40
COLS_KESSAN = ("予算現額", "支出済額", "不用額")
COLS_MEISAI = ("計", "支出済額", "不用額")
MODEL = "claude-sonnet-4-5"


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_m8mat", "sheet_m5_engine_2026-10-15.py")
BK = _mod("backing_for_m8mat", "sheet_parent_backing_2026-10-16.py")
M2 = E.M2
norm = M2.norm
M4 = _mod("m4mat_for_m8", "sheet_m4_material_2026-10-15.py")
PROMPT = M4.PROMPT          # **段 4 と同じ字**


def yen(v):
    return "" if v is None else "{:,}".format(v)


def used_values():
    """段 4〜段 7 で主張された値。**0 は除く**(段 6・段 7 と同じ理由・同じ扱い)。"""
    out = set()
    for f in PREV:
        for c in json.load(io.open(os.path.join(FX, f), encoding="utf-8"))["claims"]:
            v = c.get("value")
            if v is not None and v != 0:
                out.add(v)
    return out


def rows_in_previous_extracts():
    """段 6・段 7 の抜粋に現れた行の鍵(会計・階層・親・科目名)。"""
    keys = set()
    for f in PREV_MAT:
        mat = json.load(io.open(os.path.join(FX, f), encoding="utf-8"))
        body = (mat["prompt"].split("----- 表(ここから) -----")[1]
                .split("----- 表(ここまで) -----")[0])
        for line in body.split("\n"):
            c = [x.strip() for x in line.split("\t")]
            if c and c[0] == "会計":
                continue
            if len(c) == 6 and c[1] in ("款", "項"):
                keys.add((norm(c[0]), norm(c[1]), "", norm(c[2])))
            elif len(c) == 5 and c[1] and c[2] and c[3]:
                keys.add((norm(c[0]), norm("目"),
                          norm("%s > %s" % (c[1], c[2])), norm(c[3])))
            elif len(c) == 7 and c[1] and c[2] and c[3]:
                keys.add((norm(c[0]), norm("目"),
                          norm("%s > %s" % (c[1], c[2])), norm(c[3])))
            elif len(c) == 4 and c[0] and c[1]:
                keys.add((norm(c[0]), norm("会計"), "", norm(c[0])))
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
    seen = rows_in_previous_extracts()

    # **裏づけ B-1〜B-3 がそろった項の款名だけを使う**(封 §2-1)
    kou_ok, kou_why, kou_detail = BK.kou_parents(ks, ms, alias["table"])

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

    lines.append("【表 1】会計の一覧")
    lines.append("会計別")
    acc1 = [a["name"] for a in sk["accounts"]]
    lines.extend(acc1)
    counts["表1_行"] = len(acc1)
    counts["表1_に値を載せたか"] = False

    lines.append("")
    lines.append("【表 2】款・項別の歳出(単位: 円)")
    lines.append("会計\t階層\t款名\t科目名\t%s" % "\t".join(COLS_KESSAN))
    n, dropped = 0, 0
    for e in ents:
        if n >= KAN_HEAD:
            break
        if e["file"] != "決算書 歳出" or e["level"] not in ("款", "項"):
            continue
        if norm(e["scope"]) != norm("一般会計"):
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        if row_key(e) in seen:
            continue
        kan_name = ""
        if e["level"] == "項":
            key = (norm(e["scope"]), norm(e["name"]))
            if key not in kou_ok:
                dropped += 1
                continue                      # **推測で補完しない**
            kan_name = kou_ok[key]
        row = cols_of(e)
        if any(row.get(norm(c)) in used for c in COLS_KESSAN
               if row.get(norm(c)) is not None):
            continue
        if any(row.get(norm(c)) is None for c in COLS_KESSAN):
            continue
        lines.append("%s\t%s\t%s\t%s\t%s" % (
            e["scope"], e["level"], kan_name, e["name"],
            "\t".join(yen(row.get(norm(c))) for c in COLS_KESSAN)))
        n += 1
        chosen["表2"].append({"階層": e["level"], "款名": kan_name,
                              "科目名": e["name"],
                              "4欄で一意でない": (norm(e["scope"]), norm(e["level"]),
                                                  norm(e["name"]),
                                                  norm("支出済額")) in dup4})
    counts["表2_行"] = n
    counts["表2_裏づけが足りず落とした項"] = dropped
    counts["表2_款の行"] = sum(1 for x in chosen["表2"] if x["階層"] == "款")
    counts["表2_項の行"] = sum(1 for x in chosen["表2"] if x["階層"] == "項")

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
        if row_key(e) in seen:
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
    return extract, counts, chosen, len(used), len(seen), kou_why, kou_detail


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    extract, counts, chosen, nused, nseen, kou_why, kou_detail = build()
    rec = {"seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "model": MODEL, "runs": 1,
           "limits": {"extract_chars": MAX_EXTRACT, "report_chars": MAX_REPORT},
           "rule": ("段 4〜段 7 で主張された値(0 を除く)を持つ行を入れない / "
                    "段 6・段 7 の抜粋に現れた行を入れない / "
                    "表 1 = 会計名の一覧(値を載せない) / "
                    "表 2 = 一般会計の款と、**裏づけ 3 本がそろった項**を先頭から %d 行 / "
                    "表 3 = 親が無ければ 4 欄で一意にならない目を先頭から %d 行"
                    % (KAN_HEAD, MOKU_HEAD)),
           "value_columns": {"表2": list(COLS_KESSAN), "表3": list(COLS_MEISAI)},
           "change_from_m7": ("**表 2 に `款名` の欄が増えたことだけ。**"
                              "款の行の款名は空(問いの `R-親-2` が「款の行は親を空欄」と"
                              "決めているため)。表 1・表 3 の形は段 7 と同じ"),
           "parent_backing": {
               "項の款名": ["B-1 決算書の配置", "B-2 決算書のコード", "B-3 明細の配置"],
               "目の親": ["B-4 明細の配置", "B-5 明細のコード"],
               "裏づけが足りず表 2 から落とした項の行": counts["表2_裏づけが足りず落とした項"],
               "落ちた理由(全会計)": kou_why,
               "注": ("**目の裏づけは 2 本で、項の 3 本より 1 本少ない**(封 §2-2)。"
                      "**同じ強さの根拠として扱わない。**")},
           "seal_wording_correction": (
               "**封 §2-1 の表は、落ちた 2 件の理由を「明細に複数の款の候補が在る」と"
               "書いたが、実装で数えると理由は「決算書の中で同じ項名が 2 つの款に在る」"
               "だった(`退職手当及年金費`・`施設整備費`)。件数 2 は合っている。"
               "**封は直さない。**理由の字が違ったことをここに記録する。"),
           "prompt_identical_to_stage4": True,
           "excluded_values": nused, "excluded_rows_from_previous_extracts": nseen,
           "counts": counts, "chosen": chosen,
           "extract_chars": len(extract),
           "prompt": PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3〜段 7 の結果", "診断の結果",
                        "親の規則", "機会の件数"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋 %d 字 / 除いた値 %d 個 / 前の抜粋の行 %d 件を除外" % (len(extract), nused, nseen))
    print("表 2: %d 行(款 %d / 項 %d)/ 裏づけ不足で落とした項 %d 行"
          % (counts["表2_行"], counts["表2_款の行"], counts["表2_項の行"],
             counts["表2_裏づけが足りず落とした項"]))
    print("表 3: %d 行 / 同名で親が違う目: %s"
          % (counts["表3_行"], json.dumps(counts["表3_同名で親が違う目"], ensure_ascii=False)))
    print("->", OUT)


if __name__ == "__main__":
    main()
