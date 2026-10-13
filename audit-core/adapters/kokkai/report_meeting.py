# -*- coding: utf-8 -*-
"""入口(``verify_meeting``)の JSON → 人が読む Markdown。判定を足さない。
同じ入力なら同じ byte(``adapters.xbrl.report`` と同じ約束)。

使い方::

    python3 -m adapters.kokkai.report_meeting --in out.json --out report.md
"""

import argparse
import io
import json
import sys

STATE_ORDER = ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE", "GROUNDED")
STATE_LABEL = {
    "GROUNDED": "GROUNDED(一致)",
    "VALUE_MISMATCH": "VALUE_MISMATCH(根拠は在るが合わない)",
    "POINTER_NOT_FOUND": "POINTER_NOT_FOUND(発言番号が無い)",
    "UNVERIFIABLE": "UNVERIFIABLE(判定できない)",
}
CHECK_LABEL = {"speaker": "発言者", "quote": "引用", "number": "数"}


def cell(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\r\n", " ").replace("\n", " ").replace("\r", " ")


def fmt_num(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, int):
        return "{:,}".format(v)
    return ("{:,.6f}".format(v)).rstrip("0").rstrip(".")


def _checks_cell(checks):
    parts = []
    for k in ("speaker", "quote", "number"):
        if k in checks:
            parts.append("%s %s" % (CHECK_LABEL[k], checks[k]))
    return " / ".join(parts)


def render_markdown(out):
    doc = out.get("document") or {}
    inp = out.get("input") or {}
    eng = out.get("engine") or {}
    meta = inp.get("meeting") or {}
    claims = list(out.get("claims") or [])
    checks = list(out.get("checks") or [])
    total = doc.get("claims")
    if total is None:
        total = len(claims)

    L = []
    L.append("# 検証の報告 ― %s %s %s(%s)" % (cell(meta.get("nameOfHouse")), cell(meta.get("nameOfMeeting")),
                                             cell(meta.get("issue")), cell(meta.get("date"))))
    L.append("")
    L.append("- 道具: `%s`" % cell(out.get("tool")))
    L.append("- 会議録: issueID `%s`、発言 %s 件、sha256 `%s`" % (cell(meta.get("issueID")), fmt_num(inp.get("speeches")), cell(inp.get("meeting_sha256"))))
    L.append("- 要約: 書き手 `%s`、sha256 `%s`" % (cell(inp.get("summary_written_by")), cell(inp.get("summary_sha256"))))
    L.append("- engine の指紋: adapters `%s` / core `%s` / git `%s`" % (
        cell(eng.get("adapter_kokkai_py_sha256")), cell(eng.get("core_py_sha256")), cell(eng.get("git_commit"))))
    L.append("")
    L.append("## 要約の文(claim)ごとの状態")
    L.append("")
    L.append("- 文の件数: **%s**(検査 %s 件)" % (fmt_num(total), fmt_num(doc.get("checks"))))
    L.append("")
    L.append("| 状態 | 文の件数 | 割合 |")
    L.append("|---|---|---|")
    states = doc.get("states") or {}
    for st in STATE_ORDER:
        n = states.get(st, 0)
        share = ("%.1f%%" % (100.0 * n / total)) if total else "―"
        L.append("| %s | %s | %s |" % (STATE_LABEL[st], fmt_num(n), share))
    L.append("")
    L.append("規則(字のまま): %s" % cell(doc.get("rule")))
    L.append("")
    L.append("凡例: 1 つの文に 発言者・引用・数 の検査が最大 3 つ付く。文の状態はその検査の状態を規則の順で畳んだもの。"
             "「発言番号が無い」は、文が指した発言番号が会議録に存在しないこと。"
             "「根拠は在るが合わない」は、発言は在るが、発言者・引用・数のどれかが本文と合わないこと。"
             "この報告は照合の結果を並べるだけで、文の内容の良し悪しや、発言の内容について何も言わない。")
    L.append("")

    by = {st: [] for st in STATE_ORDER}
    other = []
    for c in claims:
        (by[c["state"]] if c.get("state") in by else other).append(c)
    for st in STATE_ORDER:
        rows = by[st]
        L.append("## %s ― %s 件" % (STATE_LABEL[st], fmt_num(len(rows))))
        L.append("")
        if not rows:
            L.append("(なし)")
            L.append("")
            continue
        L.append("| id | 発言番号 | 発言者 | 検査 | 文 |")
        L.append("|---|---|---|---|---|")
        for c in rows:
            L.append("| %s | %s | %s | %s | %s |" % (cell(c.get("id")), cell(c.get("speech_order")), cell(c.get("speaker")),
                                                   cell(_checks_cell(c.get("checks") or {})), cell(c.get("text"))))
        L.append("")
    if other:
        L.append("## その他の状態 ― %s 件" % fmt_num(len(other)))
        L.append("")
        L.append("| id | 状態 | 文 |")
        L.append("|---|---|---|")
        for c in other:
            L.append("| %s | %s | %s |" % (cell(c.get("id")), cell(c.get("state")), cell(c.get("text"))))
        L.append("")

    stopped = [r for r in checks if r.get("state") != "GROUNDED"]
    L.append("## 一致しなかった検査の中身 ― %s 件" % fmt_num(len(stopped)))
    L.append("")
    if not stopped:
        L.append("(なし)")
        L.append("")
    else:
        L.append("| 検査 id | 状態 | 文に書いたもの | 発言の側 | 理由 |")
        L.append("|---|---|---|---|---|")
        for r in stopped:
            d = r.get("detail") or {}
            if r.get("check") == "number":
                mine = "%s %s(%s)" % (fmt_num(r.get("value")), cell(r.get("unit")), cell(r.get("word")))
                theirs = "本文の数 %s 件の中に無い" % fmt_num(d.get("tokens")) if r.get("state") == "VALUE_MISMATCH" else ""
            elif r.get("check") == "quote":
                mine = "「%s」" % cell(r.get("word"))
                theirs = "本文に無い" if r.get("state") == "VALUE_MISMATCH" else ""
            else:
                mine = cell(r.get("subject"))
                theirs = cell(d.get("actual"))
            L.append("| %s | %s | %s | %s | %s |" % (cell(r.get("id")), cell(r.get("state")), mine, theirs, cell(r.get("reason")) or "―"))
        L.append("")
    L.append("---")
    L.append("この報告は入口の JSON から機械で作ったもので、判定を足していない。")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with io.open(a.inp, encoding="utf-8") as fh:
        out = json.load(fh)
    md = render_markdown(out)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(md)
    print("written: %s (%d bytes)" % (a.out, len(md.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
