# -*- coding: utf-8 -*-
"""合成の会議録(通信しない・実物を読まない)。試験と変異の共通の土台。"""

ISSUE = "TEST0001"

MEETING = {
    "meetingRecord": [{
        "issueID": ISSUE, "nameOfHouse": "衆議院", "nameOfMeeting": "試験委員会", "issue": "第1号",
        "date": "2026-01-01", "session": 1,
        "speechRecord": [
            {"speechID": ISSUE + "_000", "speechOrder": 0, "speaker": "会議録情報", "speech": "出席委員　甲　乙"},
            {"speechID": ISSUE + "_001", "speechOrder": 1, "speaker": "山田太郎",
             "speech": "○山田委員　暫定予算は三百億円で、期間は一か月であります。\r\n　令和八年の話です。"},
            {"speechID": ISSUE + "_002", "speechOrder": 2, "speaker": "佐藤花子",
             "speech": "○佐藤国務大臣　一・一兆円の規模で、一五％の伸びです。一九九一年以来であります。"},
            {"speechID": ISSUE + "_003", "speechOrder": 3, "speaker": "山田太郎",
             "speech": "○山田委員　三回目の質問です。"},
        ],
    }],
}


def summary(claims):
    return {"issueID": ISSUE, "written_by": "試験", "claims": claims}


def claim(cid, order=1, speaker="山田太郎", text="文", quote=None, number=None):
    c = {"id": cid, "text": text, "speech_order": order, "speaker": speaker}
    if quote is not None:
        c["quote"] = quote
    if number is not None:
        c["number"] = number
    return c
