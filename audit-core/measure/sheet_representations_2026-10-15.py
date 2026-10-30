# -*- coding: utf-8 -*-
"""材料の中で**同じ対象が 2 通り以上に書かれている欄**を、材料を作る前に洗い出す。

人間の指示(2026-10-15 の ②):
> 会計名だけでなく、今回の 6 欄すべてを対象にします。
> 同じ対象に複数の表記がある場合は、**どの表記を正本とするか**、**正規化できる条件は何か**、
> **対応関係が不明ならどう保留するか**を先に決めます。
> ただし、**文字列を揃えることと、対象が同一であることは別**です。
> **表記が違うだけで同一と決めたり、値が一致するだけで同一と決めたりしないでください。**

だからこの file は「候補を挙げる」ところまでしかやらない。
同一と**決める**のは、独立した裏づけ(別名表の 3 本)か、**表の構造そのもの**
(見出しの入れ子など)が在る欄だけ。無いものは `未確認` に置き、**保留にする。**
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "representations_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_rep", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm


def survey(entries, alias, meisai):
    """6 欄それぞれについて、表記が割れていないかを見る。"""
    out = {}

    # ---- 会計: 明細の表記と総括の表記。**独立した裏づけ 3 本で確かめたものだけ正本化**
    confirmed = {k: v["canonical"] for k, v in alias["table"].items()}
    unconfirmed = sorted(u["name"] for u in alias["unconfirmed"])
    out["会計"] = {
        "割れている": bool(confirmed) or bool(unconfirmed),
        "正本": "総括の表記",
        "正規化できる条件": "独立した裏づけ 3 本以上・食い違い 0(別名表)",
        "正規化する": confirmed,
        "未確認(保留にする)": unconfirmed,
        "決め方": "値の一致だけでは認めない。接尾一致 + 会計の層 + 独立 3 本",
    }

    # ---- 階層: 材料に書かれた語ではなく**構造から付けた名**。割れようがないので列挙で固定
    out["階層"] = {
        "割れている": False,
        "正本": "会計 / 合計 / 款 / 項 / 目 の 5 語だけ",
        "正規化できる条件": "―(列挙の外は受け取らない)",
        "決め方": "問いに 5 語を列挙し、他の語(款別 など)を書かせない",
    }

    # ---- 親: 区切りの書き方が割れうる。**区切りだけ**を正規化(名前は触らない)
    seps = collections.Counter()
    for e in entries:
        if e.get("parent") and ">" in e["parent"]:
            seps[" > " if " > " in e["parent"] else ">"] += 1
    out["親"] = {
        "割れている": len(seps) > 1,
        "正本": "「款名 > 項名」(半角の > と空白)",
        "正規化できる条件": "**区切りの空白だけ**を揃える。科目名そのものは揃えない",
        "材料の区切りの内訳": dict(seps),
        "決め方": "親の名前が読み取れなければ保留(問いの R-親-3)",
    }

    # ---- 科目名: 空白・全角半角の違いだけで割れていないか(**同一とは決めない**)
    groups = collections.defaultdict(set)
    for e in entries:
        if e["name"]:
            groups[norm(e["name"]).replace(" ", "").replace("　", "")].add(e["name"])
    split_names = {k: sorted(v) for k, v in groups.items() if len(v) > 1}
    out["科目名"] = {
        "割れている": bool(split_names),
        "正本": "材料に書かれた字そのまま",
        "正規化できる条件": "**NFKC と前後の空白だけ。中の空白や字を変えない**",
        "空白・全角半角だけ違う組": split_names,
        "決め方": "同じ字に見えても別の行なら別の対象。**名前では同一と決めない**",
    }

    # ---- 列: 決算書の `予算現額` と明細の `計` のように**file で見出しが違う**ことがある
    by_row = collections.defaultdict(dict)
    for e in entries:
        if e["name"] and e["level"] in ("款", "項"):
            by_row[(e["scope"], e["level"], norm(e["name"]))][norm(e["column"])] = e["value"]
    pair = collections.Counter()
    cols_by_file = collections.defaultdict(set)
    for e in entries:
        if e["column"]:
            cols_by_file[e["file"]].add(e["column"])
    # 同じ会計・同じ科目で、file をまたいで**値が等しい列の組**を数える(候補に挙げるだけ)
    kessan_cols = cols_by_file.get("決算書 歳出", set())
    meisai_cols = cols_by_file.get("事項別明細", set())
    rows_k = collections.defaultdict(dict)
    rows_m = collections.defaultdict(dict)
    for e in entries:
        if not (e["name"] and e["level"] in ("款", "項")):
            continue
        key = (e["scope"], e["level"], norm(e["name"]))
        if e["file"] == "決算書 歳出":
            rows_k[key][norm(e["column"])] = e["value"]
        elif e["file"] == "事項別明細":
            rows_m[key][norm(e["column"])] = e["value"]
    for key in set(rows_k) & set(rows_m):
        for ck, vk in rows_k[key].items():
            for cm, vm in rows_m[key].items():
                if ck != cm and vk == vm and vk is not None:
                    pair[(ck, cm)] += 1
    header_nesting = _meisai_header_nesting(meisai)
    cand = []
    for (ck, cm), n in sorted(pair.items(), key=lambda kv: -kv[1]):
        if n < 3:
            continue
        structural = header_nesting.get(cm)
        cand.append({"決算書": ck, "明細": cm, "値が一致した行": n,
                     "明細の見出しの入れ子": structural,
                     "同一と決めたか": bool(structural and norm(structural) == ck),
                     "理由": ("明細の見出しが `%s` の下に在る(構造の証拠)" % structural
                              if structural else
                              "値が一致しただけ。**同一と決めない**")})
    out["列"] = {
        "割れている": bool(cand),
        "正本": "見た表の見出しをそのまま(問いの R-列-2)",
        "正規化できる条件": "**見出しの入れ子が証拠に在る組だけ。値の一致では認めない**",
        "候補": cand,
        "決め方": "同一と決めない組は、別の列として採点する(席にもそう書く)",
    }

    # ---- 値: 全角・カンマ・円・△ を整数に直すだけ
    out["値"] = {
        "割れている": True,
        "正本": "円の整数",
        "正規化できる条件": "NFKC・カンマ・`円`・符号の `△` を落として整数にする",
        "決め方": "桁や単位を補わない。表に無い数は作らない",
    }
    return out


def _meisai_header_nesting(meisai):
    """明細の列見出しが、どの見出しの下に在るかを**表の構造から**取る。"""
    nest = {}
    for label, parent in getattr(M2, "MEISAI_COLS", {}).items():
        if isinstance(parent, str) and parent != label:
            # 例: "計" -> "予算現額(計)" のような注記から親の見出しを取る
            head = parent.split("(")[0].strip()
            if head and head != label:
                nest[norm(label)] = head
    return nest


def column_alias(meisai):
    """**見出しの入れ子という構造の証拠が在る列の組だけ**を返す({明細の字: 正本})。

    値が一致しただけの組は返さない(人間の指示 ②)。
    """
    nest = _meisai_header_nesting(meisai)
    return {k: v for k, v in nest.items() if v}


def main():
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    sk = M2.parse_soukatu(books[M2.SOUKATU])
    ks = M2.parse_kessan(books[M2.KESSAN])
    ms = M2.parse_meisai(books[M2.MEISAI])
    raw = E.fix_total_level(E.build_index(sk, ks, ms))
    alias = E.alias_table(raw)
    entries = E.canonicalize(raw, alias)
    rep = survey(entries, alias, ms)

    for k, v in rep.items():
        print("== %s / 割れている: %s" % (k, v["割れている"]))
        print("   正本: %s" % v["正本"])
        print("   正規化できる条件: %s" % v["正規化できる条件"])
        for extra in ("正規化する", "未確認(保留にする)", "候補",
                      "空白・全角半角だけ違う組", "材料の区切りの内訳"):
            if extra in v and v[extra]:
                s = json.dumps(v[extra], ensure_ascii=False)
                print("   %s: %s" % (extra, s if len(s) < 300 else s[:300] + "…"))
    rec = {"purpose": "6 欄の表記の割れを**材料を作る前に**洗い出す(人間の指示 ②)",
           "note": "文字列が似ているだけ・値が一致するだけで同一と決めない",
           "fields": rep}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
