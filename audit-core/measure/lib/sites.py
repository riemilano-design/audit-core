# -*- coding: utf-8 -*-
"""Find the places in a document where each error type can be built.

Separated from the applier so the catalogue can be counted and tested
without writing any file.

Vocabulary used in the record:

``T1_VALUE``      数字の置換 ― the replacement value appears nowhere in the
                  reference numbers, so a pointer-then-compare check must
                  disagree.
``T2_UNIT``       単位のずれ ― the digits are untouched and the unit token is
                  swapped inside its family (円/千円/百万円, 手/局/局面).
``T3_ABSENT``     原文に無い数 ― a sentence is inserted asserting a quantity
                  about a subject that the underlying data does not contain.
``T5_COINCIDENT`` 値が偶然一致して参照先が違う ― the replacement value is the
                  true value *of a different fact*. A check that asks only
                  "does some fact have this value?" passes; one that resolves
                  the pointer first does not. This is the known worst hole.

Type 2 and 3 of the human decision's six (期間・母集団の入れ替え) are not
built here: deciding which period or population a sentence inherits is a
reading of the text, not a transformation of it. Those sites are catalogued
by :func:`human_sites` and handed to a person.
"""

import contextlib
import re

from . import numbers as N
from . import scales as SC

TOL = 1e-9

# Period and population phrases. A sentence holding one of these is a
# candidate for the human-built types; the phrase itself is what a person
# would swap.
# Keyed by document kind: the shogi booklet and a filing name their periods
# and populations in completely different words, and a list tuned to one
# finds nothing in the other (measured: the XBRL list found 0 sites in the
# booklet).
PERIOD_PHRASES = {
    "xbrl": [
        "当連結会計年度", "前連結会計年度", "当事業年度", "前事業年度",
        "当期", "前期", "前年同期", "前年度", "当四半期", "翌連結会計年度",
    ],
    "shogi": ["今回", "次の 25 局", "直近", "前回", "今期"],
}
POPULATION_PHRASES = {
    "xbrl": [
        "連結", "単体", "全社", "当社グループ", "持分法適用会社", "連結子会社",
    ],
    "shogi": ["攻め", "自玉側", "先手", "後手", "全局", "前半", "後半"],
}


def _scaled(value, unit):
    """``value`` as written in plain 円 (or in whatever base ``unit``'s
    family uses), via :mod:`lib.scales`.

    直し 2026-10-08(封 第 2 部): before this, a token's digits and a
    reference's raw value were compared with no multiplier at all, so
    "短期貸付による支出 50,000千円"(5 千万円)matched a reference actually
    holding 50,000 **円** -- 1000 倍違う値が一致した(measured: 29 件の
    正しい結びを落とし、誤った 1 件だけを採っていた)。Applying the same
    lookup to both sides keeps it symmetric: a reference's own unit is
    never 千円/百万円/億円/兆円 in this material (measured: always 円 or
    円/株), so :func:`lib.scales.scaled_value` is a no-op there.
    """
    return SC.scaled_value(value, unit)


def _value_index(refs):
    """value -> list of refs with that value (exact float equality is wrong
    for floats, so this buckets on a rounded key and confirms with TOL).

    Keyed on the *scaled* value (see :func:`_scaled`), not the raw one."""
    idx = {}
    for r in refs:
        idx.setdefault(round(_scaled(r["value"], r.get("unit")), 6), []).append(r)
    return idx


def _matches(value, unit, vindex):
    return vindex.get(round(_scaled(value, unit), 6), [])


def _unit_compatible(token_unit, ref_unit):
    """True when the token's unit does not contradict the ref's unit.

    A *missing* unit used to count as compatible, which is what let section
    numbers and months resolve against arbitrary facts. Callers must now
    screen tokens with :func:`numbers.is_quantity` first, and identification
    (:func:`identified_sites`) additionally requires an explicit unit.
    """
    if token_unit is None or ref_unit is None:
        return True
    if token_unit == ref_unit:
        return True
    return N.unit_family(token_unit) == N.unit_family(ref_unit)


def _label_words(label):
    """Distinctive fragments of a reference label, for corroboration."""
    if not label:
        return []
    parts = re.split(r"[\s、。「」『』()()/／・,:：]+", str(label))
    return [w for w in parts if len(w) >= 3]


def _line_of(text, pos):
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    return text[a:b if b >= 0 else len(text)]


def data_bearing_sites(text, refs):
    """Quantity tokens whose value appears somewhere in the reference numbers.

    This is weaker than identification on purpose. It says "this number
    carries data", not "this number refers to fact X".
    """
    vindex = _value_index(refs)
    out = []
    for t in N.scan(text):
        if not N.is_quantity(text, t):
            continue
        cands = [r for r in _matches(t.value, t.unit, vindex) if _unit_compatible(t.unit, r.get("unit"))]
        if cands:
            out.append((t, cands))
    return out


def identified_sites(text, refs):
    """Quantity tokens whose reference can actually be pinned down.

    Three conditions, all needed:

    1. exactly one reference carries the value (after the unit check),
    2. the token carries an explicit unit **or** a distinctive fragment of
       the reference's label appears on the same line,
    3. the token is a quantity.

    Condition 2 is what the first version lacked. Without it, a bare integer
    that happens to match one of 900 references was called "identified", and
    the record named a reference the sentence was not about.

    Tokens that fail only condition 1 or 2 are not errors to build by
    machine: deciding what a number refers to is a reading of the text, so
    they are offered to a person instead (see :func:`unidentified_sites`).
    """
    vindex = _value_index(refs)
    out = []
    for t in N.scan(text):
        if not N.is_quantity(text, t):
            continue
        cands = [r for r in _matches(t.value, t.unit, vindex) if _unit_compatible(t.unit, r.get("unit"))]
        by_key = {r["key"]: r for r in cands}
        if len(by_key) != 1:
            continue
        ref = list(by_key.values())[0]
        if t.unit is None:
            line = _line_of(text, t.start)
            if not any(w in line for w in _label_words(ref.get("label"))):
                continue
        else:
            # A missing unit on the *reference* side is not a licence to
            # match. Measured 2026-10-08: "149百万円" was identified as an
            # employee count of 149, because that reference carried no unit.
            if ref.get("unit") is None:
                continue
            if N.unit_family(t.unit) != N.unit_family(ref.get("unit")):
                continue
        out.append((t, ref))
    return out


def unidentified_sites(text, refs):
    """Quantity tokens that carry data but cannot be pinned to one fact.

    Reported so the count is visible rather than silently dropped: these are
    the places where a machine cannot build 型 5 and a person must.
    """
    ident = {(t.start, t.end) for t, _ in identified_sites(text, refs)}
    out = []
    for t, cands in data_bearing_sites(text, refs):
        if (t.start, t.end) in ident:
            continue
        out.append({
            "span": [t.start, t.end],
            "text": t.text,
            "unit": t.unit,
            "candidate_ref_keys": sorted({r["key"] for r in cands})[:8],
            "candidate_count": len({r["key"] for r in cands}),
            "line": _line_of(text, t.start).strip()[:160],
        })
    return out


def t1_sites(text, refs):
    """数字の置換.

    Identification is **not** required. Whatever the sentence refers to, a
    replacement value that no reference carries is wrong. What is required is
    that the number carries data (its own value appears in the references) and
    that it is a quantity, so that a non-claim like a heading number is not
    counted as an injected error it could never have become.
    """
    return [
        {"type": "T1_VALUE", "token": t, "candidates": cands}
        for t, cands in data_bearing_sites(text, refs)
    ]


# A coincident value must be close enough in size to be plausible. Measured
# 2026-10-08: without this, "連結子会社は 3" became "連結子会社は 25568000"
# by borrowing a cash-flow amount, which tests nothing.
MAGNITUDE_RATIO = 10.0

# ---- 規則 T5Y(封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §0-2・§1)-----------------
# 注入の仕掛けの T5(値が偶然一致して参照先が違う)を、円族の数(12.3億円・14億3,300万円)
# にも作れるようにする。切り替えは 1 つ。既定は偽で、偽のとき ``t5_sites`` は 1 byte も
# 変えない(前の便の記録と、``select`` を記録と突き合わせて再計算する門を壊さないため)。
# 真にするのは T5Y の測定 script の process の中だけ(``t5_yen_on`` の with の中)。
# 真のとき: 篩と「値が違う」を書かれた単位の値でなく円に直した値(``_scaled``)で比べ、
# さらに相手ごとに「倍率で割って token の形で描き、読み直した円の値が相手の値と
# 書かれた桁の半分以内・描いた字が元の字と違う・読み直した値が元の値から桁の半分より
# 離れる」相手だけを残す。
t5_yen_2026_11_06 = False


@contextlib.contextmanager
def t5_yen_on():
    """切り替え ``t5_yen_2026_11_06`` を with の中だけ真にする。出るときは必ず元の値に戻す。"""
    global t5_yen_2026_11_06
    old = t5_yen_2026_11_06
    t5_yen_2026_11_06 = True
    try:
        yield
    finally:
        t5_yen_2026_11_06 = old


def t5_precision(t):
    """token の書かれた最後の桁の大きさ(円)。複合は最後の位の単位(groups の字 + 円 の倍率の最小)、
    少数は 10^-小数の桁 × 倍率、整数は 1 × 倍率。"""
    factor = SC.scale_of(t.unit) or 1
    if getattr(t, "groups", None) is not None:
        return min(SC.scale_of(g[0] + "円") or 1 for g in t.groups)
    if t.has_frac:
        return (10 ** -len(t.text.split(".")[1])) * factor
    return 1 * factor


def t5_readback(t, other_value):
    """相手の値(円)を token の形で描いて読み直す。(描いた字, 読み直した円の値)。token が 1 つに
    読めなければ (描いた字, None)。"""
    cand = other_value / float(SC.scale_of(t.unit) or 1)
    rendered = N.render_value(cand, t)
    toks = N.scan(rendered + (t.unit or ""))
    if len(toks) != 1:
        return rendered, None
    return rendered, _scaled(toks[0].value, toks[0].unit)


def t5_readable(t, other_value):
    """相手の値で T5 を作ったとき、読み直しが相手の値と書かれた桁の半分以内・描いた字が元の字と違い・
    読み直した値が元の値から桁の半分より離れるか。"""
    rendered, back = t5_readback(t, other_value)
    if back is None or rendered == t.text:
        return False
    half = t5_precision(t) / 2.0
    return abs(back - other_value) <= half + TOL and abs(back - _scaled(t.value, t.unit)) > half


def t5_sites_yen(text, refs, readback=True):
    """規則 T5Y の ``t5_sites``。``readback`` が偽なら篩(円に直した規模と値の違い)だけ。"""
    out = []
    for t, r in identified_sites(text, refs):
        v = _scaled(t.value, t.unit)
        lo, hi = v / MAGNITUDE_RATIO, v * MAGNITUDE_RATIO
        others = [
            o for o in refs
            if o["key"] != r["key"]
            and str(o.get("label")) != str(r.get("label"))
            and abs(o["value"] - v) > TOL
            and o["value"] > 0
            and lo <= o["value"] <= hi
            and _unit_compatible(t.unit, o.get("unit"))
        ]
        if readback:
            others = [o for o in others if t5_readable(t, o["value"])]
        if others:
            out.append({"type": "T5_COINCIDENT", "token": t, "ref": r, "others": others})
    return out



def t5_sites(text, refs):
    """値が偶然一致して参照先が違う.

    Needs identification, because the injected value must be guaranteed
    *different* from what the sentence truly asserts. The borrowed fact must
    also carry a different label (the same element in another context reads
    as the same thing in the record) and a comparable magnitude.
    """
    if t5_yen_2026_11_06:
        return t5_sites_yen(text, refs)
    out = []
    for t, r in identified_sites(text, refs):
        lo, hi = t.value / MAGNITUDE_RATIO, t.value * MAGNITUDE_RATIO
        others = [
            o for o in refs
            if o["key"] != r["key"]
            and str(o.get("label")) != str(r.get("label"))
            and abs(o["value"] - t.value) > TOL
            and o["value"] > 0
            and lo <= o["value"] <= hi
            and _unit_compatible(t.unit, o.get("unit"))
        ]
        if others:
            out.append({"type": "T5_COINCIDENT", "token": t, "ref": r, "others": others})
    return out


def t2_sites(text, refs):
    """単位のずれ. Site = any token carrying a unit that has a sibling in its
    family. The digits are not touched, so no reference resolution is needed:
    the error is in what the number counts.

    ``is_quantity`` must be applied here exactly as it is in
    :func:`data_bearing_sites` / :func:`identified_sites`: an ordinal or a
    section cross-reference can carry a recognised unit token (「第2回」's
    "回" is a real member of ``UNIT_FAMILIES``) without being a quantity.
    Measured 2026-10-08: without this screen, "第2回新株予約権の発行" became
    a 型 2 site and was actually injected as "第2局新株予約権の発行" in
    ``S100Z4B6``."""
    out = []
    for t in N.scan(text):
        if t.unit is None:
            continue
        if not N.is_quantity(text, t):
            continue
        fam = N.unit_family(t.unit)
        siblings = []
        if fam and len(N.UNIT_FAMILIES[fam]) > 1:
            siblings = [u for u in N.UNIT_FAMILIES[fam] if not N.same_unit(u, t.unit)]
        elif t.unit in N.COUNT_FAMILY:
            siblings = [u for u in N.COUNT_FAMILY if not N.same_unit(u, t.unit)]
        if siblings:
            out.append({"type": "T2_UNIT", "token": t, "siblings": siblings})
    return out


# Subjects that must not exist in the data or the text. Verified at build
# time; a template whose subject turns up in either is dropped rather than
# used, so this list can never silently assert something true.
ABSENT_TEMPLATES = {
    "shogi": [
        ("自陣三段目への打ち込み", "%sは %s 局面でした。"),
        ("角頭を狙った手", "%sは %s 手ありました。"),
        ("連続王手の局", "%sは %s 局でした。"),
        ("飛車を自陣に引いた局", "%sは %s 局でした。"),
        ("桂を跳ねた直後に取られた手", "%sは %s 手ありました。"),
        ("同じ駒を 3 回続けて動かした局", "%sは %s 局でした。"),
    ],
    "xbrl": [
        ("海外関連会社売上高", "%sは%s百万円となりました。"),
        ("研究開発受託収益", "%sは%s百万円であります。"),
        ("為替予約評価差額", "%sは%s百万円となっております。"),
        ("特定顧客向け保守収益", "%sは%s百万円となりました。"),
        ("試作品評価費用", "%sは%s百万円であります。"),
        ("譲渡予定資産評価益", "%sは%s百万円となっております。"),
    ],
}


def t3_sites(text, refs, kind):
    """原文に無い数. Site = a sentence boundary to insert at, paired with a
    template whose subject is absent from both the text and the data."""
    labels = " ".join(str(r.get("label") or "") for r in refs)
    templates = [
        (subj, tpl) for subj, tpl in ABSENT_TEMPLATES.get(kind, [])
        if subj not in text and subj not in labels
    ]
    if not templates:
        return []
    spans = N.sentence_spans(text)
    # Insert only after a sentence that already ends cleanly, and not at the
    # very start (a heading) or the very end.
    anchors = [
        b for (a, b) in spans[1:-1]
        if b < len(text) and text[b - 1] in "。\n" and text[a:b].strip()
    ]
    return [{"type": "T3_ABSENT", "at": at, "templates": templates} for at in anchors]


def human_sites(text, kind):
    """期間・母集団の入れ替え ― catalogued, not built.

    Returns one entry per (sentence, phrase) pair, with the alternatives a
    person could swap in. Building these needs a reading of which period or
    population the sentence inherits from its neighbours, which is the thing
    under measurement; a machine that guessed it would be writing its own
    answer key.
    """
    spans = N.sentence_spans(text)
    found = []
    for si, (a, b) in enumerate(spans):
        s = text[a:b]
        for kindname, table in (("period", PERIOD_PHRASES), ("population", POPULATION_PHRASES)):
            phrases = table.get(kind, [])
            for p in phrases:
                off = s.find(p)
                if off < 0:
                    continue
                alts = [q for q in phrases if q != p and q in text]
                found.append({
                    "kind": kindname,
                    "sentence_index": si,
                    "sentence_span": [a, b],
                    "phrase": p,
                    "phrase_span": [a + off, a + off + len(p)],
                    "alternatives_present_in_document": alts,
                    "sentence": s.strip(),
                })
    return found
