# -*- coding: utf-8 -*-
"""**他の席が封じた材料を取らないための、唯一の関門。**

EDINET から ZIP を取る道具は **5 つ**ある(2026-10-09 に 4 つ数え、2026-10-13 の
merge で main 側の 1 つが加わった):

    fixtures/xbrl/fetch_new_draw_2026-10-09.py        名前で選ぶ(記録の picked)
    fixtures/xbrl/fetch_allocated_2026-10-08.py       名前で選ぶ(記録の assigned)
    fixtures/xbrl/fetch_sealed_material_2026-10-09.py 名前で選ぶ(字の一覧 4 件。人間が回す)
    fixtures/xbrl/xbrl_probe.py                       **日付で選ぶ**(docID 順に 1 件ずつ取る)
    fixtures/xbrl/select_third_2026-10-01.py          **日付で選ぶ**(共有キャッシュに書く)

**名前の一覧だけでは、日付で選ぶ 2 つを原理的に守れない。**
だから関門は **docID と日付の両方**を持ち、**取る直前に呼ぶ。**

**import は呼び出しではない**(本線の席の指摘、2026-10-09)。
この module を import しただけでは何も守られない ―
``refuse_if_sealed()`` を **urlopen の前に呼ぶ**こと。
呼んでいるかは ``tests/adapters/xbrl/test_fetch_gate.py`` が木を歩いて照合する。

**封の一覧の正本は ``fixtures/xbrl/holdout_reserved_2026-10-12.json``(D-002)。**
ここは字で写す。写しが正本とずれたら ``test_fetch_gate`` が赤くなる。

通信しない。ファイルを書かない。
"""

# 外すときは、**その封を持っている席からの依頼**と理由を行に書くこと。
#
# 2026-10-13(merge の整合): この関門は fix5 枝で 2026-10-09 に書かれ、当時の封A/封B
# の 4 件(S100Z3JY・S100Z35K・S100Z3V1・S100Z3HP)を持っていた。その 4 件は main 側で
# 人間が fetch_sealed_material_2026-10-09.py で取り(記録 fetched_sealed_2026-10-09.json)、
# docs/NORMALIZATION_SEAL_A_RESULT_2026-10-09.md と docs/SIGN_SEAL_B_RESULT_2026-10-09.md で
# 開封・測定済み。いま封じられているのは D-002 の手順 4 専用 2 件だけ
# (fixtures/xbrl/holdout_reserved_2026-10-12.json)。
SEALED_DOCS = {
    "S100Z39P": "手順 4(未使用の書類で過適合を測る)専用。D-002 2026-10-12。独立監査 GO まで開かない",
    "S100Z4N9": "手順 4(未使用の書類で過適合を測る)専用。D-002 2026-10-12。独立監査 GO まで開かない",
}

# 履歴(関門は見ない)。2026-10-09 の封で、2026-10-09〜12 に開封済み。
OPENED_FORMER_SEALS = {
    "S100Z3JY": "封A 2026-10-09 → NORMALIZATION_SEAL_A_RESULT_2026-10-09.md",
    "S100Z35K": "封A 2026-10-09 → NORMALIZATION_SEAL_A_RESULT_2026-10-09.md",
    "S100Z3V1": "封B 2026-10-09 → SIGN_SEAL_B_RESULT_2026-10-09.md",
    "S100Z3HP": "封B 2026-10-09 → SIGN_SEAL_B_RESULT_2026-10-09.md",
}

# **日付で選ぶ道具のための錠。**
# 提出日は fixtures/xbrl/candidates_2026-09.json の date。
# S100Z39P = 2026-09-24(株式会社インテージホールディングス)、
# S100Z4N9 = 2026-09-28(トラストホールディングス株式会社)。
# この 2 日を渡すと、名前を指定しなくても到達しうる(docID 順に 1 件ずつ取るので)。
SEALED_DATES = {
    "2026-09-24": "手順 4 専用の S100Z39P がこの日の提出。日付で選ぶ道具から到達しうる",
    "2026-09-28": "手順 4 専用の S100Z4N9 がこの日の提出。日付で選ぶ道具から到達しうる",
}


class SealedMaterial(Exception):
    """封じた材料に触ろうとした。**取得は起きていない。**"""


def refuse_if_sealed(doc_id=None, date=None, where=""):
    """封じた材料なら **例外で止める**。取る直前に呼ぶこと。

    ``doc_id`` も ``date`` も省略可。**両方 None で呼ぶのは誤り**
    (守っているつもりで何も見ていない形になるので、それも止める)。
    """

    if doc_id is None and date is None:
        raise SealedMaterial(
            "refuse_if_sealed() を doc_id も date も無しで呼んでいる(%s)― "
            "何も照合していない" % (where or "呼び出し元不明",))
    if doc_id is not None and doc_id in SEALED_DOCS:
        raise SealedMaterial(
            "**取らない**: %s は他の席が封じた材料(%s)。呼び出し元 %s。"
            "席の間で承認は渡せない" % (doc_id, SEALED_DOCS[doc_id], where or "不明"))
    if date is not None:
        d = str(date)[:10].replace("/", "-")
        if d in SEALED_DATES:
            raise SealedMaterial(
                "**取らない**: %s は封じた日付(%s)。呼び出し元 %s。"
                "日付で選ぶ道具は名前を指定しなくても封じた材料に到達しうる"
                % (d, SEALED_DATES[d], where or "不明"))
    return None
