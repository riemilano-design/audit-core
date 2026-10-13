# -*- coding: utf-8 -*-
"""会議録 JSON(API の応答そのまま)→ 発言の索引。"""

import json


def load_meeting(path):
    """JSON を読んで ``{"issueID", "meta", "speeches"}`` を返す。
    ``speeches`` は ``speechOrder``(int)→ 発言 dict。"""

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return index_meeting(data)


def index_meeting(data):
    records = data.get("meetingRecord") or []
    if len(records) != 1:
        raise ValueError("meetingRecord は 1 件を想定: %d 件" % len(records))
    m = records[0]
    speeches = {}
    for s in m.get("speechRecord") or []:
        order = int(s["speechOrder"])
        if order in speeches:
            raise ValueError("speechOrder が重複: %d" % order)
        speeches[order] = s
    meta = {k: m.get(k) for k in ("issueID", "nameOfHouse", "nameOfMeeting", "issue", "date", "session")}
    return {"issueID": m.get("issueID"), "meta": meta, "speeches": speeches}
