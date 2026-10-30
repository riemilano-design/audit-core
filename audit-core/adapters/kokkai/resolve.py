# -*- coding: utf-8 -*-
"""pointer(``kokkai:<issueID>#<speechOrder>``)→ 発言。無ければ ``None``(Core が
POINTER_NOT_FOUND にする)。"""


def parse_locator(locator):
    """``"<issueID>#<order>"`` → ``(issueID, order)``。形が違えば ``None``。"""

    if "#" not in locator:
        return None
    issue, order = locator.rsplit("#", 1)
    if not order.isdigit():
        return None
    return issue, int(order)


def make_resolver(meeting):
    """``meeting`` は ``load.index_meeting`` の返り値。"""

    issue_id = meeting["issueID"]
    speeches = meeting["speeches"]

    def resolver(pointer):
        from audit_core import Resolved  # Core の型を返すためだけ(将棋 adapter と同じ形)

        parsed = parse_locator(pointer.locator)
        if parsed is None:
            return None
        issue, order = parsed
        if issue != issue_id:
            return None
        s = speeches.get(order)
        if s is None:
            return None
        return Resolved(value=None, unit=None, precision=None,
                        meta={"speaker": s.get("speaker"), "speech": s.get("speech") or "",
                              "speechID": s.get("speechID"), "speechOrder": order})

    return resolver
