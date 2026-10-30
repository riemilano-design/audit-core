# -*- coding: utf-8 -*-
"""候補範囲を絞った**代価**を人工材料で測る(封 docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md §3)。

**候補を絞れば曖昧さが減るのは当たり前で、消えた分の代価を測らないと片側しか見ていない。**

| 歯 | 人工の主張 | 測ること |
|---|---|---|
| **歯-A** | **抜粋に無い行**の値を主張(その値は抜粋のどこにも無い) | 限定は**結べない**か、誤って結ぶか |
| **歯-B** | **真の参照先は抜粋の外**だが、**同じ値が抜粋の中にも在る** | 限定は**抜粋の中の別の行に誤接続するか** |

**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**(人間の指示)。
**この歯は engine の安全性を示すものではない。絞った代価の形を見るものである。**

    python3 measure/sheet_scope76_teeth_2026-10-17.py
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
OUT = os.path.join(FX, "scope76_teeth_2026-10-17.json")
SEAL = "docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


S76 = _mod("s76_for_teeth", "sheet_scope76_2026-10-17.py")
M7 = S76.M7
M2 = S76.M2
norm = S76.norm
OPP = S76.OPP


def sentence_for(e, value):
    """人工の主張の文を**行の字から機械で**作る(私が手で書かない)。"""
    kan, _, ko = (e["parent"] or "").partition(" > ")
    head = "%sの" % e["scope"]
    if kan:
        head += "%sのうち" % kan
    if ko:
        head += "%sの" % ko
    return "%s%sは%sが%s円であった" % (head, e["name"], e["column"],
                                "{:,}".format(value))


def pick_outside(entries, cells):
    """**歯-A の材料**: 抜粋に無い行で、**その値も抜粋のどこにも無い**もの。"""
    in_vals = {c["value"] for c in cells}
    keys = {(norm(c["scope"]), norm(c["level"]), norm(c["parent"]) or "",
             norm(c["name"]), norm(c["column"]), c["value"]) for c in cells}
    names = {norm(c["name"]) for c in cells}
    for e in entries:
        k = (norm(e["scope"]), norm(e["level"]), norm(e["parent"]) or "",
             norm(e["name"]), norm(e["column"]), e["value"])
        if k in keys or e["value"] in in_vals or not e["name"]:
            continue
        if norm(e["name"]) in names or e["value"] is None or e["value"] == 0:
            continue
        return e
    return None


def pick_collision(entries, cells):
    """**歯-B の材料**: 抜粋の外の行で、**同じ値が抜粋の中にも在る**もの。

    返すのは (抜粋の外の行, 抜粋の中の同じ値の行たち)。
    **無ければ None** ―「この材料では作れない」と記録する(封 §3)。
    """
    by_val = collections.defaultdict(list)
    for c in cells:
        if c["value"]:
            by_val[c["value"]].append(c)
    keys = {(norm(c["scope"]), norm(c["level"]), norm(c["parent"]) or "",
             norm(c["name"]), norm(c["column"]), c["value"]) for c in cells}
    for e in entries:
        if not e["name"] or not e["value"]:
            continue
        k = (norm(e["scope"]), norm(e["level"]), norm(e["parent"]) or "",
             norm(e["name"]), norm(e["column"]), e["value"])
        if k in keys:
            continue
        if e["value"] in by_val:
            return e, by_val[e["value"]]
    return None, None


def measure(e, cells, args, label):
    """人工の 1 文を**両プロファイル**に当てる。**同じ関数で両方**。"""
    text = sentence_for(e, e["value"])
    r = S76.run_both(text, args, cells)
    out = {"歯": label, "文(機械で作った)": text,
           "真の参照先": {"会計": e["scope"], "階層": e["level"],
                    "親": e["parent"], "科目名": e["name"],
                    "列": e["column"], "値": e["value"],
                    "file": e["file"]},
           "切り出した主張": len(r["claims"])}
    for name, binds in (("対照群(索引 4,209 行)", r["full"]),
                        ("限定(抜粋 76 行)", r["limited"])):
        if not binds:
            out[name] = {"状態": "**主張が切り出されなかった**"}
            continue
        b = binds[0]
        ev = b.get("evidence") or {}
        out[name] = {"状態": b["state"], "候補": b.get("candidates"),
                     "鍵の通り": b.get("distinct_keys"),
                     "保留の理由": b.get("hold_reason"),
                     "結んだ行": ({"会計": ev.get("scope"), "科目名": ev.get("name"),
                                "列": ev.get("column"), "値": ev.get("value")}
                               if b["state"] == "GROUNDED" else None)}
    f, l = out["対照群(索引 4,209 行)"], out["限定(抜粋 76 行)"]
    same = (l.get("結んだ行") or {}).get("科目名") == e["name"] \
        if l["状態"] == "GROUNDED" else None
    out["限定が誤った行に結んだか"] = (None if l["状態"] != "GROUNDED"
                            else (not same))
    out["代価の形"] = ("**誤接続**" if out["限定が誤った行に結んだか"]
                   else ("**正しく結んだ**" if l["状態"] == "GROUNDED"
                         else "**結べない(見落とし)**"))
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP.cells_of(OPP.extract_of(mat))
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    base = S76.run_both("", args, cells)
    entries = base["all_entries"]

    a = pick_outside(entries, cells)
    b, hits = pick_collision(entries, cells)
    res = []
    if a is not None:
        res.append(measure(a, cells, args, "歯-A 抜粋に無い行(値も抜粋に無い)"))
    if b is not None:
        rec_b = measure(b, cells, args, "歯-B 真の参照先は抜粋の外・同じ値が抜粋にも在る")
        rec_b["抜粋の中の同じ値の行"] = [
            {k: h[k] for k in ("scope", "level", "parent", "name", "column",
                               "value")} for h in (hits or [])[:3]]
        res.append(rec_b)

    rec = {"seal": SEAL, "artificial": True,
           "step": "封 §3・§7 の 4。**人工材料。費用 0 USD**",
           "**この歯は engine の安全性を示すものではない**":
               ("**絞った代価の形**を見るものである。"
                "**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**"
                "(人間の指示 2026-10-17)"),
           "歯-B の材料は在ったか": b is not None,
           "歯-B が作れない場合の扱い": "**この材料では作れないと書く**(封 §3)",
           "候補": {"索引": len(entries), "抜粋の値のセル": len(cells)},
           "結果": res,
           "代価の形のまとめ": {x["歯"]: x["代価の形"] for x in res},
           "limits": [
               "**人工の 1 文ずつである。実データにこの形は無い** ― "
               "報告文は抜粋だけから書かれたため",
               "**文は行の字から機械で作った。**私が手で書いて誘導していない",
               "**「結べない」は安全側の代価であって、安全の証拠ではない。**"
               "網羅性が要る業務では**見落とし**そのものが損害になりうる",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 絞った代価(人工材料)===")
    print("歯-B の材料は在ったか:", b is not None)
    for x in res:
        print("\n%s" % x["歯"])
        print("  文: %s" % x["文(機械で作った)"])
        print("  真の参照先: %s / %s / %s"
              % (x["真の参照先"]["会計"], x["真の参照先"]["科目名"],
                 x["真の参照先"]["列"]))
        print("  対照群: %s" % json.dumps(x["対照群(索引 4,209 行)"],
                                       ensure_ascii=False))
        print("  限定  : %s" % json.dumps(x["限定(抜粋 76 行)"],
                                        ensure_ascii=False))
        print("  **代価の形: %s**" % x["代価の形"])
    print("\n->", OUT)


if __name__ == "__main__":
    main()
