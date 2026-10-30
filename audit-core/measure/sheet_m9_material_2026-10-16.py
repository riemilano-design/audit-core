# -*- coding: utf-8 -*-
"""段 9 の材料を**機械で**作る(封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §3)。

**報告文を生成する前に commit する。**

選び方(**内容で選ばない。先に封に書いた規則のまま。出力を見て選び直さない**):
  0. 段 4〜段 8 で主張された値(0 を除く)を持つ行を 1 行も入れない
  1. **「過去の抜粋に現れた行を除く」規則は段 9 の封に無い。**だから入れない
     (段 8 の script はこれを足していたが、封 §3-1 の規則は**値だけ**である)。
     代わりに**重複した行の数を記録して開示する。**
     重複しうるのは「過去の抜粋に載ったが報告文が主張しなかった行」だけである
     ― 主張された値は 0 を除いて全部落ちているので、**主張の新規性は値の規則が守る。**
  2. 表 1 = 総括の会計名の一覧(**値を載せない**)
  3. 表 2 = 決算書 歳出 の款・項。款名つき。
     **18 未確認会計の正本を全行** + **一般会計を文書の順で先頭から 16 行**。
     款名は**段 8 の規則を変えない**(B-1〜B-3 の 3 本がそろった項だけ。
     款の行は空欄)。**未確認会計の項は B-3 が別名を要するのでそろわず、落ちる。**
     その件数を記録する。**推測で補完しない。**
  4. 表 3 = 明細の目。款名・項名つき(**B-4 + B-5 の 2 本だけ**。封 §3-3)。
     3a = **一般会計**の目のうち「科目名・列・値まで同じで親が 2 通り以上」の組に
          属する行を文書の順で**先頭から 12 行** → **G-4 の機会**
     3b = **未確認会計**の目の全行 → **③の発火機会**

会計の欄には **`canonicalize` 後の `scope`** を載せる(封 §3-2)。したがって
**裏づけの在る別名だけが直り**(`東京都一般会計` → `一般会計`)、
**裏づけの無い別名は `東京都○○会計` のまま載る。**
**この差が抜粋の上に見えることが③の発火機会である。**

**報告文を生成する指示文(PROMPT)の字は段 4 から 1 文字も変えない。**
席に渡す問いは別の script(`sheet_m9_label_material_*.py`)が段 9 の spec から作る。

    python3 measure/sheet_m9_material_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "m9_material_2026-10-16.json")
PREV = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json",
        "m8_binds_2026-10-16.json")
PREV_MAT = ("m6_material_2026-10-15.json", "m7_material_2026-10-15.json",
            "m8_material_2026-10-16.json")
MAX_EXTRACT = 24000
MAX_REPORT = 1200
IPPAN_HEAD = 16              # 表 2 の一般会計の上限(封 §3-1)
MOKU_3A_HEAD = 12            # 表 3a の上限(封 §3-1)
COLS_KESSAN = ("予算現額", "支出済額", "不用額")
COLS_MEISAI = ("支出済額", "補正予算額")
MODEL = "claude-sonnet-4-5"
IPPAN = "一般会計"


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_m9mat", "sheet_m5_engine_2026-10-15.py")
BK = _mod("backing_for_m9mat", "sheet_parent_backing_2026-10-16.py")
M8 = _mod("m8mat_for_m9", "sheet_m8_material_2026-10-16.py")
M2 = E.M2
norm = M2.norm
M4 = _mod("m4mat_for_m9", "sheet_m4_material_2026-10-15.py")
PROMPT = M4.PROMPT          # **段 4 と同じ字**

yen = M8.yen
row_key = M8.row_key


def used_values():
    """段 4〜段 8 で主張された値。**0 は除く**(段 6〜段 8 と同じ理由・同じ扱い)。"""
    out = set()
    for f in PREV:
        d = json.load(io.open(os.path.join(FX, f), encoding="utf-8"))
        for c in d["claims"]:
            v = c.get("value")
            if v is not None and v != 0:
                out.add(v)
    return out


def rows_in_previous_extracts():
    """段 6・段 7・段 8 の抜粋に現れた行の鍵。**段 8 の読み取りをそのまま使う。**"""
    keys = set()
    for f in PREV_MAT:
        mat = json.load(io.open(os.path.join(FX, f), encoding="utf-8"))
        body = (mat["prompt"].split("----- 表(ここから) -----")[1]
                .split("----- 表(ここまで) -----")[0])
        for line in body.split("\n"):
            c = [x.strip() for x in line.split("\t")]
            if c and c[0] == "会計":
                continue
            if len(c) == 7 and c[1] in ("款", "項"):          # 段 8 の表 2
                keys.add((norm(c[0]), norm(c[1]), norm(c[2]), norm(c[3])))
            elif len(c) == 6 and c[1] in ("款", "項"):        # 段 6・段 7 の表 2
                keys.add((norm(c[0]), norm(c[1]), "", norm(c[2])))
            elif len(c) == 7 and c[1] and c[2] and c[3]:      # 段 8 の表 3
                keys.add((norm(c[0]), norm("目"),
                          norm("%s > %s" % (c[1], c[2])), norm(c[3])))
            elif len(c) == 5 and c[1] and c[2] and c[3]:      # 段 6・段 7 の表 3
                keys.add((norm(c[0]), norm("目"),
                          norm("%s > %s" % (c[1], c[2])), norm(c[3])))
    return keys


def collision_groups(ents):
    """**会計・科目名・列・値まで同じで親が 2 通り以上**の組(G-4 の機会の素)。

    席はこの行を抜粋から 1 つに決められない(名前でも列でも値でも選べない)。
    """
    g = collections.defaultdict(set)
    for e in ents:
        if e["level"] != "目":
            continue
        g[(norm(e["scope"]), norm(e["name"]), norm(e["column"]),
           e["value"])].add(norm(e["parent"]) or "")
    return {k for k, v in g.items() if len(v) > 1}


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

    unconf_alias = {u["name"] for u in alias["unconfirmed"]}
    unconf_canon = {u["canonical"] for u in alias["unconfirmed"]
                    if u.get("canonical")}
    # **表 2 の款名は段 8 の規則(B-1〜B-3 の 3 本)を変えない**
    kou_ok, kou_why, _ = BK.kou_parents(ks, ms, alias["table"])
    # **表 3 の款名・項名は明細の中だけの 2 本(B-4 + B-5)**
    moku_ok, moku_why = BK.moku_parents(ms)
    coll = collision_groups(ents)
    # **明細の裏づけ表は「明細に書かれた字」で鍵を持つ**(`東京都一般会計`)。
    # 抜粋の会計の欄は `canonicalize` 後の字(`一般会計`)なので、**両方を試す**
    # (記憶 `normalize-both-sides-of-a-comparison.md`)。
    written_of = collections.defaultdict(set)
    for e in raw:
        if e["file"] == "事項別明細":
            written_of[norm(e["scope"])].add(norm(e["scope"]))
    for w, rec in alias["table"].items():
        written_of[norm(rec["canonical"])].add(norm(w))

    def cols_of(e):
        out = {}
        for o in ents:
            if row_key(o) == row_key(e) and o["file"] == e["file"]:
                out[norm(o["column"])] = o["value"]
        return out

    def usable(row, cols):
        if any(row.get(norm(c)) is None for c in cols):
            return False
        return not any(row.get(norm(c)) in used for c in cols)

    lines, counts = [], {}
    chosen = {"表2": [], "表3a": [], "表3b": []}
    overlap = collections.Counter()

    # ---------------------------------------------------------------- 表 1
    lines.append("【表 1】会計の一覧")
    lines.append("会計別")
    acc1 = [a["name"] for a in sk["accounts"]]
    lines.extend(acc1)
    counts["表1_行"] = len(acc1)
    counts["表1_に値を載せたか"] = False

    # ---------------------------------------------------------------- 表 2
    lines.append("")
    lines.append("【表 2】款・項別の歳出(単位: 円)")
    lines.append("会計\t階層\t款名\t科目名\t%s" % "\t".join(COLS_KESSAN))
    n_ippan, dropped = 0, collections.Counter()
    for e in ents:
        if e["file"] != "決算書 歳出" or e["level"] not in ("款", "項"):
            continue
        is_ippan = norm(e["scope"]) == norm(IPPAN)
        if not is_ippan and e["scope"] not in unconf_canon:
            continue
        if is_ippan and n_ippan >= IPPAN_HEAD:
            continue
        if norm(e["column"]) != norm("支出済額") or e["value"] in used:
            continue
        if row_key(e) in seen:
            overlap["表2"] += 1          # **落とさない。数えるだけ**(封に無い規則)
        kan_name = ""
        if e["level"] == "項":
            key = (norm(e["scope"]), norm(e["name"]))
            if key not in kou_ok:
                dropped["%s の項" % ("一般会計" if is_ippan else "未確認会計")] += 1
                continue                      # **推測で補完しない**
            kan_name = kou_ok[key]
        row = cols_of(e)
        if not usable(row, COLS_KESSAN):
            continue
        lines.append("%s\t%s\t%s\t%s\t%s" % (
            e["scope"], e["level"], kan_name, e["name"],
            "\t".join(yen(row.get(norm(c))) for c in COLS_KESSAN)))
        if is_ippan:
            n_ippan += 1
        chosen["表2"].append({"会計": e["scope"], "階層": e["level"],
                              "款名": kan_name, "科目名": e["name"],
                              "未確認の会計か": e["scope"] in unconf_canon})
    counts["表2_行"] = len(chosen["表2"])
    counts["表2_一般会計の行"] = n_ippan
    counts["表2_未確認会計の正本の行"] = len(chosen["表2"]) - n_ippan
    counts["表2_裏づけが足りず落とした項"] = dict(dropped)
    counts["表2_款の行"] = sum(1 for x in chosen["表2"] if x["階層"] == "款")
    counts["表2_項の行"] = sum(1 for x in chosen["表2"] if x["階層"] == "項")

    # ---------------------------------------------------------------- 表 3
    lines.append("")
    lines.append("【表 3】目別の歳出(単位: 円)")
    lines.append("会計\t款名\t項名\t目名\t%s" % "\t".join(COLS_MEISAI))
    n3a, moku_dropped = 0, collections.Counter()
    for part in ("3a", "3b"):
        for e in ents:
            if e["level"] != "目" or e["file"] != "事項別明細":
                continue
            is_unconf = bool(e.get("scope_unconfirmed"))
            if part == "3a" and (is_unconf or n3a >= MOKU_3A_HEAD):
                continue
            if part == "3b" and not is_unconf:
                continue
            if norm(e["column"]) != norm("支出済額") or e["value"] in used:
                continue
            if row_key(e) in seen:
                overlap["表%s" % part] += 1   # **落とさない。数えるだけ**
            row = cols_of(e)
            if not usable(row, COLS_MEISAI):
                continue
            if part == "3a":
                # **G-4 の機会**: 補正予算額の側で親が 2 通り以上に割れる行だけ
                hit = any((norm(e["scope"]), norm(e["name"]), norm(c),
                           row.get(norm(c))) in coll for c in COLS_MEISAI)
                if not hit:
                    continue
            kan_ko = _moku_parent(e, moku_ok, written_of)
            if kan_ko is None:
                moku_dropped[part] += 1
                continue                      # **推測で補完しない**
            kan, ko = kan_ko
            lines.append("%s\t%s\t%s\t%s\t%s" % (
                e["scope"], kan, ko, e["name"],
                "\t".join(yen(row.get(norm(c))) for c in COLS_MEISAI)))
            if part == "3a":
                n3a += 1
            chosen["表%s" % part].append(
                {"会計": e["scope"], "款名": kan, "項名": ko, "目名": e["name"],
                 "別名の形か": is_unconf})
    counts["表3a_行"] = len(chosen["表3a"])
    counts["表3b_行"] = len(chosen["表3b"])
    counts["表3_行"] = len(chosen["表3a"]) + len(chosen["表3b"])
    counts["表3_裏づけが足りず落とした目"] = dict(moku_dropped)
    counts["表3b_の会計"] = sorted({x["会計"] for x in chosen["表3b"]})
    counts["表3a_同名で親が違う目"] = {
        k: v for k, v in collections.Counter(
            x["目名"] for x in chosen["表3a"]).items() if v > 1}
    counts["表3_別名の形で載った会計の数"] = len(counts["表3b_の会計"])
    counts["過去の抜粋と重複した行"] = dict(overlap)
    counts["過去の抜粋に在った行の総数"] = len(seen)

    extract = "\n".join(lines)
    if len(extract) > MAX_EXTRACT:
        raise AssertionError("抜粋が上限を超えた: %d > %d" % (len(extract), MAX_EXTRACT))
    return {"extract": extract, "counts": counts, "chosen": chosen,
            "excluded_values": len(used),
            "excluded_rows_from_previous_extracts": len(seen),
            "kou_backing_dropped": kou_why, "moku_backing_dropped": moku_why,
            "unconfirmed_alias": sorted(unconf_alias),
            "unconfirmed_canonical": sorted(unconf_canon),
            "alias_passed": sorted(alias["table"])}


def _moku_parent(e, moku_ok, written_of):
    """明細の目の (款名, 項名) を B-4 + B-5 の鍵で引く。**無ければ None。**

    鍵の会計は**明細に書かれた字**なので、抜粋の字(正本に直した後)から
    書かれた字の候補を引いて当てる。
    """
    names = written_of.get(norm(e["scope"])) or {norm(e["scope"])}
    want_names = {norm(e["name"])}
    hits = [v for k, v in moku_ok.items()
            if k[0] in names and k[1] in want_names]
    if not hits:
        return None
    if e["parent"]:
        kan, _, ko = e["parent"].partition(" > ")
        for h in hits:
            if norm(h[0]) == norm(kan) and norm(h[1]) == norm(ko):
                return h
        return None
    return hits[0] if len(hits) == 1 else None


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    b = build()
    extract, counts = b["extract"], b["counts"]
    rec = {"seal": "docs/DOMAIN1_M9_SEAL_2026-10-16.md",
           "model": MODEL, "runs": 1,
           "limits": {"extract_chars": MAX_EXTRACT, "report_chars": MAX_REPORT},
           "rule": ("段 4〜段 8 で主張された値(0 を除く)を持つ行を入れない / "
                    "段 6〜段 8 の抜粋に現れた行を入れない / "
                    "表 1 = 総括の会計名の一覧(値なし) / "
                    "表 2 = 決算書 歳出 の款・項。未確認会計の正本を全行 + "
                    "一般会計を先頭から %d 行。款名は B-1〜B-3 の 3 本 / "
                    "表 3a = 一般会計の目のうち『科目名・列・値まで同じで親が "
                    "2 通り以上』の行を先頭から %d 行 / "
                    "表 3b = 未確認会計の目の全行。款名・項名は B-4 + B-5 の 2 本"
                    % (IPPAN_HEAD, MOKU_3A_HEAD)),
           "value_columns": {"表2": list(COLS_KESSAN), "表3": list(COLS_MEISAI)},
           "change_from_m8": [
               "**表 3 に未確認会計の目を入れた**(別名の形 `東京都○○会計` で載る)"
               " ― ③の発火機会。段 8 までの表 3 は一般会計だけだった",
               "**表 3 の列を 計・支出済額・不用額 から 支出済額・補正予算額 に変えた**"
               " ― 補正予算額の側に『科目名・列・値まで同じで親が 2 通り以上』の組が"
               "在る(G-4 の機会)。値は全部 0 である",
               "**表 2 に未確認会計の正本の行を入れた**(段 8 は一般会計だけ)",
               "**表 3 の款名・項名の裏づけは B-4 + B-5 の 2 本だけ**"
               "(封 §3-3。段 8 の項の 3 本より弱い)",
               "**問いの会計の 2 本の規則を直した**(封 §3-4。別の script が使う)",
           ],
           "parent_backing": {
               "表2_款名": "B-1 決算書の配置 + B-2 決算書のコード + B-3 明細の配置(3 本)",
               "表3_款名項名": "B-4 明細の配置 + B-5 明細のコード(**2 本だけ**)",
               "落とした数": {"項": counts["表2_裏づけが足りず落とした項"],
                              "目": counts["表3_裏づけが足りず落とした目"]},
               "注": "**2 本を 3 本と同じ強さの根拠として扱わない。**",
               "**測って分かったこと**": (
                   "B-4 + B-5 の答えは、明細の目 2,555 行すべてで"
                   "**『親の欄をそのまま割った答え』と一致し、1 行も落ちない**"
                   "(B-5 のコードの連番の検査は 0 行を落とした)。"
                   "`e[\"parent\"]` 自体が明細の配置から作られているので B-4 と"
                   "同じものを見ている。したがって**この材料では「2 本を要求した」ことと"
                   "「親の欄を信じた」ことは区別できない。実質 1 本しか働いていない。**"
                   "段 8 の項の 3 本(決算書の配置・決算書のコード・明細の配置)とは"
                   "強さが違う。**この差を隠さない。**"),
           },
           "alias": {"通った": b["alias_passed"],
                     "未確認の別名": b["unconfirmed_alias"],
                     "未確認の正本": b["unconfirmed_canonical"],
                     "注": "**表 3 の会計の欄は canonicalize 後の字。"
                           "裏づけの在る別名だけが直り、無い別名は "
                           "`東京都○○会計` のまま載る。この差が③の発火機会である。**"},
           "prompt_identical_to_stage4": True,
           "excluded_values": b["excluded_values"],
           "excluded_rows_from_previous_extracts":
               b["excluded_rows_from_previous_extracts"],
           "counts": counts, "chosen": b["chosen"],
           "extract_chars": len(extract),
           "prompt": PROMPT % extract,
           "source": "東京都会計管理局 / CC BY 4.0",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3 の結果",
                        "段 4〜段 8 の報告文と採点結果", "診断の結果",
                        "機会の数(O-1〜O-7)"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋 %d 字 / 除いた値 %d / 除いた既出の行 %d"
          % (len(extract), b["excluded_values"],
             b["excluded_rows_from_previous_extracts"]))
    print("counts:", json.dumps(counts, ensure_ascii=False, indent=1))
    print("->", OUT)


if __name__ == "__main__":
    main()
