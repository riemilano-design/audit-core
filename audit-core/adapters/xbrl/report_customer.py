# -*- coding: utf-8 -*-
"""入口(``verify_document``)の JSON を、**客(開示担当者)が上司にそのまま見せられる**日本語の報告にする。

封 ``docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md`` §1。既存の ``report.py``(人間の決定 2026-10-13
「判定に手を加えない・golden」)は 1 字も触らず、``fmt_num``・``cell`` だけを借りる。

**判定(state・reason・pointer・recomputed)は足さず変えず、並べ方と字だけを変える。** LLM なし。
同じ JSON からは同じバイト列(golden)。

節の順(state・reason から決定論で引く):

1. **違う** = VALUE_MISMATCH。文の抜粋 / 文の値 / 出典の値(**文と同じ単位に直す**)/ 出典(日本語)。
2. **要確認** = POINTER_NOT_FOUND・UNVERIFIABLE のうち 3. 以外。文の抜粋 / 文の値 / 理由(日本語 1 行)。
3. **対象外**(出典に無い)= reason が ``OUT_OF_SCOPE_REASONS``、**判断しない** = ``NOT_JUDGED_REASONS``。件数と抜粋だけ。
4. **一致** = GROUNDED。件数と出典の内訳(当期 / 前期 / 計算)。行は ``--full`` のときだけ。
5. 末尾に小さく: 書類・入力の sha256・engine の指紋・profile。

使い方::

    python3 -m adapters.xbrl.report_customer --in out.json --out report.md [--labels <dir>] [--full]

``--labels`` は標準タクソノミのラベル file(``*_lab.xml``)を置いた dir(repo の外。
fixtures/xbrl/TAXONOMY_LABELS_README.md)。無ければ要素名のまま出す。
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

from .report import cell, fmt_num

# ---------------------------------------------------------------------------
# 字で留める表
# ---------------------------------------------------------------------------

# 文の単位 → 円に対する倍率(vocabulary.UNIT_SCALE と同じ値。engine を import しないで字で持つ)
UNIT_SCALE = {"百万円": 1e6, "千円": 1e3, "億円": 1e8, "兆円": 1e12, "円": 1}
# そのまま並べる単位(engine の recomputed が文と同じ単位で出る: 率・ポイント)
RATE_UNITS = ("%", "％", "ポイント")

# 封 §1-3 (a): 出典(XBRL)にその数が無い = 「対象外」
OUT_OF_SCOPE_REASONS = (
    "no_element(unit not in XBRL)",
    "no_prior_member_context",
)
# 封 §1-3 (c): 判断しないのが正しい = 「判断しない」
NOT_JUDGED_REASONS = (
    "no_subject",
    "target_or_plan",
    "ambiguous(member)",
)

# reason → 日本語 1 行。登録簿の理由の全部(``registry_setup`` の POINTER_NOT_FOUND 9 + UNVERIFIABLE 7 = 16 =
# ``recipes.UNBOUND_REASON_STATE`` の 14 key + ``other_frame`` + ``no_same_value``)を網羅する(門で縛る)。
# 表に無い reason は字のまま出す(赤にしない)。
REASON_JA = {
    "no_element": "文の項目に当たる数が出典(XBRL)に見つからなかった",
    "no_element(unit not in XBRL)": "文の単位(株・名・件 など)の数は出典(XBRL)に無い",
    "no_element(ratio without fact)": "率の元になる数が出典(XBRL)に無い",
    "no_prior_member_context": "前期の同じ区分(セグメント等)の数が出典(XBRL)に無い",
    "no_subject": "文に主語(どの項目の数か)が無い",
    "ambiguous(member)": "文の区分(セグメント等)が 1 つに決まらない",
    "ambiguous(elements)": "文の項目に当たる要素が複数あり 1 つに決まらない",
    "state_word(no line)": "増減の語に当てる行が出典(XBRL)に無い",
    "prior is 0": "前期の値が 0 で率が計算できない",
    "no_element(point without prior phrase)": "「ポイント」の差に前期を指す言い回しが無い",
    "target_or_plan": "目標・計画の数(実績ではない)",
    "no_element(text needs money fact)": "増減の語に当てる金額の数が出典(XBRL)に無い",
    "no_element(no prior for text)": "増減の語に当てる前期の数が出典(XBRL)に無い",
    "no_element(no prior2 for prior-year diff)": "前期の増減に当てる前々期の数が出典(XBRL)に無い",
    # P24 frame_rebind(登録簿の理由 ``other_frame``)。封 §1 の字。
    "other_frame": "同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる",
    # P25 last_branch_names_only_if_evidence(登録簿の理由 ``no_same_value``)。封 §1 の字。
    "no_same_value": "出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる",
}

# context の頭 → 期の字
PERIOD_JA = {
    "CurrentYearDuration": "当期",
    "Prior1YearDuration": "前期",
    "Prior2YearDuration": "前々期",
    "CurrentYearInstant": "当期末",
    "Prior1YearInstant": "前期末",
    "Prior2YearInstant": "前々期末",
}
_PERIOD_RE = re.compile(r"^(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)")
# context の区分(member)→ 字。標準の 1 つだけ。会社ごとのセグメント名は字のまま。
MEMBER_JA = {"NonConsolidatedMember": "単体"}

# xbrl: でない pointer(計算・符号)→ 日本語。a・b は 1 本目・2 本目の期の字で埋める。
# recipes.py の pointer → comparator の表(formula:… / builtin:…)と同じ字。
OP_JA = {
    "formula:a-b": "{a} − {b}",
    "formula:a-b(pure)": "{a} − {b}(ポイント)",
    "formula:cur/prior*100": "{a} ÷ {b} × 100",
    "formula:a/b*100": "{a} ÷ {b} × 100",
    "builtin:sign(cur-prior)": "{a} − {b} の符号",
    "builtin:sign(cur-prior)==direction": "{a} − {b} の符号",
    "builtin:sign(cur-prior)==direction&amount": "{a} − {b} の符号と大きさ",
    "builtin:sign(|cur|-|prior|)": "{a} と {b} の大きさの差の符号",
    "builtin:sign(|cur|-|prior|)==direction": "{a} と {b} の大きさの差の符号",
    "builtin:flow_sign(cur)==direction": "{a} の符号",
}
# xbrl: の pointer が 2 本で計算の pointer が無いとき(recipes: pct_change(cur,prior))
PCT_CHANGE_JA = "前期比({a} ÷ {b} − 1)"

STATE_MISMATCH = "VALUE_MISMATCH"
STATE_GROUNDED = "GROUNDED"
STATES_UNBOUND = ("POINTER_NOT_FOUND", "UNVERIFIABLE")

SECTION_MISMATCH = "違う"
SECTION_CHECK = "要確認"
SECTION_OUT = "対象外"
SECTION_NOT_JUDGED = "判断しない"
SECTION_MATCH = "一致"
SECTION_OTHER = "その他"

STANDARD_LABEL_ROLE = "http://www.xbrl.org/2003/role/label"
_XLINK = "{http://www.w3.org/1999/xlink}"
_XML_NS = "{http://www.w3.org/XML/1998/namespace}"


# ---------------------------------------------------------------------------
# ラベル(repo の外の file を読むだけ。無ければ空の表)
# ---------------------------------------------------------------------------

def parse_label_linkbase(data, role=STANDARD_LABEL_ROLE):
    """ラベル linkbase → ``{loc の指す id(jppfs_cor_NetSales など): 日本語の標準ラベル}``。"""

    root = ET.fromstring(data)
    loc_id, lab_text, arcs = {}, {}, []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "loc":
            href = el.get(_XLINK + "href") or ""
            loc_id[el.get(_XLINK + "label")] = href.split("#")[-1]
        elif tag == "label":
            if (el.get(_XLINK + "role") or "") != role:
                continue
            if not (el.get(_XML_NS + "lang") or "").startswith("ja"):
                continue
            lab_text[el.get(_XLINK + "label")] = el.text or ""
        elif tag == "labelArc":
            arcs.append((el.get(_XLINK + "from"), el.get(_XLINK + "to")))
    out = {}
    for a, b in arcs:
        if a in loc_id and b in lab_text:
            out[loc_id[a]] = unicodedata.normalize("NFKC", lab_text[b].strip())
    return out


def load_labels(directory):
    """dir の ``*_lab.xml`` を全部読む。``None`` / 無い dir なら空の表。file 名順(決定論)。"""

    labels = {}
    if not directory or not os.path.isdir(directory):
        return labels
    for name in sorted(os.listdir(directory)):
        if not name.endswith("_lab.xml"):
            continue
        with open(os.path.join(directory, name), "rb") as fh:
            labels.update(parse_label_linkbase(fh.read()))
    return labels


# ---------------------------------------------------------------------------
# pointer → 日本語
# ---------------------------------------------------------------------------

def split_pointer(p):
    """``xbrl:jppfs_cor:NetSales@CurrentYearDuration_XMember`` → (``jppfs_cor:NetSales``, ``CurrentYearDuration_XMember``)。
    xbrl: でなければ ``(None, None)``。"""

    if not isinstance(p, str) or not p.startswith("xbrl:"):
        return None, None
    name, _, ctx = p[5:].partition("@")
    return name, ctx


def split_context(ctx):
    """context → (期の字, 区分 or None)。``CurrentYearDuration_FooMember`` → ("当期", "FooMember")。
    知らない形は (字のまま, None)。"""

    m = _PERIOD_RE.match(ctx or "")
    if not m:
        return (ctx or ""), None
    head = m.group(1) + m.group(2)
    rest = (ctx or "")[len(head):]
    word = PERIOD_JA[head]
    if rest.startswith("_") and rest[1:]:
        return word, rest[1:]
    if rest:
        return word + rest, None
    return word, None


def period_ja(ctx):
    """context → 期の字(区分は落とす。区分は ``source_ja`` が 1 回だけ後ろに付ける)。"""

    return split_context(ctx)[0]


def member_ja(member):
    """区分の字。``NonConsolidatedMember`` → 単体、ほかは字のまま(会社ごとの名前)。"""

    return MEMBER_JA.get(member, member)


def element_ja(name, labels):
    """``jppfs_cor:NetSales`` → 標準ラベル(表に在れば)。無ければ要素名のまま。"""

    if not name:
        return ""
    key = name.replace(":", "_")
    return labels.get(key) or name


def source_ja(pointers, labels):
    """pointer の列 → 出典の日本語 1 欄。

    xbrl: の pointer は「ラベル 期」を「 / 」で並べ、計算・符号の pointer は ``OP_JA`` で
    期の字を埋めて後ろに「(…)」で付ける。xbrl: 2 本で計算の pointer が無ければ前期比。
    知らない pointer は字のまま。"""

    facts, ops, members = [], [], []
    for p in pointers or []:
        name, ctx = split_pointer(p)
        if name is None:
            ops.append(p)
        else:
            per, mem = split_context(ctx)
            facts.append((element_ja(name, labels), per))
            if mem and mem not in members:
                members.append(mem)
    if not facts and not ops:
        return ""
    parts = ["%s %s" % (lab, per) if per else lab for lab, per in facts]
    a = facts[0][1] if len(facts) > 0 else "a"
    b = facts[1][1] if len(facts) > 1 else "b"
    # 同じ要素なら期の字だけで式を書く。別の要素なら「ラベル 期」で書く。
    if len(facts) >= 2 and facts[0][0] != facts[1][0]:
        a = "%s %s" % facts[0]
        b = "%s %s" % facts[1]
    tails = []
    for op in ops:
        fmt = OP_JA.get(op)
        tails.append(fmt.format(a=a, b=b) if fmt else op)
    if not ops and len(facts) == 2:
        tails.append(PCT_CHANGE_JA.format(a=a, b=b))
    text = " / ".join(parts)
    if tails:
        text += "(" + "、".join(tails) + ")"
    if members:
        text += "[区分: " + "、".join(member_ja(m) for m in members) + "]"
    return text


# ---------------------------------------------------------------------------
# 値
# ---------------------------------------------------------------------------

def claim_value_ja(c):
    """文の値。数なら 値+単位、語の主張なら語。"""

    if c.get("value") is not None:
        unit = c.get("unit") or ""
        return fmt_num(c["value"]) + (" " + unit if unit else "")
    return c.get("word") or ""


def source_value_ja(c):
    """出典の値を**文と同じ単位**に直した字。

    - 文の単位が金額(UNIT_SCALE)なら recomputed(円)を倍率で割る(直接の値も差も engine は円で返す)。
    - 率・ポイントは engine の値がもう文と同じ単位なのでそのまま。
    - 単位の無い語の主張(増加・減少 など)は engine の値(円の差 or 当期の値)に「円」を付ける。
    - それ以外の単位(名・株 …)はそのまま単位を付ける。
    recomputed が無ければ「―」。"""

    v = c.get("recomputed")
    if v is None:
        return "―"
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return cell(v)
    unit = c.get("unit") or ""
    if unit in UNIT_SCALE:
        scale = UNIT_SCALE[unit]
        return fmt_num(v / scale if scale != 1 else v) + " " + unit
    if unit in RATE_UNITS:
        return fmt_num(v) + " " + unit
    if not unit and c.get("value") is None:
        return fmt_num(v) + " 円"
    return fmt_num(v) + (" " + unit if unit else "")


# ---------------------------------------------------------------------------
# 節の振り分け(state・reason から決定論で)
# ---------------------------------------------------------------------------

def section_of(c):
    st = c.get("state")
    if st == STATE_MISMATCH:
        return SECTION_MISMATCH
    if st == STATE_GROUNDED:
        return SECTION_MATCH
    if st in STATES_UNBOUND:
        r = c.get("reason") or ""
        if r in OUT_OF_SCOPE_REASONS:
            return SECTION_OUT
        if r in NOT_JUDGED_REASONS:
            return SECTION_NOT_JUDGED
        return SECTION_CHECK
    return SECTION_OTHER


def reason_ja(reason):
    """reason → 日本語 1 行。表に無ければ字のまま。空なら「―」。"""

    if not reason:
        return "―"
    return REASON_JA.get(reason, reason)


def match_kind(c):
    """一致の内訳: 当期 / 前期 / 計算 / その他。
    xbrl: 1 本で当期の context → 当期、前期(前々期)の context → 前期、xbrl: 2 本以上か計算・符号の pointer → 計算。"""

    ptrs = c.get("pointers") or []
    facts = [split_pointer(p) for p in ptrs]
    facts = [(n, x) for n, x in facts if n is not None]
    if len(ptrs) == 1 and len(facts) == 1:
        ctx = facts[0][1] or ""
        if ctx.startswith("CurrentYear"):
            return "当期"
        if ctx.startswith("Prior"):
            return "前期"
        return "その他"
    if len(facts) >= 2 or len(ptrs) > len(facts):
        return "計算"
    return "その他"


MATCH_KINDS = ("当期", "前期", "計算", "その他")


# ---------------------------------------------------------------------------
# 描く
# ---------------------------------------------------------------------------

def _excerpt(c):
    return cell(c.get("span")) or "―"


def render_markdown(out, labels=None, full=False):
    """入口の出力(dict)→ Markdown(str)。純粋関数。``labels`` は ``load_labels`` の表(None は空)。"""

    labels = labels or {}
    doc = out.get("document") or {}
    inp = out.get("input") or {}
    eng = out.get("engine") or {}
    claims = list(out.get("claims") or [])
    total = doc.get("claims")
    if total is None:
        total = len(claims)

    by = {SECTION_MISMATCH: [], SECTION_CHECK: [], SECTION_OUT: [], SECTION_NOT_JUDGED: [],
          SECTION_MATCH: [], SECTION_OTHER: []}
    for c in claims:
        by[section_of(c)].append(c)
    kinds = {k: 0 for k in MATCH_KINDS}
    for c in by[SECTION_MATCH]:
        kinds[match_kind(c)] += 1

    src = (inp.get("instance_source") or "(書類)").rsplit("/", 1)[-1]
    L = []
    L.append("# 文章と出典(XBRL)の照合 ― %s" % cell(src))
    L.append("")
    L.append("文章の中の数と増減の語を、同じ書類の XBRL の値と突き合わせた。判定は道具が出したまま並べ替えている(足していない)。")
    L.append("")
    L.append("| 区分 | 件数 | 意味 |")
    L.append("|---|---|---|")
    L.append("| %s | %s | 出典に当たる値があり、文の値と**違う** |" % (SECTION_MISMATCH, fmt_num(len(by[SECTION_MISMATCH]))))
    L.append("| %s | %s | 道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる |" % (SECTION_CHECK, fmt_num(len(by[SECTION_CHECK]))))
    L.append("| %s | %s | 出典(XBRL)にその数は無い(株数・人数など) |" % (SECTION_OUT, fmt_num(len(by[SECTION_OUT]))))
    L.append("| %s | %s | 主語が無い・目標や計画・区分が決まらない。道具は判断しない |" % (SECTION_NOT_JUDGED, fmt_num(len(by[SECTION_NOT_JUDGED]))))
    L.append("| %s | %s | 出典の値と一致した |" % (SECTION_MATCH, fmt_num(len(by[SECTION_MATCH]))))
    if by[SECTION_OTHER]:
        L.append("| %s | %s | 上のどれでもない状態 |" % (SECTION_OTHER, fmt_num(len(by[SECTION_OTHER]))))
    L.append("| 合計 | %s | |" % fmt_num(total))
    L.append("")

    # 1. 違う
    rows = by[SECTION_MISMATCH]
    L.append("## 1. %s ― %s 件" % (SECTION_MISMATCH, fmt_num(len(rows))))
    L.append("")
    L.append("出典に当たる値は見つかったが、文の値と違う。文の誤りか、当てた出典の誤りかは、この表では決めない。「出典の値」は文と同じ単位に直してある。")
    L.append("")
    if rows:
        L.append("| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |")
        L.append("|---|---|---|---|---|")
        for c in rows:
            L.append("| %s | %s | %s | %s | %s |" % (
                cell(c.get("id")), _excerpt(c), cell(claim_value_ja(c)) or "―",
                cell(source_value_ja(c)), cell(source_ja(c.get("pointers"), labels)) or "―"))
    else:
        L.append("(なし)")
    L.append("")

    # 2. 要確認
    rows = by[SECTION_CHECK]
    L.append("## 2. %s ― %s 件" % (SECTION_CHECK, fmt_num(len(rows))))
    L.append("")
    L.append("道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる。")
    L.append("")
    if rows:
        L.append("| # | 文の抜粋 | 文の値 | 理由 |")
        L.append("|---|---|---|---|")
        for c in rows:
            L.append("| %s | %s | %s | %s |" % (
                cell(c.get("id")), _excerpt(c), cell(claim_value_ja(c)) or "―", cell(reason_ja(c.get("reason")))))
    else:
        L.append("(なし)")
    L.append("")

    # 3. 対象外・判断しない
    L.append("## 3. %s ― %s 件 / %s ― %s 件" % (
        SECTION_OUT, fmt_num(len(by[SECTION_OUT])), SECTION_NOT_JUDGED, fmt_num(len(by[SECTION_NOT_JUDGED]))))
    L.append("")
    L.append("%s: 出典(XBRL)にその数は無い(株数・人数・区分ごとの前期の数など)。%s: 主語が無い・目標や計画の数・区分が 1 つに決まらない文。道具は判断しない。" % (
        SECTION_OUT, SECTION_NOT_JUDGED))
    L.append("")
    for name in (SECTION_OUT, SECTION_NOT_JUDGED):
        rows = by[name]
        L.append("### %s ― %s 件" % (name, fmt_num(len(rows))))
        L.append("")
        if rows:
            for c in rows:
                L.append("- %s: %s(%s)" % (cell(c.get("id")), _excerpt(c), cell(reason_ja(c.get("reason")))))
        else:
            L.append("(なし)")
        L.append("")

    # 4. 一致
    rows = by[SECTION_MATCH]
    L.append("## 4. %s ― %s 件" % (SECTION_MATCH, fmt_num(len(rows))))
    L.append("")
    L.append("文の値と出典の値が一致した。出典の内訳: 当期 %s 件 / 前期 %s 件 / 計算 %s 件%s。" % (
        fmt_num(kinds["当期"]), fmt_num(kinds["前期"]), fmt_num(kinds["計算"]),
        " / その他 %s 件" % fmt_num(kinds["その他"]) if kinds["その他"] else ""))
    L.append("")
    if full:
        if rows:
            L.append("| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |")
            L.append("|---|---|---|---|---|")
            for c in rows:
                L.append("| %s | %s | %s | %s | %s |" % (
                    cell(c.get("id")), _excerpt(c), cell(claim_value_ja(c)) or "―",
                    cell(source_value_ja(c)), cell(source_ja(c.get("pointers"), labels)) or "―"))
        else:
            L.append("(なし)")
        L.append("")
    elif rows:
        L.append("(行は `--full` で出す)")
        L.append("")

    # その他(通常は無い)
    rows = by[SECTION_OTHER]
    if rows:
        L.append("## %s ― %s 件" % (SECTION_OTHER, fmt_num(len(rows))))
        L.append("")
        L.append("| # | 状態 | 文の抜粋 | 文の値 | 理由 |")
        L.append("|---|---|---|---|---|")
        for c in rows:
            L.append("| %s | %s | %s | %s | %s |" % (
                cell(c.get("id")), cell(c.get("state")), _excerpt(c), cell(claim_value_ja(c)) or "―",
                cell(reason_ja(c.get("reason")))))
        L.append("")

    # 5. 末尾
    L.append("---")
    L.append("")
    rep = inp.get("text_replaced") or {}
    L.append("<sub>書類: %s</sub>  " % cell(inp.get("instance_source")))
    L.append("<sub>入力 ZIP の sha256: %s(%s bytes)</sub>  " % (cell(inp.get("zip_sha256")), fmt_num(inp.get("zip_bytes"))))
    if rep:
        L.append("<sub>照合した文章の sha256: %s(%s 字)</sub>  " % (cell(rep.get("text_sha256")), fmt_num(rep.get("text_chars"))))
    else:
        L.append("<sub>照合した文章: 書類の原文</sub>  ")
    L.append("<sub>engine の指紋: adapters %s / core %s / git %s</sub>  " % (
        cell(eng.get("adapter_xbrl_py_sha256")), cell(eng.get("core_py_sha256")), cell(eng.get("git_commit"))))
    L.append("<sub>profile: %s / 道具: %s</sub>" % (cell(out.get("profile")), cell(out.get("tool"))))
    L.append("")
    return "\n".join(L)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--in", dest="inp", required=True, help="verify_document の出力 JSON")
    parser.add_argument("--out", required=True, help="書き出す Markdown")
    parser.add_argument("--labels", default=None, help="標準タクソノミのラベル file(*_lab.xml)の dir。無ければ要素名")
    parser.add_argument("--full", action="store_true", help="一致の行も出す")
    args = parser.parse_args(argv)
    with io.open(args.inp, "r", encoding="utf-8") as f:
        out = json.load(f)
    md = render_markdown(out, load_labels(args.labels), args.full)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print("written:", args.out, "claims:", len(out.get("claims") or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
