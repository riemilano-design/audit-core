# -*- coding: utf-8 -*-
"""誤りを**機械の規則で**植える(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §2)。

**生成しない。凍結した報告文の金額を 1 つだけ置き換えるだけ。費用 0 USD。**

  対象   = 各文の「正解集合に在る最小 id の主張」(**文 17 は使わない** ― R035 の罠)
  型     = 群 I(I-1 桁の入れ替え / I-2 末尾 1 桁)・群 II(II-1 列 / II-2 別の科目)
  割り当て = **型を「作れる文の数」の昇順**に並べ、各型に
             **結べた主張の文 1 つと結べなかった主張の文 1 つ**(番号の昇順)

**正解ラベルは改変前の原資料(抜粋の行)と、ここで作る改変記録から確定する。**
**Core の判定規則を使わない。**

**1 つの変種は 1 つの誤りだけ。**別に「束ねた変種」(8 件を 8 つの文に)を作るが、
**同じ文に 2 件入れない。**束ねたことで結果が変わらないかは Core 側で突き合わせる。

    python3 measure/sheet_errdet_make_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
REPORT = os.path.join(FX, "m11_report_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
OUT = os.path.join(FX, "errdet_make_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"

SKIP_SENTENCE = 17                 # **R035 の罠が在る文。使わない**(封 §2-1 の 3)
TRAP_ID = "R035"
# **列の候補の順は封 §2-2 の字のまま**
COLUMN_ORDER = ("支出済額", "予算現額", "不用額", "補正予算額")
TYPES = ("I-1", "I-2", "II-1", "II-2")   # 同数のときの並び(封 §2-3 の 2)
GROUP = {"I-1": "群 I", "I-2": "群 I", "II-1": "群 II", "II-2": "群 II"}
KIND = {"I-1": "値が原資料に無い", "I-2": "値が原資料に無い",
        "II-1": "列の取り違え", "II-2": "別の科目の値"}


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RUN = _mod("run11_for_errdet", "sheet_m11_run_2026-10-16.py")
SE = RUN.NEW
M7 = SE.M7
OLD = M7.OLD
M2 = RUN.M2
OPP = _mod("opp9_for_errdet", "sheet_m9_opportunity_2026-10-16.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def comma(n):
    """表記を作る。**カンマ区切り + 円。桁数は変えない**(封 §2-2)。"""
    return "{:,}円".format(n)


# --------------------------------------------------------------- 型ごとの値
def swap_digits(v):
    """**I-1**: 十進表記の 2 桁目と 3 桁目を入れ替える。同じ数字なら次の組へ。

    候補を**順に**返す(後条件に落ちたら次へ。封 §2-2)。
    """
    s = str(abs(v))
    out = []
    for i in range(1, len(s) - 1):
        if s[i] == s[i + 1]:
            continue
        t = list(s)
        t[i], t[i + 1] = t[i + 1], t[i]
        if t[0] == "0":
            continue
        out.append(int("".join(t)) * (1 if v >= 0 else -1))
    return out


def last_digit(v):
    """**I-2**: 末尾の桁に +1(9 なら −1)。落ちたら +2…+9(封 §2-2)。"""
    out = []
    base = abs(v)
    first = base - 1 if base % 10 == 9 else base + 1
    out.append(first)
    for d in range(2, 10):
        out.append(base + d)
    return [x * (1 if v >= 0 else -1) for x in out]


def other_column(cell, cells):
    """**II-1**: 同じ行の別の列の値。候補の順は `COLUMN_ORDER`。"""
    same = [c for c in cells
            if c["scope"] == cell["scope"] and c["level"] == cell["level"]
            and (c["parent"] or "") == (cell["parent"] or "")
            and c["name"] == cell["name"]]
    by = {c["column"]: c for c in same}
    return [by[col]["value"] for col in COLUMN_ORDER
            if col in by and col != cell["column"]]


def other_row(cell, cells):
    """**II-2**: 同じ会計・同じ階層・同じ列の別の行の値(抜粋の並び順)。"""
    return [c["value"] for c in cells
            if c["scope"] == cell["scope"] and c["level"] == cell["level"]
            and c["column"] == cell["column"] and c["name"] != cell["name"]]


def candidates_for(kind, cell, cells):
    if kind == "I-1":
        return swap_digits(cell["value"])
    if kind == "I-2":
        return last_digit(cell["value"])
    if kind == "II-1":
        return other_column(cell, cells)
    if kind == "II-2":
        return other_row(cell, cells)
    raise AssertionError("知らない型: %s" % kind)


def ok_value(kind, v, cell, cells, index_values, sentence_values):
    """**後条件**(封 §2-2)。(通るか, 落ちた理由) を返す。**判定を 1 か所に置く。**"""
    if v == cell["value"]:
        return False, "正しい参照先の値と同じ"
    if v in sentence_values:
        return False, "同じ文に既に出ている数"
    in_excerpt = any(c["value"] == v for c in cells)
    if GROUP[kind] == "群 I":
        if in_excerpt:
            return False, "抜粋に在る(群 I は原資料に無い値でなければならない)"
        if v in index_values:
            return False, "索引 4,209 行に在る(群 I は原資料に無い値でなければならない)"
        return True, None
    if not in_excerpt:
        return False, "抜粋に無い(群 II は原資料に在る値でなければならない)"
    return True, None


def pick_value(kind, cell, cells, index_values, sentence_values):
    """候補を順に当て、**最初に後条件を通ったもの**を返す。"""
    tried = []
    for v in candidates_for(kind, cell, cells):
        ok, why = ok_value(kind, v, cell, cells, index_values, sentence_values)
        tried.append({"値": v, "通ったか": ok, "落ちた理由": why})
        if ok:
            return v, tried
    return None, tried


# --------------------------------------------------------------- 置き換え
def amount_spans(text):
    """金額の出現を**順に**返す。**k 番目の出現が k 番目の主張**であることを確かめる。"""
    return [(m.start(), m.end(), m.group(0)) for m in OLD.AMOUNT.finditer(text)]


def check_alignment(text, claims):
    sp = amount_spans(text)
    if len(sp) != len(claims):
        raise AssertionError("金額の数が主張の数と違う: %d != %d"
                             % (len(sp), len(claims)))
    for (_s, _e, got), c in zip(sp, claims):
        if got != c["text"]:
            raise AssertionError("%s の表記が違う: %r != %r"
                                 % (c["id"], got, c["text"]))
    return True


def replace_at(text, claims, repl):
    """`repl` = {claim_id: 新しい表記}。**後ろから置き換える**(位置がずれないように)。"""
    sp = amount_spans(text)
    idx = {c["id"]: i for i, c in enumerate(claims)}
    out = text
    for cid in sorted(repl, key=lambda x: -idx[x]):
        s, e, _g = sp[idx[cid]]
        out = out[:s] + repl[cid] + out[e:]
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(作り直さない)" % OUT)
    shas = RUN.check_shas()
    report = load(REPORT)["report"]
    mat = load(MAT)
    cells = OPP.cells_of(OPP.extract_of(mat))
    rec_in = load(BINDS)
    claims = rec_in["claims"]
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    gold = {r["id"]: r for r in load(GOLD)["rows"]}
    check_alignment(report, claims)

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    raw = M7.fix_total_level(M7.build_index(*args))
    index_values = {e["value"] for e in raw}

    by_sent = collections.defaultdict(list)
    for c in claims:
        by_sent[c["sentence_index"]].append(c)
    sent_values = {si: {c["value"] for c in cs} for si, cs in by_sent.items()}

    # ---------------------------------------------------- 対象(封 §2-1)
    targets = []
    for si in sorted(by_sent):
        if si == SKIP_SENTENCE:
            continue
        ids = [c["id"] for c in sorted(by_sent[si], key=lambda x: x["id"])
               if gold[c["id"]]["正解"]]
        if ids:
            targets.append({"文": si, "id": ids[0],
                            "結べた": bn[ids[0]]["state"] == "GROUNDED"})
    claim_of = {c["id"]: c for c in claims}

    # ---------------------------------------------------- 作れるか(封 §2-2)
    feasible, tried_log = {}, {}
    for kind in TYPES:
        feasible[kind] = {}
        for t in targets:
            cid = t["id"]
            g = gold[cid]["正解"]
            cell = {"scope": g["会計(印字)"], "level": g["階層"],
                    "parent": g["親"], "name": g["科目名"],
                    "column": g["列"], "value": g["値"]}
            v, tried = pick_value(kind, cell, cells, index_values,
                                  sent_values[t["文"]] - {g["値"]})
            tried_log[(kind, cid)] = tried
            if v is not None:
                feasible[kind][t["文"]] = {"id": cid, "値": v, "cell": cell}
    order = sorted(TYPES, key=lambda k: (len(feasible[k]), TYPES.index(k)))

    # ---------------------------------------------------- 割り当て(封 §2-3)
    used, planted, failed = set(), [], []
    strat = {t["文"]: t["結べた"] for t in targets}
    for kind in order:
        for want in (True, False):
            pick = None
            for si in sorted(feasible[kind]):
                if si in used or strat[si] != want:
                    continue
                pick = si
                break
            if pick is None:
                failed.append({"型": kind, "層": "結べた" if want else "結べなかった",
                               "理由": "作れる未使用の文が無い"})
                continue
            used.add(pick)
            f = feasible[kind][pick]
            cid = f["id"]
            planted.append({
                "id": cid, "文": pick, "型": kind, "群": GROUP[kind],
                "誤りの種類(正解ラベル)": KIND[kind],
                "Core が結べた主張か": strat[pick],
                "元の値": claim_of[cid]["value"], "元の表記": claim_of[cid]["text"],
                "植えた値": f["値"], "植えた表記": comma(f["値"]),
                "正しい参照先(改変前)": gold[cid]["正解"],
                "候補の試行": tried_log[(kind, cid)]})
    planted.sort(key=lambda x: x["id"])

    # ---------------------------------------------------- 変種を作る
    variants = []
    for p in planted:
        text = replace_at(report, claims, {p["id"]: p["植えた表記"]})
        variants.append({"名前": "1 件だけ: %s / %s" % (p["id"], p["型"]),
                         "誤りの id": [p["id"]], "本文": text,
                         "字数": len(text)})
    bundle_repl = {p["id"]: p["植えた表記"] for p in planted}
    bundle = replace_at(report, claims, bundle_repl)
    sentences_used = sorted({p["文"] for p in planted})
    if len(sentences_used) != len(planted):
        raise SystemExit("**同じ文に 2 件入っている。封 §1-1 の違反**")

    rec = {"seal": SEAL, "step": "封 §8 の 2。**生成しない。費用 0 USD**",
           "engine_sha": shas,
           "元の報告文": {"字数": len(report), "主張": len(claims)},
           "対象の候補(各文の正解集合の最小 id)": targets,
           "**文 17 を使わない理由**": ("`%s`(文面の「マイナス」)の罠が在る。"
                              "同じ文に誤りを足すと罠と干渉する(封 §2-1 の 3)"
                              % TRAP_ID),
           "型の並び(作れる文の数の昇順)": [
               {"型": k, "作れる文": sorted(feasible[k])} for k in order],
           "植えた誤り": planted,
           "植えた件数": len(planted),
           "作れなかった組み合わせ": failed,
           "型ごとの件数": dict(collections.Counter(p["型"] for p in planted)),
           "層ごとの件数": {"結べた": sum(1 for p in planted
                                 if p["Core が結べた主張か"]),
                      "結べなかった": sum(1 for p in planted
                                  if not p["Core が結べた主張か"])},
           "使った文": sentences_used,
           "束ねた変種": {"誤りの id": sorted(bundle_repl), "本文": bundle,
                    "字数": len(bundle),
                    "注": "**8 件を 8 つの別々の文に入れた。同じ文に 2 件入れない**"},
           "1 件ずつの変種": variants,
           "罠": {"id": TRAP_ID,
                 "注": ("**文書は正しい。`extract_claims` が符号を落とす。**"
                       "**検出率の分母に入れない。偽警報の側で別に数える**"
                       "(封 §2-4)")},
           "正解ラベルの出どころ": ("**改変前の原資料(抜粋の行)とこの改変記録。**"
                          "**Core の判定規則を使っていない**"),
           "層化の開示": ("**層化(結べた / 結べなかった)に Core の結果を使った。"
                     "正解ラベルには使っていない**(封 §2-3 の 4)")}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 誤りを機械の規則で植えた(生成しない。費用 0)===")
    print("対象の候補: %s" % [(t["文"], t["id"], "結" if t["結べた"] else "保")
                        for t in targets])
    print("型の並び(作れる文の数の昇順): %s"
          % [(k, len(feasible[k])) for k in order])
    print("**植えた誤り %d 件**(型ごと %s / 層ごと %s)"
          % (len(planted), json.dumps(rec["型ごとの件数"], ensure_ascii=False),
             json.dumps(rec["層ごとの件数"], ensure_ascii=False)))
    for p in planted:
        print("  %s 文%-2d %-4s %-8s %s: %s -> %s"
              % (p["id"], p["文"], p["型"], p["群"],
                 "結べた" if p["Core が結べた主張か"] else "結べなかった",
                 p["元の表記"], p["植えた表記"]))
    if failed:
        print("**作れなかった組み合わせ: %s**"
              % json.dumps(failed, ensure_ascii=False))
    print("束ねた変種: %d 字 / 使った文 %s" % (len(bundle), sentences_used))
    print("->", OUT)


if __name__ == "__main__":
    main()
