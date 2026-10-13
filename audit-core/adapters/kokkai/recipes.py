# -*- coding: utf-8 -*-
"""席の claims(要約の文 + 添えた根拠)→ Core の Recipe。

claim 1 件 → 発言者の recipe(必ず)+ 引用の recipe(quote が在れば)+ 数の
recipe(number が在れば)。``speech_order`` が無い claim は UNVERIFIABLE
``no_pointer_given``、``speaker`` が無い claim の発言者の recipe は
``no_speaker_given``。
"""

import audit_core as core

from . import numerals as N
from . import registry_setup as RS

CHECK_SPEAKER = "speaker"
CHECK_QUOTE = "quote"
CHECK_NUMBER = "number"


def _claim(cid, check, subject, value, unit, text, extra=None):
    prov = {"claim_id": cid, "check": check, "text": text}
    if extra:
        prov.update(extra)
    return core.Claim(id="%s/%s" % (cid, check), form=core.Form.DIRECT_VALUE, subject=subject,
                      value=value, unit=unit, modifiers=core.Modifiers(), provenance=prov)


def build_recipes(summary):
    """``summary`` は席の JSON(dict)。Recipe の list を返す(claims の順、check の順)。"""

    issue_id = summary.get("issueID")
    out = []
    for c in summary.get("claims") or []:
        cid = c["id"]
        text = c.get("text") or ""
        order = c.get("speech_order")
        speaker = c.get("speaker")
        quote = c.get("quote")
        number = c.get("number")

        if not isinstance(order, int) or isinstance(order, bool):
            out.append(core.Recipe(
                claim=_claim(cid, CHECK_SPEAKER, speaker, None, None, text),
                pointers=(), contract=None, unverifiable_reason=RS.NO_POINTER_GIVEN))
            continue

        pointer = core.Pointer(RS.SCHEME, "%s#%d" % (issue_id, order))

        if not isinstance(speaker, str) or speaker.strip() == "":
            out.append(core.Recipe(
                claim=_claim(cid, CHECK_SPEAKER, None, None, None, text),
                pointers=(pointer,), contract=None, unverifiable_reason=RS.NO_SPEAKER_GIVEN))
        else:
            out.append(core.Recipe(
                claim=_claim(cid, CHECK_SPEAKER, speaker, None, None, text),
                pointers=(pointer,),
                contract=core.Contract(comparator="speaker_equals", params={"expected": speaker})))

        if isinstance(quote, str) and quote.strip() != "":
            out.append(core.Recipe(
                claim=_claim(cid, CHECK_QUOTE, speaker, None, None, text, {"word": quote}),
                pointers=(pointer,),
                contract=core.Contract(comparator="quote_in_speech", params={"quote": quote})))

        if isinstance(number, dict) and number.get("value") is not None:
            unit = N.normalize_unit(number.get("unit"))
            out.append(core.Recipe(
                claim=_claim(cid, CHECK_NUMBER, speaker, float(number["value"]), unit, text,
                             {"word": number.get("text")}),
                pointers=(pointer,),
                contract=core.Contract(comparator="number_in_speech", params={"text": number.get("text")})))
    return out
