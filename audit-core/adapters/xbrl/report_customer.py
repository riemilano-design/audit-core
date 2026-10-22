# -*- coding: utf-8 -*-
"""入口(``verify_document``)の JSON を、**客(開示担当者)が上司にそのまま見せられる**日本語の報告にする。

封 ``docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md`` §1(段 1)と、その直し ``docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md`` §1(段 2)。
既存の ``report.py``(人間の決定 2026-10-13「判定に手を加えない・golden」)は 1 字も触らず、``fmt_num``・``cell`` だけを借りる。

**判定(state・reason・pointer・recomputed)は足さず変えず、並べ方と字だけを変える。節の割り当ても変えない。** LLM なし。
同じ JSON からは同じバイト列(golden)。本文と ``.provenance.json`` の両方。

節の順(state・reason から決定論で引く):

1. **違う** = VALUE_MISMATCH。文の抜粋 / 文の値 / 出典の値(**文と同じ単位・同じ書き方に直す**)/ 出典(日本語)。
2. **要確認** = POINTER_NOT_FOUND・UNVERIFIABLE のうち 3. 以外。文の抜粋 / 文の値 / 理由(日本語 1 行)。
3. **対象外**(出典に無い)= reason が ``OUT_OF_SCOPE_REASONS``、**判断しない** = ``NOT_JUDGED_REASONS``。件数と抜粋だけ(抜粋は数の途中で切らない)。
4. **一致** = GROUNDED。件数と出典の内訳(当期 / 前期 / 計算)。行は ``--full`` のときだけ。
5. 末尾は 1 行だけ(機械用の記録の在りか)。書類・入力の sha256・engine の指紋・profile・ラベルの file の sha256 は本文に書かず、
   同じ名前の ``.provenance.json``(機械用。``render_provenance``)に出す。

段 2 の直し(封 §1):
(1) ラベルは ``fixtures/xbrl/taxonomy_labels_sha256.txt``(名簿)に在る file 名だけを読み、sha256 が合わない file は使わない(使わなかったことを provenance に書く)。
    名簿に無い file は dir に在っても読まない。
(2) 文の値は文の字(span の中の金額の字)のまま出し、出典の値も同じ単位・同じ書き方に直す。語の主張は span の中でいちばん近い金額の字の単位、
    無ければ書類で最も多い単位。同じ金額の字が無い行は claim の単位のまま出す(読み取れない行)。
(3) 出典の値は文の書いた桁に丸めた字を先に、丸める前の値を括弧で後に(「61 百万円(61.274)」)。(4) 出典の値が負なら「△」。
(5) 会社ごとの要素・区分は書類の ZIP の ``XBRL/PublicDoc/*_lab.xml``(書類自身のラベル)で日本語に(``--zip``)。
(6) 「違う」の意味の欄に「文の誤りか、当てた出典の誤りかは決めない」。(8) ``--zip`` があれば表題を書類から(提出者名 = DEI、書類の種類 = 書類の題名 ``DocumentTitleCoverPage``(無ければ ``DocumentTypeDEI``)、当期の期末日 = DEI)。
(9) 対象外・判断しないの抜粋は数の字の途中で切らない。

使い方::

    python3 -m adapters.xbrl.report_customer --in out.json --out report.md [--labels <dir>] [--zip <書類.zip>] [--full]

``--labels`` は標準タクソノミのラベル file(``*_lab.xml``)を置いた dir(repo の外。
fixtures/xbrl/TAXONOMY_LABELS_README.md)。dir の中で読むのは名簿に在る file だけ。無ければ要素名のまま出す。
``--out`` の隣に ``<out の拡張子を除いた名前>.provenance.json`` を書く。
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

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


#: ラベルの名簿(``{file 名: sha256}``)の置き場。module の 2 つ上の fixtures/xbrl/ にある。
ROSTER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           "fixtures", "xbrl", "taxonomy_labels_sha256.txt")
STATUS_USED = "used"
STATUS_MISMATCH = "sha256_mismatch"
STATUS_MISSING = "missing"


def load_roster(path=None):
    """名簿 ``fixtures/xbrl/taxonomy_labels_sha256.txt``(``<sha256>  <file 名>`` の行)→ ``{file 名: sha256}``。
    ``#`` で始まる行と空行は読まない。名簿が無ければ空(= 何も読まない)。"""

    path = path or ROSTER_PATH
    out = {}
    if not os.path.isfile(path):
        return out
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                out[parts[1].strip()] = parts[0].lower()
    return out


def _strip_member_word(text):
    return re.sub(r"\s*[\[［]メンバー[\]］]\s*$", "", text)


def load_labels_with_meta(directory=None, zip_path=None, roster=None):
    """標準ラベルと書類自身のラベルを 1 つの表に。返すのは ``(表, 読んだ・読まなかった file の [{file, sha256, status}])``。

    - 標準ラベル: ``directory`` の中で**名簿に在る file 名だけ**を読む(名簿に無い file は dir に在っても読まない)。
      sha256 が名簿と合わない file は使わず ``status`` に ``sha256_mismatch``、dir に無ければ ``missing``。
    - 書類自身のラベル: ``zip_path`` の ``XBRL/PublicDoc/*_lab.xml``(``zip:<file 名>``)。
    標準ラベルが先(同じ key なら標準)。書類のラベルは ``<prefix>_<Local>`` の key のほかに、context の id に現れる形
    ``member:<prefix><Local>``(区分の字を引くため)でも引けるようにする。"""

    roster = load_roster() if roster is None else roster
    labels, meta = {}, []
    if directory and os.path.isdir(directory):
        for name in sorted(roster):
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                meta.append({"file": name, "sha256": None, "status": STATUS_MISSING})
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            got = hashlib.sha256(data).hexdigest()
            if got != roster[name]:
                meta.append({"file": name, "sha256": got, "status": STATUS_MISMATCH})
                continue
            labels.update(parse_label_linkbase(data))
            meta.append({"file": name, "sha256": got, "status": STATUS_USED})
    if zip_path:
        with open(zip_path, "rb") as fh:
            zb = fh.read()
        z = zipfile.ZipFile(io.BytesIO(zb))
        doc = {}
        for name in sorted(z.namelist()):
            if name.startswith("XBRL/PublicDoc/") and name.endswith("_lab.xml"):
                data = z.read(name)
                doc.update(parse_label_linkbase(data))
                meta.append({"file": "zip:" + name.rsplit("/", 1)[-1], "sha256": hashlib.sha256(data).hexdigest(), "status": STATUS_USED})
        for key in sorted(doc):
            labels.setdefault(key, doc[key])
            if "_" in key:
                pre, loc = key.rsplit("_", 1)
                labels.setdefault("member:" + pre + loc, _strip_member_word(doc[key]))
    return labels, meta


def load_labels(directory, roster=None):
    """dir の標準ラベルを読む。**名簿に在る file 名だけ**(sha256 が合うものだけ)。``None`` / 無い dir なら空の表。"""

    return load_labels_with_meta(directory, None, roster)[0]


def dei_from_zip(zip_path, instance_source=None):
    """書類の ZIP から ``{filer, doctype, period_end}``。

    - ``filer`` = DEI の ``FilerNameInJapaneseDEI``(提出者名)。
    - ``doctype`` = 書類の題名 ``jpcrp_cor:DocumentTitleCoverPage``(「有価証券報告書」。司令塔の判断 2026-10-21)。**無ければ** DEI の ``DocumentTypeDEI``(様式名「第三号様式」)に落とす。
    - ``period_end`` = DEI の ``CurrentPeriodEndDateDEI``(無ければ ``CurrentFiscalYearEndDateDEI``)。
    読めなければ値は None。"""

    want = {"FilerNameInJapaneseDEI": "filer", "DocumentTypeDEI": "dei_type", "DocumentTitleCoverPage": "title",
            "CurrentPeriodEndDateDEI": "period_end", "CurrentFiscalYearEndDateDEI": "fy_end"}
    got = {}
    with zipfile.ZipFile(zip_path) as z:
        names = sorted(n for n in z.namelist() if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl"))
        if instance_source in names:
            names = [instance_source]
        if names:
            with z.open(names[0]) as fh:
                for _ev, el in ET.iterparse(fh, events=("end",)):
                    local = el.tag.split("}")[-1]
                    if local in want:
                        text = (el.text or "").strip()
                        if text and want[local] not in got:       # 題名は同じ名前の要素が複数ある。空でない最初のもの
                            got[want[local]] = text
                    if len(got) == len(want):
                        break
    return {"filer": got.get("filer"), "doctype": got.get("title") or got.get("dei_type"),
            "period_end": got.get("period_end") or got.get("fy_end")}


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


_STD_MEMBER_PREFIXES = ("jpcrp_cor", "jppfs_cor", "jpigp_cor")


def _split_members(rest):
    """context の期の後ろ(``A_B``)を区分の列に。会社の接頭辞は ``_`` を含む(``jpcrp030000-asr_E05536-000Foo``)ので、
    ``Member`` で終わるまで ``_`` で継ぐ。"""

    out, cur = [], []
    for tok in rest.split("_"):
        cur.append(tok)
        if tok.endswith("Member"):
            out.append("_".join(cur))
            cur = []
    if cur:
        out.append("_".join(cur))
    return out


def member_label(member, labels):
    """区分 1 つの字。標準の 1 つ(単体)・書類自身のラベル・標準ラベルの順。引けなければ None。"""

    if member in MEMBER_JA:
        return MEMBER_JA[member]
    labels = labels or {}
    w = labels.get("member:" + member)
    if not w:
        for pre in _STD_MEMBER_PREFIXES:
            w = labels.get(pre + "_" + member)
            if w:
                break
    return w or None


def member_ja(member, labels=None):
    """区分の字。``NonConsolidatedMember`` → 単体。ラベルの表(書類自身のラベル・標準ラベル)に在ればその字、無ければ字のまま。
    1 つの context に区分が 2 つ以上あれば「・」で継ぐ。"""

    return "・".join(member_label(m, labels) or m for m in _split_members(member))


def unresolved_names(pointers, labels):
    """pointer の列のうち、ラベルが引けず**要素名・区分名の字のまま出る**ものの名前の列(重複なし・出る順)。"""

    out = []
    for p in pointers or []:
        name, ctx = split_pointer(p)
        if name is None:
            continue
        if not (labels or {}).get(name.replace(":", "_")) and name not in out:
            out.append(name)
        _per, mem = split_context(ctx)
        if mem:
            for m in _split_members(mem):
                if member_label(m, labels) is None and m not in out:
                    out.append(m)
    return out


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
        text += "[区分: " + "、".join(member_ja(m, labels) for m in members) + "]"
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


# --- 段 2(封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md §1-2・3・4): 文の字の単位・桁・符号 ---

NEG = "△"            # 日本の財務諸表の書き方(出典の値が負のとき)

# 文の字の金額。engine を import しないで字で持つ(extract.AMOUNT_JP_RE・NUM_RE と同じ字の形を読む)。
_AMT_PLAIN_RE = re.compile(r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s*(百万円|千円|億円|兆円|万円|円)")
_AMT_KANJI_RE = re.compile(r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(?:(\d+(?:\.\d+)?)兆)?(?:(\d+(?:\.\d+)?)億)?"
                           r"(?:(\d+)千)?(?:(\d+)百)?(?:(\d+)?(万))?円")
WRITTEN_SCALE = {"兆円": 1e12, "億円": 1e8, "百万円": 1e6, "万円": 1e4, "千円": 1e3, "円": 1}
WRITTEN_ORDER = ("百万円", "千円", "億円", "兆円", "万円", "円")   # 書類で最も多い単位が同数のときの順


class Amount(object):
    """span の中の金額の字 1 つ。``text`` は字そのまま、``yen`` は円の値(符号なし)、``unit`` は書いた単位、
    ``compound`` は兆・億を前に書く形(「26億23百万円」)か、``decimals`` は書いた桁(いちばん小さい位の小数の桁数)。"""

    __slots__ = ("pos", "text", "yen", "unit", "compound", "decimals")

    def __init__(self, pos, text, yen, unit, compound, decimals):
        self.pos, self.text, self.yen, self.unit, self.compound, self.decimals = pos, text, yen, unit, compound, decimals


def _decimals_of_text(t):
    return len(t.split(".", 1)[1]) if t and "." in t else 0


def written_amounts(span):
    """span の中の金額の字 → ``[Amount]``(位置順)。"""

    span = unicodedata.normalize("NFKC", span or "")
    out, taken = [], []
    for m in _AMT_KANJI_RE.finditer(span):
        g = m.groups()
        if not any(g[1:6]):
            continue
        big = bool(g[1] or g[2] or g[6])
        if g[6] and not g[5] and not (g[1] or g[2] or g[3] or g[4]):
            continue
        if g[3] and not (g[1] or g[2] or g[4] or g[5] or g[6]):
            continue          # 「805千円」= 805 千円。千の位だけの漢数字形(805,000 円)とは読まない(「3千5百円」は下の形のまま)。plain 側が千円として読む
        yen = 0.0
        for val, mult in ((g[1], 1e12), (g[2], 1e8), (g[3], 1e7 if big else 1e3), (g[4], 1e6 if big else 1e2), (g[5], 1e4)):
            if val:
                yen += float(val) * mult
        if g[4] or g[3]:
            unit = "百万円" if big else "円"
        elif g[5]:
            unit = "万円"
        elif g[2]:
            unit = "億円"
        elif g[1]:
            unit = "兆円"
        else:
            unit = "円"
        compound = bool((g[1] or g[2]) and unit not in ("億円", "兆円")) or bool(unit == "億円" and g[1])
        last = [x for x in (g[1], g[2], g[3], g[4], g[5]) if x][-1]
        out.append(Amount(m.start(), m.group(0).strip(), yen, unit, compound, _decimals_of_text(last)))
        taken.append((m.start(), m.end()))
    for m in _AMT_PLAIN_RE.finditer(span):
        if any(a <= m.start() < b for a, b in taken):
            continue
        yen = float(m.group(2).replace(",", "") + (m.group(3) or "")) * WRITTEN_SCALE[m.group(4)]
        out.append(Amount(m.start(), m.group(0).strip(), yen, m.group(4), False, _decimals_of_text(m.group(3) or "")))
    return sorted(out, key=lambda a: a.pos)


def written_amount_of(c):
    """claim の値と同じ金額の字(span の中)。見つからなければ None。"""

    unit = c.get("unit")
    v = c.get("value")
    if unit not in UNIT_SCALE or v is None or isinstance(v, bool):
        return None
    target = abs(v) * UNIT_SCALE[unit]
    for a in written_amounts(c.get("span")):
        if abs(a.yen - target) <= 1e-6 * max(1.0, target):
            return a
    return None


def doc_unit_of(claims):
    """書類で最も多い書いた単位(金額の claim の span から)。無ければ円。同数なら ``WRITTEN_ORDER`` の順。"""

    cnt = {}
    for c in claims:
        a = written_amount_of(c)
        if a is not None:
            cnt[a.unit] = cnt.get(a.unit, 0) + 1
    if not cnt:
        return "円"
    top = max(cnt.values())
    for u in WRITTEN_ORDER:
        if cnt.get(u) == top:
            return u
    return "円"


def word_amount_of(c, doc_unit):
    """語の主張(単位なし)の出典の値に使う単位・書き方: span の中で語にいちばん近い金額の字、無ければ書類で最も多い単位(桁は 0)。
    返すのは ``(単位, 兆・億を前に書く形か, 桁, 'span' か 'doc')``。"""

    span = unicodedata.normalize("NFKC", c.get("span") or "")
    word = c.get("word") or ""
    at = span.rfind(word) if word else -1
    best = None
    for a in written_amounts(span):
        d = abs(a.pos - at) if at >= 0 else a.pos
        if best is None or d < best[0]:
            best = (d, a)
    if best is not None:
        return best[1].unit, best[1].compound, best[1].decimals, "span"
    return doc_unit, False, 0, "doc"


def decimals_of(value):
    """claim の値の小数の桁数(26.2 → 1、40539.0 → 0)。"""

    try:
        t = repr(float(value))
    except (TypeError, ValueError):
        return 0
    if "e" in t or "E" in t or "n" in t:
        return 0
    frac = t.split(".", 1)[1] if "." in t else ""
    return 0 if frac.strip("0") == "" else len(frac)


def _D(x):
    return Decimal(repr(float(x))) if not isinstance(x, Decimal) else x


def _q(x, d):
    return x.quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)


def _plain(q, d):
    return format(q, ",.%df" % d)


def _trim(x4):
    """小数 4 桁に丸めた Decimal → 末尾の 0 を落とした字(fmt_num と同じ)。"""

    t = format(x4, ",.4f")
    return t.rstrip("0").rstrip(".") if "." in t else t


def _compound_text(total_small, small_scale, unit):
    """小さい単位で数えた量 ``total_small``(Decimal)→ 「26億23百万円」の形。"""

    rest, head = total_small, ""
    for big_scale, name in ((1e12, "兆"), (1e8, "億")):
        if big_scale > small_scale:
            k = Decimal(repr(big_scale)) / Decimal(repr(float(small_scale)))
            n = int(rest // k)
            if n:
                head += "%d%s" % (n, name)
                rest -= n * k
    if rest > 0:
        t = format(rest, ",.4f").rstrip("0").rstrip(".")
        return head + t + unit
    return head + "円"


def format_source(v, unit, compound, decimals, target=None):
    """円(率・ポイントは同じ単位)の値 ``v`` を、書いた単位 ``unit`` と桁 ``decimals`` で。丸めた字を先に、丸める前の値が違えば括弧で後に。
    負なら ``△``。兆・億を前に書く形(``compound``)は「26億24百万円」の形で、単位の前に空白を置かない。

    ``target``(同じ単位で数えた文の値、Decimal)を渡すと、丸め方を四捨五入と切り捨てのうち**文の値と同じになる方**にする
    (どちらも違えば四捨五入。「一致」の節の主表示。司令塔の判断 2026-10-21)。渡さなければ四捨五入。括弧の生の値は変わらない。"""

    d = _D(v)
    neg = d < 0
    a = abs(d)

    def pick(x):
        half = _q(x, decimals)
        if target is not None and half != _q(target, decimals):
            floor = x.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_DOWN)
            if floor == _q(target, decimals):
                return floor
        return half

    if unit in WRITTEN_SCALE:
        scale = Decimal(repr(float(WRITTEN_SCALE[unit])))
        s_small = a / scale
        qd = pick(s_small)
        q4 = _q(s_small, 4)
        if compound:
            main = _compound_text(qd, WRITTEN_SCALE[unit], unit)
            raw = _compound_text(q4, WRITTEN_SCALE[unit], unit)
        else:
            main = _plain(qd, decimals) + " " + unit
            raw = _trim(q4)
        differs = q4 != qd
    else:
        qd = pick(a)
        q4 = _q(a, 4)
        main = _plain(qd, decimals) + (" " + unit if unit else "")
        raw = _trim(q4)
        differs = q4 != qd
    sign = NEG if neg else ""
    text = (sign if qd != 0 else "") + main
    if differs:
        text += "(" + sign + raw + ")"
    return text


_RATE_RE = re.compile(r"(?<![\d.,])(△|▲|-|マイナス)?\s*(\d+(?:\.\d+)?)\s*(%|ポイント)")


def written_rate_sign(c):
    """率・ポイントの claim の値と同じ数の字(span の中)の符号の字。符号が無ければ ``""``、同じ数の字が無ければ None。"""

    unit = c.get("unit")
    v = c.get("value")
    if unit not in RATE_UNITS or v is None or isinstance(v, bool):
        return None
    u = unicodedata.normalize("NFKC", unit)
    for m in _RATE_RE.finditer(unicodedata.normalize("NFKC", c.get("span") or "")):
        if m.group(3) == u and abs(float(m.group(2)) - abs(v)) < 1e-9:
            return m.group(1) or ""
    return None


def claim_value_written(c):
    """文の値: span に同じ金額の字があればその字のまま、無ければ ``claim_value_ja``。"""

    a = written_amount_of(c)
    if a is not None:
        return a.text
    sign = written_rate_sign(c)
    if sign is not None:                  # 率・ポイント: 数は今までの書き方、符号は文の字のまま(文に △ があれば △、- なら -、無ければ付けない)
        return sign + fmt_num(abs(c["value"])) + " " + c["unit"]
    return claim_value_ja(c)


def source_value_report(c, doc_unit="円", prefer_sentence=False):
    """出典の値(報告の字)。``(字, 種類)`` を返す。種類:

    - ``written``: 金額の claim で span に同じ金額の字がある。文の単位・書き方・桁に直す。
    - ``unread``: 金額の claim だが span に同じ金額の字が無い(読み取れない行)。claim の単位のまま、claim の値の桁で。
    - ``word_span`` / ``word_doc``: 語の主張。span の中でいちばん近い金額の字の単位 / 書類で最も多い単位。
    - ``other``: 率・ポイント・その他の単位(claim の値の桁で、単位は claim のまま)。
    recomputed が無ければ「―」(``none``)。

    ``prefer_sentence`` は「一致」の節の主表示用: 丸めを四捨五入と切り捨てのうち文の値と同じになる方にする(``format_source`` の ``target``)。"""

    v = c.get("recomputed")
    if v is None:
        return "―", "none"
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return cell(v), "other"
    unit = c.get("unit") or ""
    val = c.get("value")
    if unit in UNIT_SCALE and val is not None and not isinstance(val, bool):
        a = written_amount_of(c)
        if a is not None:
            tgt = Decimal(repr(a.yen)) / Decimal(repr(float(WRITTEN_SCALE[a.unit]))) if prefer_sentence else None
            return format_source(v, a.unit, a.compound, a.decimals, tgt), "written"
        tgt = abs(_D(val)) if prefer_sentence else None
        return format_source(v, unit, False, decimals_of(val), tgt), "unread"
    if not unit and val is None:
        wunit, compound, dec, how = word_amount_of(c, doc_unit)
        return format_source(v, wunit, compound, dec), "word_" + how
    tgt = abs(_D(val)) if (prefer_sentence and val is not None and not isinstance(val, bool)) else None
    return format_source(v, unit, False, decimals_of(val) if val is not None else 0, tgt), "other"


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


_TRAIL_NUM_RE = re.compile(r"[\d][\d,.]*$")


def trim_partial_number(span):
    """抜粋の両端が数の字の途中で切れているとき、その数を落とす(封 §1-9: 切るなら数の前か後)。

    - 後ろ: 末尾が数字(と桁区切り・小数点)で終わる = 単位や後ろの字が見えない数。落とす(「…支出が6」→「…支出が」)。
    - 前: 先頭が小数点か桁区切りで始まる(「.2ポイント増」)= 前の字が切れた数。その数だけ落とす。
    落とした結果が空になるときは元の字のまま。"""

    t = span or ""
    out = t
    m = _TRAIL_NUM_RE.search(out)
    if m:
        out = out[:m.start()]
    m = re.match(r"^[.,]\d[\d,.]*", out)
    if m:
        out = out[m.end():]
    return out if out.strip() else t


def _excerpt_trimmed(c):
    return cell(trim_partial_number(c.get("span"))) or "―"


TITLE_FALLBACK = "文章と出典(XBRL)の照合"


def _title(src, dei):
    """表題。``dei``(提出者名・書類の種類・当期の期末日が全部ある)なら「<提出者名> <書類の種類>(<期末日>)の数の点検」、無ければ今の字。"""

    if dei and dei.get("filer") and dei.get("doctype") and dei.get("period_end"):
        return "# %s %s(%s)の数の点検" % (cell(dei["filer"]), cell(dei["doctype"]), cell(dei["period_end"]))
    return "# %s ― %s" % (TITLE_FALLBACK, cell(src))


LEGEND = "出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)"
FOOT_LINE = "<sub>書類の指紋・道具の版・照合した文章の指紋は、同じ名前の `.provenance.json`(機械用)に置いた。</sub>"


def render_markdown(out, labels=None, full=False, dei=None):
    """入口の出力(dict)→ Markdown(str)。純粋関数。``labels`` は ``load_labels`` の表(None は空)、``dei`` は ``dei_from_zip`` の結果(None は表題が今の字)。"""

    labels = labels or {}
    doc = out.get("document") or {}
    inp = out.get("input") or {}
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
    doc_unit = doc_unit_of(claims)

    src = (inp.get("instance_source") or "(書類)").rsplit("/", 1)[-1]
    L = []
    L.append(_title(src, dei))
    L.append("")
    L.append("文章の中の数と増減の語を、同じ書類の XBRL の値と突き合わせた。判定は道具が出したまま並べ替えている(足していない)。")
    L.append("")
    L.append("| 区分 | 件数 | 意味 |")
    L.append("|---|---|---|")
    L.append("| %s | %s | 出典に当たる値があり、文の値と**違う**。文の誤りか、当てた出典の誤りかは決めない |" % (SECTION_MISMATCH, fmt_num(len(by[SECTION_MISMATCH]))))
    L.append("| %s | %s | 道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる |" % (SECTION_CHECK, fmt_num(len(by[SECTION_CHECK]))))
    L.append("| %s | %s | 出典(XBRL)にその数は無い(株数・人数など) |" % (SECTION_OUT, fmt_num(len(by[SECTION_OUT]))))
    L.append("| %s | %s | 主語が無い・目標や計画・区分が決まらない。道具は判断しない |" % (SECTION_NOT_JUDGED, fmt_num(len(by[SECTION_NOT_JUDGED]))))
    L.append("| %s | %s | 出典の値と一致した |" % (SECTION_MATCH, fmt_num(len(by[SECTION_MATCH]))))
    if by[SECTION_OTHER]:
        L.append("| %s | %s | 上のどれでもない状態 |" % (SECTION_OTHER, fmt_num(len(by[SECTION_OTHER]))))
    L.append("| 合計 | %s | |" % fmt_num(total))
    L.append("")

    def value_row(c, prefer_sentence=False):
        return "| %s | %s | %s | %s | %s |" % (
            cell(c.get("id")), _excerpt(c), cell(claim_value_written(c)) or "―",
            cell(source_value_report(c, doc_unit, prefer_sentence)[0]), cell(source_ja(c.get("pointers"), labels)) or "―")

    # 1. 違う
    rows = by[SECTION_MISMATCH]
    L.append("## 1. %s ― %s 件" % (SECTION_MISMATCH, fmt_num(len(rows))))
    L.append("")
    L.append("出典に当たる値は見つかったが、文の値と違う。文の誤りか、当てた出典の誤りかは、この表では決めない。「出典の値」は文と同じ単位に直してある。")
    L.append("")
    L.append(LEGEND)
    L.append("")
    if rows:
        L.append("| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |")
        L.append("|---|---|---|---|---|")
        for c in rows:
            L.append(value_row(c))
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
                cell(c.get("id")), _excerpt(c), cell(claim_value_written(c)) or "―", cell(reason_ja(c.get("reason")))))
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
                L.append("- %s: %s(%s)" % (cell(c.get("id")), _excerpt_trimmed(c), cell(reason_ja(c.get("reason")))))
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
    L.append(LEGEND)
    L.append("")
    if full:
        if rows:
            L.append("| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |")
            L.append("|---|---|---|---|---|")
            for c in rows:
                L.append(value_row(c, True))
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
                cell(c.get("id")), cell(c.get("state")), _excerpt(c), cell(claim_value_written(c)) or "―",
                cell(reason_ja(c.get("reason")))))
        L.append("")

    # 5. 末尾(封 §1-7): 指紋・sha256 は本文に書かず、同じ名前の .provenance.json(機械用)へ。
    L.append("---")
    L.append("")
    L.append(FOOT_LINE)
    L.append("")
    return "\n".join(L)


def body_sha256(md):
    return hashlib.sha256(md.encode("utf-8")).hexdigest()


def render_provenance(out, md, label_meta=None, dei=None, zip_sha256=None):
    """機械用の記録(封 §1-7)。本文から外した字(入力の sha256・engine の指紋・profile・道具)と、本文の sha256、ラベルの file の sha256(と使ったか)。
    同じ入力から同じバイト列(時刻を入れない・key は並べる)。"""

    inp = out.get("input") or {}
    rec = {
        "report": {"module": "adapters.xbrl.report_customer", "body_sha256": body_sha256(md)},
        "input": {"instance_source": inp.get("instance_source"), "zip_sha256": inp.get("zip_sha256"),
                  "zip_bytes": inp.get("zip_bytes"), "text_replaced": inp.get("text_replaced")},
        "engine": out.get("engine") or {},
        "profile": out.get("profile"),
        "tool": out.get("tool"),
        "labels": sorted(label_meta or [], key=lambda x: x.get("file") or ""),
        "title": dei,
        "zip_given": ({"sha256": zip_sha256, "same_as_input": zip_sha256 == inp.get("zip_sha256")} if zip_sha256 else None),
    }
    return json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def provenance_path(md_path):
    return os.path.splitext(md_path)[0] + ".provenance.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--in", dest="inp", required=True, help="verify_document の出力 JSON")
    parser.add_argument("--out", required=True, help="書き出す Markdown(隣に <名前>.provenance.json も書く)")
    parser.add_argument("--labels", default=None, help="標準タクソノミのラベル file(*_lab.xml)の dir。名簿に在る file だけ読む。無ければ要素名")
    parser.add_argument("--zip", default=None, help="書類の ZIP(書類自身のラベル *_lab.xml で会社ごとの要素・区分を日本語に。DEI で表題)")
    parser.add_argument("--full", action="store_true", help="一致の行も出す")
    args = parser.parse_args(argv)
    with io.open(args.inp, "r", encoding="utf-8") as f:
        out = json.load(f)
    labels, meta = load_labels_with_meta(args.labels, args.zip)
    dei, zsha = None, None
    if args.zip:
        dei = dei_from_zip(args.zip, (out.get("input") or {}).get("instance_source"))
        with open(args.zip, "rb") as fh:
            zsha = hashlib.sha256(fh.read()).hexdigest()
    md = render_markdown(out, labels, args.full, dei)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    with io.open(provenance_path(args.out), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_provenance(out, md, meta, dei, zsha))
    print("written:", args.out, "claims:", len(out.get("claims") or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
