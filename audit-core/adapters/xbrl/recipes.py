# -*- coding: utf-8 -*-
"""Build Core ``Recipe`` objects for one document under one profile
(``P1`` or ``P5F``).

This module (together with :mod:`run`) is the only place in the Adapter
that imports ``audit_core`` (the Core). The claim-building control flow
below is a transcription of the ``main()`` functions in
``fixtures/xbrl/xbrl_probe.py`` / ``xbrl_probe3.py`` / ``xbrl_probe4.py`` /
``xbrl_probe5.py`` (the P-8-fixed, member-aware, Claim-level-marker
behaviour that ``xbrl_probe5.py``'s ``main`` exercises with ``FIX_ON=1``),
re-expressed using the module-split functions in :mod:`instance`,
:mod:`extract`, :mod:`vocabulary` instead of the originals' inline code.
It is not imported from the originals.

The mapping from a raw (script-shaped) claim to the Core's four layers
(``Claim`` / ``Modifiers`` / ``Pointer`` / ``Contract``) and to the two
short-circuit reasons on ``Recipe`` is a transcription of
``fixtures/xbrl/make_core_expectation.py`` (``map_claim``, ``state_of``,
``STATE``, ``period``, ``member_of``), which is itself the one writing rule
C-0 fixed for turning script output into the Core's expectation JSON.
"""

import dataclasses
import io
import re
import unicodedata
import zipfile

import audit_core as core

from . import extract as E
from . import instance as I
from . import vocabulary as V

# ---------------------------------------------------------------------------
# C-0 §2 (fixtures/xbrl/make_core_expectation.py: STATE). Fixed by the human
# decision of 2026-10-06; not to be changed by this Adapter.
# ---------------------------------------------------------------------------
UNBOUND_REASON_STATE = {
    "no_element": "POINTER_NOT_FOUND",
    "no_element(unit not in XBRL)": "POINTER_NOT_FOUND",
    "no_element(ratio without fact)": "POINTER_NOT_FOUND",
    "no_prior_member_context": "POINTER_NOT_FOUND",
    "no_subject": "UNVERIFIABLE",
    "ambiguous(member)": "UNVERIFIABLE",
    "ambiguous(elements)": "UNVERIFIABLE",
    "state_word(no line)": "UNVERIFIABLE",
    "prior is 0": "UNVERIFIABLE",
    # Core 接続 C-1g §1-3(人間の決定、2026-10-06、profile P6 のみ)。既存 9 件
    # の写し元(frozen の C-0 §2)は変えず、新しい理由を 1 件だけ足す。
    "no_element(point without prior phrase)": "POINTER_NOT_FOUND",
    # Core 接続 C-1h §1-2/§1-3(人間の決定、2026-10-06、profile P7 のみ)。
    "target_or_plan": "UNVERIFIABLE",
    "no_element(text needs money fact)": "POINTER_NOT_FOUND",
    "no_element(no prior for text)": "POINTER_NOT_FOUND",
    # XBRL 直し §1b(人間の決定、2026-10-08、profile P8 のみ)。前々期の値が
    # 無いとき、当期の残高や偶然一致した fact で代用せず止める。
    "no_element(no prior2 for prior-year diff)": "POINTER_NOT_FOUND",
}


def _state_of(reason, result):
    """make_core_expectation.py: state_of の写し。"""

    if result in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE"):
        return result
    r = reason or ""
    if r in UNBOUND_REASON_STATE:
        return UNBOUND_REASON_STATE[r]
    if r.startswith("ambiguous("):
        return "UNVERIFIABLE"
    raise KeyError(r)


def _ctx_of(pointer_text):
    # 'xbrl:name@context' -> (name, context)
    name, ctx = pointer_text[5:].split("@")
    return name, ctx


def _period(ctx):
    m = re.match(r"(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)", ctx)
    return (m.group(1), m.group(2)) if m else ("?", "?")


def _member_of_ctx(ctx):
    parts = ctx.split("_", 1)
    return parts[1] if len(parts) > 1 and "Member" in parts[1] else None


def _pointer_list(raw_pointer):
    if raw_pointer is None:
        return []
    if isinstance(raw_pointer, list):
        return list(raw_pointer)
    return [raw_pointer]


# ---------------------------------------------------------------------------
# Raw claim construction (one document, one profile). Shape matches the
# probe scripts' claim dicts: id / sentence / span / value / unit / subject /
# form / pointer / bound / reason / result / recomputed / match / member /
# member_source / sign_token / word.
# ---------------------------------------------------------------------------

# A1(主語の規則の直し、人間の追加指示、2026-10-08): 金額が向きの語に
# **直に付いている**と見なす形。字で書く。
# ``""`` は「金額の直後がそのまま向きの語」(「30,950千円増加」)。
DIRECTION_AMOUNT_GAPS = ("", "の")
DIFFERENCE_NOUNS = ("増加額", "減少額", "増加分", "減少分")

_MONEY_UNIT_RE_AFTER = re.compile(r"(増加|減少|増|減)")
_MONEY_DIFF_PHRASE_RE = re.compile(r"(増加額|減少額|比べて)")
_PREV_YEAR_PHRASE = "前連結会計年度は"

# ---------------------------------------------------------------------------
# Core 接続 C-1g §1-2(人間の決定、2026-10-06): CF 流量項目の符号の規約。
# profile.flow_sign が真のときだけ使う(P1/P5F は常に偽で、この一群は呼ばれ
# ない)。
# ---------------------------------------------------------------------------
_FLOW_DIRECTION_RE = re.compile(r"増加額|減少額|増加|減少")


def _flow_direction_word(s, subj, a, b):
    """主語の終わりから数の開始(a)まで、または数の終わり(b)の直後 4 字に
    増加額/減少額/増加/減少 があれば +1/-1、無ければ None。
    """

    if not subj:
        return None
    head_end = s[:a].rfind(subj)
    if head_end < 0:
        return None
    window1 = s[head_end + len(subj):a]
    window2 = s[b:b + 4]
    for window in (window1, window2):
        m = _FLOW_DIRECTION_RE.search(window)
        if m:
            return 1 if m.group(0).startswith("増") else -1
    return None


def _apply_flow_sign(claim, s, a, b, rounding=None, flow_base=None, mag_trunc=False):
    """§1-2。直接値の Claim が CF 流量項目の 1 件の fact に束縛されていて、
    向きの語があるときだけ、claim["flow_convention"]/["claim_direction"] を
    足し、normalization の札を abs を落とした梯子(round/truncate)に直す。
    derived diff(pointer がリスト)や value_only(subject 無し)には触れない。
    """

    if not claim.get("bound") or not claim.get("subject"):
        return
    pointer = claim.get("pointer")
    if not isinstance(pointer, str) or not pointer.startswith("xbrl:"):
        return
    name = pointer[5:].split("@")[0]
    conv = _flow_sign_of(name, flow_base)
    if conv is None:
        return
    direction = _flow_direction_word(s, claim["subject"], a, b)
    if direction is None:
        return
    claim["flow_convention"] = conv
    claim["claim_direction"] = direction
    target_abs = abs(claim["value"]) * claim["unit_scale"]
    how = V.match_value(abs(claim["recomputed"]), target_abs, claim["claim_scale"], rounding, mag_trunc)
    if how is not None:
        claim["match"] = how


# ---------------------------------------------------------------------------
# Core 接続 C-1g §1-3(人間の決定、2026-10-06): ポイント差の derived form。
# profile.point_diff が真のときだけ使う。
# ---------------------------------------------------------------------------
_POINT_PRIOR_PHRASE_RE = re.compile(r"前期比|前連結会計年度|前年")
_POINT_DIRECTION_RE = re.compile(r"増加|増|減少|減|下回")


PCT_TOLERANCE_DEFAULT = 0.15   # P1〜P17 の % の許容(字で留める)
_DECIMALS_RE = re.compile(r"\d+(?:[.．](\d+))?")


def pct_tolerance(profile, s, a, b):
    """P18: % の主張の許容。旗が偽なら ``PCT_TOLERANCE_DEFAULT``。真なら、数の字
    ``s[a:b]`` に書かれた小数の桁 d から ``0.5 * 10**(-d) + 0.01``
    (1 桁 → 0.06、0 桁 → 0.51、2 桁 → 0.015)。"""

    if profile is None or not getattr(profile, "pct_tolerance_from_decimals", False):
        return PCT_TOLERANCE_DEFAULT
    m = _DECIMALS_RE.search(s[a:b])
    d = len(m.group(1)) if (m and m.group(1)) else 0
    return 0.5 * (10 ** (-d)) + 0.01


def _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol=PCT_TOLERANCE_DEFAULT):
    """単位 ポイント・主語あり(呼び出し側の条件)の Claim を、前期の比率
    との derived diff として組む。前期の語が無ければ新しい理由
    ``no_element(point without prior phrase)``、前期の語があっても当期・
    前期の pure の対が見つからなければ ``no_element``。
    """

    window = s[max(0, a - 25):a]
    if not _POINT_PRIOR_PHRASE_RE.search(window):
        claim["reason"] = "no_element(point without prior phrase)"
        return
    dm = _POINT_DIRECTION_RE.search(s[b:b + 10])
    sign = -1 if (dm and dm.group(0) in ("減少", "減", "下回")) else 1
    cur = [f for f in I.facts_for(elems, facts, contexts, member)
           if f["context"].startswith("CurrentYear") and (f["unit"] or "").lower().startswith("pure")]
    pri = [f for f in I.facts_for(elems, facts, contexts, member)
           if f["context"].startswith("Prior1Year") and (f["unit"] or "").lower().startswith("pure")]
    pairs = [(c, p) for c in cur for p in pri
             if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
    if not pairs:
        claim["reason"] = "no_element"
        return
    c, p = pairs[0]
    claim["form"] = "derived_value"
    claim["value"] = sign * num
    claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "formula:a-b(pure)"]
    claim["bound"] = True
    recomputed = round((c["value"] - p["value"]) * 100, 2)
    claim["recomputed"] = recomputed
    claim["result"] = "GROUNDED" if abs(recomputed - claim["value"]) <= tol else "VALUE_MISMATCH"


def _direct_value_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts,
                        profile=None, rounding=None):
    scale = prec if unit == "円" else V.UNIT_SCALE[unit]
    unit_scale = 1.0 if unit == "円" else V.UNIT_SCALE[unit]
    mag_trunc = bool(profile is not None and getattr(profile, "truncate_on_magnitude", False))
    if mag_trunc:
        claim["magnitude_truncate"] = True
    target = sign * num * unit_scale
    # C-1d §3.1 (comparators.py reads only evidence/claim.value/contract.params):
    # carry the two numbers the equals_within / diff(a-b) comparators need to
    # reproduce this function's own `scale`/`target` at verify time.
    claim["unit_scale"] = unit_scale
    claim["claim_scale"] = scale
    pool = I.facts_for(elems, facts, contexts, member) if subj else [f for f in facts if I.ctx_ok(f["context"], contexts, member)]
    pool = [f for f in pool if f["unit"] and f["unit"].upper().startswith("JPY")]
    is_diff = bool(_MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(_MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
    hits = [(f, V.match_value(f["value"], target, scale, rounding, mag_trunc)) for f in pool]
    hits = [(f, how) for f, how in hits if how]
    if profile is not None and profile.period_cue and _prior_cue(s, a, b):
        # C2: 当期・前期で同じ値のとき、「(同」「前期」の直後の数は前期の fact を先に。
        hits = sorted(hits, key=lambda fh: 0 if fh[0]["context"].startswith("Prior1Year") else 1)
    if hits and not (is_diff and subj):
        fams = sorted({f["name"] for f, _ in hits})
        if subj or len(fams) == 1:
            if subj:
                f, how = hits[0]
                claim["pointer"] = "xbrl:%s@%s" % (f["name"], f["context"])
                claim["bound"] = True
                claim["result"] = "GROUNDED"
                claim["recomputed"] = f["value"]
                claim["match"] = how
            else:
                # 封 BINDING_FIX_PLAN_2026-10-08(案ア、人間の決定 2026-10-08)。
                # subject が取れていない数の主張は、候補事実の家族が 1 つに
                # 絞れても束縛しない。pointer/bound/recomputed を立てず、
                # reason="no_subject" のまま返す(UNBOUND_REASON_STATE により
                # UNVERIFIABLE になる)。
                claim["reason"] = "no_subject"
        else:
            # C-1d §3.3: the registered reason name is the count-free
            # `ambiguous(elements)` (so a 3rd document's different element
            # count does not require a new registration); the count itself
            # moves to Claim.provenance["ambiguous_count"] (see claim_to_recipe).
            claim["reason"] = "ambiguous(elements)"
            claim["ambiguous_count"] = len(fams)
    elif subj:
        fs = I.facts_for(elems, facts, contexts, member)
        fs = [f for f in fs if f["unit"] and f["unit"].upper().startswith("JPY")]
        by = {}
        for f in fs:
            by.setdefault(f["name"], {})[f["context"]] = f
        found = None
        prev_year_phrase = _PREV_YEAR_PHRASE in s[max(0, a - 15):a]
        for name, ctxs in by.items():
            def ctx(prefix):
                return next((v for k, v in ctxs.items() if k.startswith(prefix)), None)
            pairs = [("Prior1Year", "Prior2Year")] if prev_year_phrase else [("CurrentYear", "Prior1Year")]
            for pa, pb in pairs:
                fa, fb = ctx(pa), ctx(pb)
                if fa and fb:
                    how = V.match_value(fa["value"] - fb["value"], target, scale, rounding, mag_trunc)
                    if how:
                        found = (fa, fb, how)
                        break
            if found:
                break
        if found:
            fa, fb, how = found
            claim["form"] = "derived_value"
            claim["pointer"] = ["xbrl:%s@%s" % (fa["name"], fa["context"]), "xbrl:%s@%s" % (fb["name"], fb["context"]), "formula:a-b"]
            claim["bound"] = True
            claim["result"] = "GROUNDED"
            claim["recomputed"] = fa["value"] - fb["value"]
            claim["match"] = how
        elif hits:
            f, how = hits[0]
            claim["pointer"] = "xbrl:%s@%s" % (f["name"], f["context"])
            claim["bound"] = True
            claim["result"] = "GROUNDED"
            claim["recomputed"] = f["value"]
            claim["match"] = how
            claim["reason"] = "diff phrase but value matched a fact"
        else:
            cur = [f for f in fs if f["context"].startswith("CurrentYear")]
            if cur:
                if prev_year_phrase and profile is not None and profile.prior2_required:
                    # XBRL 直し §1b: 「前連結会計年度は…」= 前期と前々期の差を
                    # 言う主張で、その対が引けなかったとき、**当期の残高**に
                    # 結び直すのが代用である。代用せずここで止める。
                    #
                    # 止めるのはこの枝だけにする。1 つ上の ``elif hits:`` は
                    # 主張の数と**値が実際に一致した** fact に結ぶ枝で、代用では
                    # ない(2 社目 S100Z4B6 の N079「前連結会計年度は営業損失
                    # 9,709千円」= 前期の実額が、まさにこの枝で前期の fact に
                    # 正しく結ばれている)。2026-10-08 の 2 社目の実測で、
                    # 最初の実装がその 2 件を誤って止めたので枝を狭めた。
                    claim["reason"] = "no_element(no prior2 for prior-year diff)"
                    return
                claim["pointer"] = "xbrl:%s@%s" % (cur[0]["name"], cur[0]["context"])
                claim["bound"] = True
                claim["result"] = "VALUE_MISMATCH"
                claim["recomputed"] = cur[0]["value"]
                claim["reason"] = "value differs(segment/other period?)"
            else:
                claim["reason"] = "no_element"
    else:
        claim["reason"] = "no_element"


# ---------------------------------------------------------------------------
# Core 接続 C-1h §1-2(人間の決定、2026-10-06): 目標値・計画値の数の Claim。
# profile.target_word が真のときだけ使う。窓の 10 は字で留める(定数名)。
# 数の手前だけを見る(後ろの語は見ない)。文章 Claim には掛けない。
# ---------------------------------------------------------------------------
_TARGET_WINDOW = 10
_TARGET_RE = re.compile(r"目標|計画")

# ---------------------------------------------------------------------------
# XBRL 直し §3(人間の決定、2026-10-08): 目標・見通しの判定を、数の主張と
# 文字の主張の両方に掛ける。語を広げ、数(または向きの語)の**後ろ**に来る
# 文型も拾う。後ろの窓は同じ節の中だけを見る(``、``・``。``・括弧で打ち切る)
# ― 「5.8% となり、目標を達成することができませんでした」のような、実績の数の
# 後ろに目標の語が別の節で来る文を止めてしまわないため。
# 窓の幅は字で書く(定数から土台を作らない)。
# ---------------------------------------------------------------------------
_TARGET_AFTER_WINDOW = 20
_TARGET_BOTH_RE = re.compile(r"目標|計画|見込|見通")
_CLAUSE_END_RE = re.compile(r"[、。()（）]")


def _target_or_plan(s, a, b, profile):
    """``a`` は数(または向きの語)の開始、``b`` は終わりの位置。

    ``profile.target_both`` が真: 手前 10 字 + 後ろ 20 字(節の中だけ)に
    ``目標|計画|見込|見通``。
    偽で ``profile.target_word`` が真(P7): 手前 10 字に ``目標|計画`` だけ
    (C-1h の挙動そのまま)。
    どちらも偽(P1/P5F/P6): 常に偽。
    """

    if profile is None:
        return False
    if profile.target_both:
        if _TARGET_BOTH_RE.search(s[max(0, a - _TARGET_WINDOW):a]):
            return True
        after = s[b:b + _TARGET_AFTER_WINDOW]
        cut = _CLAUSE_END_RE.search(after)
        if cut is not None:
            after = after[:cut.start()]
        return bool(_TARGET_BOTH_RE.search(after))
    if profile.target_word:
        return bool(_TARGET_RE.search(s[max(0, a - _TARGET_WINDOW):a]))
    return False


def _first_matching_pair(pairs, matches, profile):
    """P17 A2'(計画 §6): ``external_revenue_for_sales`` が真のときだけ、率の対は
    「合う対」を先に採る(同じ語の要素の一覧の中で。無ければ従来どおり先頭)。
    偽なら従来どおり ``pairs[0]``。"""

    if profile is not None and getattr(profile, "external_revenue_for_sales", False):
        for c, p in pairs:
            if matches(c, p):
                return c, p
    return pairs[0]


def _dispatch_num_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts, profile,
                        rounding=None, flow_base=None):
    """§1-2 の目標値判定を通らなかった数の Claim の、既存の単位ごとの振り分け
    (C-1d/C-1g と不変)。"""
    mag_trunc = bool(profile is not None and getattr(profile, "truncate_on_magnitude", False))   # P19
    tol = pct_tolerance(profile, s, a, b)   # P18(偽なら 0.15 のまま)
    if tol != PCT_TOLERANCE_DEFAULT:
        claim["pct_tolerance"] = tol

    window_pm = s[max(0, a - 25):b + 6]
    pm = E.PCT_DIR_RE.search(window_pm) if unit in ("％", "%") else None
    if pm is not None:
        pm = E.own_sign_match(window_pm, num)  # P-8 (always applied; P1 is unaffected, see §6)
    window_pr = s[max(0, a - 12):b + 3]
    pr = E.PCT_RATIO_RE.search(window_pr) if unit in ("％", "%") and not pm else None
    pct_phrase = None
    if unit in ("％", "%") and not pm and not pr and profile.pct_change_phrase:
        # C4: 「46.0%の大幅減益」「20.7%の大幅増加」― % と向きの語の間に の/大幅 が挟まる形。
        for mm in _PCT_PHRASE_RE.finditer(window_pm):
            if abs(float(mm.group(1)) - num) < 1e-9:
                pct_phrase = mm
                break
    if unit in ("％", "%") and pr:
        claim["form"] = "derived_value"
        if subj:
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
            pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
            pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
            if pairs:
                c, p = _first_matching_pair(pairs, lambda c, p: p["value"] != 0 and abs(c["value"] / p["value"] * 100 - num) <= tol, profile)
                claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "formula:cur/prior*100"]
                claim["bound"] = True
                if p["value"] != 0:
                    ratio = c["value"] / p["value"] * 100
                    claim["recomputed"] = round(ratio, 2)
                    claim["result"] = "GROUNDED" if abs(ratio - num) <= tol else "VALUE_MISMATCH"
                else:
                    claim["result"] = "UNVERIFIABLE"
                    claim["reason"] = "prior is 0"
            else:
                claim["reason"] = "no_prior_member_context" if (member and member != E.AMBIG and cur) else "no_element"
        else:
            claim["reason"] = "no_subject"
    elif unit in ("％", "%") and ((pm and (pm.group(4) or pm.group(7))) or pct_phrase):
        claim["form"] = "derived_value"
        tok = (pm.group(4) or pm.group(7)) if pm else pct_phrase.group(3)
        sgn = 1 if tok in ("増", "増加", "増益", "増収") else -1
        claim["value"] = sgn * num
        claim["sign_token"] = (pm or pct_phrase).group(0)
        if subj:
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
            pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
            pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
            if pairs:
                c, p = _first_matching_pair(pairs, lambda c, p: p["value"] != 0 and abs((c["value"] - p["value"]) / abs(p["value"]) * 100 - claim["value"]) <= tol, profile)
                claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"])]
                claim["bound"] = True
                if p["value"] != 0:
                    pct = (c["value"] - p["value"]) / abs(p["value"]) * 100
                    claim["recomputed"] = round(pct, 2)
                    claim["result"] = "GROUNDED" if abs(pct - claim["value"]) <= tol else "VALUE_MISMATCH"
                else:
                    claim["result"] = "UNVERIFIABLE"
                    claim["reason"] = "prior is 0"
            else:
                claim["reason"] = "no_prior_member_context" if (member and member != E.AMBIG and cur) else "no_element"
        else:
            claim["reason"] = "no_subject"
    elif unit in V.UNIT_SCALE:
        claim["form"] = "direct_value"
        _direct_value_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts,
                            profile, rounding)
        if profile.flow_sign:
            _apply_flow_sign(claim, s, a, b, rounding, flow_base, mag_trunc)
    elif unit in ("％", "%", "ポイント"):
        claim["form"] = "direct_value"
        if profile.point_diff and unit == "ポイント" and subj:
            _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol)
        elif profile.ratio_table and _ratio_word_before(s, a) is not None:
            # C5: 「売上総利益率は32.5%」― 率そのものの fact が無くても、分子/分母の
            # 2 fact(同じ期)で 分子/分母*100 を照合する。
            rword = _ratio_word_before(s, a)
            num_e, den_e = V.RATIO_TABLE[rword]
            want = "Prior1Year" if (profile.period_cue and _prior_cue(s, a, b)) else "CurrentYear"
            nf = [f for f in I.facts_for([num_e], facts, contexts, member) if f["context"].startswith(want) and f["unit"] and f["unit"].upper().startswith("JPY")]
            df = [f for f in I.facts_for([den_e], facts, contexts, member) if f["context"].startswith(want) and f["unit"] and f["unit"].upper().startswith("JPY")]
            claim["subject"] = rword
            claim["subject_from"] = "ratio_table"
            if nf and df and df[0]["value"] != 0:
                n, d = nf[0], df[0]
                claim["form"] = "derived_value"
                claim["pointer"] = ["xbrl:%s@%s" % (n["name"], n["context"]), "xbrl:%s@%s" % (d["name"], d["context"]), "formula:a/b*100"]
                claim["bound"] = True
                ratio = n["value"] / d["value"] * 100
                claim["recomputed"] = round(ratio, 2)
                claim["result"] = "GROUNDED" if abs(ratio - num) <= tol else "VALUE_MISMATCH"
            else:
                claim["reason"] = "no_element(ratio without fact)"
        elif subj and any((f["unit"] or "").lower().startswith("pure") for f in I.facts_for(elems, facts, contexts, member)):
            want = "Prior1Year" if (profile.period_cue and _prior_cue(s, a, b)) else "CurrentYear"  # C2
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith(want) and (f["unit"] or "").lower().startswith("pure")]
            if cur:
                fv = cur[0]["value"]
                fvp = fv * 100 if abs(fv) <= 1.5 else fv
                claim["pointer"] = "xbrl:%s@%s" % (cur[0]["name"], cur[0]["context"])
                claim["bound"] = True
                claim["recomputed"] = round(fvp, 2)
                claim["result"] = "GROUNDED" if abs(fvp - num) <= tol else "VALUE_MISMATCH"
            else:
                claim["reason"] = "no_element"
        else:
            claim["reason"] = "no_element(ratio without fact)" if subj else "no_subject"
    elif unit in ("名", "人"):
        claim["form"] = "direct_value"
        # C-1d §3.1: equals_within's optional abs_tolerance branch
        # (not exercised by the 224-claim material; none bind).
        claim["abs_tolerance"] = 0.5
        cur = [f for f in I.facts_for(["NumberOfEmployees"], facts, contexts, member) if f["context"].startswith("CurrentYear")]
        if subj and elems == ["NumberOfEmployees"] and cur:
            hit = [f for f in cur if abs(f["value"] - num) <= 0.5]
            chosen = (hit or cur)[0]
            claim["pointer"] = "xbrl:%s@%s" % (chosen["name"], chosen["context"])
            claim["bound"] = True
            claim["result"] = "GROUNDED" if hit else "VALUE_MISMATCH"
            claim["recomputed"] = chosen["value"]
        else:
            claim["reason"] = "no_element"
    else:
        claim["form"] = "direct_value"
        claim["reason"] = "no_element(unit not in XBRL)"


# ---------------------------------------------------------------------------
# XBRL 直し §6(人間の決定、2026-10-08): 括弧内の前期の方向語。
# profile.text_prior_year_paren が真のときだけ使う。
#
# 「…22 億 8 千 1 百万円増加(前連結会計年度は 14 億 7 千 5 百万円増加)し、…」の
# 括弧の中の「増加」は**前期の**増加であって、当期 − 前期ではなく前期 − 前々期を
# 指す。数の主張の側には同じ扱いが既にある(_direct_value_claim の
# prev_year_phrase、窓 15 字)。その文字版が無いのが T008・T022 の誤りの機構。
#
# 判定は**文字の窓ではなく括弧の深さ**で行う ― 「前連結会計年度は」(8 字)+ 金額
# (8 字以上)で 16 字以上になり、数の側の窓 15 字では前の字に届かないため。
# ---------------------------------------------------------------------------
PAREN_OPEN_CHARS = "(（"
PAREN_CLOSE_CHARS = ")）"


def _enclosing_paren(s, pos, open_chars=PAREN_OPEN_CHARS, close_chars=PAREN_CLOSE_CHARS):
    """``pos`` を囲む、いちばん内側の丸括弧の ``(開きの位置, 閉じの位置)``。
    囲んでいなければ ``None``。閉じていない括弧は行末までを範囲とする
    (内側の括弧は外側より先に閉じるので、最初に見つかった「囲んでいる対」が
    いちばん内側になる)。
    """

    stack = []
    for i, ch in enumerate(s):
        if ch in open_chars:
            stack.append(i)
        elif ch in close_chars:
            if stack:
                o = stack.pop()
                if o < pos < i:
                    return (o, i)
    if stack and stack[-1] < pos:
        return (stack[-1], len(s))
    return None


def _in_prior_year_paren(s, pos):
    """``pos`` が、「前連結会計年度は」を含む丸括弧の中にあるか。
    語そのものは数の側と同じ ``_PREV_YEAR_PHRASE`` を使う(1 か所で持つ)。
    """

    span = _enclosing_paren(s, pos)
    if span is None:
        return False
    return _PREV_YEAR_PHRASE in s[span[0]:span[1]]


# ---------------------------------------------------------------------------
# 主語の規則の直し(人間の判断 1、2026-10-08)の S2・A1。
# S1・S3 は ``extract.subject_of`` の ``skip`` で書いてある(順位は変えない)。
# ---------------------------------------------------------------------------


def _elements_for_word(subjects, word):
    """語彙の中で ``word`` に**最初に**当たる行の要素。

    **``dict(subjects)`` を使ってはいけない** ― 同じ語が 2 回出てくる語彙では
    ``dict`` は**最後**を採るが、``subject_of`` は(同じ終わり・同じ長さなら)
    **一覧の早い方**を採る。ここは ``subject_of`` と同じ側に揃える。
    """

    for w, elems in subjects:
        if w == word:
            return elems
    return None


def _direction_amount_check(claim, s, word_start, word_end, rounding, mag_trunc=False):
    """A1(人間の追加指示、2026-10-08): 向きの語と**同じ節**に金額が在れば、
    向きだけでなく金額も ``|当期 − 前期|`` と照合する。

    節に限るのは、**文に限ると列挙の文で他の項目の金額を拾う**からである。
    節の中に金額が 2 つ以上在るときは**向きの語にいちばん近いもの 1 つ**を採り、
    何件在ったかを ``amount_in_clause_count`` に残す(人が全件読めるように)。

    **これは通る主張を増やす直しではない。** 金額が合わなければ
    ``GROUNDED`` を ``VALUE_MISMATCH`` に落とすだけで、逆向きには動かさない。

    ## 封を狭めた理由(2026-10-08、1 回目の実測の後)

    封じた計画は「**同じ節**に金額が在れば照合する」だった。4 書類で測ったら
    **正しかった主張を 3 件止めた** ― 封じた合格条件(「2 件まで。3 件以上なら
    規則が広すぎるので狭めてから測り直す」)に当たったので狭めた。

    止めた 3 件のうち 2 件は**差ではなく水準**を拾っていた ―
    「営業利益は、前連結会計年度に比べて38.1%増加し**253百万円**となりました」
    「期初の業績予想を上回る**393億94百万円**となりました」。
    節の中でいちばん近い金額が、増減ではなくその期の残高・売上だった。

    だから採る金額を「**向きの語に直に付いた金額**」に限る ―
    金額の直後(``の`` を 1 つ挟むのは許す)に向きの語が来る形
    (「30,950千円増加」「8億96百万円増加」)か、金額の直前が
    ``増加額``/``減少額`` などの差を表す名詞である形(「減少額14,472千円」)。
    **水準の金額は「…となりました」で終わるので、どちらの形にも入らない。**
    """

    left, right = E.clause_span(s, word_start, word_end)
    found = []
    for (a, b, signed, unit, prec) in E.iter_numbers(s[left:right]):
        if unit not in V.UNIT_SCALE:
            continue
        start, end = left + a, left + b
        gap_text = s[end:word_start] if end <= word_start else None
        attached_after = gap_text in DIRECTION_AMOUNT_GAPS
        attached_before = any(s[:start].endswith(n) for n in DIFFERENCE_NOUNS)
        if not (attached_after or attached_before):
            continue
        gap = min(abs(start - word_end), abs(word_start - end))
        found.append((gap, signed, unit, prec))
    claim["amount_in_clause_count"] = len(found)
    if not found:
        return
    found.sort(key=lambda r: r[0])
    _gap, signed, unit, prec = found[0]
    unit_scale = 1.0 if unit == "円" else V.UNIT_SCALE[unit]
    claim_scale = prec if unit == "円" else V.UNIT_SCALE[unit]
    claim["value"] = abs(signed)
    claim["unit"] = unit
    claim["unit_scale"] = unit_scale
    claim["claim_scale"] = claim_scale
    claim["amount_in_clause"] = abs(signed) * unit_scale
    if rounding is not None:
        claim["rounding"] = rounding
    how = V.match_value(abs(claim["recomputed"]), abs(signed) * unit_scale, claim_scale, rounding, mag_trunc)
    claim["amount_match"] = how
    claim["match"] = how
    if how is None and claim["result"] == "GROUNDED":
        claim["result"] = "VALUE_MISMATCH"


def _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, rounding=None, flow_base=None):
    num_claims = []
    cf_ctx = _cf_context_flags(sentences) if flow_base else None
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, prec) in E.iter_numbers(s):
            member, msrc = claim_member(si, a)
            after = s[b:b + 3]
            around = s[max(0, a - 12):b + 4]
            if E.EXCLUDE_AFTER.match(after) or E.EXCLUDE_CONTEXT.search(around):
                continue
            sign = -1 if signed < 0 else 1
            num = abs(signed)
            subj, elems = E.subject_of(s, a, profile.subjects, E.subject_skip_for(profile),
                                       cause_topic=profile.subject_skip_before_cause_marker)
            felems = _flow_elems_for(s, subj, a, flow_base, cf_ctx[si]) if flow_base else None
            orig_elems = elems
            if felems is not None:
                elems = felems  # C3: 「Xの増加額 N円」は X の CF 増減項目
            claim = {
                "id": "N%03d" % (len(num_claims) + 1,), "sentence": si, "span": s[max(0, a - 30):b + 10],
                # XBRL 直し(2026-10-08): 文の中の位置。文の切り方を変える直し
                # (§4)の前後で主張を 1 対 1 に対応づけるためだけに使う計器で、
                # Claim・Recipe には写らない(claim_to_recipe は読まない)。
                "pos": a,
                "value": sign * num, "unit": unit, "subject": subj, "form": None, "pointer": None,
                "bound": False, "reason": None, "result": None, "recomputed": None,
            }
            if felems is not None:
                claim["subject_from"] = "flow_item"
            base_claim = dict(claim)
            if _target_or_plan(s, a, b, profile):
                # Core 接続 C-1h §1-2(P7)+ XBRL 直し §3(P8): 目標・計画・
                # 見込み・見通しの数は UNVERIFIABLE。
                claim["form"] = "direct_value"
                claim["result"] = "UNVERIFIABLE"
                claim["reason"] = "target_or_plan"
            else:
                _dispatch_num_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts,
                                    profile, rounding, flow_base)
                if felems is not None and claim.get("result") != "GROUNDED":
                    # C3 の fall back: CF 増減項目で裏が取れなければ、元の要素(残高)で
                    # もう 1 度だけ試し、そちらが GROUNDED ならそれを採る。
                    retry = dict(base_claim)
                    retry.pop("subject_from", None)
                    _dispatch_num_claim(retry, s, a, b, sign, num, unit, prec, subj, orig_elems, member, facts, contexts,
                                        profile, rounding, None)
                    if retry.get("result") == "GROUNDED":
                        claim = retry
            if rounding is not None and claim.get("unit_scale") is not None:
                claim["rounding"] = rounding
            if profile.member_on:
                if msrc == "ambiguous" and not claim["bound"]:
                    claim["reason"] = "ambiguous(member)"
                claim["member"] = None if member == E.AMBIG else member
                claim["member_source"] = msrc
            num_claims.append(claim)
    return num_claims


def _text_unbound_reason(profile, member, cur, elems, facts, contexts):
    """§1-3(人間の決定、2026-10-06): 主語が束縛でき、当期・前期の対が
    見つからなかったときの理由(既存の member 優先条件はそのまま維持し、
    その後ろだけを分割する)。``cur`` は JPY の当期 fact の列。
    ``profile.text_reason_split`` が偽の既存の挙動(P1/P5F/P6)はまったく
    変えない(cur_any を計算しない)。
    """

    if member and member != E.AMBIG and cur:
        return "no_prior_member_context"
    if not profile.text_reason_split:
        return "no_element"
    cur_any = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
    if not cur_any:
        return "no_element"
    if not cur:
        return "no_element(text needs money fact)"
    return "no_element(no prior for text)"


def _build_raw_text_claims(sentences, facts, contexts, profile, claim_member, rounding=None, flow_base=None):
    text_claims = []
    cf_ctx = _cf_context_flags(sentences) if flow_base else None
    for si, s in enumerate(sentences):
        for w, sg in E.DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
                member, msrc = claim_member(si, m.start())
                subj, elems = E.subject_of(s, m.start(), profile.subjects, E.subject_skip_for(profile),
                                           cause_topic=profile.subject_skip_before_cause_marker)
                felems = _flow_elems_for(s, subj, m.start(), flow_base, cf_ctx[si]) if (flow_base and w in ("増加", "減少")) else None
                if felems is not None:
                    elems = felems  # C3: 「Xの減少」は X の CF 増減項目(flow_sign の経路へ)
                claim = {
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": subj, "pos": m.start(),
                    "form": "threshold", "pointer": None, "bound": False, "result": None, "reason": None,
                    "direction": sg,
                }
                if felems is not None:
                    claim["subject_from"] = "flow_item"
                if profile.subject_direction_object:
                    # S2: 「<名詞>を増加/減少」なら、向きが掛かっているのは
                    # **その目的語**である。語彙に在ればそれを主語にし、
                    # 無ければ主張にしない(たまたま近くの語に当たって
                    # 通ってしまう型を止める)。
                    obj = E.direction_object(s, m.start())
                    if obj is not None and obj != subj:
                        oelems = _elements_for_word(profile.subjects, obj)
                        if oelems is None:
                            claim["dropped"] = "direction_object(no subject: %s)" % obj
                        else:
                            subj, elems = obj, oelems
                            claim["subject"] = subj
                            claim["subject_from"] = "direction_object"
                if profile.direction_word_lexicon and not claim.get("dropped"):
                    # S4: 増収/減収 は売上高系へ、増益/減益 は利益系へ。
                    # 0 個なら指す先が無い・2 個以上ならどれか決められないので、
                    # どちらも主張にしない。
                    fam = V.direction_family_words(s, w)
                    if fam is not None:
                        if len(fam) != 1:
                            claim["dropped"] = "direction_word(%d in the sentence)" % len(fam)
                        else:
                            fword = fam[0][0]
                            felems = _elements_for_word(profile.subjects, fword)
                            if felems is None:
                                claim["dropped"] = "direction_word(no subject: %s)" % fword
                            else:
                                subj, elems = fword, felems
                                claim["subject"] = subj
                                claim["subject_from"] = "direction_word"
                flow_conv = None
                if subj and profile.flow_sign:
                    for e in elems:
                        c = _flow_sign_of(e, flow_base)
                        if c is not None:
                            flow_conv = c
                            break
                expend_conv = False
                if subj and flow_conv is None and profile.expenditure_sign:
                    # Core 接続 C-1h §1-1: flow_convention が先に効く(非 None
                    # ならこの判定はしない)。
                    for e in elems:
                        if V.expenditure_convention(e):
                            expend_conv = True
                            break
                if claim.get("dropped"):
                    # S2・S4 で落とした主張は、束縛まで進めない(どちらにしても
                    # 末尾で外すので、結果の欄を埋めずに素通りさせる)。
                    pass
                elif _target_or_plan(s, m.start(), m.end(), profile):
                    # XBRL 直し §3: 向きの語の手前 10 字・後ろ 20 字(節の中)に
                    # 目標|計画|見込|見通 があれば、盤面の事実ではなく将来の
                    # 見通しなので束縛しない(「売上高の拡大を見込みます」)。
                    claim["result"] = "UNVERIFIABLE"
                    claim["reason"] = "target_or_plan"
                elif subj and flow_conv is not None:
                    # Core 接続 C-1g §1-2: 主語が CF 流量項目なら、前期との
                    # 対でなく当期 1 件の fact + builtin:flow_sign(cur)==direction
                    # で束縛する(値そのものが増減を表すので前期は要らない)。
                    # C2: 同じ節に「前期は」が在れば前期の CF fact。
                    cf_pre = "Prior1Year" if (profile.period_cue and _prior_cue_clause(s, m.start())) else "CurrentYear"
                    cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith(cf_pre) and f["unit"] and f["unit"].upper().startswith("JPY")]
                    if cur:
                        c = cur[0]
                        claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "builtin:flow_sign(cur)==direction"]
                        claim["bound"] = True
                        claim["flow_convention"] = flow_conv
                        actual = 0 if c["value"] == 0 else (1 if c["value"] * flow_conv > 0 else -1)
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = c["value"]
                    else:
                        claim["reason"] = "no_element"
                elif subj and expend_conv:
                    # Core 接続 C-1h §1-1: 「支出」系項目は当期・前期の JPY
                    # fact の対に束縛し、文の「増加/減少」は大きさ(絶対値)の
                    # 増減として builtin:sign(|cur|-|prior|)==direction で見る。
                    cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year") and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "builtin:sign(|cur|-|prior|)"]
                        claim["bound"] = True
                        claim["expenditure_convention"] = True
                        acur, apri = abs(c["value"]), abs(p["value"])
                        diff = acur - apri
                        actual = 0 if diff == 0 else (1 if diff > 0 else -1)
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = diff
                    else:
                        claim["reason"] = _text_unbound_reason(profile, member, cur, elems, facts, contexts)
                elif subj:
                    # XBRL 直し §6: 括弧の中の前期の方向語は、当期・前期ではなく
                    # 前期・前々期の対に結ぶ。期の組だけを差し替え、以降の
                    # 判定(符号の向き・理由)は同じ 1 か所を通す。
                    prior_paren = (profile.text_prior_year_paren and _in_prior_year_paren(s, m.start())) or \
                        (profile.period_cue and _prior_cue_clause(s, m.start()))  # C2
                    a_pre, b_pre = ("Prior1Year", "Prior2Year") if prior_paren else ("CurrentYear", "Prior1Year")
                    cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith(a_pre) and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith(b_pre)]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace(a_pre, "") == p["context"].replace(b_pre, "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "builtin:sign(cur-prior)"]
                        claim["bound"] = True
                        actual = 1 if c["value"] - p["value"] > 0 else -1
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = c["value"] - p["value"]
                        if profile.direction_amount_check:
                            # A1(人間の追加指示): 同じ節に金額が在れば金額も照合する。
                            _direction_amount_check(claim, s, m.start(), m.end(), rounding,
                                                    getattr(profile, "truncate_on_magnitude", False))
                    elif prior_paren:
                        # 前々期が無いときは代用せず止める(数の側の §1b と同じ
                        # 原因なので同じ理由の名前を使う。登録簿は増やさない)。
                        claim["reason"] = "no_element(no prior2 for prior-year diff)"
                    else:
                        claim["reason"] = _text_unbound_reason(profile, member, cur, elems, facts, contexts)
                else:
                    claim["reason"] = "no_subject"
                if profile.member_on:
                    if msrc == "ambiguous" and not claim["bound"]:
                        claim["reason"] = "ambiguous(member)"
                    claim["member"] = None if member == E.AMBIG else member
                    claim["member_source"] = msrc
                if profile.drop_qualitative and not claim.get("subject"):
                    # XBRL 直し §5(広い版): 主語が語彙に引けない向きの語を
                    # 主張にしない。
                    #
                    # **2026-10-08 の実測で、この枝は広すぎることが分かった。**
                    # 1 社目では景気の語(「わが国経済は…改善」)だったが、
                    # 2 社目・3 社目では実在の勘定科目が混ざっていた ―
                    # 「売上原価は 30,950 千円増加」「流動資産は…37 百万円減少」
                    # 「固定資産は…239 百万円増加」など、**語彙に主語が無いだけ**の
                    # 主張を黙って分母から消していた(3 書類で 3 / 18 / 20 件)。
                    # 狭い版(``drop_state_words_only``、profile P10)はこの枝を
                    # 通らず、向きの語は ``no_subject`` のまま残す ― その件数が
                    # 語彙の穴の大きさを指す計器になる。
                    # 経緯は docs/XBRL_FIX5_NARROW_PLAN_2026-10-08.md。
                    claim["dropped"] = "qualitative(no subject)"
                text_claims.append(claim)
        for w in E.STATE_WORDS:
            for m in re.finditer(w, s):
                st = {
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": None, "pos": m.start(), "form": "threshold",
                    "pointer": None, "bound": False, "result": "UNVERIFIABLE", "reason": "state_word(no line)",
                }
                if profile.drop_qualitative or profile.drop_state_words_only:
                    # XBRL 直し §5: 状態語(堅調・不透明・回復…)は構造上どの
                    # 行にも束縛されない(``state_word(no line)``)。主張にしない。
                    # 狭い版(§5')が落とすのはこの群**だけ**である。
                    st["dropped"] = "qualitative(state word)"
                text_claims.append(st)
    # 番号を振った**後に**落とす ― ID は欠番になるが、直す前との対応づけが
    # ずれない(落とした件数と ID を結果に書けるようにするため)。
    if (profile.drop_qualitative or profile.drop_state_words_only
            or profile.subject_direction_object or profile.direction_word_lexicon):
        text_claims = [c for c in text_claims if not c.get("dropped")]
    return text_claims


def _rounding_evidence(num_claims):
    """XBRL 直し §2: 丸め方を決める根拠。束縛できた金額の主張ごとに
    ``(差, 桁)`` を返す。差は**その主張の照合が実際に使った軸**で測る
    (``abs+`` の札が付いたもの・CF 流量項目は絶対値の軸)。
    """

    rows = []
    for c in num_claims:
        how = c.get("match")
        if not how or c.get("unit_scale") is None or c.get("recomputed") is None:
            continue
        on_abs = how.startswith("abs+") or c.get("flow_convention") is not None
        target = (abs(c["value"]) if on_abs else c["value"]) * c["unit_scale"]
        fact = abs(c["recomputed"]) if on_abs else c["recomputed"]
        rows.append((fact - target, c["claim_scale"]))
    return rows


def _member_material(zb, inst, text, sentences, profile):
    if not profile.member_on:
        return [(None, None)] * len(sentences), {}
    z = zipfile.ZipFile(io.BytesIO(zb))
    if profile.segment_denominator:
        # Core 接続 C-1g §1-4(人間の承認、2026-10-06): P6 だけ事業 member に
        # 限った分母を使う(凍結の member_denominator は系譜の試験のため不変)。
        members = I.segment_member_denominator(inst["contexts"])
    else:
        members = I.member_denominator(inst["contexts"])
    id2label = I.labels_from_zip(z, inst["names"])
    ntext = unicodedata.normalize("NFKC", text)
    reg, _rows, _hand = E.build_registry(members, id2label, ntext, profile.run3)
    paras = E.paragraph_index(text, sentences, profile.paren_sentence)
    if profile.segment_carry_to_result_sentence:
        # P17 A'': 従来の段落内の引き継ぎ + 「結果の文」への段落またぎの引き継ぎ。
        sent_member = E.resolve_members_to_result_sentence(sentences, paras, reg)
    else:
        sent_member = E.resolve_members(sentences, paras, reg)
    return sent_member, reg


def _label_tables(zb, inst, profile):
    """ラベルの表を 2 つ返す ― 書類自身のインライン XBRL から(§7)と、
    標準タクソノミの日本語標準ラベルから(§8)。使わない設定なら空の辞書。
    """

    doc_labels = {}
    if profile.label_vocabulary:
        z = zipfile.ZipFile(io.BytesIO(zb))
        doc_labels = I.inline_labels(
            z, inst["names"],
            statement_only=profile.label_statement_rows_only,
            contexts=inst["contexts"] if profile.label_statement_rows_only else None)
    tax_labels = {}
    if profile.taxonomy_labels:
        # §8 の名前空間の限定。``taxonomy_labels_all_ns`` は**参考専用**。
        namespaces = None if profile.taxonomy_labels_all_ns else ("jppfs",)
        locals_ = {f["name"].split(":")[-1] for f in inst["facts"]}
        tax_labels = I.taxonomy_labels(locals_, namespaces=namespaces)
    return doc_labels, tax_labels


# ---------------------------------------------------------------------------
# 概念で結ぶ直し(2026-10-13)。C2: 期の手がかり。C3: CF 増減項目をラベルで引く。
# どれも profile のフラグ(P16)が真のときだけ呼ばれる。
# ---------------------------------------------------------------------------
_PRIOR_CUE_RE = re.compile(r"(前期末|前期|前連結会計年度末|前連結会計年度|前事業年度末|前事業年度|前年同期)(は|には|の|、)?$")
_PRIOR_PAREN_RE = re.compile(r"[(（]\s*同\s*$")
_PRIOR_CLAUSE_RE = re.compile(r"(前期|前連結会計年度|前事業年度|前年同期)(は|には)")


def _prior_cue(s, a, b=None):
    """C2: 数の直前(12 字)が「前期」「前期末」「(同」などで終わるか、数の直後が
    「から」(「32.5%から29.8%へ」の前の数)か。「前期比 2.9%増」の 前期比 は当期の
    主張なので当たらない(末尾が 比)。"""

    w = s[max(0, a - 12):a]
    if _PRIOR_CUE_RE.search(w) or _PRIOR_PAREN_RE.search(w):
        return True
    return b is not None and s[b:b + 2] == "から"


def _prior_cue_clause(s, pos):
    """C2(向きの語): 同じ節(直前の読点・句点より後)に「前期は」などが在るか。"""

    # 閉じた括弧の中(「(前連結会計年度は営業損失9,709千円)の減益」の括弧)は別の節なので除く。
    seg = re.sub(r"[(（][^()（）]*[)）]", "", s[:pos])
    cut = max(seg.rfind("、"), seg.rfind("。"))
    return bool(_PRIOR_CLAUSE_RE.search(seg[cut + 1:]))


_PCT_PHRASE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(％|%)\s*の?(?:大幅な?)?(増加|減少|増益|減益|増収|減収|増|減)")
# 語と数の間に許すもの: 助詞、「前期の」、そして「32.5%から」(AからBへ の A)。
_RATIO_PARTICLE_RE = re.compile(r"^(は|が|を|も|の|、|\s)*(前期(末)?の)?(\d+(?:\.\d+)?\s*[％%]から)?$")


def _ratio_word_before(s, a):
    """C5: 数の手前 24 字に RATIO_TABLE の語が在り、語と数の間が助詞(と「前期の」「NN%から」)だけなら、その語
    (いちばん長いもの)。無ければ None。"""

    head = s[max(0, a - 24):a]
    best = None
    for w in V.RATIO_TABLE:
        i = head.rfind(w)
        if i < 0 or not _RATIO_PARTICLE_RE.match(head[i + len(w):]):
            continue
        if best is None or len(w) > len(best):
            best = w
    return best


_FLOW_LABEL_RE = re.compile(r"^(.+?)の(増減額|増加額|減少額|増減|増加|減少)")
_FLOW_TAIL_RE = re.compile(r"^の(増加額|減少額|増加|減少)")
# C3 を掛けるのはキャッシュ・フローの説明の文だけ。貸借対照表の説明(「純資産の増加は…
# 退職給付に係る調整累計額の増加10億8千5百万円による」)の「Xの増加」は残高の 2 時点が正しい。
_CF_CONTEXT_RE = re.compile(r"キャッシュ・フロー|資金|営業活動|投資活動|財務活動|収入|支出")


def _flow_items_by_base(zb, inst, profile):
    """C3: ``{勘定科目の語: [CF 増減項目の局所名, ...]}``。書類のラベルと標準タクソノミの
    ラベルのうち「Xの増減額(△は…)」の形で、要素が ``flow_convention`` を持つものだけ。
    """

    doc_labels, tax_labels = _label_tables(zb, inst, profile)
    # 会社拡張の要素(例 jpcrp030000-asr_E36539-000:DecreaseIncreaseInContractAssetsOpeCF)の
    # ラベルは書類の ZIP の _lab.xml にだけ在る。id は <prefix>_<Local> の形。
    z = zipfile.ZipFile(io.BytesIO(zb))
    ext_labels = {}
    for eid, label in I.labels_from_zip(z, inst["names"]).items():
        ext_labels.setdefault(label, []).append(eid.rsplit("_", 1)[-1])
    base, sign = {}, {}
    for table in (doc_labels, tax_labels, ext_labels):
        for label, locals_ in table.items():
            m = _FLOW_LABEL_RE.match(label)
            if not m:
                continue
            flows = [e for e in locals_ if V.flow_convention(e) is not None]
            if not flows:
                continue
            bucket = base.setdefault(m.group(1), [])
            for e in flows:
                if e not in bucket:
                    bucket.append(e)
                # 符号の規約はラベルの括弧が正本: 「(△は増加)」= 負が増加 = -1、
                # 「(△は減少)」= 負が減少 = +1。無ければ要素名の規約(flow_convention)。
                if "△は増加" in label:
                    sign[e] = -1
                elif "△は減少" in label:
                    sign[e] = 1
    return {"base": base, "sign": sign}


def statement_facts_first(facts):
    """C1: 計算書(jppfs_cor)の fact を先に置いた新しい列(安定な並べ替え。中身は同じ)。"""

    return sorted(facts, key=lambda f: 0 if f["name"].startswith(I.STATEMENT_PREFIX + ":") else 1)


def _flow_sign_of(element_name, flow_base):
    """C3: CF 増減項目の符号の規約。ラベルの括弧から取れたものを優先し、
    無ければ ``vocabulary.flow_convention``(要素名)に落とす。"""

    local = element_name.split(":")[-1]
    if flow_base and local in flow_base.get("sign", {}):
        return flow_base["sign"][local]
    return V.flow_convention(element_name)


def _cf_context_flags(sentences, back=2):
    """C3: 文ごとに「この文か直前 ``back`` 文にキャッシュ・フローの手がかり語が在るか」。
    AI 文は理由を番号つきで文に分けるので、手がかり語が 1〜2 文前に在ることがある。"""

    hit = [bool(_CF_CONTEXT_RE.search(s)) for s in sentences]
    return [any(hit[max(0, i - back):i + 1]) for i in range(len(sentences))]


def _flow_elems_for(s, subj, pos, flow_base, cf_context=None):
    """C3: 主語の直後が「の増加/減少(額)」(向きの語なら「の」だけ)で、その語の
    CF 増減項目がラベルで引けるなら、その要素の一覧。引けなければ ``None``。"""

    table = (flow_base or {}).get("base") or {}
    if not subj or subj not in table:
        return None
    if cf_context is None:
        cf_context = bool(_CF_CONTEXT_RE.search(s))
    if not cf_context:
        return None
    head = s[:pos]
    i = head.rfind(subj)
    if i < 0:
        return None
    tail = s[i + len(subj):pos]
    if tail == "の" or _FLOW_TAIL_RE.match(tail):
        return list(table[subj])
    return None


def _label_subjects(zb, inst, profile):
    """XBRL 直し §7・§7b・§8: ラベルから取った「日本語の勘定科目名 → 要素」を
    主語の一覧の**行**にして返す。

    返すのは 3 つ。

    ``hand_rows``
        手書きの語彙の行(順も件数もそのまま)。``label_overrides_dead_hand``
        (§7b)が真のときだけ、**手書きの要素で fact を 1 件も引けず、かつ
        ラベル側の要素が 1 件以上引ける**語の要素をラベルのものに差し替える。
        引けないラベルには差し替えない(2 社目の ``繰延税金負債`` のように、
        手書きもラベルも同じ名前で両方引けない語が在る)。
    ``added``
        **手書きの語彙に無い語**の行。書類のラベルを先に、足りない語を標準
        タクソノミで埋める(会社自身の表の言葉が本文の言い回しに近いので先)。
        並びは**長い名前が先**(``subject_of`` は同じ終わり位置・同じ長さなら
        先に在る方を採るので、並べる順を決めておく)。
    ``overrides``
        §7b で差し替えた語の記録(人間の指示: 「(b) でラベルに切り替わった
        ときは記録に残し、件数と該当の語を報告する」)。
    """

    doc_labels, tax_labels = _label_tables(zb, inst, profile)
    facts, contexts = inst["facts"], inst["contexts"]

    def resolves(elems):
        return bool(I.facts_for(list(elems), facts, contexts))

    def exists_any_context(elem):
        # P17 A2': member 付きの context にしか無い要素(セグメントの外部売上高)も「在る」と数える。
        return any(f["name"].split(":")[-1] == elem for f in facts)

    hand_rows, overrides = [], []
    for w, elems in profile.subjects:
        replaced = None
        if profile.label_overrides_dead_hand and not resolves(elems):
            for source, table in (("document", doc_labels), ("taxonomy", tax_labels)):
                cand = table.get(w)
                if cand and resolves(cand):
                    replaced = (source, list(cand))
                    break
        if replaced is None:
            hand_rows.append((w, list(elems)))
            continue
        source, cand = replaced
        overrides.append({"word": w, "hand": list(elems), "label": cand, "source": source})
        hand_rows.append((w, cand))

    hand = {w for w, _e in profile.subjects}
    added = {}
    for table in (doc_labels, tax_labels):
        for w, elems in table.items():
            if w not in hand and w not in added:
                added[w] = list(elems)
    rows = sorted(added.items(), key=lambda r: (-len(r[0]), r[0]))
    added_rows = [(w, list(elems)) for w, elems in rows]
    hand_rows, added_rows = augment_subject_rows(hand_rows, added_rows, doc_labels, exists_any_context, profile)
    return hand_rows, added_rows, overrides


# P17 A2・B2・C(計画 docs/P17_PLAN_2026-10-14.md §1)。純粋関数(試験のため)。
_EXTERNAL_REVENUE = "RevenuesFromExternalCustomers"
_SALES_WORD = "売上高"
_NET_SUFFIXES = ("(純額)", "（純額）")


def augment_subject_rows(hand_rows, added_rows, doc_labels, exists, profile):
    """主語の行(手書き・ラベル由来)に P17 の 3 つの旗を当てる。旗が全部偽なら
    1 つも変えない(同じ内容の新しい list を返す)。

    - ``external_revenue_for_sales``: 「売上高」の要素の末尾に外部顧客への売上高を足す
      (書類にその要素の fact が、どの context であれ 1 件でも在るときだけ ― ``exists(elem)``)。
    - ``loss_variants``: 「〜利益」の語に「〜損失」が無ければ同じ要素で足す(added の末尾)。
    - ``prefer_net_when_labelled``: 書類のラベルに「W(純額)」が在れば、その要素を W の先頭に。
    """

    hand = [(w, list(e)) for w, e in hand_rows]
    added = [(w, list(e)) for w, e in added_rows]
    if getattr(profile, "external_revenue_for_sales", False) and exists(_EXTERNAL_REVENUE):
        for rows in (hand, added):
            for k, (w, e) in enumerate(rows):
                if w == _SALES_WORD and _EXTERNAL_REVENUE not in e:
                    rows[k] = (w, e + [_EXTERNAL_REVENUE])
    if getattr(profile, "prefer_net_when_labelled", False):
        for rows in (hand, added):
            for k, (w, e) in enumerate(rows):
                net = None
                for suf in _NET_SUFFIXES:
                    net = doc_labels.get(w + suf)
                    if net:
                        break
                if net:
                    net = list(net)
                    rows[k] = (w, net + [x for x in e if x not in net])
    if getattr(profile, "loss_variants", False):
        words = {w for w, _e in hand} | {w for w, _e in added}
        extra = []
        for w, e in hand + added:
            if w.endswith("利益"):
                v = w[:-2] + "損失"
                if v not in words:
                    words.add(v)
                    extra.append((v, list(e)))
        added = added + extra
    return hand, added


def build_raw_claims(zb, profile, info=None):
    """1 文書・1 profile ぶんの、原本と同じ形(辞書)の num_claims / text_claims
    を作る。recipes.to_recipes の前段(確認・再現がしやすいように分けておく)。

    ``info`` に辞書を渡すと、測るのに要る数(文の数・決めた丸め方とその根拠)
    をそこに書き込む。渡さなければ何もしない(既存の呼び出しは不変)。
    """

    inst = I.load_instance(zb)
    # P20(封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md): 連結財務諸表が無い書類では、
    # 単体の枠を素の枠として扱う。**判定はここで書類ごとに 1 度だけ行い、以降の全段が
    # 同じ決定を見る**(主張ごとに決めると同じ書類で連結と単体が混ざる)。語彙の組み立て
    # (``_label_subjects``・``_flow_items_by_base``)も素の枠で足切りするので、
    # **それより前**に置かないと旗が半分しか効かない。
    # 旗が偽か、連結の枠に財務の要素が 1 種でも在る書類では同じ辞書がそのまま返るので、
    # 振る舞いは 1 行も変わらない。context の id は**書き換えない**(pointer が名乗る枠と
    # 値の出どころを一致させる。別名を張ると「違う対象の数値を正しい根拠として扱う」に
    # なる ― 2026-10-14 の人間の指示)。
    inst["contexts"] = I.with_nonconsolidated_fallback(
        inst["contexts"], inst["facts"], profile.nonconsolidated_fallback)
    if profile.label_vocabulary or profile.taxonomy_labels:
        # XBRL 直し §7/§7b/§8: 主語の一覧をラベルで直した profile で以降を回す
        # (``subject_of`` も他の関数も 1 行も変えない)。
        hand_rows, added, overrides = _label_subjects(zb, inst, profile)
        profile = dataclasses.replace(profile, subjects=tuple(hand_rows) + tuple(added))
        if info is not None:
            info["label_subjects_added"] = len(added)
            info["label_overrides"] = overrides
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    if profile.statement_facts_first:
        # C1: 計算書(jppfs_cor)の fact を先に置く(安定な並べ替え)。「最初の候補」を
        # 採る既存の全箇所が、業績概要(jpcrp_cor:…SummaryOfBusinessResults)より
        # 本表を先に見るようになる。fact の中身は変えない。
        facts = statement_facts_first(facts)
    flow_base = _flow_items_by_base(zb, inst, profile) if profile.flow_item_from_label else None
    if info is not None and flow_base is not None:
        info["flow_items"] = len(flow_base["base"])
    mdna_name = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna_name]) if mdna_name else ""
    sentences = E.split_sentences(text, profile.paren_sentence)
    sent_member, reg = _member_material(zb, inst, text, sentences, profile)

    def claim_member(si, pos):
        if not (profile.member_on and profile.claim_level_member):
            return sent_member[si]
        return E.claim_member_B(sentences[si], pos, reg, sent_member[si])

    num_claims = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, flow_base=flow_base)
    rounding = None
    if profile.doc_rounding:
        # XBRL 直し §2: 1 周目(今までの梯子)で根拠を数え、書類の丸め方を
        # 1 つに決め、2 周目はその 1 つだけで照合し直す。
        rounding, r_only, t_only = V.decide_rounding(_rounding_evidence(num_claims))
        num_claims = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, rounding, flow_base=flow_base)
        if info is not None:
            info["rounding_round_only"] = r_only
            info["rounding_truncate_only"] = t_only
    text_claims = _build_raw_text_claims(sentences, facts, contexts, profile, claim_member, rounding, flow_base=flow_base)
    if info is not None:
        info["sentences"] = len(sentences)
        info["mdna_chars"] = len(text)
        info["rounding"] = rounding
    return num_claims, text_claims


# ---------------------------------------------------------------------------
# Raw claim -> Core Recipe (make_core_expectation.py: map_claim の写し)
# ---------------------------------------------------------------------------

_FORM_MAP = {
    "direct_value": core.Form.DIRECT_VALUE,
    "derived_value": core.Form.DERIVED_VALUE,
    "threshold": core.Form.THRESHOLD,
}


def claim_to_recipe(raw, kind):
    """1 件の原本形式の claim 辞書を Core の Recipe へ写す。"""

    ptrs = _pointer_list(raw["pointer"])
    xptrs = [p for p in ptrs if p.startswith("xbrl:")]
    others = [p for p in ptrs if not p.startswith("xbrl:")]
    schemes = sorted({p.split(":")[0] for p in ptrs})
    form_name = raw["form"]
    form = _FORM_MAP[form_name]

    tr = tuple("/".join(_period(_ctx_of(p)[1])) for p in xptrs)

    population = None
    if xptrs:
        mems = {_member_of_ctx(_ctx_of(p)[1]) for p in xptrs}
        if len(mems) == 1 and None not in mems:
            population = "member:" + next(iter(mems))
        elif mems == {None}:
            population = "consolidated"
        else:
            population = "mixed"
    elif raw.get("member"):
        population = "member:" + raw["member"].split(":")[-1]

    normalization = raw.get("match")
    modifiers = core.Modifiers(population=population, time_range=tr, normalization=normalization)
    pointers = tuple(core.Pointer.parse(p) for p in ptrs)

    state = _state_of(raw.get("reason"), raw.get("result"))
    unverifiable_reason = None
    not_found_reason = None
    if state == "UNVERIFIABLE":
        unverifiable_reason = raw.get("reason")
    elif state == "POINTER_NOT_FOUND":
        not_found_reason = raw.get("reason")

    # C-1d §3.1: Contract.params carries the real numbers/flags the
    # registered comparators (adapters/xbrl/comparators.py) read at verify
    # time (unit_scale/claim_scale/abs_tolerance/tolerance/pure_threshold/
    # direction). This replaces the C-1c placeholder ``{"tolerance": <str>}``.
    contract = None
    if ptrs:
        if kind == "text":
            # Core 接続 C-1g §1-2: 主語が CF 流量項目の text claim は 2 本の
            # pointer(当期 fact + builtin:flow_sign(cur)==direction)。それ以外
            # は従来どおり当期・前期の 2 本 + builtin:sign(cur-prior)。
            if raw.get("flow_convention") is not None:
                comparator = "builtin:flow_sign(cur)==direction"
                params = {"direction": raw.get("direction"), "flow_convention": raw.get("flow_convention")}
            elif raw.get("expenditure_convention"):
                # Core 接続 C-1h §1-1: 「支出」系項目の text claim は当期・
                # 前期の 2 本 + builtin:sign(|cur|-|prior|)==direction(大きさ
                # の増減)。
                comparator = "builtin:sign(|cur|-|prior|)==direction"
                params = {"direction": raw.get("direction")}
            else:
                comparator = "builtin:sign(cur-prior)==direction"
                params = {"direction": raw.get("direction")}
                if raw.get("amount_in_clause") is not None:
                    # A1: 同じ節に金額が在った向きの主張だけ、符号 **と** 金額を
                    # 見る比較器に替える。金額が無い主張は今までどおり符号だけ。
                    comparator = "builtin:sign(cur-prior)==direction&amount"
                    params["unit_scale"] = raw.get("unit_scale")
                    params["claim_scale"] = raw.get("claim_scale")
                    if raw.get("rounding") is not None:
                        params["rounding"] = raw["rounding"]
                    if raw.get("magnitude_truncate"):
                        params["magnitude_truncate"] = True
        elif form_name == "direct_value":
            if raw.get("unit") not in ("%", "％", "ポイント"):
                comparator = "equals_within"
                if raw.get("unit") in ("名", "人"):
                    params = {"abs_tolerance": raw.get("abs_tolerance")}
                else:
                    params = {"unit_scale": raw.get("unit_scale"), "claim_scale": raw.get("claim_scale")}
                    if raw.get("magnitude_truncate"):
                        params["magnitude_truncate"] = True
                    # Core 接続 C-1g §1-2: CF 流量項目で向きの語がある場合だけ、
                    # equals_within に符号つきの判定を足す params を渡す。
                    if raw.get("flow_convention") is not None:
                        params["flow_convention"] = raw["flow_convention"]
                        params["claim_direction"] = raw["claim_direction"]
                    # XBRL 直し §2: 書類単位で決めた丸め方を検証時にも使う。
                    if raw.get("rounding") is not None:
                        params["rounding"] = raw["rounding"]
            else:
                comparator = "equals_within(pure*100)"
                params = {"tolerance": raw.get("pct_tolerance", PCT_TOLERANCE_DEFAULT), "pure_threshold": 1.5}
        else:
            f = others[0] if others else ""
            comparator = {
                "formula:cur/prior*100": "ratio*100",
                "formula:a/b*100": "ratio*100",  # C5(分子/分母*100。評価器は同じ)
                "formula:a-b": "diff(a-b) equals_within",
                # Core 接続 C-1g §1-3: ポイント差の derived diff。
                "formula:a-b(pure)": "diff(a-b)(pure*100)",
            }.get(f, "pct_change(cur,prior)")
            if comparator == "diff(a-b) equals_within":
                params = {"unit_scale": raw.get("unit_scale"), "claim_scale": raw.get("claim_scale")}
                # XBRL 直し §2: 書類単位で決めた丸め方を検証時にも使う。
                if raw.get("rounding") is not None:
                    params["rounding"] = raw["rounding"]
                if raw.get("magnitude_truncate"):
                    params["magnitude_truncate"] = True
            else:
                params = {"tolerance": raw.get("pct_tolerance", PCT_TOLERANCE_DEFAULT)}
        contract = core.Contract(comparator=comparator, params=params)

    provenance = {
        "kind": kind,
        "sentence": raw.get("sentence"),
        "span": raw.get("span"),
        "word": raw.get("word"),
        "value_only": (raw.get("reason") or "").startswith("value_only"),
        "diff_phrase_direct": raw.get("reason") == "diff phrase but value matched a fact",
        "sign_token": raw.get("sign_token"),
        "ambiguous_count": raw.get("ambiguous_count"),
        "member_source": raw.get("member_source"),
        "schemes": schemes,
    }

    claim = core.Claim(
        id=raw["id"], form=form, subject=raw.get("subject"), value=raw.get("value"),
        unit=raw.get("unit"), modifiers=modifiers, provenance=provenance,
    )
    return core.Recipe(
        claim=claim, pointers=pointers, contract=contract,
        unverifiable_reason=unverifiable_reason, not_found_reason=not_found_reason,
    )


def build_recipes(zb, profile, info=None):
    """1 文書・1 profile ぶんの Core Recipe の列(num の後に text。原本の
    num_claims + text_claims の順のまま)。``info`` は build_raw_claims へ素通し。
    """

    num_claims, text_claims = build_raw_claims(zb, profile, info)
    recipes = [claim_to_recipe(c, "num") for c in num_claims]
    recipes += [claim_to_recipe(c, "text") for c in text_claims]
    return recipes
