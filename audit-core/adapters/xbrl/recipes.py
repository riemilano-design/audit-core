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


def _apply_flow_sign(claim, s, a, b, rounding=None):
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
    conv = V.flow_convention(name)
    if conv is None:
        return
    direction = _flow_direction_word(s, claim["subject"], a, b)
    if direction is None:
        return
    claim["flow_convention"] = conv
    claim["claim_direction"] = direction
    target_abs = abs(claim["value"]) * claim["unit_scale"]
    how = V.match_value(abs(claim["recomputed"]), target_abs, claim["claim_scale"], rounding)
    if how is not None:
        claim["match"] = how


# ---------------------------------------------------------------------------
# Core 接続 C-1g §1-3(人間の決定、2026-10-06): ポイント差の derived form。
# profile.point_diff が真のときだけ使う。
# ---------------------------------------------------------------------------
_POINT_PRIOR_PHRASE_RE = re.compile(r"前期比|前連結会計年度|前年")
_POINT_DIRECTION_RE = re.compile(r"増加|増|減少|減|下回")


def _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num):
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
    claim["result"] = "GROUNDED" if abs(recomputed - claim["value"]) <= 0.15 else "VALUE_MISMATCH"


def _direct_value_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts,
                        profile=None, rounding=None):
    scale = prec if unit == "円" else V.UNIT_SCALE[unit]
    unit_scale = 1.0 if unit == "円" else V.UNIT_SCALE[unit]
    target = sign * num * unit_scale
    # C-1d §3.1 (comparators.py reads only evidence/claim.value/contract.params):
    # carry the two numbers the equals_within / diff(a-b) comparators need to
    # reproduce this function's own `scale`/`target` at verify time.
    claim["unit_scale"] = unit_scale
    claim["claim_scale"] = scale
    pool = I.facts_for(elems, facts, contexts, member) if subj else [f for f in facts if I.ctx_ok(f["context"], contexts, member)]
    pool = [f for f in pool if f["unit"] and f["unit"].upper().startswith("JPY")]
    is_diff = bool(_MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(_MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
    hits = [(f, V.match_value(f["value"], target, scale, rounding)) for f in pool]
    hits = [(f, how) for f, how in hits if how]
    if hits and not (is_diff and subj):
        fams = sorted({f["name"] for f, _ in hits})
        if subj or len(fams) == 1:
            f, how = hits[0]
            claim["pointer"] = "xbrl:%s@%s" % (f["name"], f["context"])
            claim["bound"] = True
            claim["result"] = "GROUNDED"
            claim["recomputed"] = f["value"]
            claim["match"] = how
            if not subj:
                claim["reason"] = "value_only(no subject)"
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
                    how = V.match_value(fa["value"] - fb["value"], target, scale, rounding)
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


def _dispatch_num_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts, profile,
                        rounding=None):
    """§1-2 の目標値判定を通らなかった数の Claim の、既存の単位ごとの振り分け
    (C-1d/C-1g と不変)。"""

    window_pm = s[max(0, a - 25):b + 6]
    pm = E.PCT_DIR_RE.search(window_pm) if unit in ("％", "%") else None
    if pm is not None:
        pm = E.own_sign_match(window_pm, num)  # P-8 (always applied; P1 is unaffected, see §6)
    window_pr = s[max(0, a - 12):b + 3]
    pr = E.PCT_RATIO_RE.search(window_pr) if unit in ("％", "%") and not pm else None
    if unit in ("％", "%") and pr:
        claim["form"] = "derived_value"
        if subj:
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
            pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
            pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
            if pairs:
                c, p = pairs[0]
                claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "formula:cur/prior*100"]
                claim["bound"] = True
                if p["value"] != 0:
                    ratio = c["value"] / p["value"] * 100
                    claim["recomputed"] = round(ratio, 2)
                    claim["result"] = "GROUNDED" if abs(ratio - num) <= 0.15 else "VALUE_MISMATCH"
                else:
                    claim["result"] = "UNVERIFIABLE"
                    claim["reason"] = "prior is 0"
            else:
                claim["reason"] = "no_prior_member_context" if (member and member != E.AMBIG and cur) else "no_element"
        else:
            claim["reason"] = "no_subject"
    elif unit in ("％", "%") and pm and (pm.group(4) or pm.group(7)):
        claim["form"] = "derived_value"
        sgn = 1 if (pm.group(4) or pm.group(7)) in ("増", "増加") else -1
        claim["value"] = sgn * num
        claim["sign_token"] = pm.group(0)
        if subj:
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
            pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
            pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
            if pairs:
                c, p = pairs[0]
                claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"])]
                claim["bound"] = True
                if p["value"] != 0:
                    pct = (c["value"] - p["value"]) / abs(p["value"]) * 100
                    claim["recomputed"] = round(pct, 2)
                    claim["result"] = "GROUNDED" if abs(pct - claim["value"]) <= 0.15 else "VALUE_MISMATCH"
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
            _apply_flow_sign(claim, s, a, b, rounding)
    elif unit in ("％", "%", "ポイント"):
        claim["form"] = "direct_value"
        if profile.point_diff and unit == "ポイント" and subj:
            _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num)
        elif subj and any((f["unit"] or "").lower().startswith("pure") for f in I.facts_for(elems, facts, contexts, member)):
            cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and (f["unit"] or "").lower().startswith("pure")]
            if cur:
                fv = cur[0]["value"]
                fvp = fv * 100 if abs(fv) <= 1.5 else fv
                claim["pointer"] = "xbrl:%s@%s" % (cur[0]["name"], cur[0]["context"])
                claim["bound"] = True
                claim["recomputed"] = round(fvp, 2)
                claim["result"] = "GROUNDED" if abs(fvp - num) <= 0.15 else "VALUE_MISMATCH"
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


def _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, rounding=None):
    num_claims = []
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, prec) in E.iter_numbers(s):
            member, msrc = claim_member(si, a)
            after = s[b:b + 3]
            around = s[max(0, a - 12):b + 4]
            if E.EXCLUDE_AFTER.match(after) or E.EXCLUDE_CONTEXT.search(around):
                continue
            sign = -1 if signed < 0 else 1
            num = abs(signed)
            subj, elems = E.subject_of(s, a, profile.subjects)
            claim = {
                "id": "N%03d" % (len(num_claims) + 1,), "sentence": si, "span": s[max(0, a - 30):b + 10],
                # XBRL 直し(2026-10-08): 文の中の位置。文の切り方を変える直し
                # (§4)の前後で主張を 1 対 1 に対応づけるためだけに使う計器で、
                # Claim・Recipe には写らない(claim_to_recipe は読まない)。
                "pos": a,
                "value": sign * num, "unit": unit, "subject": subj, "form": None, "pointer": None,
                "bound": False, "reason": None, "result": None, "recomputed": None,
            }
            if _target_or_plan(s, a, b, profile):
                # Core 接続 C-1h §1-2(P7)+ XBRL 直し §3(P8): 目標・計画・
                # 見込み・見通しの数は UNVERIFIABLE。
                claim["form"] = "direct_value"
                claim["result"] = "UNVERIFIABLE"
                claim["reason"] = "target_or_plan"
            else:
                _dispatch_num_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts,
                                    profile, rounding)
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


def _build_raw_text_claims(sentences, facts, contexts, profile, claim_member):
    text_claims = []
    for si, s in enumerate(sentences):
        for w, sg in E.DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
                member, msrc = claim_member(si, m.start())
                subj, elems = E.subject_of(s, m.start(), profile.subjects)
                claim = {
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": subj, "pos": m.start(),
                    "form": "threshold", "pointer": None, "bound": False, "result": None, "reason": None,
                    "direction": sg,
                }
                flow_conv = None
                if subj and profile.flow_sign:
                    for e in elems:
                        c = V.flow_convention(e)
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
                if _target_or_plan(s, m.start(), m.end(), profile):
                    # XBRL 直し §3: 向きの語の手前 10 字・後ろ 20 字(節の中)に
                    # 目標|計画|見込|見通 があれば、盤面の事実ではなく将来の
                    # 見通しなので束縛しない(「売上高の拡大を見込みます」)。
                    claim["result"] = "UNVERIFIABLE"
                    claim["reason"] = "target_or_plan"
                elif subj and flow_conv is not None:
                    # Core 接続 C-1g §1-2: 主語が CF 流量項目なら、前期との
                    # 対でなく当期 1 件の fact + builtin:flow_sign(cur)==direction
                    # で束縛する(値そのものが増減を表すので前期は要らない)。
                    cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and f["unit"] and f["unit"].upper().startswith("JPY")]
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
                    prior_paren = profile.text_prior_year_paren and _in_prior_year_paren(s, m.start())
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
                    # XBRL 直し §5: 主語が語彙に引けない向きの語は、景気や
                    # 業界についての定性的な言い回し(「わが国経済は…改善」
                    # 「役割は…拡大しております」)であって、どの行とも
                    # 照合できない。主張にしない。
                    claim["dropped"] = "qualitative(no subject)"
                text_claims.append(claim)
        for w in E.STATE_WORDS:
            for m in re.finditer(w, s):
                st = {
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": None, "pos": m.start(), "form": "threshold",
                    "pointer": None, "bound": False, "result": "UNVERIFIABLE", "reason": "state_word(no line)",
                }
                if profile.drop_qualitative:
                    # XBRL 直し §5: 状態語(堅調・不透明・回復…)は構造上どの
                    # 行にも束縛されない(``state_word(no line)``)。主張にしない。
                    st["dropped"] = "qualitative(state word)"
                text_claims.append(st)
    # 番号を振った**後に**落とす ― ID は欠番になるが、直す前との対応づけが
    # ずれない(落とした件数と ID を結果に書けるようにするため)。
    if profile.drop_qualitative:
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
    sent_member = E.resolve_members(sentences, paras, reg)
    return sent_member, reg


def build_raw_claims(zb, profile, info=None):
    """1 文書・1 profile ぶんの、原本と同じ形(辞書)の num_claims / text_claims
    を作る。recipes.to_recipes の前段(確認・再現がしやすいように分けておく)。

    ``info`` に辞書を渡すと、測るのに要る数(文の数・決めた丸め方とその根拠)
    をそこに書き込む。渡さなければ何もしない(既存の呼び出しは不変)。
    """

    inst = I.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    mdna_name = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna_name]) if mdna_name else ""
    sentences = E.split_sentences(text, profile.paren_sentence)
    sent_member, reg = _member_material(zb, inst, text, sentences, profile)

    def claim_member(si, pos):
        if not (profile.member_on and profile.claim_level_member):
            return sent_member[si]
        return E.claim_member_B(sentences[si], pos, reg, sent_member[si])

    num_claims = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member)
    rounding = None
    if profile.doc_rounding:
        # XBRL 直し §2: 1 周目(今までの梯子)で根拠を数え、書類の丸め方を
        # 1 つに決め、2 周目はその 1 つだけで照合し直す。
        rounding, r_only, t_only = V.decide_rounding(_rounding_evidence(num_claims))
        num_claims = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, rounding)
        if info is not None:
            info["rounding_round_only"] = r_only
            info["rounding_truncate_only"] = t_only
    text_claims = _build_raw_text_claims(sentences, facts, contexts, profile, claim_member)
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
        elif form_name == "direct_value":
            if raw.get("unit") not in ("%", "％", "ポイント"):
                comparator = "equals_within"
                if raw.get("unit") in ("名", "人"):
                    params = {"abs_tolerance": raw.get("abs_tolerance")}
                else:
                    params = {"unit_scale": raw.get("unit_scale"), "claim_scale": raw.get("claim_scale")}
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
                params = {"tolerance": 0.15, "pure_threshold": 1.5}
        else:
            f = others[0] if others else ""
            comparator = {
                "formula:cur/prior*100": "ratio*100",
                "formula:a-b": "diff(a-b) equals_within",
                # Core 接続 C-1g §1-3: ポイント差の derived diff。
                "formula:a-b(pure)": "diff(a-b)(pure*100)",
            }.get(f, "pct_change(cur,prior)")
            if comparator == "diff(a-b) equals_within":
                params = {"unit_scale": raw.get("unit_scale"), "claim_scale": raw.get("claim_scale")}
                # XBRL 直し §2: 書類単位で決めた丸め方を検証時にも使う。
                if raw.get("rounding") is not None:
                    params["rounding"] = raw["rounding"]
            else:
                params = {"tolerance": 0.15}
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
