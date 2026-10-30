# -*- coding: utf-8 -*-
"""候補範囲を抜粋 76 行に限定する実験(封 docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md)。

**規則は 1 つも変えない。`bind` に渡す候補の母集団だけ変える。費用 0 USD。**

  対照群 = 索引 4,209 行(段 11 の B。凍結済み)
  限定   = **抜粋 76 行に在る行だけ**

**語彙・列の手がかり・主張の切り出しは索引全体から作る**(封 §1-2)。
ここを限定すると主張そのものが変わり、件ごとの比較ができなくなる。
**`extract_claims` が 35 件でなければ実験を無効にする。**

判定は **R-4(一意に接続したもののうち正解集合と一致した数)**。
**R-3 が増えても R-4 が増えなければ成功と書かない。**

    python3 measure/sheet_scope76_2026-10-17.py
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
OUT = os.path.join(FX, "scope76_2026-10-17.json")
SEAL = "docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RUN = _mod("run11_for_s76", "sheet_m11_run_2026-10-16.py")
SE = RUN.NEW                      # 歳入側の engine(段 11 の B)
M7 = SE.M7
M2 = RUN.M2
norm = RUN.norm
S = _mod("abscore_for_s76", "sheet_poc_ab_score_2026-10-17.py")
OPP = RUN.OPP


def excerpt_keys(cells, fold):
    """抜粋の行の鍵。**会計は engine と同じ別名表で畳む**(封 §1-3)。"""
    out = set()
    for c in cells:
        s = norm(c["scope"])
        out.add((fold.get(s, s), norm(c["level"]), norm(c["parent"]) or "",
                 norm(c["name"]), norm(c["column"]), c["value"]))
    return out


def entry_key(e, fold):
    s = norm(e["scope"])
    return (fold.get(s, s), norm(e["level"]), norm(e["parent"]) or "",
            norm(e["name"]), norm(e["column"]), e["value"])


def restrict(entries, keys, fold):
    """**候補の母集団だけを絞る。**判定を 1 か所に置く(字で書くと変異が黙る)。"""
    return [e for e in entries if entry_key(e, fold) in keys]


def run_both(text, args, cells):
    """対照群と限定プロファイルを**同じ呼び出し順**で走らせる。

    `M7.run` と同じ順。**違いは `bind` に渡す候補だけ。**
    """
    raw = M7.fix_total_level(M7.build_index(*args))
    al = SE.alias_table(raw)                    # **段 11 と同じ別名表**
    entries = M7.canonicalize(raw, al)
    cues = M7.column_cues(entries)              # **索引全体から作る(封 §1-2)**
    vocab = M7.vocabulary(entries)
    claims = M7.extract_claims(text, vocab, cues)
    fold = {norm(k): norm(v["canonical"]) for k, v in al["table"].items()}
    keys = excerpt_keys(cells, fold)
    cand = restrict(entries, keys, fold)
    full = [M7.bind(c, entries) for c in claims]
    lim = [M7.bind(c, cand) for c in claims]
    return {"claims": claims, "full": full, "limited": lim,
            "entries": len(entries), "candidates": len(cand),
            "excerpt_keys": len(keys), "alias": al, "fold": fold,
            "all_entries": entries}


def state_of(b):
    return b["state"]


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    shas = RUN.check_shas()
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP.cells_of(OPP.extract_of(mat))
    gold = {r["id"]: r for r in json.load(io.open(GOLD, encoding="utf-8"))["rows"]}
    frozen = json.load(io.open(BINDS, encoding="utf-8"))
    fb = {b["claim_id"]: b for b in frozen["binds_new"]}

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    r = run_both(report, args, cells)
    claims = {c["id"]: c for c in r["claims"]}
    if len(claims) != 35:
        raise SystemExit("**主張が %d 件。35 件でないので実験は無効**" % len(claims))
    full = {b["claim_id"]: b for b in r["full"]}
    lim = {b["claim_id"]: b for b in r["limited"]}
    # **対照群が凍結した記録と一致すること**(呼び出し順が同じことの確認)
    diff = [cid for cid in full
            if full[cid]["state"] != fb[cid]["state"]]
    if diff:
        raise SystemExit("**対照群が段 11 の記録と違う: %s**" % diff)

    rows, r2 = [], []
    for cid in sorted(claims):
        g = gold[cid]
        fs, ls = state_of(full[cid]), state_of(lim[cid])
        row = {"id": cid, "正解集合か": bool(g["正解"]),
               "対照群": {"状態": fs, "候補": full[cid].get("candidates"),
                       "鍵の通り": full[cid].get("distinct_keys"),
                       "保留の理由": full[cid].get("hold_reason")},
               "限定": {"状態": ls, "候補": lim[cid].get("candidates"),
                      "鍵の通り": lim[cid].get("distinct_keys"),
                      "保留の理由": lim[cid].get("hold_reason")}}
        if ls == "GROUNDED":
            ev = lim[cid].get("evidence") or {}
            ans = {"会計": ev.get("scope"), "階層": ev.get("level"),
                   "親": ev.get("parent"), "科目名": ev.get("name"),
                   "列": ev.get("column"), "値": ev.get("value")}
            row["限定の参照先"] = ans
            row["限定が正解と一致"] = (S.same_row(ans, g["正解"])
                               if g["正解"] else None)
        rows.append(row)
        if fs != "GROUNDED" and bool(g["正解"]):
            r2.append(row)

    r3 = [x for x in r2 if x["限定"]["状態"] == "GROUNDED"]
    r4 = [x for x in r3 if x.get("限定が正解と一致")]
    wrong = [x for x in r3 if x.get("限定が正解と一致") is False]
    broke = [x for x in rows
             if x["対照群"]["状態"] == "GROUNDED" and x["限定"]["状態"] != "GROUNDED"]
    moved = [x for x in rows
             if x["対照群"]["状態"] == "GROUNDED" and x["限定"]["状態"] == "GROUNDED"
             and x.get("限定が正解と一致") is False]
    apart4 = [x for x in rows if not x["正解集合か"]
              and x["対照群"]["状態"] == "GROUNDED"]
    apart_changed = [x for x in apart4 if x["限定"]["状態"] != "GROUNDED"]

    rec = {"seal": SEAL, "step": "封 §7 の 2・3。**費用 0 USD**",
           "engine_sha": shas, "min_independent": SE.MIN_INDEPENDENT,
           "変えたもの": "**`bind` に渡す候補の母集団だけ**",
           "変えていないもの": ["6 欄の鍵", "接続の一意性条件", "別名規則",
                        "親の規則", "語彙", "列の手がかり", "主張の切り出し"],
           "主張の数": len(claims),
           "対照群が段 11 の記録と一致": not diff,
           "R-1 候補に残った行": {"索引の行": r["entries"],
                          "候補": r["candidates"],
                          "抜粋の鍵": r["excerpt_keys"],
                          "抜粋の値のセル": len(cells)},
           "R-2 保留 12 件それぞれ": r2,
           "R-3 一意に接続した": {"件数": len(r3), "ids": [x["id"] for x in r3]},
           "R-4 **判定** 正解と一致した": {"件数": len(r4),
                               "ids": [x["id"] for x in r4]},
           "R-3 のうち正解と違った(**誤接続**)": {"件数": len(wrong),
                                    "ids": [x["id"] for x in wrong]},
           "R-5 既存の接続": {"壊れた": [x["id"] for x in broke],
                        "別の行に動いて誤接続になった": [x["id"] for x in moved],
                        "注": "**壊れた件数を接続数の増加で相殺しない**"},
           "R-6 別枠で推測していた件": {"件数": len(apart4),
                             "ids": [x["id"] for x in apart4],
                             "状態が変わった": [x["id"] for x in apart_changed]},
           "判定": ("**R-4 = %d 件。R-3 = %d 件。**%s"
                  % (len(r4), len(r3),
                     "**候補範囲の限定は効いた**" if len(r4) >= 1 and not broke
                     else "**効かなかった / 既存が壊れた**")),
           "注": ("**候補を絞れば曖昧さが減るのは当たり前である**(封 §6 の 1)。"
                 "**R-4 が増えても「engine が良くなった」とは書かない。**"
                 "「**母集団を変えると解ける**」である"),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 候補範囲を抜粋 76 行に限定(規則は変えていない)===")
    print("索引 %d 行 → 候補 %d 行(抜粋の鍵 %d / 値のセル %d)"
          % (r["entries"], r["candidates"], r["excerpt_keys"], len(cells)))
    print("主張 %d 件・対照群は段 11 の記録と一致: %s"
          % (len(claims), not diff))
    print("**R-2 保留 12 件の変化:**")
    for x in r2:
        print("   %-5s 鍵の通り %s -> %s / %s -> %s%s"
              % (x["id"], x["対照群"]["鍵の通り"], x["限定"]["鍵の通り"],
                 x["対照群"]["状態"], x["限定"]["状態"],
                 "" if x["限定"]["状態"] != "GROUNDED"
                 else ("(正解と一致: %s)" % x.get("限定が正解と一致"))))
    print("**R-3 一意に接続 %d 件 / R-4 正解と一致 %d 件 / 誤接続 %d 件**"
          % (len(r3), len(r4), len(wrong)))
    print("**R-5 既存の接続が壊れた: %s / 誤接続に動いた: %s**"
          % ([x["id"] for x in broke] or "なし", [x["id"] for x in moved] or "なし"))
    print("R-6 別枠で推測していた %d 件のうち状態が変わった: %s"
          % (len(apart4), [x["id"] for x in apart_changed] or "なし"))
    print("**判定: %s**" % rec["判定"])
    print("->", OUT)


if __name__ == "__main__":
    main()
