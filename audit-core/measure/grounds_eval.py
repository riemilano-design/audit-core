# -*- coding: utf-8 -*-
"""独立ラベル(2 席一致の確定ラベル)に対する**根拠レベル**の採点。

engine の出力 ``{claim_id: {"state": ..., "pointers": [...]}}`` と、
``fixtures/xbrl/independent_grounds_labels_2026-10-13.json`` の確定ラベルを突き合わせ、
Claim ごとに「結んだ fact の集合がラベルの fact の集合と一致するか」を判定する。

- 一致 = (局所名, context) の**集合として完全一致**(厳密)。
- 同値類 v0 = 末尾の ``SummaryOfBusinessResults`` を落とし ``TotalAssets`` を ``Assets`` に
  読み替えた上での一致。**厳密と v0 は必ず併記する**(どちらか一方だけを出さない)。
- 解析できない pointer は 0 件と数えず ``AssertionError`` で止まる。

指標(分母はすべて確定ラベル L、または L のうち GROUNDED にした G):

- ``E1_strict``   根拠まで正しく通した件数(GROUNDED ∧ 厳密一致)
- ``E2_strict``   誤った根拠で通した件数(GROUNDED ∧ 厳密不一致)、``E2_v0`` は v0 版
- ``E3``          止めた件数(L のうち GROUNDED でない)

使い方::

    python3 measure/grounds_eval.py <dump.json> [<dump2.json> ...]
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS_PATH = os.path.join(os.path.dirname(HERE), "fixtures", "xbrl",
                           "independent_grounds_labels_2026-10-13.json")
LABELS_SHA256 = "1aa397f8c841c49e5b90de495062117eb17655c2d67b7887493ca517c91c7f79"

_SUMMARY_SUFFIX = "SummaryOfBusinessResults"
_ALIASES = {"TotalAssets": "Assets"}


def canon(local_name):
    """同値類 v0 の正規形。"""

    e = local_name
    if e.endswith(_SUMMARY_SUFFIX):
        e = e[:-len(_SUMMARY_SUFFIX)]
    return _ALIASES.get(e, e)


def parse_pointer(text):
    """``xbrl:<prefix>:<Local>@<context>`` -> ``(Local, context)``。fact でない
    (``builtin:``/``formula:``)なら ``None``。形に当たらなければ ``ValueError``。
    接頭辞は数字・ハイフンを含みうる(会社拡張)。"""

    if not text.startswith("xbrl:"):
        return None
    rest = text[5:]
    if ":" not in rest:
        raise ValueError(text)
    _prefix, rest2 = rest.split(":", 1)
    if "@" not in rest2:
        raise ValueError(text)
    local, context = rest2.split("@", 1)
    return (local, context)


def fact_set(pointers):
    out, bad = set(), []
    for p in pointers:
        try:
            t = parse_pointer(p)
        except ValueError:
            bad.append(p)
            continue
        if t is not None:
            out.add(t)
    if bad:
        raise AssertionError("unparseable pointers (%d): %r" % (len(bad), bad))
    return out


def load_labels(path=LABELS_PATH):
    """確定ラベルだけ ``{id: {"fact": set, "direction": bool, "exposure": bool}}``。"""

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    out = {}
    for row in data["labels"]:
        if not row["分類"].startswith("確定"):
            continue
        forms = row.get("形") or []
        form = forms[0] if forms else None
        out[row["id"]] = {
            "fact": set(tuple(x) for x in row["fact"]),
            "direction": form == "符号・方向",
            "exposure": bool(row.get("同値の他の候補")),
        }
    return out


def score(dump, labels):
    """Claim ごとの判定の列。``dump`` に無い id は ``state="MISSING"``。"""

    rows = []
    for cid, lab in labels.items():
        q = dump.get(cid)
        if q is None:
            rows.append({"id": cid, "state": "MISSING", "direction": lab["direction"]})
            continue
        arm = fact_set(q["pointers"])
        strict = (arm == lab["fact"])
        v0 = ({(canon(e), c) for e, c in arm} == {(canon(e), c) for e, c in lab["fact"]})
        rows.append({
            "id": cid, "state": q["state"], "strict": strict, "v0": v0,
            "direction": lab["direction"], "exposure": lab["exposure"],
            "arm": sorted(arm), "label": sorted(lab["fact"]),
            "subject": q.get("subject"), "span": q.get("span"), "reason": q.get("reason"),
        })
    return rows


def summarize(rows, select=None):
    """``select(row) -> bool`` で絞った行の指標(件数)。"""

    R = [r for r in rows if r["state"] != "MISSING" and (select is None or select(r))]
    G = [r for r in R if r["state"] == "GROUNDED"]
    return {
        "L": len(R),
        "G": len(G),
        "E1_strict": sum(1 for r in G if r["strict"]),
        "E2_strict": sum(1 for r in G if not r["strict"]),
        "E2_v0": sum(1 for r in G if not r["v0"]),
        "E3": len(R) - len(G),
        "MISSING": sum(1 for r in rows if r["state"] == "MISSING" and (select is None or select(r))),
    }


def report(rows, title):
    def line(name, m):
        g = m["G"] or 1
        L = m["L"] or 1
        return ("  %-8s L=%3d G=%3d  E1'=%3d (%5.1f%% of L)  E2厳密=%2d (%5.1f%% of G)  "
                "E2v0=%2d (%5.1f%% of G)  E3=%3d (%5.1f%% of L)"
                % (name, m["L"], m["G"], m["E1_strict"], 100.0 * m["E1_strict"] / L,
                   m["E2_strict"], 100.0 * m["E2_strict"] / g, m["E2_v0"], 100.0 * m["E2_v0"] / g,
                   m["E3"], 100.0 * m["E3"] / L))
    out = ["== %s ==" % title,
           line("全形", summarize(rows)),
           line("値の形", summarize(rows, lambda r: not r["direction"])),
           line("方向の形", summarize(rows, lambda r: r["direction"]))]
    missing = [r["id"] for r in rows if r["state"] == "MISSING"]
    if missing:
        out.append("  MISSING: %d %s" % (len(missing), missing[:10]))
    return "\n".join(out)


def main(argv):
    labels = load_labels()
    for path in argv:
        with open(path, encoding="utf-8") as fh:
            dump = json.load(fh)
        rows = score(dump, labels)
        print(report(rows, os.path.basename(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
