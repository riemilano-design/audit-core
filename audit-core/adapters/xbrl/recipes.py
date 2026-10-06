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


def _apply_flow_sign(claim, s, a, b):
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
    how = V.match_value(abs(claim["recomputed"]), target_abs, claim["claim_scale"])
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


def _direct_value_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts):
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
    hits = [(f, V.match_value(f["value"], target, scale)) for f in pool]
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
                    how = V.match_value(fa["value"] - fb["value"], target, scale)
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
                claim["pointer"] = "xbrl:%s@%s" % (cur[0]["name"], cur[0]["context"])
                claim["bound"] = True
                claim["result"] = "VALUE_MISMATCH"
                claim["recomputed"] = cur[0]["value"]
                claim["reason"] = "value differs(segment/other period?)"
            else:
                claim["reason"] = "no_element"
    else:
        claim["reason"] = "no_element"


def _build_raw_num_claims(sentences, facts, contexts, profile, claim_member):
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
                "value": sign * num, "unit": unit, "subject": subj, "form": None, "pointer": None,
                "bound": False, "reason": None, "result": None, "recomputed": None,
            }
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
                _direct_value_claim(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts)
                if profile.flow_sign:
                    _apply_flow_sign(claim, s, a, b)
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
            if profile.member_on:
                if msrc == "ambiguous" and not claim["bound"]:
                    claim["reason"] = "ambiguous(member)"
                claim["member"] = None if member == E.AMBIG else member
                claim["member_source"] = msrc
            num_claims.append(claim)
    return num_claims


def _build_raw_text_claims(sentences, facts, contexts, profile, claim_member):
    text_claims = []
    for si, s in enumerate(sentences):
        for w, sg in E.DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
                member, msrc = claim_member(si, m.start())
                subj, elems = E.subject_of(s, m.start(), profile.subjects)
                claim = {
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": subj,
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
                if subj and flow_conv is not None:
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
                elif subj:
                    cur = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pri = [f for f in I.facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = ["xbrl:%s@%s" % (c["name"], c["context"]), "xbrl:%s@%s" % (p["name"], p["context"]), "builtin:sign(cur-prior)"]
                        claim["bound"] = True
                        actual = 1 if c["value"] - p["value"] > 0 else -1
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = c["value"] - p["value"]
                    else:
                        claim["reason"] = "no_prior_member_context" if (member and member != E.AMBIG and cur) else "no_element"
                else:
                    claim["reason"] = "no_subject"
                if profile.member_on:
                    if msrc == "ambiguous" and not claim["bound"]:
                        claim["reason"] = "ambiguous(member)"
                    claim["member"] = None if member == E.AMBIG else member
                    claim["member_source"] = msrc
                text_claims.append(claim)
        for w in E.STATE_WORDS:
            for m in re.finditer(w, s):
                text_claims.append({
                    "id": "T%03d" % (len(text_claims) + 1,), "sentence": si, "word": w,
                    "span": s[max(0, m.start() - 30):m.end() + 5], "subject": None, "form": "threshold",
                    "pointer": None, "bound": False, "result": "UNVERIFIABLE", "reason": "state_word(no line)",
                })
    return text_claims


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
    paras = E.paragraph_index(text, sentences)
    sent_member = E.resolve_members(sentences, paras, reg)
    return sent_member, reg


def build_raw_claims(zb, profile):
    """1 文書・1 profile ぶんの、原本と同じ形(辞書)の num_claims / text_claims
    を作る。recipes.to_recipes の前段(確認・再現がしやすいように分けておく)。
    """

    inst = I.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    mdna_name = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna_name]) if mdna_name else ""
    sentences = E.split_sentences(text)
    sent_member, reg = _member_material(zb, inst, text, sentences, profile)

    def claim_member(si, pos):
        if not (profile.member_on and profile.claim_level_member):
            return sent_member[si]
        return E.claim_member_B(sentences[si], pos, reg, sent_member[si])

    num_claims = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member)
    text_claims = _build_raw_text_claims(sentences, facts, contexts, profile, claim_member)
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


def build_recipes(zb, profile):
    """1 文書・1 profile ぶんの Core Recipe の列(num の後に text。原本の
    num_claims + text_claims の順のまま)。
    """

    num_claims, text_claims = build_raw_claims(zb, profile)
    recipes = [claim_to_recipe(c, "num") for c in num_claims]
    recipes += [claim_to_recipe(c, "text") for c in text_claims]
    return recipes
