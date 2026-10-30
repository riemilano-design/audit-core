# -*- coding: utf-8 -*-
"""X-2 の計数器(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §4)。**3 通りで数える。**

人間の必須条件:

> **X-2 を独立して評価する。**抜粋の印字と正本の表記の違いを、採点器とエンジンで
> 非対称に扱わない。**どちらかに不利な正規化を施して性能を演出しない。**

| 記号 | 数え方 | 使い道 |
|---|---|---|
| **X-2対称** | 抜粋と engine の**両側**に、その engine の別名表を当ててから比べる | **合否** |
| **X-2非対称** | 段 9 の素の 4 欄(抜粋の字そのまま) | **開示だけ** |
| **X-2三欄** | **会計を外し** `(階層, 親, 科目名)` だけ(**別名表に依らない**) | **裏取り** |

**鍵の作り方は 1 か所しか持たない** ― `sheet_m11_opportunity_2026-10-16.py` の
`key4` / `alias_fold` を呼ぶ(門つき)。**同じ関数を両側に当てることが対称性である。**
engine の出力は既に正本なので畳み込みは**冪等**であり、
**「engine にだけ別の正規化を掛ける」ことをしていない。**

  usage: import して `count(binds, cells, alias_table)` を呼ぶ
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


OPP11 = _mod("m11opp_for_x2", "sheet_m11_opportunity_2026-10-16.py")
key4 = OPP11.key4
alias_fold = OPP11.alias_fold
norm = OPP11.norm


def _cell_keys(cells, fold):
    return {key4(c["scope"], c["level"], c["parent"], c["name"], fold)
            for c in cells}


def _three(k4):
    """会計を外した 3 欄。**別名表に依らない**(封 §4)。"""
    return k4[1:]


def count(binds, cells, alias_table):
    """結んだ主張のうち**抜粋に無い行**に結んだものを 3 通りで数える。

    `binds` は `{claim_id: bind}`。GROUNDED だけを見る(結んでいないものは対象外)。
    **判定を 1 か所に置く** ― 字で書くと「全部抜粋の中」の材料で変異が黙る。
    """
    fold = alias_fold(alias_table)
    sym = _cell_keys(cells, fold)
    raw = _cell_keys(cells, {})
    three = {_three(k) for k in sym} | {_three(k) for k in raw}
    out = {"X-2対称": 0, "X-2非対称": 0, "X-2三欄": 0,
           "X-1対称": 0, "結んだ主張": 0,
           "X-2対称の明細": [], "X-2非対称の明細": [], "X-2三欄の明細": []}
    for cid in sorted(binds):
        b = binds[cid]
        if b.get("state") != "GROUNDED":
            continue
        ev = b.get("evidence") or {}
        out["結んだ主張"] += 1
        ks = key4(ev.get("scope"), ev.get("level"), ev.get("parent"),
                  ev.get("name"), fold)
        kr = key4(ev.get("scope"), ev.get("level"), ev.get("parent"),
                  ev.get("name"), {})
        if ks in sym:
            out["X-1対称"] += 1
        else:
            out["X-2対称"] += 1
            out["X-2対称の明細"].append({"id": cid, "engine_row": list(ks)})
        if kr not in raw:
            out["X-2非対称"] += 1
            out["X-2非対称の明細"].append({"id": cid, "engine_row": list(kr)})
        if _three(ks) not in three:
            out["X-2三欄"] += 1
            out["X-2三欄の明細"].append({"id": cid, "engine_row": list(_three(ks))})
    for k in ("X-2対称の明細", "X-2非対称の明細", "X-2三欄の明細"):
        out[k] = out[k][:10]
    return out


def verdict(counts):
    """封 §6 の線。**合否の判定を 1 か所に置く。**"""
    if counts.get("結んだ主張", 0) == 0:
        return {"判定": "**未測定**(結んだ主張が 0 件)", "合格": False,
                "理由": "数えられないので合格の根拠に含めない(封 §8)"}
    ok = counts["X-2対称"] == 0 and counts["X-2三欄"] == 0
    return {"判定": "合格" if ok else "**不合格**", "合格": ok,
            "理由": ("X-2対称 = %d 件・X-2三欄 = %d 件(線はどちらも 0 件)。"
                     "**非対称 = %d 件は開示だけで、性能として書かない**"
                     % (counts["X-2対称"], counts["X-2三欄"],
                        counts["X-2非対称"]))}
