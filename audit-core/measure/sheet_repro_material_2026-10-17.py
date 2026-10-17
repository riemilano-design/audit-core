# -*- coding: utf-8 -*-
"""別資料(令和５年度)の抜粋と指示文を作る(封 docs/DOMAIN1_REPRO_SEAL_2026-10-17.md §2)。

**費用 0 USD。生成しない。**作るのは**報告文を生成するための指示文**までである。

**段 9 の `build()` をそのまま呼ぶ。**差し替えたのは**読む file だけ**
(`sheet_repro_profile_2026-10-17.py` が差し替えて戻す)。
**規則・表の形・列・上限・指示文の文面は 1 文字も変えない。**

    python3 measure/sheet_repro_material_2026-10-17.py
"""
import hashlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "repro_material_2026-10-17.json")
MAT11REC = os.path.join(FX, "m11_material_2026-10-16.json")
SEAL = "docs/DOMAIN1_REPRO_SEAL_2026-10-17.md"
# 段 11 / 誤り検出の**実測**から出した見込み(封 §5)
EST = {"報告文(sonnet)": (82529, 15.0), "seat1(sonnet)": (101111, 15.0),
       "seat2(haiku)": (70493, 5.0)}


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PR = _mod("profile5_for_mat", "sheet_repro_profile_2026-10-17.py")
MAT11 = _mod("mat11_for_repro", "sheet_m11_material_2026-10-16.py")
M9 = MAT11.M9
OPP = MAT11.OPP


def estimate():
    """**下見の費用**(全部が出力だと仮定した上限)。**実費ではない。**"""
    rows, total = {}, 0.0
    for k, (tok, rate) in EST.items():
        usd = round(tok * rate / 1e6, 4)
        rows[k] = {"見込みトークン(実測から)": tok, "単価": rate, "上限": usd}
        total += usd
    return {"内訳": rows,
            "費-1 報告文 + 2 席": round(total, 4),
            "費-2 報告文 + 1 席(sonnet)": round(
                total - rows["seat2(haiku)"]["上限"], 4),
            "人間の目安": 3.0,
            "費-1 は目安の中か": round(total, 4) <= 3.0,
            "注": ("**見込みであって保証値ではない。**"
                  "**全部が出力だと仮定した上限で、実費はこれより小さい**")}


# 封 §1-1 の実装。**年度の字で動いている所を機械で数える**(直さない)
YEAR = u"令和６年度"
DECIDES = ("startswith", "re.match", "re.compile", "==")


def year_coupled_sites():
    """凍結した道具の中で **年度の字が判定に使われている所**を数える。

    **字を直さない。数えて記録するだけ。**
    """
    out = []
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("sheet_repro_"):
            continue
        for i, line in enumerate(
                io.open(os.path.join(HERE, name), encoding="utf-8")
                .read().split("\n"), 1):
            if YEAR not in line:
                continue
            kind = ("判定に使っている"
                    if any(d in line for d in DECIDES) else "字(説明・指示文)")
            out.append({"file": "measure/" + name, "行": i, "種類": kind,
                        "字": line.strip()[:110]})
    return out


def structure_check(counts):
    """封 §1-1。**parse が落ちた / 行数が 0 / 会計の集合が取れない なら止める。**

    **判定を 1 か所に置く。**(止めるか, 理由) を返す。
    """
    why = []
    if counts.get("表1_行", 0) == 0:
        why.append("会計の集合が取れない(表 1 が 0 行)")
    if counts.get("表2_行", 0) == 0:
        why.append("決算書 歳出の行が 0(表 2 が 0 行)")
    if counts.get("表3_行", 0) == 0:
        why.append("事項別明細 歳出の行が 0(表 3 が 0 行)")
    return bool(why), why


def main():
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    # **使う module が持っている M2 の実体を渡す**(渡さないと効かない)
    with PR.year5(M9.M2, MAT11.M9.M2):
        if not PR.is_year5(M9.M2, MAT11.M9.M2):
            raise SystemExit("**プロファイルが切り替わっていない**")
        if M9.M2.KESSAN != PR.F.KESSAN:
            raise SystemExit("**抜粋を作る側が令和５年度を見ていない**")
        b = MAT11.build()
        extract, counts = b["extract"], b["counts"]
        forms = MAT11.check_alias_forms_are_printed(extract)
        cells = OPP.cells_of(extract)
        stop = MAT11.stop_check(counts, len(cells))
        prompt = M9.PROMPT % extract   # **段 4 と同じ指示文。1 文字も変えない**
    stopped, why = structure_check(counts)
    sites = year_coupled_sites()
    old = json.load(io.open(MAT11REC, encoding="utf-8"))
    if stopped:
        # **止めたら指示文を記録に入れない。**入れると生成できてしまう
        rec = {"seal": SEAL,
               "step": "封 §8 の 4 で**止めた**。**費用 0 USD。生成していない**",
               "**止めた**": True, "止めた理由": why,
               "規則": ("封 §1-1。**parse が落ちた / 行数が 0 / "
                      "会計の集合が取れない場合は、そこで止めて"
                      "「別資料は同じ構造ではなかった」と書く。"
                      "parser を直して通すことはしない**"),
               "**指示文は記録に入れていない**": "止めたので生成できないようにした",
               "別資料": {"総括": PR.F.SOUKATU, "決算書 歳出": PR.F.KESSAN,
                       "事項別明細 歳出": PR.F.MEISAI,
                       "決算書 歳入": PR.F.SAINYUU,
                       "事項別明細 歳入": PR.F.MEISAI_SAINYUU},
               "counts": counts, "value_cells": len(cells),
               "extract_chars": len(extract),
               "alias": {"通った": b["alias_passed"],
                         "未確認の別名": b["unconfirmed_alias"]},
               "診断: 年度の字で動いている所": {
                   "判定に使っている": [s for s in sites
                                if s["種類"] == "判定に使っている"],
                   "字(説明・指示文)の数": len([s for s in sites
                                      if s["種類"] != "判定に使っている"]),
                   "全部": sites},
               "**指示文も年度の字を持っている**": (
                   "`sheet_m4_material` の `PROMPT` は「令和６年度の歳入歳出決算の"
                   "抜粋です」と書いている。**別資料でこれを変えないと事実と違い、"
                   "変えると封の「指示文は 1 文字も変えない」に反する。"
                   "だからここで人間の判断を求める**"),
               "段 11 との比べ(**同じ表に混ぜない。形の確認だけ**)": {
                   "段 11 の値のセル": old["value_cells"],
                   "令和５年度の値のセル": len(cells),
                   "段 11 の表 2 の行": old["counts"]["表2_行"],
                   "令和５年度の表 2 の行": counts["表2_行"]},
               "下見の費用": estimate(),
               "次の段": ("**生成しない。**直すなら別の封を切る"
                       "(動きを変える変更 → 独立した監査の GO が要る)"),
               "limits_note": [
                   "**別資料の中身が違うのではない。道具が年度の字に縛られている。**",
                   "**parser を直して通していない**(封 §1-1)。",
                   "**費用 0 USD。報告文も席も生成していない。**",
               ]}
        json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("=== 別資料(令和５年度)― **封 §1-1 で止めた**(費用 0)===")
        print("止めた理由: %s" % "・".join(why))
        print("counts: 表1 %s / 表2 %s / 表3 %s / 値のセル %d"
              % (counts.get("表1_行"), counts.get("表2_行"),
                 counts.get("表3_行"), len(cells)))
        print("**年度の字が判定に使われている所: %d 件**"
              % len(rec["診断: 年度の字で動いている所"]["判定に使っている"]))
        for s in rec["診断: 年度の字で動いている所"]["判定に使っている"]:
            print("   %s:%d %s" % (s["file"], s["行"], s["字"][:80]))
        print("字(説明・指示文)の数: %d 件"
              % rec["診断: 年度の字で動いている所"]["字(説明・指示文)の数"])
        print("**parser を直して通さない。生成しない。**")
        print("->", OUT)
        return
    rec = {"seal": SEAL,
           "step": "封 §8 の 4。**費用 0 USD。生成していない**",
           "別資料": {"総括": PR.F.SOUKATU, "決算書 歳出": PR.F.KESSAN,
                   "事項別明細 歳出": PR.F.MEISAI,
                   "決算書 歳入": PR.F.SAINYUU,
                   "事項別明細 歳入": PR.F.MEISAI_SAINYUU},
           "rule_source": "measure/sheet_m9_material_2026-10-16.py の build()",
           "**差し替えたのは読む file だけ**": True,
           "model": M9.MODEL, "runs": 0,
           "limits": {"extract_chars": M9.MAX_EXTRACT,
                      "report_chars": M9.MAX_REPORT},
           "counts": counts, "value_cells": len(cells),
           "alias_forms_in_extract": forms,
           "stop_check": stop,
           "alias": {"通った": b["alias_passed"],
                     "未確認の別名": b["unconfirmed_alias"]},
           "段 11 との比べ(**同じ表に混ぜない。形の確認だけ**)": {
               "段 11 の抜粋の字数": len(old["prompt"]),
               "令和５年度の抜粋の字数": len(prompt),
               "段 11 の値のセル": old["value_cells"],
               "令和５年度の値のセル": len(cells)},
           "指示文が段 4 と同じ": prompt.count("----- 表(ここから) -----") == 1,
           "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
           "prompt_chars": len(prompt),
           "prompt": prompt,
           "extract_chars": len(extract),
           "下見の費用": estimate(),
           "次の段": ("**人間に費-1 / 費-2 の判断を求める。**"
                   "許可が出てから報告文を 1 回だけ生成する(封 §8 の 5・6)"),
           "limits_note": [
               "**生成していない。**この記録は指示文までである。",
               "**除外する標本(段 4〜段 9)は令和６年度の値なので、"
               "令和５年度ではほとんど当たらない。**規則は変えずにそのまま呼んだ。",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 別資料(令和５年度)の抜粋(費用 0。生成していない)===")
    print("抜粋 %d 字 / 値のセル %d / 指示文 %d 字"
          % (len(extract), len(cells), len(prompt)))
    print("counts: %s" % json.dumps(counts, ensure_ascii=False))
    print("別名: 通った %s / 未確認 %s"
          % (b["alias_passed"], b["unconfirmed_alias"]))
    print("抜粋に在る別名の形: %s" % json.dumps(forms, ensure_ascii=False)[:200])
    print("stop_check: %s" % json.dumps(stop, ensure_ascii=False))
    print("段 11: 抜粋 %d 字 / 値のセル %d" % (len(old["prompt"]),
                                       old["value_cells"]))
    print("**下見の費用: %s**" % json.dumps(rec["下見の費用"], ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
