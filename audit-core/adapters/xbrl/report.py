# -*- coding: utf-8 -*-
"""入口(``verify_document``)の JSON を、人が読める Markdown の報告にする。

人間の決定(2026-10-13、パッケージ「報告の装置」): **判定に手を加えない。** JSON に在る
state・pointer・reason・値をそのまま並べ替えて見せるだけ。LLM は使わない。同じ JSON から
は同じバイト列が出る(golden で留める)。

並び: 書類の旗と件数 → VALUE_MISMATCH(文の値 / 根拠の値 / pointer)→ POINTER_NOT_FOUND
→ UNVERIFIABLE → GROUNDED。見つからなかった行は「見つからなかった」とだけ書く。

使い方::

    python3 -m adapters.xbrl.report --in out.json --out report.md
"""

import argparse
import io
import json
import sys

STATE_ORDER = ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE", "GROUNDED")
STATE_LABEL = {
    "GROUNDED": "一致(GROUNDED)",
    "VALUE_MISMATCH": "値が違う(VALUE_MISMATCH)",
    "POINTER_NOT_FOUND": "根拠が見つからない(POINTER_NOT_FOUND)",
    "UNVERIFIABLE": "判定できない(UNVERIFIABLE)",
}
STATE_NOTE = {
    "VALUE_MISMATCH": "根拠は見つかったが、文の値と根拠の値が違う。文の誤りか、結び先の誤りかは、この表では決めない。",
    "POINTER_NOT_FOUND": "文の主張に当たる根拠が書類に見つからなかった。",
    "UNVERIFIABLE": "主語や形が取れず、判定を止めた。",
    "GROUNDED": "文の値と根拠の値が一致した。",
}


def fmt_num(v):
    """数を人が読む形に。整数は桁区切り、小数は末尾の 0 を落とす。None は空。"""

    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return "{:,}".format(v)
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return repr(v)
        if v.is_integer():
            return "{:,}".format(int(v))
        return "{:,.4f}".format(v).rstrip("0").rstrip(".")
    return str(v)


def cell(s):
    """Markdown の表の 1 欄。縦棒と改行を潰す。None は空。"""

    if s is None:
        return ""
    return str(s).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def claim_value(c):
    """文の側の値。数なら 値+単位、文字の主張なら word。"""

    if c.get("value") is not None:
        unit = c.get("unit") or ""
        return fmt_num(c["value"]) + (" " + unit if unit else "")
    return c.get("word") or ""


def _cells(c):
    """1 Claim の欄(id の後ろ): 主語・文の値・根拠から出た値・pointer・理由・文。"""

    ptrs = c.get("pointers") or []
    return [
        cell(c.get("subject")) or "―",
        cell(claim_value(c)),
        cell(fmt_num(c.get("recomputed"))) if c.get("recomputed") is not None else "―",
        cell(" ; ".join(ptrs)) if ptrs else "―",
        cell(c.get("reason")) or "―",
        cell(c.get("span")),
    ]


def _row(c):
    return "| " + " | ".join([cell(c.get("id"))] + _cells(c)) + " |"


def render_markdown(out):
    """入口の出力(dict)→ Markdown(str)。純粋関数。"""

    doc = out.get("document") or {}
    inp = out.get("input") or {}
    eng = out.get("engine") or {}
    claims = list(out.get("claims") or [])
    states = doc.get("states") or {}
    total = doc.get("claims")
    if total is None:
        total = len(claims)

    L = []
    src = inp.get("instance_source") or "(書類)"
    L.append("# 検証の報告 ― %s" % cell(src.rsplit("/", 1)[-1]))
    L.append("")
    L.append("- 道具: `%s` / profile: `%s`" % (cell(out.get("tool")), cell(out.get("profile"))))
    L.append("- 入力 ZIP の sha256: `%s`(%s bytes)" % (cell(inp.get("zip_sha256")), fmt_num(inp.get("zip_bytes"))))
    if inp.get("text_replaced"):
        L.append("- 文章の差し替え: あり(`%s`)" % cell(inp.get("text_replaced")))
    else:
        L.append("- 文章の差し替え: なし(書類の原文)")
    L.append("- engine の指紋: adapters `%s` / core `%s` / git `%s`" % (
        cell(eng.get("adapter_xbrl_py_sha256")), cell(eng.get("core_py_sha256")), cell(eng.get("git_commit"))))
    L.append("")
    L.append("## 書類レベル")
    L.append("")
    flag = doc.get("unverifiable")
    L.append("- 判定: **%s**%s" % (
        "UNVERIFIABLE(書類として判定できない)" if flag else "旗なし(書類レベルの UNVERIFIABLE には当たらない)",
        "(理由: %s)" % cell(doc.get("unverifiable_why")) if doc.get("unverifiable_why") else ""))
    L.append("- 主張の件数: **%s**" % fmt_num(total))
    L.append("")
    L.append("| 状態 | 件数 | 割合 |")
    L.append("|---|---|---|")
    for st in STATE_ORDER:
        n = states.get(st, 0)
        share = ("%.1f%%" % (100.0 * n / total)) if total else "―"
        L.append("| %s | %s | %s |" % (STATE_LABEL[st], fmt_num(n), share))
    L.append("")
    L.append("規則(字のまま): %s" % cell(doc.get("rule")))
    L.append("")

    by = {st: [] for st in STATE_ORDER}
    other = []
    for c in claims:
        (by[c["state"]] if c.get("state") in by else other).append(c)
    for st in STATE_ORDER:
        rows = by[st]
        L.append("## %s ― %s 件" % (STATE_LABEL[st], fmt_num(len(rows))))
        L.append("")
        L.append(STATE_NOTE[st])
        L.append("")
        if not rows:
            L.append("(なし)")
            L.append("")
            continue
        L.append("| id | 主語 | 文の値 | 根拠から出た値 | 根拠(pointer) | 理由 | 文 |")
        L.append("|---|---|---|---|---|---|---|")
        for c in rows:
            L.append(_row(c))
        L.append("")
    if other:
        L.append("## その他の状態 ― %s 件" % fmt_num(len(other)))
        L.append("")
        L.append("| id | state | 主語 | 文の値 | 根拠の値 | 根拠 | 理由 | 文 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for c in other:
            L.append("| " + " | ".join([cell(c.get("id")), cell(c.get("state"))] + _cells(c)) + " |")
        L.append("")
    L.append("---")
    L.append("この報告は入口の JSON を並べ替えただけで、判定を足していない。「根拠から出た値」は engine が根拠から計算した値(直接の値は書類の単位 = 円など、率・差は文と同じ単位)。「文の値」は文の単位のまま。")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="inp", required=True, help="verify_document の出力 JSON")
    parser.add_argument("--out", required=True, help="書き出す Markdown")
    args = parser.parse_args(argv)
    with io.open(args.inp, "r", encoding="utf-8") as f:
        out = json.load(f)
    md = render_markdown(out)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print("written:", args.out, "claims:", len(out.get("claims") or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
